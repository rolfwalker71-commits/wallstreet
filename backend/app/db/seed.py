from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.glossary_seed import GLOSSARY_SEED
from app.models import (
    Asset,
    AssetClass,
    GlossaryTerm,
    Portfolio,
)

WATCHLIST_META: dict[str, dict] = {
    "AAPL": {"name": "Apple Inc.", "asset_class": AssetClass.STOCK, "exchange": "NASDAQ"},
    "MSFT": {"name": "Microsoft Corp.", "asset_class": AssetClass.STOCK, "exchange": "NASDAQ"},
    "NVDA": {"name": "NVIDIA Corp.", "asset_class": AssetClass.STOCK, "exchange": "NASDAQ"},
    "VOO": {"name": "Vanguard S&P 500 ETF", "asset_class": AssetClass.ETF, "exchange": "NYSEARCA"},
    "BTC-USD": {
        "name": "Bitcoin",
        "asset_class": AssetClass.CRYPTO,
        "coingecko_id": "bitcoin",
    },
    "ETH-USD": {
        "name": "Ethereum",
        "asset_class": AssetClass.CRYPTO,
        "coingecko_id": "ethereum",
    },
    "NESN.SW": {
        "name": "Nestlé N",
        "asset_class": AssetClass.STOCK,
        "exchange": "SIX",
    },
    "VWCE.DE": {
        "name": "Vanguard FTSE All-World UCITS ETF",
        "asset_class": AssetClass.ETF,
        "exchange": "XETRA",
    },
    "CSSMI.SW": {
        "name": "iShares SMI (CH)",
        "asset_class": AssetClass.ETF,
        "exchange": "SIX",
    },
    "IDTL.L": {
        "name": "iShares $ Treasury Bond 20+yr UCITS ETF",
        "asset_class": AssetClass.BOND,
        "exchange": "LSE",
    },
    "ZGLD.SW": {
        "name": "Swisscanto Gold ETF",
        "asset_class": AssetClass.COMMODITY,
        "exchange": "SIX",
    },
}

async def upsert_glossary(session: AsyncSession) -> None:
    rows = (await session.execute(select(GlossaryTerm))).scalars().all()
    by_slug = {row.slug: row for row in rows}
    for item in GLOSSARY_SEED:
        row = by_slug.get(item["slug"])
        if row is None:
            session.add(GlossaryTerm(**item))
            continue
        row.term = item["term"]
        row.short_definition = item["short_definition"]
        row.long_explanation = item["long_explanation"]
        row.related_terms = item["related_terms"]
        row.chart_hint = item.get("chart_hint")


async def seed_if_empty(session: AsyncSession) -> None:
    settings = get_settings()

    existing_assets = (await session.execute(select(Asset))).scalars().first()
    if existing_assets is None:
        for symbol in settings.watchlist_symbols:
            meta = WATCHLIST_META.get(
                symbol,
                {"name": symbol, "asset_class": AssetClass.STOCK},
            )
            session.add(
                Asset(
                    symbol=symbol,
                    name=meta["name"],
                    asset_class=meta["asset_class"],
                    exchange=meta.get("exchange"),
                    coingecko_id=meta.get("coingecko_id"),
                    currency="USD",
                    watched=True,
                )
            )

    existing_pf = (await session.execute(select(Portfolio))).scalars().first()
    if existing_pf is None:
        cash = Decimal(str(settings.default_cash))
        session.add(
            Portfolio(
                name="Paper Depot",
                base_currency=settings.default_currency,
                cash_balance=cash,
                initial_capital=cash,
                is_paper=True,
                broker_adapter=None,
            )
        )

    existing_glossary = (await session.execute(select(GlossaryTerm))).scalars().first()
    if existing_glossary is None:
        for item in GLOSSARY_SEED:
            session.add(GlossaryTerm(**item))

    # US-Retail-ETFs/Fonds ohne PRIIPs-KID: in der CH oft nicht kaufbar.
    for symbol in ("TLT", "GLD", "EURUSD=X", "VTSAX", "VOO"):
        found = (
            await session.execute(select(Asset).where(Asset.symbol == symbol))
        ).scalar_one_or_none()
        if found is not None:
            found.watched = False

    for symbol in ("NESN.SW", "VWCE.DE", "CSSMI.SW", "IDTL.L", "ZGLD.SW"):
        found = (
            await session.execute(select(Asset).where(Asset.symbol == symbol))
        ).scalar_one_or_none()
        meta = WATCHLIST_META[symbol]
        currency = "CHF" if symbol.endswith(".SW") else "EUR" if symbol.endswith(".DE") else "USD"
        if found is None:
            session.add(
                Asset(
                    symbol=symbol,
                    name=meta["name"],
                    asset_class=meta["asset_class"],
                    exchange=meta.get("exchange"),
                    currency=currency,
                    watched=True,
                )
            )
        else:
            found.watched = True
            found.asset_class = meta["asset_class"]
            found.name = meta["name"]

    await session.commit()