from fastapi import APIRouter

from app.api.v1 import agents, alerts, assets, auth, glossary, health, market, portfolio, push, recommendations, settings

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(glossary.router, prefix="/glossary", tags=["glossary"])
api_router.include_router(push.router, prefix="/push", tags=["push"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])