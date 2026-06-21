import os
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_IDS = [int(x) for x in os.getenv("CHAT_IDS", "").split(",") if x.strip()]

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "300"))
MAX_QUOTE_AGE_S = int(os.getenv("MAX_QUOTE_AGE_S", "120"))

TICKER_MAP = {
    "PAXG": os.getenv("TICKER_PAXG", "PAXG"),
    "XAUT": os.getenv("TICKER_XAUT", "XAUT"),
    "XAU":  os.getenv("TICKER_XAU",  "XAU"),
}

XAU_SOURCE = os.getenv("XAU_SOURCE", "variational")  # variational | external
GOLD_API_KEY = os.getenv("GOLD_API_KEY", "")

PAXG_XAUT_HIGH = Decimal(os.getenv("PAXG_XAUT_HIGH", "20"))
PAXG_XAUT_LOW  = Decimal(os.getenv("PAXG_XAUT_LOW",  "10"))
XAU_XAUT_HIGH  = Decimal(os.getenv("XAU_XAUT_HIGH",  "17"))
XAU_XAUT_LOW   = Decimal(os.getenv("XAU_XAUT_LOW",   "7"))
RESET_BUFFER   = Decimal(os.getenv("RESET_BUFFER",    "2"))
COOLDOWN_S     = int(os.getenv("COOLDOWN_S", "900"))

if POLL_SECONDS < 30:
    print(f"WARNING: POLL_SECONDS={POLL_SECONDS} is very aggressive. "
          f"Variational quotes cache up to 600s. Recommended minimum: 60.")
