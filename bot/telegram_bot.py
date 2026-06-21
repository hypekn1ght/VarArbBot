import logging
from datetime import datetime, timezone
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from bot import config
from bot import state as state_module
from bot.alerts import CONDITIONS, Condition, evaluate
from bot.prices import get_xau_price
from bot.spreads import mark_spread
from bot.variational import Listing, fetch_listings, is_stale

logger = logging.getLogger(__name__)

REF_URL = "https://omni.variational.io/?ref=OMNIA5"


def build_keyboard(cond: Condition) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(f"Short {cond.short_leg}", url=REF_URL),
        InlineKeyboardButton(f"Long {cond.long_leg}",  url=REF_URL),
    ]])


def build_message(
    cond: Condition,
    paxg_mark: Decimal,
    xaut_mark: Decimal,
    xau_mark: Decimal,
    spread_paxg_xaut: Decimal,
    spread_xau_xaut: Decimal,
    stale: bool,
) -> str:
    stale_banner = "⚠️ *STALE QUOTE DATA*\n\n" if stale else ""
    direction = ">" if cond.direction == "above" else "<"
    label = cond.key.replace("_", " ")
    return (
        f"{stale_banner}"
        f"{cond.alert_emoji} *{label}*\n"
        f"Spread {direction} {cond.threshold}\n\n"
        f"*Prices*\n"
        f"PAXG: `{paxg_mark}`\n"
        f"XAUT: `{xaut_mark}`\n"
        f"XAU:  `{xau_mark}`\n\n"
        f"*Spreads*\n"
        f"PAXG − XAUT: `{spread_paxg_xaut}`\n"
        f"XAU  − XAUT: `{spread_xau_xaut}`"
    )


async def poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    bot = context.bot
    app_state = context.bot_data["state"]
    chat_ids  = context.bot_data["chat_ids"]

    try:
        listings = await fetch_listings()
    except Exception as e:
        logger.error(f"Failed to fetch listings: {e}")
        return

    try:
        paxg = listings[config.TICKER_MAP["PAXG"]]
        xaut = listings[config.TICKER_MAP["XAUT"]]
    except KeyError as e:
        logger.error(f"Required ticker missing from API response: {e}")
        return

    try:
        xau_mark = await get_xau_price(listings)
    except Exception as e:
        logger.error(f"XAU price fetch failed: {e}")
        return

    stale = is_stale(paxg, config.MAX_QUOTE_AGE_S) or is_stale(xaut, config.MAX_QUOTE_AGE_S)

    spread_paxg_xaut = mark_spread(paxg, xaut)

    xau_listing = Listing(
        ticker="XAU", mark=xau_mark,
        bid_1k=None, ask_1k=None, updated_at=None,
    )
    spread_xau_xaut = mark_spread(xau_listing, xaut)

    spread_map = {
        ("PAXG", "XAUT"): spread_paxg_xaut,
        ("XAU",  "XAUT"): spread_xau_xaut,
    }

    for cond in CONDITIONS:
        value = spread_map[cond.pair]
        cs    = app_state[cond.key]
        armed = cs["armed"]

        if not state_module.is_cooled_down(app_state, cond.key, config.COOLDOWN_S):
            continue

        should_fire, new_armed = evaluate(cond, value, armed)
        cs["armed"] = new_armed

        if should_fire:
            cs["last_fired"] = datetime.now(timezone.utc).isoformat()
            text = build_message(
                cond,
                paxg.mark, xaut.mark, xau_mark,
                spread_paxg_xaut, spread_xau_xaut,
                stale,
            )
            kb = build_keyboard(cond)
            for chat_id in chat_ids:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode="Markdown",
                        reply_markup=kb,
                    )
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")

    state_module.save(app_state)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.effective_chat.id
    chat_ids = context.bot_data["chat_ids"]
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        logger.info(f"New subscriber: {chat_id}")
    await update.message.reply_text(
        f"✅ *Variational Spread Bot active*\n\n"
        f"Polling every `{config.POLL_SECONDS}s` ({config.POLL_SECONDS // 60} min)\n\n"
        f"*Thresholds*\n"
        f"PAXG−XAUT › `{config.PAXG_XAUT_HIGH}` or ‹ `{config.PAXG_XAUT_LOW}`\n"
        f"XAU−XAUT  › `{config.XAU_XAUT_HIGH}` or ‹ `{config.XAU_XAUT_LOW}`\n\n"
        f"Chat ID: `{chat_id}`",
        parse_mode="Markdown",
    )


def build_app(initial_state: dict, initial_chat_ids: list) -> Application:
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data["state"]    = initial_state
    app.bot_data["chat_ids"] = initial_chat_ids
    app.add_handler(CommandHandler("start", start))
    app.job_queue.run_repeating(poll_job, interval=config.POLL_SECONDS, first=5)
    return app
