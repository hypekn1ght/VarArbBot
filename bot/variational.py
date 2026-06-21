from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

import httpx

BASE_URL = "https://omni-client-api.prod.ap-northeast-1.variational.io"


@dataclass
class Listing:
    ticker: str
    mark: Decimal
    bid_1k: Optional[Decimal]
    ask_1k: Optional[Decimal]
    updated_at: Optional[datetime]


async def fetch_listings() -> dict[str, "Listing"]:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{BASE_URL}/metadata/stats")
        r.raise_for_status()
        data = r.json()
    out: dict[str, Listing] = {}
    for l in data["listings"]:
        q   = l.get("quotes") or {}
        s1k = q.get("size_1k") or {}
        ts  = q.get("updated_at")
        out[l["ticker"]] = Listing(
            ticker     = l["ticker"],
            mark       = Decimal(str(l["mark_price"])),
            bid_1k     = Decimal(str(s1k["bid"])) if s1k.get("bid") else None,
            ask_1k     = Decimal(str(s1k["ask"])) if s1k.get("ask") else None,
            updated_at = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None,
        )
    return out


def is_stale(listing: Listing, max_age_s: int) -> bool:
    if listing.updated_at is None:
        return True
    age = (datetime.now(timezone.utc) - listing.updated_at).total_seconds()
    return age > max_age_s


async def validate_tickers(listings: dict, ticker_map: dict) -> None:
    """Raises SystemExit if any required ticker is missing from the API response."""
    missing = [logical for logical, real in ticker_map.items() if real not in listings]
    if missing:
        sample = sorted(listings.keys())[:60]
        raise SystemExit(
            f"\n[FATAL] Tickers not found on Variational: {missing}\n"
            f"Available tickers (first 60): {sample}\n"
            f"Fix TICKER_MAP in .env or set XAU_SOURCE=external.\n"
        )
