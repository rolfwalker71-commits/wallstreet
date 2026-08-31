from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.router import api_router
from app.config import get_settings
from app.db.base import Base
from app.db.seed import seed_if_empty
from app.db.session import async_session_factory, engine
from app.jobs.scheduler import start_scheduler, stop_scheduler
from sqlalchemy import text

from app.models import *  # noqa: F401,F403

logger = logging.getLogger("wallstreet")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "ALTER TABLE transactions "
                "ADD COLUMN IF NOT EXISTS realized_pnl NUMERIC(20, 8)"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE assets "
                "ADD COLUMN IF NOT EXISTS watched BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE recommendations "
                "ADD COLUMN IF NOT EXISTS suggested_symbols JSONB"
            )
        )
        for value in ("FUND", "COMMODITY", "FOREX"):
            await conn.execute(
                text(f"ALTER TYPE asset_class ADD VALUE IF NOT EXISTS '{value}'")
            )
        for col, default in (
            ("target_stock_pct", "60"),
            ("target_bond_pct", "20"),
            ("target_commodity_pct", "5"),
            ("target_crypto_pct", "0"),
            ("target_cash_pct", "15"),
            ("max_single_position_pct", "5"),
        ):
            await conn.execute(
                text(
                    f"ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS {col} "
                    f"NUMERIC(5, 2) NOT NULL DEFAULT {default}"
                )
            )
        await conn.execute(text("ALTER TABLE assets ADD COLUMN IF NOT EXISTS user_note TEXT"))
        await conn.execute(
            text(
                "DO $$ BEGIN "
                "CREATE TYPE alert_kind AS ENUM ('below', 'above', 'pct_today'); "
                "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
            )
        )
    async with async_session_factory() as session:
        await seed_if_empty(session)
        from app.services.vapid import ensure_vapid

        await ensure_vapid(session, subject=settings.vapid_subject)
        from app.agents.llm import set_mini_only
        from app.jobs.scheduler import reschedule_agent
        from app.services.prefs import get_prefs

        prefs = await get_prefs(session)
        set_mini_only(prefs.agent_mini_only)
    start_scheduler()
    reschedule_agent(prefs.agent_interval_minutes)
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