from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState

EDUCATOR_SYSTEM = """Du bist der Finance Educator.
Erkläre die Fachbegriffe aus der Empfehlung in einem Satz auf Deutsch.
Antworte als JSON-Objekt { "TERM": "kurze Erklärung", ... }.
"""


def educator_node(state: AgentState) -> AgentState:
    terms = state.get("glossary_terms") or []
    notes: dict[str, str] = {}
    llm = get_llm(mini=True)
    if llm and terms:
        msg = llm.invoke(
            [
                SystemMessage(content=EDUCATOR_SYSTEM),
                HumanMessage(
                    content=f"Begriffe: {', '.join(terms)}\nKontext: {state.get('rationale', '')[:500]}"
                ),
            ]
        )
        import json
        import re

        text = str(msg.content)
        match = re.search(r"\{.*\}", text, re.S)
        try:
            notes = json.loads(match.group(0) if match else text)
        except json.JSONDecodeError:
            notes = {t: "Siehe Lexikon." for t in terms}
    else:
        notes = {t: "Siehe Lexikon-Eintrag." for t in terms}

    return {"glossary_notes": notes}