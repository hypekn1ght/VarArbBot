import asyncio
import logging

from bot import config
from bot import state as state_module
from bot.variational import fetch_listings, validate_tickers
from bot.telegram_bot import build_app

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)


async def startup_check() -> None:
    listings = await fetch_listings()
    tickers_to_check = {
        k: v for k, v in config.TICKER_MAP.items()
        if not (k == "XAU" and config.XAU_SOURCE == "external")
    }
    await validate_tickers(listings, tickers_to_check)


def main() -> None:
    asyncio.get_event_loop().run_until_complete(startup_check())
    loaded_state = state_module.load()
    chat_ids = list(config.CHAT_IDS)
    app = build_app(initial_state=loaded_state, initial_chat_ids=chat_ids)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
