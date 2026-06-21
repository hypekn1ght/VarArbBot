from decimal import Decimal

from bot.variational import Listing
from bot import config


async def get_xau_price(listings: dict[str, Listing]) -> Decimal:
    if config.XAU_SOURCE == "variational":
        ticker = config.TICKER_MAP["XAU"]
        return listings[ticker].mark
    else:
        return await _fetch_external_xau()


async def _fetch_external_xau() -> Decimal:
    # STUB: implement if XAU is not on Variational.
    # Example providers: metals-api.com, goldapi.io, frankfurter.app (XAU/USD)
    # Most require an API key set as GOLD_API_KEY in .env.
    #
    # Example (goldapi.io):
    #   import httpx
    #   async with httpx.AsyncClient(timeout=10) as c:
    #       r = await c.get(
    #           "https://www.goldapi.io/api/XAU/USD",
    #           headers={"x-access-token": config.GOLD_API_KEY},
    #       )
    #       r.raise_for_status()
    #       return Decimal(str(r.json()["price"]))
    raise NotImplementedError(
        "External XAU feed not implemented. "
        "Set XAU_SOURCE=variational or implement _fetch_external_xau()."
    )
