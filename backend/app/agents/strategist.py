from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, invoke_llm
from app.agents.state import AgentState

STRATEGIST_SYSTEM = """Du bist Senior-Strategist für ein privates Paper-Depot.
Schreibe eine echte Handelsempfehlung auf Deutsch — keine Floskeln, kein Marketing.

Antworte ausschließlich als JSON:
{
  "action": "buy"|"hold"|"sell",
  "confidence": 0.0-1.0,
  "risk_reward_ratio": number|null,
  "rationale": "5-9 Sätze auf Deutsch",
  "proposed_qty": number|null,
  "proposed_price": number|null,
  "glossary_terms": ["RSI", "..."]
}

Die rationale MUSS enthalten:
1) Klare Handlung und These in einem Satz.
2) Was News (nur wenn sie den Titel betreffen) und Technicals dafür/dagegen sagen.
3) Das wichtigste Risiko.
4) Was deine Meinung ändern würde.
Wenn keine titel-spezifischen News da sind: sag das und stütze dich ehrlich auf Kurs/Indikatoren und Marktumfeld.
Sei konservativ. Bei Widerspruch: hold. Paper: kleine Menge (1-5 Stück, Crypto 0.01).
"""


def _heuristic(state: AgentState) -> dict:
    tech = state.get("technicals") or {}
    rsi = tech.get("rsi_14")
    sentiment = state.get("sentiment", "neutral")
    action = "hold"
    confidence = 0.45
    if rsi is not None and rsi <= 32 and sentiment != "bearish":
        action = "buy"
        confidence = 0.58
    elif rsi is not None and rsi >= 72 and sentiment != "bullish":
        action = "sell"
        confidence = 0.56
    price = tech.get("last_close")
    qty = 1.0 if state.get("asset_class") != "crypto" else 0.01
    idea = (state.get("idea_reason") or "").strip()
    why = f" Ausgangsidee: {idea}" if idea else ""
    return {
        "action": action,
        "confidence": confidence,
        "risk_reward_ratio": 1.5 if action != "hold" else None,
        "rationale": (
            f"{'Kauf' if action == 'buy' else 'Verkauf' if action == 'sell' else 'Halten'} "
            f"für {state.get('symbol')}: ohne LLM, nur Regelwerk (RSI {rsi}, Sentiment {sentiment})."
            f"{why} {state.get('quant_brief', '')} {state.get('news_brief', '')[:280]}"
        ),
        "proposed_qty": qty if action != "hold" else None,
        "proposed_price": price,
        "glossary_terms": ["RSI", "SMA", "MACD"],
    }


def strategist_node(state: AgentState) -> AgentState:
    llm = get_llm(mini=False)
    if llm is None:
        decision = _heuristic(state)
    else:
        payload = {
            "symbol": state.get("symbol"),
            "name": state.get("asset_name"),
            "idea_reason": state.get("idea_reason"),
            "sentiment": state.get("sentiment"),
            "news_brief": state.get("news_brief"),
            "quant_brief": state.get("quant_brief"),
            "technicals": state.get("technicals"),
            "has_specific_news": bool(state.get("news_items")),
        }
        msg = invoke_llm(
            llm,
            [
                SystemMessage(content=STRATEGIST_SYSTEM),
                HumanMessage(content=json.dumps(payload, default=str)),
            ],
            purpose="strategist",
        )
        text = str(msg.content)
        match = re.search(r"\{.*\}", text, re.S)
        try:
            decision = json.loads(match.group(0) if match else text)
        except json.JSONDecodeError:
            decision = _heuristic(state)
            decision["rationale"] = f"LLM-Antwort nicht parsebar. Fallback.\n{text[:400]}"

    return {
        "action": decision.get("action", "hold"),
        "confidence": float(decision.get("confidence") or 0.4),
        "risk_reward_ratio": decision.get("risk_reward_ratio"),
        "rationale": decision.get("rationale") or "",
        "proposed_qty": decision.get("proposed_qty"),
        "proposed_price": decision.get("proposed_price"),
        "glossary_terms": decision.get("glossary_terms") or ["RSI"],
    }
