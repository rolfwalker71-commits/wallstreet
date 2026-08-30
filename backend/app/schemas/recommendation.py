from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models.enums import (
    AgentLogStatus,
    AgentName,
    RecommendationAction,
    RecommendationStatus,
)
from app.schemas.common import AssetOut, ORMModel


class AgentLogOut(ORMModel):
    id: UUID
    run_id: UUID
    agent_name: AgentName
    step: str
    status: AgentLogStatus
    reasoning: str | None
    output_payload: dict | None
    duration_ms: int | None
    created_at: datetime


class RecommendationOut(ORMModel):
    id: UUID
    run_id: UUID
    action: RecommendationAction
    confidence: Decimal
    risk_reward_ratio: Decimal | None
    rationale: str
    news_summary: str | None
    news_sources: list | None
    technicals: dict | None
    proposed_qty: Decimal | None
    proposed_price: Decimal | None
    status: RecommendationStatus
    glossary_terms: list | None
    suggested_symbols: list | None = None
    created_at: datetime
    asset: AssetOut
    agent_logs: list[AgentLogOut] = []