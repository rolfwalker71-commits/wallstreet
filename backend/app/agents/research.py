from __future__ import annotations

from app.agents.state import AgentState
from app.services.news import fetch_rss, filter_for_symbol


def _headline_line(item: dict) -> str:
    source = item.get("source") or ""
    title = item.get("title") or ""
    when = item.get("published_at") or ""
    extra = f", {when}" if when else ""
    return f"- [{source}{extra}] {title}".strip()


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
        }
        for n in matched[:8]
    ]
    if items:
        brief = (
            f"{len(items)} Meldung(en), die {symbol} namentlich nennen:\n"
            + "\n".join(_headline_line(i) for i in items)
        )
    else:
        brief = f"Keine Meldung, die {symbol} namentlich nennt."

    return {
        "news_items": items,
        "news_brief": brief,
        "sentiment": "neutral",
    }
