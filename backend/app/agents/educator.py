from __future__ import annotations

from app.agents.state import AgentState


def educator_node(state: AgentState) -> AgentState:
    terms = state.get("glossary_terms") or []
    notes = {term: "Siehe Lexikon." for term in terms}
    return {"glossary_notes": notes}
