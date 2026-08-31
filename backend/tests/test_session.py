from datetime import UTC, datetime

from app.models.enums import AssetClass
from app.services.session import session_info, venue_key


def test_venue_from_suffix() -> None:
    assert venue_key("VWCE.DE") == "XETRA"
    assert venue_key("NESN.SW") == "SIX"
    assert venue_key("AAPL") == "US"


def test_crypto_always_open() -> None:
    info = session_info("BTC-USD", AssetClass.CRYPTO)
    assert info.market_open is True
    assert info.delayed is False
    assert info.session_label == "24h offen"


def test_us_closed_on_sunday() -> None:
    sunday = datetime(2026, 8, 30, 16, 0, tzinfo=UTC)
    info = session_info("AAPL", AssetClass.STOCK, now=sunday)
    assert info.delayed is True
    assert info.market_open is False
    assert "geschlossen" in info.session_label
