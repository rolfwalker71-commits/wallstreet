from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _tick() -> None:
    from app.agents.runner import run_watchlist_cycle

    async with async_session_factory() as session:
        try:
            recs = await run_watchlist_cycle(session)
            logger.info("Agenten-Lauf fertig: %s Empfehlungen", len(recs))
        except Exception:
            logger.exception("Agenten-Lauf fehlgeschlagen")
            await session.rollback()


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _tick,
        "interval",
        minutes=max(5, settings.agent_cron_minutes),
        id="agent_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler aktiv, Intervall %s min", settings.agent_cron_minutes)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None