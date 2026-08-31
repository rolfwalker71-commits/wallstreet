from __future__ import annotations

from app.agents.state import AgentState
from app.services.facts import quant_fact_brief
from app.services.market import get_technicals


def quant_node(state: AgentState) -> AgentState:
    symbol = state["symbol"]
    tech = get_technicals(symbol)
    payload = tech.model_dump()
    return {
        "technicals": payload,
        "quant_brief": quant_fact_brief(payload),
    }