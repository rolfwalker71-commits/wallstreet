from fastapi import APIRouter

from app import __version__
from app.config import get_settings
from app.schemas.common import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(
        status="ok",
        app=settings.app_name,
        version=__version__,
        llm_enabled=settings.llm_enabled,
        llm_model=settings.openai_model if settings.llm_enabled else None,
    )