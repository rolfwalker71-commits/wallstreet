from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.jobs.scheduler import reschedule_agent
from app.services.fx import get_fx_bundle
from app.services.prefs import get_prefs, update_prefs

router = APIRouter()


class PrefsIn(BaseModel):
    display_currency: str | None = None
    push_min_confidence: float | None = None
    push_digest: bool | None = None
    calendar_push: bool | None = None
    agent_interval_minutes: int | None = None
    agent_watchlist_only: bool | None = None
    agent_mini_only: bool | None = None


@router.get("")
async def read_settings(db: AsyncSession = Depends(get_db)) -> dict:
    prefs = await get_prefs(db)
    fx = await get_fx_bundle(db)
    return {**prefs.as_public(), "fx": fx}


@router.patch("")
async def patch_settings(payload: PrefsIn, db: AsyncSession = Depends(get_db)) -> dict:
    data = payload.model_dump(exclude_unset=True)
    try:
        prefs = await update_prefs(db, data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    if "agent_interval_minutes" in data:
        reschedule_agent(prefs.agent_interval_minutes)
    fx = await get_fx_bundle(db)
    return {**prefs.as_public(), "fx": fx}
