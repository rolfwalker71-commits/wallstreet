from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Recommendation, SignalOutcome
from app.models.enums import RecommendationAction

HORIZONS = (5, 20, 60)
BENCH_SYMBOL = "VWCE.DE"


def close_after_trading_days(closes: list[tuple[datetime, float]], start: datetime, days: int) -> float | None:
    """Erster Schlusskurs am oder nach start, dann +days Handelstage."""
    if days < 0 or not closes:
        return None
    start_cmp = start if start.tzinfo else start.replace(tzinfo=UTC)
    after = [c for c in closes if _aware(c[0]) >= start_cmp]
    if not after:
        return None
    idx = days
    if idx >= len(after):
        return None
    return after[idx][1]


def return_pct(entry: float, later: float | None) -> float | None:
    if later is None or entry <= 0:
        return None
    return (later / entry - 1.0) * 100.0


def compute_horizons(
    *,
    entry: float,
    start: datetime,
    asset_closes: list[tuple[datetime, float]],
    bench_closes: list[tuple[datetime, float]] | None = None,
    bench_entry: float | None = None,
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for days in HORIZONS:
        later = close_after_trading_days(asset_closes, start, days)
        out[f"ret_{days}d"] = return_pct(entry, later)
        if bench_closes and bench_entry and bench_entry > 0:
            bench_later = close_after_trading_days(bench_closes, start, days)
            out[f"bench_{days}d"] = return_pct(bench_entry, bench_later)
        else:
            out[f"bench_{days}d"] = None
    return out


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def _history_closes(symbol: str, period: str = "1y") -> list[tuple[datetime, float]]:
    from app.services.market import fetch_history

    hist = fetch_history(symbol, period=period)
    if hist is None or hist.empty or "Close" not in hist:
        return []
    closes: list[tuple[datetime, float]] = []
    for idx, close in hist["Close"].dropna().items():
        ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
        if not isinstance(ts, datetime):
            continue
        closes.append((_aware(ts), float(close)))
    return closes


def _entry_from_rec(rec: Recommendation) -> float | None:
    if rec.proposed_price and rec.proposed_price > 0:
        return float(rec.proposed_price)
    tech = rec.technicals or {}
    last = tech.get("last_close")
    if last:
        try:
            return float(last)
        except (TypeError, ValueError):
            return None
    if rec.asset and rec.asset.last_price:
        return float(rec.asset.last_price)
    return None


def _complete(row: SignalOutcome) -> bool:
    return row.ret_60d is not None


def outcome_to_dict(row: SignalOutcome | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "entry_price": float(row.entry_price),
        "ret_5d": float(row.ret_5d) if row.ret_5d is not None else None,
        "ret_20d": float(row.ret_20d) if row.ret_20d is not None else None,
        "ret_60d": float(row.ret_60d) if row.ret_60d is not None else None,
        "bench_5d": float(row.bench_5d) if row.bench_5d is not None else None,
        "bench_20d": float(row.bench_20d) if row.bench_20d is not None else None,
        "bench_60d": float(row.bench_60d) if row.bench_60d is not None else None,
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
        "complete": _complete(row),
    }


def _apply(row: SignalOutcome, computed: dict[str, float | None]) -> None:
    for key in ("ret_5d", "ret_20d", "ret_60d", "bench_5d", "bench_20d", "bench_60d"):
        val = computed.get(key)
        if val is None:
            continue
        current = getattr(row, key)
        if current is None:
            setattr(row, key, Decimal(str(round(val, 6))))
    row.computed_at = datetime.now(UTC)


async def ensure_outcome(session: AsyncSession, rec: Recommendation, *, force: bool = False) -> SignalOutcome | None:
    row = rec.outcome
    if row is None:
        row = (
            await session.execute(
                select(SignalOutcome).where(SignalOutcome.recommendation_id == rec.id)
            )
        ).scalar_one_or_none()
    if row and _complete(row) and not force:
        return row
    entry = _entry_from_rec(rec)
    if entry is None:
        return row
    symbol = rec.asset.symbol if rec.asset else None
    if not symbol:
        return row
    asset_closes = _history_closes(symbol, "1y")
    bench_closes = _history_closes(BENCH_SYMBOL, "1y")
    start = rec.created_at if rec.created_at.tzinfo else rec.created_at.replace(tzinfo=UTC)
    bench_entry = close_after_trading_days(bench_closes, start, 0)
    computed = compute_horizons(
        entry=entry,
        start=start,
        asset_closes=asset_closes,
        bench_closes=bench_closes,
        bench_entry=bench_entry,
    )
    if row is None:
        row = SignalOutcome(recommendation_id=rec.id, entry_price=Decimal(str(entry)))
        session.add(row)
    _apply(row, computed)
    rec.outcome = row
    await session.flush()
    return row


async def summarize_outcomes(session: AsyncSession) -> dict[str, Any]:
    rows = (
        await session.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.outcome), selectinload(Recommendation.asset))
            .order_by(Recommendation.created_at.desc())
            .limit(400)
        )
    ).scalars().all()
    buckets: dict[str, dict[str, list[float]]] = {
        action.value: {"ret_5d": [], "ret_20d": [], "ret_60d": []} for action in RecommendationAction
    }
    pending = 0
    stored = 0
    for rec in rows:
        if rec.outcome is None:
            pending += 1
            continue
        stored += 1
        action = rec.action.value
        for key in ("ret_5d", "ret_20d", "ret_60d"):
            val = getattr(rec.outcome, key)
            if val is not None:
                buckets[action][key].append(float(val))
    summary = {}
    for action, horizons in buckets.items():
        summary[action] = {
            key: (round(sum(vals) / len(vals), 2) if vals else None)
            for key, vals in horizons.items()
        }
        summary[action]["count"] = max((len(v) for v in horizons.values()), default=0)
    return {"by_action": summary, "stored": stored, "pending": pending}


async def refresh_due_outcomes(session: AsyncSession, limit: int = 40) -> int:
    rows = (
        await session.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.outcome), selectinload(Recommendation.asset))
            .order_by(Recommendation.created_at.asc())
            .limit(200)
        )
    ).scalars().all()
    done = 0
    for rec in rows:
        if rec.outcome and _complete(rec.outcome):
            continue
        try:
            await ensure_outcome(session, rec)
            done += 1
        except Exception:
            continue
        if done >= limit:
            break
    return done


async def outcome_for(session: AsyncSession, rec_id: UUID) -> SignalOutcome | None:
    rec = (
        await session.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.outcome), selectinload(Recommendation.asset))
            .where(Recommendation.id == rec_id)
        )
    ).scalar_one_or_none()
    if rec is None:
        return None
    return await ensure_outcome(session, rec)
