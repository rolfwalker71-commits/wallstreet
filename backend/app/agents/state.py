from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    symbol: str
    asset_name: str
    asset_class: str
    news_items: list[dict[str, Any]]
    news_brief: str
    sentiment: str
    technicals: dict[str, Any]
    quant_brief: str
    action: str
    confidence: float
    risk_reward_ratio: float | None
    rationale: str
    proposed_qty: float | None
    proposed_price: float | None
    glossary_terms: list[str]
    glossary_notes: dict[str, str]
    idea_reason: str
    errors: list[str]