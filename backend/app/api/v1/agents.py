from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runner import run_watchlist_cycle
from app.config import get_settings
from app.db.session import get_db
from app.models import AgentLog
from app.models.enums import AgentName
from app.schemas.recommendation import AgentLogOut, RecommendationOut
from app.services.prefs import get_prefs
from app.services.usage import usage_summary

router = APIRouter()


@router.get("/logs", response_model=list[AgentLogOut])
async def list_logs(
    agent_name: AgentName | None = None,
    run_id: UUID | None = None,
    limit: int = Query(default=80, le=300),
    db: AsyncSession = Depends(get_db),
) -> list[AgentLogOut]:
    stmt = select(AgentLog).order_by(AgentLog.created_at.desc()).limit(limit)
    if agent_name:
        stmt = stmt.where(AgentLog.agent_name == agent_name)
    if run_id:
        stmt = stmt.where(AgentLog.run_id == run_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [AgentLogOut.model_validate(r) for r in rows]


@router.get("/usage")
async def llm_usage(db: AsyncSession = Depends(get_db)) -> dict:
    settings = get_settings()
    prefs = await get_prefs(db)
    summary = await usage_summary(db)
    minutes = prefs.agent_interval_minutes
    cycles_per_day = 24 * 60 / max(5, minutes)
    summary["interval_minutes"] = minutes
    summary["cycles_per_day"] = round(cycles_per_day, 1)
    summary["watchlist_only"] = prefs.agent_watchlist_only
    summary["mini_only"] = prefs.agent_mini_only
    discover = "ohne Discover" if prefs.agent_watchlist_only else "1× Discover (mini)"
    model = settings.openai_mini_model if prefs.agent_mini_only else "Hauptmodell / Mini"
    summary["estimate"] = (
        f"Pro Lauf: {discover}, je Titel Research/Quant/Strategist ({model}). "
        f"Intervall {minutes} Min → ca. {cycles_per_day:.0f} Läufe/Tag. "
        "Push nur bei neuem Kauf/Verkauf, nicht bei jedem Halten."
    )
    return summary


@router.post("/run", response_model=list[RecommendationOut])
async def trigger_run(
    symbols: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    wanted = [s.strip() for s in symbols.split(",")] if symbols else None
    recs = await run_watchlist_cycle(db, wanted)
    return [RecommendationOut.model_validate(r) for r in recs]