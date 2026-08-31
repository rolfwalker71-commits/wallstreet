from __future__ import annotations

from app.agents.state import AgentState
from app.services.facts import (
    action_from_technicals,
    as_float,
    build_fact_rationale,
    headlines_from_sources,
)


def strategist_node(state: AgentState) -> AgentState:
    tech = state.get("technicals") or {}
    action, confidence = action_from_technicals(tech)
    headlines = headlines_from_sources(state.get("news_items"))
    qty = 1.0 if state.get("asset_class") != "crypto" else 0.01
    price = as_float(tech.get("last_close"))
    rationale = build_fact_rationale(
        symbol=str(state.get("symbol") or ""),
        name=str(state.get("asset_name") or state.get("symbol") or ""),
        technicals=tech,
        headlines=headlines,
        action=action,
    )
    return {
        "action": action,
        "confidence": confidence,
        "risk_reward_ratio": 1.5 if action != "hold" else None,
        "rationale": rationale,
        "proposed_qty": qty if action != "hold" else None,
        "proposed_price": price,
        "glossary_terms": ["RSI", "SMA", "MACD"],
    }
