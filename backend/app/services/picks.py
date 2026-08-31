from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AgentLog, Asset, Recommendation
from app.models.enums import (
    AgentLogStatus,
    AgentName,
    RecommendationAction,
    RecommendationStatus,
)
from app.services.facts import as_float, build_fact_rationale, headlines_from_sources
from app.services.swiss_tradable import is_swiss_buyable

PICKS_STEP = "buy_picks_facts"
PICKS_TTL = timedelta(hours=12)
PICKS_LIMIT = 10
CANDIDATE_POOL = 16


@dataclass(frozen=True)
class AssetSnapshot:
    symbol: str
    name: str
    asset_class: str
    exchange: str | None
    watched: bool
    notes: str | None
    last_price: float | None
    currency: str
    last_action: str | None
    last_confidence: float | None
    headlines: tuple[str, ...]
    technicals: dict[str, Any]


def buy_score(snap: AssetSnapshot) -> float:
    """Rangfolge für Kauf-Kandidaten. Höher = eher Kauf jetzt."""
    if not is_swiss_buyable(snap.symbol, snap.asset_class, snap.exchange):
        return -100.0
    if snap.asset_class == "forex":
        return -100.0

    score = 0.0
    tech = snap.technicals or {}
    rsi = as_float(tech.get("rsi_14"))
    sma20 = as_float(tech.get("sma_20"))
    sma50 = as_float(tech.get("sma_50"))
    macd = as_float(tech.get("macd"))
    macd_signal = as_float(tech.get("macd_signal"))
    close = as_float(tech.get("last_close")) or snap.last_price

    if snap.last_action == "buy":
        score += 1.8 * (snap.last_confidence or 0.5)
    elif snap.last_action == "sell":
        score -= 1.6
    elif snap.last_action == "hold":
        score += 0.15

    if rsi is not None:
        if rsi <= 30:
            score += 1.4
        elif rsi <= 40:
            score += 0.9
        elif rsi <= 50:
            score += 0.35
        elif rsi >= 72:
            score -= 1.0
        elif rsi >= 65:
            score -= 0.4

    if sma20 is not None and sma50 is not None:
        score += 0.45 if sma20 > sma50 else -0.2
    if close is not None and sma50 is not None:
        if close < sma50 and rsi is not None and rsi <= 40:
            score += 0.35
        elif close > sma50:
            score += 0.25

    if macd is not None and macd_signal is not None:
        score += 0.25 if macd > macd_signal else -0.1
    return score


def fact_rationale(snap: AssetSnapshot, action: str | None = None) -> str:
    rsi = as_float((snap.technicals or {}).get("rsi_14"))
    rule = action
    if rule is None and rsi is not None and rsi <= 32:
        rule = "buy"
    body = build_fact_rationale(
        symbol=snap.symbol,
        name=snap.name,
        currency=snap.currency,
        price=snap.last_price,
        technicals=snap.technicals,
        headlines=list(snap.headlines),
        last_action=snap.last_action,
        last_confidence=snap.last_confidence,
        action=rule,
    )
    return f"{body} Listenplatz nach RSI, SMA-20/50 und MACD. Keine Kursprognose."


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _headline_notes(notes: str | None) -> tuple[str, ...]:
    text = (notes or "").strip()
    if text.startswith("Headline:"):
        title = text.removeprefix("Headline:").strip()
        return (title,) if title else ()
    return ()


def _to_snapshot(asset: Asset, rec: Recommendation | None) -> AssetSnapshot:
    tech = (rec.technicals if rec else None) or {}
    headlines = headlines_from_sources(rec.news_sources if rec else None)
    extra = _headline_notes(asset.notes)
    merged = tuple(dict.fromkeys([*headlines, *extra]))
    return AssetSnapshot(
        symbol=asset.symbol,
        name=asset.name,
        asset_class=asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class),
        exchange=asset.exchange,
        watched=bool(asset.watched),
        notes=asset.notes,
        last_price=as_float(asset.last_price),
        currency=asset.currency or "USD",
        last_action=rec.action.value if rec else None,
        last_confidence=as_float(rec.confidence) if rec else None,
        headlines=merged,
        technicals=tech,
    )


async def _latest_recs_by_asset(session: AsyncSession) -> dict:
    rows = (
        (
            await session.execute(
                select(Recommendation)
                .options(selectinload(Recommendation.asset))
                .order_by(Recommendation.created_at.desc())
            )
        )
        .scalars()
        .all()
    )
    latest: dict = {}
    for row in rows:
        if row.asset_id not in latest:
            latest[row.asset_id] = row
    return latest


