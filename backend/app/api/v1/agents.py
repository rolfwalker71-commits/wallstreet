from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.runner import run_watchlist_cycle
from app.db.session import get_db
from app.models import AgentLog
from app.models.enums import AgentName
from app.schemas.recommendation import AgentLogOut, RecommendationOut

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


@router.post("/run", response_model=list[RecommendationOut])
async def trigger_run(
    symbols: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    wanted = [s.strip() for s in symbols.split(",")] if symbols else None
    recs = await run_watchlist_cycle(db, wanted)
    return [RecommendationOut.model_validate(r) for r in recs]