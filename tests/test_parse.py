import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from bot.variational import fetch_listings, Listing, is_stale


MOCK_RESPONSE = {
    "num_markets": 2,
    "listings": [
        {
            "ticker": "PAXG",
            "name": "PAX Gold",
            "mark_price": "3342.50",
            "quotes": {
                "size_1k": {"bid": "3341.00", "ask": "3344.00"},
                "updated_at": "2024-01-15T12:00:00Z",
            },
        },
        {
            "ticker": "XAUT",
            "name": "Tether Gold",
            "mark_price": "3319.80",
            "quotes": {
                "size_1k": {"bid": "3318.50", "ask": "3321.10"},
                "updated_at": "2024-01-15T12:01:00Z",
            },
        },
        {
            # Listing with no quotes block
            "ticker": "NOQUOTE",
            "name": "No Quote Token",
            "mark_price": "100.00",
        },
    ],
}


@pytest.mark.asyncio
async def test_fetch_listings_parses_decimals():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json.return_value = MOCK_RESPONSE

    with patch("bot.variational.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        listings = await fetch_listings()

    paxg = listings["PAXG"]
    assert isinstance(paxg.mark, Decimal)
    assert paxg.mark == Decimal("3342.50")
    assert isinstance(paxg.bid_1k, Decimal)
    assert paxg.bid_1k == Decimal("3341.00")
    assert isinstance(paxg.ask_1k, Decimal)
    assert paxg.ask_1k == Decimal("3344.00")

    # No float anywhere
    assert type(paxg.mark) is Decimal
    assert type(paxg.bid_1k) is Decimal


@pytest.mark.asyncio
async def test_fetch_listings_parses_updated_at():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json.return_value = MOCK_RESPONSE

    with patch("bot.variational.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        listings = await fetch_listings()

    paxg = listings["PAXG"]
    assert isinstance(paxg.updated_at, datetime)
    assert paxg.updated_at.tzinfo is not None  # timezone-aware


@pytest.mark.asyncio
async def test_fetch_listings_handles_missing_quotes():
    mock_resp = MagicMock()
    mock_resp.raise_for_status = lambda: None
    mock_resp.json.return_value = MOCK_RESPONSE

    with patch("bot.variational.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        listings = await fetch_listings()

    nq = listings["NOQUOTE"]
    assert nq.bid_1k is None
    assert nq.ask_1k is None
    assert nq.updated_at is None
    assert nq.mark == Decimal("100.00")


def test_is_stale_no_updated_at():
    listing = Listing(ticker="X", mark=Decimal("1"), bid_1k=None, ask_1k=None, updated_at=None)
    assert is_stale(listing, max_age_s=120) is True


def test_is_stale_fresh():
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    listing = Listing(
        ticker="X", mark=Decimal("1"), bid_1k=None, ask_1k=None,
        updated_at=now - timedelta(seconds=60),
    )
    assert is_stale(listing, max_age_s=120) is False


def test_is_stale_old():
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    listing = Listing(
        ticker="X", mark=Decimal("1"), bid_1k=None, ask_1k=None,
        updated_at=now - timedelta(seconds=200),
    )
    assert is_stale(listing, max_age_s=120) is True