async def load_snapshots(session: AsyncSession) -> list[AssetSnapshot]:
    assets = (await session.execute(select(Asset).order_by(Asset.symbol))).scalars().all()
    recs = await _latest_recs_by_asset(session)
    snaps: list[AssetSnapshot] = []
    for asset in assets:
        if not is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange):
            continue
        snaps.append(_to_snapshot(asset, recs.get(asset.id)))
    snaps.sort(key=buy_score, reverse=True)
    return snaps


def rank_candidates(snaps: list[AssetSnapshot], pool: int = CANDIDATE_POOL) -> list[AssetSnapshot]:
    ranked = [s for s in sorted(snaps, key=buy_score, reverse=True) if s.last_action != "sell"]
    positive = [s for s in ranked if buy_score(s) > 0]
    return (positive or ranked)[:pool]


def _rule_picks(candidates: list[AssetSnapshot], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for snap in candidates[:limit]:
        tech = snap.technicals or {}
        qty = 0.01 if snap.asset_class == "crypto" else 1
        rsi = as_float(tech.get("rsi_14"))
        conf = 0.52
        if rsi is not None and rsi <= 32:
            conf = 0.58
        if snap.last_action == "buy" and snap.last_confidence:
            conf = max(conf, min(snap.last_confidence, 0.7))
        out.append(
            {
                "symbol": snap.symbol,
                "confidence": round(conf, 4),
                "risk_reward_ratio": None,
                "rationale": fact_rationale(snap),
                "proposed_qty": qty,
                "proposed_price": snap.last_price or as_float(tech.get("last_close")),
            }
        )
    return out


async def cached_picks(session: AsyncSession) -> list[Recommendation] | None:
    log = (
        await session.execute(
            select(AgentLog)
            .where(AgentLog.step == PICKS_STEP, AgentLog.status == AgentLogStatus.SUCCEEDED)
            .order_by(AgentLog.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if log is None:
        return None
    created = log.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    if datetime.now(UTC) - created > PICKS_TTL:
        return None
    rows = (
        (
            await session.execute(
                select(Recommendation)
                .options(
                    selectinload(Recommendation.asset),
                    selectinload(Recommendation.agent_logs),
                )
                .where(Recommendation.run_id == log.run_id)
                .order_by(Recommendation.confidence.desc())
            )
        )
        .scalars()
        .all()
    )
    return list(rows) or None


async def generate_buy_picks(session: AsyncSession) -> list[Recommendation]:
    started = time.perf_counter()
    snaps = await load_snapshots(session)
    candidates = rank_candidates(snaps)
    by_symbol = {s.symbol.upper(): s for s in snaps}
    assets = {
        a.symbol.upper(): a
        for a in (await session.execute(select(Asset))).scalars().all()
    }
    decided = _rule_picks(candidates, PICKS_LIMIT)
    run_id = uuid4()
    recs: list[Recommendation] = []
    for item in decided:
        symbol = str(item["symbol"]).upper()
        asset = assets.get(symbol)
        snap = by_symbol.get(symbol)
        if asset is None or snap is None:
            continue
        if not is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange):
            continue
        rec = Recommendation(
            asset_id=asset.id,
            run_id=run_id,
            action=RecommendationAction.BUY,
            confidence=_decimal(item.get("confidence")) or Decimal("0.52"),
            risk_reward_ratio=_decimal(item.get("risk_reward_ratio")),
            rationale=str(item["rationale"]),
            news_summary=None,
            news_sources=[{"title": h} for h in snap.headlines] or None,
            technicals=snap.technicals or None,
            proposed_qty=_decimal(item.get("proposed_qty")),
            proposed_price=_decimal(item.get("proposed_price")),
            status=RecommendationStatus.OPEN,
            glossary_terms=["RSI", "SMA", "MACD"],
        )
        session.add(rec)
        recs.append(rec)

    await session.flush()
    for rec in recs:
        await session.refresh(rec, attribute_names=["asset", "agent_logs"])

    elapsed = int((time.perf_counter() - started) * 1000)
    session.add(
        AgentLog(
            run_id=run_id,
            agent_name=AgentName.STRATEGIST,
            step=PICKS_STEP,
            status=AgentLogStatus.SUCCEEDED,
            reasoning=f"{len(recs)} faktenbasierte Kaufregeln aus {len(candidates)} Kandidaten",
            output_payload={"symbols": [r.asset.symbol for r in recs if r.asset]},
            duration_ms=elapsed,
        )
    )
    await session.flush()
    return recs


async def list_buy_picks(session: AsyncSession, *, refresh: bool = False) -> list[Recommendation]:
    if not refresh:
        cached = await cached_picks(session)
        if cached:
            return cached
    return await generate_buy_picks(session)
