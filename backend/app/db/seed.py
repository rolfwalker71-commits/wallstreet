from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
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
}

GLOSSARY_SEED: list[dict] = [
    {
        "term": "RSI",
        "slug": "rsi",
        "short_definition": "Relative Strength Index — Momentum-Oszillator von 0 bis 100.",
        "long_explanation": (
            "Der RSI misst die Stärke jüngster Kursbewegungen. Werte über 70 gelten oft "
            "als überkauft, unter 30 als überverkauft. Er wird typischerweise über 14 Perioden berechnet."
        ),
        "related_terms": ["MACD", "SMA", "EMA"],
        "chart_hint": "rsi",
    },
    {
        "term": "SMA",
        "slug": "sma",
        "short_definition": "Simple Moving Average — einfacher gleitender Durchschnitt.",
        "long_explanation": (
            "Der SMA glättet Kurse über n Perioden mit gleichem Gewicht. "
            "Kreuzungen (z. B. SMA-50 vs. SMA-200) werden als Trendwechsel gelesen."
        ),
        "related_terms": ["EMA", "MACD"],
        "chart_hint": "sma",
    },
    {
        "term": "EMA",
        "slug": "ema",
        "short_definition": "Exponential Moving Average — gleitender Durchschnitt mit mehr Gewicht auf jüngere Kurse.",
        "long_explanation": (
            "Im Gegensatz zum SMA reagiert der EMA schneller auf neue Preise. "
            "Häufig genutzt in MACD und kurzfristigen Trendfiltern."
        ),
        "related_terms": ["SMA", "MACD"],
        "chart_hint": "ema",
    },
    {
        "term": "MACD",
        "slug": "macd",
        "short_definition": "Moving Average Convergence Divergence — Trend- und Momentum-Indikator.",
        "long_explanation": (
            "MACD ist die Differenz zweier EMAs (meist 12 und 26). Die Signallinie (EMA 9) "
            "und das Histogramm helfen, Momentum-Wechsel zu erkennen."
        ),
        "related_terms": ["EMA", "RSI"],
        "chart_hint": "macd",
    },
    {
        "term": "Sharpe Ratio",
        "slug": "sharpe-ratio",
        "short_definition": "Rendite je Einheit Risiko, relativ zum risikofreien Zinssatz.",
        "long_explanation": (
            "Sharpe = (Portfoliorendite − risikofreier Zins) / Volatilität. "
            "Höher ist besser; Werte über 1 gelten oft als akzeptabel."
        ),
        "related_terms": ["Stop-Loss", "Market Cap"],
        "chart_hint": None,
    },
    {
        "term": "Stop-Loss",
        "slug": "stop-loss",
        "short_definition": "Automatische Verkaufsorder unterhalb eines Schwellenkurses zur Verlustbegrenzung.",
        "long_explanation": (
            "Ein Stop-Loss begrenzt das Abwärtsrisiko. Zu enge Stops können durch normale "
            "Volatilität ausgelöst werden; zu weite Stops erhöhen den Maximalverlust."
        ),
        "related_terms": ["Sharpe Ratio"],
        "chart_hint": None,
    },
    {
        "term": "Market Cap",
        "slug": "market-cap",
        "short_definition": "Marktkapitalisierung: Aktienkurs × ausstehende Aktien (bzw. Coin-Preis × Umlaufmenge).",
        "long_explanation": (
            "Die Market Cap beschreibt die Größe eines Unternehmens oder Coins. "
            "Sie ist kein Qualitätsmaß, hilft aber bei der Einordnung (Large/Mid/Small Cap)."
        ),
        "related_terms": ["ETF"],
        "chart_hint": None,
    },
    {
        "term": "ETF",
        "slug": "etf",
        "short_definition": "Exchange Traded Fund — börsengehandelter Fonds, oft indexbasiert.",
        "long_explanation": (
            "ETFs bündeln viele Titel und werden wie Aktien gehandelt. "
            "Beliebt für breite Markt-Exponierung (z. B. S&P 500) bei niedrigen Kosten."
        ),
        "related_terms": ["Market Cap"],
        "chart_hint": None,
    },
]


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

    await session.commit()