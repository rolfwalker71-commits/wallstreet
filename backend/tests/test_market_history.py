from app.services.market import PERIOD_INTERVAL, resolve_history_period


def test_resolve_known_periods() -> None:
    assert resolve_history_period("1d") == "1d"
    assert resolve_history_period("5d") == "5d"
    assert resolve_history_period("1mo") == "1mo"
    assert resolve_history_period("3mo") == "3mo"
    assert resolve_history_period("6mo") == "6mo"
    assert resolve_history_period("1y") == "1y"
    assert resolve_history_period("5y") == "5y"


def test_resolve_unknown_falls_back() -> None:
    assert resolve_history_period("max") == "6mo"
    assert resolve_history_period("") == "6mo"


def test_intraday_intervals() -> None:
    assert PERIOD_INTERVAL["1d"] == "5m"
    assert PERIOD_INTERVAL["5d"] == "30m"
    assert PERIOD_INTERVAL["1mo"] == "1d"
    assert PERIOD_INTERVAL["5y"] == "1d"
