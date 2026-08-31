from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.llm import get_llm, invoke_llm
from app.models import AgentLog, Asset, Recommendation
from app.models.enums import (
    AgentLogStatus,
    AgentName,
    RecommendationAction,
    RecommendationStatus,
)
from app.services.swiss_tradable import is_swiss_buyable
from app.services.usage import persist_usage, usage_scope

logger = logging.getLogger("wallstreet")

PICKS_STEP = "buy_picks"
PICKS_TTL = timedelta(hours=12)
PICKS_LIMIT = 10
CANDIDATE_POOL = 16

PICKS_SYSTEM = """Du bist Desk-Stratege für ein privates Paper-Depot eines Schweizer Privatanlegers.
Die Liste ist bereits auf in der Schweiz typischerweise kaufbare Titel gefiltert
(keine US-ETFs/Fonds ohne PRIIPs-KID, kein Forex, keine Futures).
Optionen und Hebelprodukte nur wählen, wenn sie in der Liste stehen.

Wähle bis zu 10 klare KAUF-JETZT-Ideen. Lieber weniger als 10, wenn die Lage dünn ist —
keine erzwungenen Käufe. Quer über Aktien, ETFs, Obligationen, Fonds, Rohstoffprodukte, Crypto.

Antworte ausschließlich als JSON:
{
  "picks": [
    {
      "symbol": "NESN.SW",
      "confidence": 0.0-1.0,
      "risk_reward_ratio": number|null,
      "rationale": "4-7 Sätze auf Deutsch",
      "proposed_qty": number|null,
      "proposed_price": number|null
    }
  ]
}

Jede rationale MUSS enthalten:
1) Klare Kauf-These in einem Satz.
2) Was Technicals und ggf. News dafür/dagegen sagen.
3) Das wichtigste Risiko.
4) Was die Meinung ändern würde.
Nur Symbole aus der übergebenen Liste. Keine Verkäufe, kein Halten.
"""


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
    last_rationale: str | None
    news_summary: str | None
    technicals: dict[str, Any]


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def buy_score(snap: AssetSnapshot) -> float:
    """Rangfolge für Kauf-Kandidaten. Höher = eher Kauf jetzt."""
    if not is_swiss_buyable(snap.symbol, snap.asset_class, snap.exchange):
        return -100.0
    if snap.asset_class == "forex":
        return -100.0

    score = 0.0
    tech = snap.technicals or {}
    rsi = _num(tech.get("rsi_14"))
    sma20 = _num(tech.get("sma_20"))
    sma50 = _num(tech.get("sma_50"))
    macd = _num(tech.get("macd"))
    macd_signal = _num(tech.get("macd_signal"))
    close = _num(tech.get("last_close")) or snap.last_price

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

    if snap.notes and not snap.watched:
        score += 0.25
    return score


def heuristic_rationale(snap: AssetSnapshot) -> str:
    tech = snap.technicals or {}
    rsi = _num(tech.get("rsi_14"))
    sma20 = _num(tech.get("sma_20"))
    sma50 = _num(tech.get("sma_50"))
    close = _num(tech.get("last_close")) or snap.last_price
    rsi_txt = f"{rsi:.1f}" if rsi is not None else "n/a"
    trend = "unbekannt"
    if sma20 is not None and sma50 is not None:
        trend = "Aufwärtstrend (SMA-20 über SMA-50)" if sma20 > sma50 else "unter der mittelfristigen Lage (SMA-20 unter SMA-50)"
    vs50 = ""
    if close is not None and sma50 is not None:
        vs50 = " Der Kurs liegt über dem SMA-50." if close > sma50 else " Der Kurs notiert unter dem SMA-50 — Einstieg eher als Erholung."
    news = (snap.news_summary or "").strip()
    news_txt = (
        f" News: {news[:280]}"
        if news
        else " Es liegen keine titel-spezifischen News vor — die These stützt sich auf Kurs und Indikatoren."
    )
    idea = f" Ausgangsidee: {snap.notes}" if snap.notes and not snap.watched else ""
    return (
        f"Kauf jetzt in {snap.name} ({snap.symbol}): "
        f"relativ zum restlichen, in der Schweiz kaufbaren Universum ist das einer der klareren Einstiege."
        f"{idea} Technicals: RSI {rsi_txt}, {trend}.{vs50}{news_txt} "
        f"Wichtigstes Risiko: die letzte Agentenlage war {snap.last_action or 'offen'} — "
        f"kein Garant für eine unmittelbare Gegenbewegung. "
        f"Die Meinung ändern würde ein Bruch unter die jüngste Range oder RSI deutlich über 70 ohne Pause."
    )


