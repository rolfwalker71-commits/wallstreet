from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.models import Portfolio
from app.models.enums import TransactionSide
from app.services.market import fetch_history

BENCH_SYMBOL = "VWCE.DE"


def _closes(symbol: str, period: str = "2y") -> dict[str, float]:
    hist = fetch_history(symbol, period=period)
    if hist is None or hist.empty or "Close" not in hist:
        return {}
    out: dict[str, float] = {}
    for idx, close in hist["Close"].dropna().items():
        ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
        if isinstance(ts, datetime):
            out[ts.date().isoformat()] = float(close)
        else:
            out[str(idx)[:10]] = float(close)
    return out


def _ffill(dates: list[str], series: dict[str, float]) -> dict[str, float | None]:
    last: float | None = None
    filled: dict[str, float | None] = {}
    for day in dates:
        if day in series:
            last = series[day]
        filled[day] = last
    return filled


def replay_equity(
    *,
    initial_cash: float,
    transactions: list[dict[str, Any]],
    price_by_symbol: dict[str, dict[str, float]],
    bench_prices: dict[str, float],
) -> list[dict[str, Any]]:
    """Tägliche Depotkurve vs. Benchmark, beide auf 100 am Start normiert."""
    if not transactions:
        return []
    days = sorted({tx["date"][:10] for tx in transactions})
    all_days: set[str] = set()
    for series in price_by_symbol.values():
        all_days.update(series)
    all_days.update(bench_prices)
    start = days[0]
    dates = sorted(d for d in all_days if d >= start)
    if not dates:
        dates = days

    txs_by_day: dict[str, list[dict[str, Any]]] = {}
    for tx in sorted(transactions, key=lambda t: t["date"]):
        txs_by_day.setdefault(tx["date"][:10], []).append(tx)

    filled = {sym: _ffill(dates, series) for sym, series in price_by_symbol.items()}
    bench_filled = _ffill(dates, bench_prices)

    cash = initial_cash
    qty: dict[str, float] = {}
    points: list[dict[str, Any]] = []
    start_equity: float | None = None
    start_bench: float | None = None

    for day in dates:
        for tx in txs_by_day.get(day, []):
            symbol = tx["symbol"]
            q = float(tx["qty"])
            price = float(tx["price"])
            if tx["side"] == "buy":
                cash -= q * price
                qty[symbol] = qty.get(symbol, 0.0) + q
            elif tx["side"] == "sell":
                cash += q * price
                qty[symbol] = qty.get(symbol, 0.0) - q
        holdings = 0.0
        for symbol, amount in qty.items():
            if amount <= 0:
                continue
            px = filled.get(symbol, {}).get(day)
            if px is None:
                continue
            holdings += amount * px
        equity = cash + holdings
        bench = bench_filled.get(day)
        if start_equity is None:
            start_equity = equity if equity > 0 else initial_cash
        if start_bench is None and bench:
            start_bench = bench
        points.append(
            {
                "date": day,
                "equity": round(equity, 2),
                "benchmark": round(bench, 4) if bench is not None else None,
                "equity_idx": round(equity / start_equity * 100, 2) if start_equity else None,
                "benchmark_idx": (
                    round(bench / start_bench * 100, 2) if bench is not None and start_bench else None
                ),
            }
        )
    return points


async def portfolio_curve(portfolio: Portfolio, period: str = "2y") -> dict[str, Any]:
    txs = [
        {
            "date": tx.executed_at.isoformat() if tx.executed_at else "",
            "symbol": tx.asset.symbol if tx.asset else "",
            "qty": float(tx.quantity),
            "price": float(tx.price),
            "side": tx.side.value if hasattr(tx.side, "value") else str(tx.side),
        }
        for tx in portfolio.transactions
        if tx.side in {TransactionSide.BUY, TransactionSide.SELL} and tx.asset
    ]
    symbols = sorted({t["symbol"] for t in txs if t["symbol"]})
    prices = {sym: _closes(sym, period) for sym in symbols}
    bench = _closes(BENCH_SYMBOL, period)
    points = replay_equity(
        initial_cash=float(portfolio.initial_capital),
        transactions=txs,
        price_by_symbol=prices,
        bench_prices=bench,
    )
    return {
        "benchmark": BENCH_SYMBOL,
        "currency": portfolio.base_currency,
        "points": points,
    }
