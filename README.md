# Variational Spread Bot

Telegram bot that polls the Variational Omni API and sends alerts when gold-perpetual spreads cross defined thresholds.

## Setup

### 1. Verify tickers (run once)
```bash
pip install httpx
python probe.py   # run from repo root (ArbNotifBot/)
```
Check the output. If `XAU` is absent, set `TICKER_XAU=GOLD` (or the correct value) in `.env`, or set `XAU_SOURCE=external` and implement `_fetch_external_xau()` in `bot/prices.py`.

### 2. Install dependencies
```bash
cd variational-spread-bot
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN and leave CHAT_IDS blank for now
```

### 4. Run
```bash
python -m bot.main
```
Send `/start` to your bot from Telegram — it will print your chat ID and add you as a subscriber.

### 5. Tests
```bash
pytest tests/
```

## Docker
```bash
docker build -t spread-bot .
docker run --env-file .env -v $(pwd)/state.json:/app/state.json spread-bot
```

## Alert conditions

| Condition | Fires when | Trade |
|---|---|---|
| PAXG_XAUT_HIGH | PAXG − XAUT > $20 | Short PAXG / Long XAUT |
| PAXG_XAUT_LOW | PAXG − XAUT < $10 | Short XAUT / Long PAXG |
| XAU_XAUT_HIGH | XAU − XAUT > $17 | Short XAU / Long XAUT |
| XAU_XAUT_LOW | XAU − XAUT < $7 | Short XAUT / Long XAU |

Hysteresis: each condition fires once, then re-arms only after the spread retreats by `RESET_BUFFER` ($2 default). A hard `COOLDOWN_S` (15 min default) prevents re-fire even if hysteresis misfires.

## State persistence

`state.json` is written after every poll. On restart, armed/last_fired state is restored — a restart mid-extreme-spread won't re-fire or lose re-arm progress.
