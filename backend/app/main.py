from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.middleware import TotpGateMiddleware
from app.api.router import api_router
from app.config import get_settings
from app.db.base import Base
from app.db.seed import seed_if_empty
from app.db.session import async_session_factory, engine
from app.jobs.scheduler import start_scheduler, stop_scheduler
from sqlalchemy import text

from app.models import *  # noqa: F401,F403

logger = logging.getLogger("wallstreet")


_SCHEMA_STATEMENTS = (
    "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS realized_pnl NUMERIC(20, 8)",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS watched BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE assets ADD COLUMN IF NOT EXISTS user_note TEXT",
    "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS suggested_symbols JSONB",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS target_stock_pct NUMERIC(5, 2) NOT NULL DEFAULT 60",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS target_bond_pct NUMERIC(5, 2) NOT NULL DEFAULT 20",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS target_commodity_pct NUMERIC(5, 2) NOT NULL DEFAULT 5",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS target_crypto_pct NUMERIC(5, 2) NOT NULL DEFAULT 0",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS target_cash_pct NUMERIC(5, 2) NOT NULL DEFAULT 15",
    "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS max_single_position_pct NUMERIC(5, 2) NOT NULL DEFAULT 5",
)


async def _prepare_schema(conn) -> None:
    await conn.execute(
        text(
            "DO $$ BEGIN "
            "CREATE TYPE alert_kind AS ENUM ('below', 'above', 'pct_today'); "
            "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        )
    )
    try:
        await conn.run_sync(Base.metadata.create_all)
    except Exception:
        logger.exception("create_all übersprungen")
    for value in ("FUND", "COMMODITY", "FOREX"):
        try:
            await conn.execute(text(f"ALTER TYPE asset_class ADD VALUE IF NOT EXISTS '{value}'"))
        except Exception:
            logger.exception("asset_class %s", value)
    for stmt in _SCHEMA_STATEMENTS:
        try:
            await conn.execute(text(stmt))
        except Exception:
            logger.exception("Schema: %s", stmt)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    try:
        async with engine.begin() as conn:
            await _prepare_schema(conn)
    except Exception:
        logger.exception("Schema-Migration fehlgeschlagen — API startet trotzdem")

    from app.agents.llm import set_mini_only
    from app.jobs.scheduler import reschedule_agent
    from app.services.prefs import AppPrefs, get_prefs
    from app.services.vapid import ensure_vapid

    prefs = AppPrefs()
    try:
        async with async_session_factory() as session:
            await seed_if_empty(session)
            await ensure_vapid(session, subject=settings.vapid_subject)
            prefs = await get_prefs(session)
            set_mini_only(prefs.agent_mini_only)
            await session.commit()
    except Exception:
        logger.exception("Seed/Prefs fehlgeschlagen — API startet trotzdem")

    try:
        start_scheduler()
        reschedule_agent(prefs.agent_interval_minutes)
    except Exception:
        logger.exception("Scheduler nicht gestartet")
    logger.info(
        "Wallstreet API bereit (v%s, LLM %s)",
        __version__,
        "an" if settings.llm_enabled else "aus — Heuristik",
    )
    yield
    stop_scheduler()
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    app.add_middleware(TotpGateMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()