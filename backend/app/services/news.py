from __future__ import annotations

from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, NewsItem
from app.schemas.market import NewsOut

RSS_FEEDS: list[tuple[str, str]] = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
]


def _published(entry: dict) -> datetime | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (TypeError, ValueError):
        return None


def fetch_rss(limit_per_feed: int = 12) -> list[NewsOut]:
    items: list[NewsOut] = []
    seen: set[str] = set()
    for source, url in RSS_FEEDS:
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:limit_per_feed]:
            link = entry.get("link") or ""
            if not link or link in seen:
                continue
            seen.add(link)
            items.append(
                NewsOut(
                    title=entry.get("title") or "Ohne Titel",
                    url=link,
                    source=source,
                    published_at=_published(entry),
                    summary=entry.get("summary"),
                )
            )
    items.sort(key=lambda n: n.published_at or datetime.min.replace(tzinfo=UTC), reverse=True)
    return items


SYMBOL_ALIASES: dict[str, list[str]] = {
    "AAPL": ["apple", "iphone", "aapl"],
    "MSFT": ["microsoft", "msft"],
    "NVDA": ["nvidia", "nvda"],
    "VOO": ["voo", "s&p 500", "s&p500", "sp500"],
    "TSLA": ["tesla", "tsla"],
    "AMZN": ["amazon", "amzn"],
    "GOOGL": ["alphabet", "google", "googl"],
    "META": ["meta", "facebook"],
    "AMD": ["amd"],
    "BTC-USD": ["bitcoin", "btc"],
    "ETH-USD": ["ethereum", "eth"],
    "SOL-USD": ["solana", "sol"],
}


def filter_for_symbol(items: list[NewsOut], symbol: str, name: str | None = None) -> list[NewsOut]:
    needle = [symbol.lower().replace("-usd", "")]
    needle.extend(SYMBOL_ALIASES.get(symbol.upper(), []))
    if name:
        needle.append(name.lower())
        first = name.split()[0].lower()
        if len(first) > 3:
            needle.append(first)
    needles = [n for n in dict.fromkeys(needle) if n and len(n) > 2]
    matched: list[NewsOut] = []
    for item in items:
        blob = f"{item.title} {item.summary or ''}".lower()
        if any(n in blob for n in needles):
            matched.append(item.model_copy(update={"symbol": symbol}))
    return matched


async def persist_news(
    session: AsyncSession,
    items: list[NewsOut],
    asset: Asset | None = None,
) -> int:
    stored = 0
    for item in items:
        exists = (
            await session.execute(select(NewsItem).where(NewsItem.url == item.url))
        ).scalar_one_or_none()
        if exists:
            continue
        session.add(
            NewsItem(
                asset_id=asset.id if asset else None,
                title=item.title,
                url=item.url,
                source=item.source,
                published_at=item.published_at,
                summary=item.summary,
                sentiment=item.sentiment,
            )
        )
        stored += 1
    await session.flush()
    return stored