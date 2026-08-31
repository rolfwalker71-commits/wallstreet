from __future__ import annotations

import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


async def _agent_tick() -> None:
    from app.agents.runner import run_watchlist_cycle
    from app.services.prefs import get_prefs

    async with async_session_factory() as session:
        try:
            prefs = await get_prefs(session)
            recs = await run_watchlist_cycle(session)
            logger.info(
                "Agenten-Lauf fertig: %s Empfehlungen (Intervall %s, Watchlist-only %s, Mini %s)",
                len(recs),
                prefs.agent_interval_minutes,
                prefs.agent_watchlist_only,
                prefs.agent_mini_only,
            )
        except Exception:
            logger.exception("Agenten-Lauf fehlgeschlagen")
            await session.rollback()


async def _light_tick() -> None:
    from app.services.alerts import check_alerts
    from app.services.calendar import notify_calendar
    from app.services.outcomes import refresh_due_outcomes
    from app.services.prefs import get_prefs
    from app.services.push import flush_digest

    async with async_session_factory() as session:
        try:
            fired = await check_alerts(session)
            cal = await notify_calendar(session)
            due = await refresh_due_outcomes(session, limit=20)
            prefs = await get_prefs(session)
            digest = 0
            if prefs.push_digest and datetime.now(UTC).hour == 17:
                digest = await flush_digest(session)
            await session.commit()
            if fired or cal or due or digest:
                logger.info(
                    "Leichter Tick: %s Alarme, %s Kalender, %s Bilanzen, digest=%s",
                    len(fired),
                    cal,
                    due,
                    digest,
                )
        except Exception:
            logger.exception("Leichter Tick fehlgeschlagen")
            await session.rollback()


def reschedule_agent(minutes: int) -> None:
    if _scheduler is None:
        return
    _scheduler.reschedule_job(
        "agent_cycle",
        trigger="interval",
        minutes=max(5, minutes),
    )
    logger.info("Agenten-Intervall neu: %s min", minutes)


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    settings = get_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _agent_tick,
        "interval",
        minutes=max(5, settings.agent_cron_minutes),
        id="agent_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _light_tick,
        "interval",
        minutes=15,
        id="light_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduler aktiv, Intervall %s min + leichter Tick 15 min", settings.agent_cron_minutes)
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
