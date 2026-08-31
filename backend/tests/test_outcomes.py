from datetime import UTC, datetime, timedelta

from app.services.outcomes import close_after_trading_days, compute_horizons, return_pct


def _series(start: datetime, n: int, first: float = 100.0, step: float = 1.0):
    return [(start + timedelta(days=i), first + i * step) for i in range(n)]


def test_return_pct() -> None:
    assert return_pct(100, 110) == 10.0
    assert return_pct(100, 90) == -10.0
    assert return_pct(0, 10) is None
    assert return_pct(100, None) is None


def test_close_after_trading_days_skips_pre_start() -> None:
    start = datetime(2026, 1, 10, tzinfo=UTC)
    closes = _series(datetime(2026, 1, 1, tzinfo=UTC), 20, first=50)
    assert close_after_trading_days(closes, start, 0) == 59
    assert close_after_trading_days(closes, start, 5) == 64
    assert close_after_trading_days(closes, start, 60) is None


def test_horizons_vs_benchmark() -> None:
    start = datetime(2026, 3, 1, tzinfo=UTC)
    asset = _series(start, 70, first=100, step=1)
    bench = _series(start, 70, first=200, step=0.5)
    out = compute_horizons(entry=100, start=start, asset_closes=asset, bench_closes=bench, bench_entry=200)
    assert out["ret_5d"] == 5.0
    assert out["ret_20d"] == 20.0
    assert out["ret_60d"] == 60.0
    assert out["bench_5d"] == 1.25
    assert abs(out["bench_20d"] - 5.0) < 1e-9
