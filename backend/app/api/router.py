from fastapi import APIRouter

from app.api.v1 import agents, assets, glossary, health, market, portfolio, recommendations

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(glossary.router, prefix="/glossary", tags=["glossary"])