from datetime import UTC, datetime

from app.models.enums import AssetClass
from app.services.session import session_close_as_of, session_info, venue_key


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
    assert info.freshness_label == "letzter Schluss"


def test_stale_print_is_not_today() -> None:
    now = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)
    last = datetime(2026, 8, 27, 15, 30, tzinfo=UTC)
    info = session_info("VWCE.L", AssetClass.ETF, now=now, last_print=last)
    assert info.market_open is False
    assert info.session_label == "kein Kurs von heute"


def test_daily_midnight_maps_to_session_close() -> None:
    midnight = datetime(2026, 8, 28, 4, 0, tzinfo=UTC)
    close = session_close_as_of(midnight, "US")
    assert close.astimezone(UTC).hour == 20
