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
    async with async_session_factory() as session:
        await seed_if_empty(session)
    start_scheduler()
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