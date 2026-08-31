from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm, invoke_llm
from app.agents.state import AgentState
from app.services.news import fetch_rss, filter_for_symbol


RESEARCH_SYSTEM = """Du bist der Research-Agent. Bewerte NUR Meldungen, die diesen Titel wirklich betreffen.
Erfinde keine Unternehmensnews. Fehlen spezifische Meldungen, sag das klar und nutze nur das Marktumfeld.
Antworte auf Deutsch:

SENTIMENT: bullish|bearish|neutral
BRIEF: 4-8 Sätze. Was ist neu, warum es für eine Handelsentscheidung zählt, wie belastbar die Quellen sind.
"""


def research_node(state: AgentState) -> AgentState:
    symbol = state["symbol"]
    name = state.get("asset_name")
    raw = fetch_rss()
    matched = filter_for_symbol(raw, symbol, name)
    items = [
        {
            "title": n.title,
            "url": n.url,
            "source": n.source,
            "published_at": n.published_at.isoformat() if n.published_at else None,
            "summary": n.summary,
        }
        for n in matched[:8]
    ]
    market = [
        f"- [{n.source}] {n.title}"
        for n in raw[:6]
    ]
    idea = (state.get("idea_reason") or "").strip()

    llm = get_llm(mini=True)
    if not items:
        brief = (
            f"Keine Meldungen, die {symbol} namentlich nennen."
            + (f" Entdeckungsgrund: {idea}" if idea else "")
            + (" Marktumfeld: " + " ".join(n.title for n in raw[:3]) if raw else "")
        )
        sentiment = "neutral"
    else:
        brief = "Top-Meldungen: " + "; ".join(i["title"] for i in items[:3])
        sentiment = "neutral"

    if llm:
        payload = (
            f"Asset: {symbol} ({name})\n"
            f"Idee/Kontext: {idea or 'Watchlist-Analyse'}\n\n"
            f"Titel-spezifische News ({len(items)}):\n"
            + ("\n".join(f"- [{i['source']}] {i['title']}" for i in items) or "(keine)")
            + "\n\nMarktumfeld:\n"
            + ("\n".join(market) or "(keine Feeds)")
        )
        msg = invoke_llm(
            llm,
            [
                SystemMessage(content=RESEARCH_SYSTEM),
                HumanMessage(content=payload),
            ],
            purpose="research",
        )
        text = str(msg.content)
        brief = text
        lower = text.lower()
        if "bullish" in lower.split("sentiment", 1)[-1][:80]:
            sentiment = "bullish"
        elif "bearish" in lower.split("sentiment", 1)[-1][:80]:
            sentiment = "bearish"
        elif "bullish" in lower and "bearish" not in lower[:120]:
            sentiment = "bullish"
        elif "bearish" in lower and "bullish" not in lower[:120]:
            sentiment = "bearish"

    return {
        "news_items": items,
        "news_brief": brief,
        "sentiment": sentiment,
    }
