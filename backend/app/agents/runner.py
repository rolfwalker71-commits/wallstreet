from __future__ import annotations

import time
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.discover import discover_ideas, related_symbols
from app.agents.graph import agent_graph
from app.agents.llm import set_mini_only
from app.config import get_settings
from app.services.alerts import check_alerts
from app.services.prefs import get_prefs
from app.models import AgentLog, Asset, Recommendation
from app.models.enums import (
    AgentLogStatus,
    AgentName,
    RecommendationAction,
    RecommendationStatus,
)
from app.services.market import get_quote, persist_quote
from app.services.push import notify_new_signals
from app.services.usage import persist_usage, usage_scope
from app.services.news import persist_news
from app.services.swiss_tradable import filter_swiss_symbols, is_swiss_buyable


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


async def _log(
    session: AsyncSession,
    *,
    run_id,
    agent: AgentName,
    step: str,
    status: AgentLogStatus,
    reasoning: str | None = None,
    output: dict | None = None,
    duration_ms: int | None = None,
    recommendation_id=None,
) -> AgentLog:
    row = AgentLog(
        run_id=run_id,
        agent_name=agent,
        step=step,
        status=status,
        reasoning=reasoning,
        output_payload=output,
        duration_ms=duration_ms,
        recommendation_id=recommendation_id,
    )
    session.add(row)
    await session.flush()
    return row


async def run_for_asset(
    session: AsyncSession,
    asset: Asset,
    idea_reason: str | None = None,
) -> Recommendation:
    run_id = uuid4()
    started = time.perf_counter()
    await _log(
        session,
        run_id=run_id,
        agent=AgentName.RESEARCH,
        step="cycle_start",
        status=AgentLogStatus.STARTED,
        output={"symbol": asset.symbol},
    )

    initial = {
        "symbol": asset.symbol,
        "asset_name": asset.name,
        "asset_class": asset.asset_class.value,
        "idea_reason": idea_reason or (asset.notes if not asset.watched else None) or "",
    }
    try:
        with usage_scope() as bucket:
            final = await agent_graph.ainvoke(initial)
            await persist_usage(session, bucket, run_id)
    except Exception as exc:
        await _log(
            session,
            run_id=run_id,
            agent=AgentName.STRATEGIST,
            step="graph_failed",
            status=AgentLogStatus.FAILED,
            reasoning=str(exc),
        )
        raise

    elapsed = int((time.perf_counter() - started) * 1000)
    action = RecommendationAction(final.get("action") or "hold")

    rec = Recommendation(
        asset_id=asset.id,
        run_id=run_id,
        action=action,
        confidence=_decimal(final.get("confidence")) or Decimal("0.4"),
        risk_reward_ratio=_decimal(final.get("risk_reward_ratio")),
        rationale=final.get("rationale") or "",
        news_summary=final.get("news_brief"),
        news_sources=final.get("news_items"),
        technicals=final.get("technicals"),
        proposed_qty=_decimal(final.get("proposed_qty")),
        proposed_price=_decimal(final.get("proposed_price")),
        status=RecommendationStatus.OPEN,
        glossary_terms=final.get("glossary_terms"),
        suggested_symbols=filter_swiss_symbols(
            related_symbols(
                " ".join(
                    [
                        str(final.get("rationale") or ""),
                        str(final.get("news_brief") or ""),
                        " ".join(
                            str(n.get("title") or "")
                            for n in (final.get("news_items") or [])
                            if isinstance(n, dict)
                        ),
                    ]
                ),
                exclude={asset.symbol},
            )
        )
        or None,
    )
    session.add(rec)
    await session.flush()

    await _log(
        session,
        run_id=run_id,
        agent=AgentName.RESEARCH,
        step="news",
        status=AgentLogStatus.SUCCEEDED,
        reasoning=final.get("news_brief"),
        output={"sentiment": final.get("sentiment"), "items": final.get("news_items")},
        recommendation_id=rec.id,
    )
    await _log(
        session,
        run_id=run_id,
        agent=AgentName.QUANT,
        step="technicals",
        status=AgentLogStatus.SUCCEEDED,
        reasoning=final.get("quant_brief"),
        output=final.get("technicals"),
        recommendation_id=rec.id,
    )
    await _log(
        session,
        run_id=run_id,
        agent=AgentName.STRATEGIST,
        step="decision",
        status=AgentLogStatus.SUCCEEDED,
        reasoning=final.get("rationale"),
        output={"action": action.value, "confidence": str(rec.confidence)},
        duration_ms=elapsed,
        recommendation_id=rec.id,
    )
    await _log(
        session,
        run_id=run_id,
        agent=AgentName.EDUCATOR,
        step="glossary",
        status=AgentLogStatus.SUCCEEDED,
        reasoning="Fachbegriffe zur Empfehlung erklärt.",
        output=final.get("glossary_notes"),
        recommendation_id=rec.id,
    )

    quote = await get_quote(asset.symbol, session)
    if quote:
        await persist_quote(session, quote)
        rec.proposed_price = rec.proposed_price or quote.price

    from app.schemas.market import NewsOut
    from app.models.enums import Sentiment

    raw_news = final.get("news_items") or []
    news_models = [
        NewsOut(
            title=n.get("title") or "",
            url=n.get("url") or "",
            source=n.get("source") or "unknown",
            summary=n.get("summary"),
            sentiment=Sentiment(final["sentiment"]) if final.get("sentiment") in Sentiment._value2member_map_ else None,
        )
        for n in raw_news
        if n.get("url")
    ]
    if news_models:
        await persist_news(session, news_models, asset)

    rec = (
        await session.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.asset),
                selectinload(Recommendation.agent_logs),
            )
            .where(Recommendation.id == rec.id)
        )
    ).scalar_one()

    return rec


async def run_watchlist_cycle(session: AsyncSession, symbols: list[str] | None = None) -> list[Recommendation]:
    settings = get_settings()
    prefs = await get_prefs(session)
    set_mini_only(prefs.agent_mini_only)
    reasons: dict[str, str] = {}
    if symbols:
        wanted = [s.upper() for s in symbols]
        assets = (
            await session.execute(select(Asset).where(Asset.symbol.in_(wanted)))
        ).scalars().all()
    else:
        assets = (
            await session.execute(select(Asset).where(Asset.watched.is_(True)).order_by(Asset.symbol))
        ).scalars().all()
        assets = [
            a
            for a in assets
            if is_swiss_buyable(a.symbol, a.asset_class, a.exchange)
        ]
        if not assets:
            wanted = settings.watchlist_symbols
            assets = (
                await session.execute(select(Asset).where(Asset.symbol.in_(wanted)))
            ).scalars().all()
        seen = {a.symbol for a in assets}
        if not prefs.agent_watchlist_only:
            with usage_scope() as bucket:
                ideas = await discover_ideas(session, limit=5)
                await persist_usage(session, bucket)
            for extra, reason in ideas:
                reasons[extra.symbol] = reason
                if extra.symbol not in seen:
                    assets.append(extra)
                    seen.add(extra.symbol)

    results: list[Recommendation] = []
    for asset in assets:
        rec = await run_for_asset(session, asset, idea_reason=reasons.get(asset.symbol))
        results.append(rec)
        await session.commit()
    try:
        await notify_new_signals(session, results)
        await check_alerts(session)
        await session.commit()
    except Exception:
        await session.rollback()
    return results