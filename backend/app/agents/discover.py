from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.llm import get_llm, invoke_llm
from app.models import Asset
from app.services.assets import AssetError, get_or_create_asset
from app.services.news import fetch_rss
from app.services.swiss_tradable import is_swiss_buyable

DISCOVER_SYSTEM = """Du listest nur Ticker, die wörtlich in den Headlines stehen.
Keine Interpretation, keine erfundenen Ticker, keine Begründung aus Wissen.

Erlaubt: Einzelaktien (auch US), UCITS-ETFs, SIX (.SW), Xetra/LSE-UCITS (.DE / .L), Crypto (BTC-USD, ETH-USD).
Verboten: US-ETFs ohne KID (VOO, SPY, TLT, GLD), US-Funds (VTSAX), Devisen (=X), Futures (=F).

JSON-Array:
[{"symbol":"NESN.SW","headline":"exakte Schlagzeile aus der Liste"}]
Die headline MUSS eine der gelieferten Headlines sein. Sonst weglassen."""

NAME_HINTS = {
    "tesla": "TSLA",
    "amazon": "AMZN",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "jpmorgan": "JPM",
    "goldman": "GS",
    "berkshire": "BRK-B",
    "palantir": "PLTR",
    "amd": "AMD",
    "intel": "INTC",
    "broadcom": "AVGO",
    "solana": "SOL-USD",
    "apple": "AAPL",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
}


def related_symbols(text: str, exclude: set[str] | None = None) -> list[str]:
    return _from_headlines(text, {s.upper() for s in (exclude or set())})


def _from_headlines(text: str, watched: set[str]) -> list[str]:
    found: list[str] = []
    lower = text.lower()
    for needle, ticker in NAME_HINTS.items():
        if needle in lower and ticker not in watched and ticker not in found:
            if is_swiss_buyable(ticker):
                found.append(ticker)
    for match in re.findall(r"\b([A-Z]{2,5})\b", text):
        if match in watched or match in found:
            continue
        if match in {"CEO", "CFO", "ETF", "USD", "GDP", "FED", "AI", "IPO", "SEC"}:
            continue
        if match in NAME_HINTS.values() or match in {"TSLA", "AMZN", "GOOGL", "META", "AMD"}:
            if is_swiss_buyable(match):
                found.append(match)
    return found[:6]


async def discover_ideas(
    session: AsyncSession,
    limit: int = 5,
) -> list[tuple[Asset, str]]:
    watched_rows = (
        await session.execute(select(Asset).where(Asset.watched.is_(True)))
    ).scalars().all()
    watched = {a.symbol.upper() for a in watched_rows}
    news = fetch_rss()
    titles = {n.title.strip() for n in news if n.title}
    blob = "\n".join(f"- {n.title}" for n in news[:30])
    reasons: dict[str, str] = {}
    for item in news[:30]:
        for sym in _from_headlines(item.title, watched):
            reasons.setdefault(sym, f"Headline: {item.title}")

    llm = get_llm(mini=True)
    if llm:
        try:
            msg = invoke_llm(
                llm,
                [
                    SystemMessage(content=DISCOVER_SYSTEM),
                    HumanMessage(
                        content=f"Watchlist: {', '.join(sorted(watched))}\n\nHeadlines:\n{blob}"
                    ),
                ],
                purpose="discover",
            )
            match = re.search(r"\[.*\]", str(msg.content), re.S)
            parsed = json.loads(match.group(0) if match else str(msg.content))
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                sym = str(item.get("symbol") or "").upper()
                headline = str(item.get("headline") or item.get("reason") or "").strip()
                if not sym or sym in watched or not is_swiss_buyable(sym):
                    continue
                if headline not in titles:
                    continue
                if not _from_headlines(headline, set()):
                    continue
                reasons.setdefault(sym, f"Headline: {headline}")
        except Exception:
            pass

    ideas: list[tuple[Asset, str]] = []
    for sym, reason in reasons.items():
        if len(ideas) >= limit:
            break
        if not is_swiss_buyable(sym):
            continue
        try:
            asset = await get_or_create_asset(session, sym, watched=False)
            if asset.watched:
                continue
            if reason:
                asset.notes = reason
            ideas.append((asset, reason))
        except AssetError:
            continue
    await session.flush()
    return ideas


async def discover_assets(session: AsyncSession, limit: int = 3) -> list[Asset]:
    return [asset for asset, _ in await discover_ideas(session, limit=limit)]