def snapshot_payload(snap: AssetSnapshot) -> dict[str, Any]:
    tech = snap.technicals or {}
    return {
        "symbol": snap.symbol,
        "name": snap.name,
        "asset_class": snap.asset_class,
        "watched": snap.watched,
        "notes": snap.notes,
        "last_price": snap.last_price,
        "currency": snap.currency,
        "last_action": snap.last_action,
        "last_confidence": snap.last_confidence,
        "score": round(buy_score(snap), 3),
        "rsi_14": tech.get("rsi_14"),
        "sma_20": tech.get("sma_20"),
        "sma_50": tech.get("sma_50"),
        "macd": tech.get("macd"),
        "macd_signal": tech.get("macd_signal"),
        "news_summary": (snap.news_summary or "")[:400],
        "last_rationale": (snap.last_rationale or "")[:360],
    }


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _to_snapshot(asset: Asset, rec: Recommendation | None) -> AssetSnapshot:
    tech = (rec.technicals if rec else None) or {}
    return AssetSnapshot(
        symbol=asset.symbol,
        name=asset.name,
        asset_class=asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class),
        exchange=asset.exchange,
        watched=bool(asset.watched),
        notes=asset.notes,
        last_price=_num(asset.last_price),
        currency=asset.currency or "USD",
        last_action=rec.action.value if rec else None,
        last_confidence=_num(rec.confidence) if rec else None,
        last_rationale=rec.rationale if rec else None,
        news_summary=rec.news_summary if rec else None,
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
    ranked = sorted(snaps, key=buy_score, reverse=True)
    positive = [s for s in ranked if buy_score(s) > 0]
    chosen = (positive or ranked)[:pool]
    return chosen


def _heuristic_picks(candidates: list[AssetSnapshot], limit: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for snap in candidates[:limit]:
        tech = snap.technicals or {}
        qty = 0.01 if snap.asset_class == "crypto" else 1
        conf = 0.52 + min(0.2, max(0.0, buy_score(snap) / 8))
        if snap.last_action == "buy" and snap.last_confidence:
            conf = max(conf, snap.last_confidence)
        out.append(
            {
                "symbol": snap.symbol,
                "confidence": round(min(0.78, conf), 4),
                "risk_reward_ratio": 1.4,
                "rationale": heuristic_rationale(snap),
                "proposed_qty": qty,
                "proposed_price": snap.last_price or _num(tech.get("last_close")),
            }
        )
    return out


def _parse_llm_picks(text: str, allowed: set[str]) -> list[dict[str, Any]]:
    match = re.search(r"\{.*\}", text, re.S)
    raw = json.loads(match.group(0) if match else text)
    rows = raw.get("picks") if isinstance(raw, dict) else raw
    if not isinstance(rows, list):
        return []
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = str(row.get("symbol") or "").strip().upper()
        if symbol not in allowed or symbol in seen:
            continue
        rationale = str(row.get("rationale") or "").strip()
        if len(rationale) < 40:
            continue
        seen.add(symbol)
        out.append(
            {
                "symbol": symbol,
                "confidence": row.get("confidence"),
                "risk_reward_ratio": row.get("risk_reward_ratio"),
                "rationale": rationale,
                "proposed_qty": row.get("proposed_qty"),
                "proposed_price": row.get("proposed_price"),
            }
        )
        if len(out) >= PICKS_LIMIT:
            break
    return out


def _llm_picks(candidates: list[AssetSnapshot]) -> list[dict[str, Any]] | None:
    llm = get_llm(mini=True)
    if llm is None:
        return None
    payload = [snapshot_payload(s) for s in candidates]
    allowed = {s.symbol.upper() for s in candidates}
    msg = invoke_llm(
        llm,
        [
            SystemMessage(content=PICKS_SYSTEM),
            HumanMessage(content=json.dumps({"candidates": payload}, default=str)),
        ],
        purpose="buy_picks",
    )
    try:
        parsed = _parse_llm_picks(str(msg.content), allowed)
    except json.JSONDecodeError:
        logger.warning("buy_picks: LLM-JSON nicht parsebar")
        return None
    return parsed or None


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

    run_id = uuid4()
    with usage_scope() as bucket:
        decided = _llm_picks(candidates)
        await persist_usage(session, bucket, run_id)
    if not decided:
        decided = _heuristic_picks(candidates, PICKS_LIMIT)

    recs: list[Recommendation] = []
    for item in decided[:PICKS_LIMIT]:
        symbol = str(item["symbol"]).upper()
        asset = assets.get(symbol)
        snap = by_symbol.get(symbol)
        if asset is None or snap is None:
            continue
        if not is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange):
            continue
        tech = snap.technicals or None
        qty = item.get("proposed_qty")
        if qty is None:
            qty = 0.01 if snap.asset_class == "crypto" else 1
        price = item.get("proposed_price") or snap.last_price
        rec = Recommendation(
            asset_id=asset.id,
            run_id=run_id,
            action=RecommendationAction.BUY,
            confidence=_decimal(item.get("confidence")) or Decimal("0.55"),
            risk_reward_ratio=_decimal(item.get("risk_reward_ratio")),
            rationale=str(item.get("rationale") or heuristic_rationale(snap)),
            news_summary=snap.news_summary,
            technicals=tech,
            proposed_qty=_decimal(qty),
            proposed_price=_decimal(price),
            status=RecommendationStatus.OPEN,
            glossary_terms=["RSI", "SMA", "PRIIPs"],
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
            reasoning=f"{len(recs)} Kaufempfehlungen aus {len(candidates)} Kandidaten",
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
