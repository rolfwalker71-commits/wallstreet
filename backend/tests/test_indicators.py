import pandas as pd

from app.services.indicators import compute_technicals, rsi


def test_rsi_bounds() -> None:
    closes = pd.Series(
        [100, 102, 101, 103, 99, 98, 100, 104, 107, 105, 106, 108, 110, 109, 111, 108, 112],
        dtype=float,
    )
    value = rsi(closes, 14)
    assert value is not None
    assert 0 <= value <= 100


def test_rsi_all_up() -> None:
    closes = pd.Series([100.0 + i for i in range(20)])
    assert rsi(closes, 14) == 100.0


def test_technicals_keys() -> None:
    closes = pd.Series([float(100 + (i % 5)) for i in range(80)])
    data = compute_technicals(closes)
    assert "rsi_14" in data
    assert "macd" in data
    assert data["last_close"] == float(closes.iloc[-1])