from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import httpx
import pandas as pd
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetClass
from app.schemas.market import HistoryOut, HistoryPoint, QuoteOut, TechnicalsOut
from app.services.classify import COINGECKO_IDS, infer_asset_class
from app.services.indicators import compute_technicals
from app.services.session import (
    VENUES,
    bar_as_of,
    looks_like_daily_midnight,
    session_close_as_of,
    session_info,
    venue_key,
)

CRYPTO_VS = "usd"


def _infer_class(symbol: str) -> AssetClass:
    return infer_asset_class(symbol)


async def fetch_coingecko_quote(coingecko_id: str, symbol: str) -> QuoteOut | None:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coingecko_id,
        "vs_currencies": CRYPTO_VS,
        "include_24hr_change": "true",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get(coingecko_id) or {}
    price = data.get(CRYPTO_VS)
    if price is None:
        return None
    return QuoteOut(
        symbol=symbol,
        name=coingecko_id.title(),
        asset_class=AssetClass.CRYPTO,
        price=Decimal(str(price)),
        change_pct=data.get(f"{CRYPTO_VS}_24h_change"),
        currency="USD",
        as_of=datetime.now(UTC),
        delayed=False,
        source="CoinGecko",
    )


def fetch_yfinance_quote(symbol: str) -> QuoteOut | None:
    ticker = yf.Ticker(symbol)
    try:
        daily = ticker.history(period="5d", interval="1d", auto_adjust=True)
    except Exception:
        daily = None
    if daily is None or daily.empty:
        return None
    daily_close = daily["Close"].dropna()
    if daily_close.empty:
        return None
    price = float(daily_close.iloc[-1])
    prev = float(daily_close.iloc[-2]) if len(daily_close) > 1 else None
    as_of = bar_as_of(daily_close.index[-1])
    precision = "day"
    volume = None
    if "Volume" in daily.columns and not daily["Volume"].dropna().empty:
        volume = float(daily["Volume"].dropna().iloc[-1])

    guess = session_info(symbol, _infer_class(symbol))
    if guess.market_open:
        try:
            intra = ticker.history(period="1d", interval="5m", auto_adjust=True)
        except Exception:
            intra = None
        if intra is not None and not intra.empty:
            intra_close = intra["Close"].dropna()
            if not intra_close.empty:
                price = float(intra_close.iloc[-1])
                as_of = bar_as_of(intra_close.index[-1])
                precision = "minute"
                if "Volume" in intra.columns and not intra["Volume"].dropna().empty:
                    volume = float(intra["Volume"].dropna().iloc[-1])

    change = ((price - prev) / prev * 100) if prev else None
    return QuoteOut(
        symbol=symbol,
        name=symbol,
        asset_class=_infer_class(symbol),
        price=Decimal(str(round(price, 6))),
        change_pct=change,
        currency="USD",
        as_of=as_of,
        volume=volume,
        delayed=True,
        source="Yahoo Finance",
        as_of_precision=precision,
    )


async def get_quote(symbol: str, session: AsyncSession | None = None) -> QuoteOut | None:
    asset: Asset | None = None
    if session is not None:
        asset = (
            await session.execute(select(Asset).where(Asset.symbol == symbol.upper()))
        ).scalar_one_or_none()

    quote: QuoteOut | None = None
    if asset and asset.asset_class == AssetClass.CRYPTO and asset.coingecko_id:
        quote = await fetch_coingecko_quote(asset.coingecko_id, symbol.upper())

    if quote is None and symbol.upper() in COINGECKO_IDS:
        quote = await fetch_coingecko_quote(COINGECKO_IDS[symbol.upper()], symbol.upper())

    if quote is None:
        try:
            quote = fetch_yfinance_quote(symbol)
        except Exception:
            quote = None
    if quote is None:
        return None
    precision = quote.as_of_precision or "minute"
    as_of = quote.as_of
    is_crypto = quote.asset_class == AssetClass.CRYPTO or quote.symbol.upper().endswith("-USD")
    if not is_crypto:
        key = venue_key(quote.symbol, asset.exchange if asset else None)
        tz_name = VENUES[key][1]
        if precision == "day" and looks_like_daily_midnight(as_of, tz_name):
            as_of = session_close_as_of(as_of, key)
    info = session_info(
        quote.symbol,
        quote.asset_class,
        asset.exchange if asset else None,
        last_print=as_of,
        as_of_precision=precision,
    )
    return quote.model_copy(
        update={
            "as_of": as_of,
            "delayed": info.delayed,
            "source": info.source,
            "venue_label": info.venue_label,
            "market_open": info.market_open,
            "session_label": info.session_label,
            "freshness_label": info.freshness_label,
            "as_of_precision": info.as_of_precision,
        }
    )


ALLOWED_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}

PERIOD_INTERVAL = {
    "1d": "5m",
    "5d": "30m",
    "1mo": "1d",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d",
    "2y": "1d",
    "5y": "1d",
}


def resolve_history_period(period: str) -> str:
    return period if period in ALLOWED_PERIODS else "6mo"


def fetch_history(symbol: str, period: str = "6mo") -> pd.DataFrame:
    chosen = resolve_history_period(period)
    interval = PERIOD_INTERVAL[chosen]
    try:
        hist = yf.Ticker(symbol).history(period=chosen, interval=interval, auto_adjust=True)
    except Exception:
        hist = None
    if hist is None or hist.empty:
        if interval != "1d":
            try:
                hist = yf.Ticker(symbol).history(period=chosen, interval="1d", auto_adjust=True)
            except Exception:
                return pd.DataFrame()
        else:
            return pd.DataFrame()
    return hist if hist is not None else pd.DataFrame()


def get_history_series(
    symbol: str,
    period: str = "6mo",
    since: datetime | None = None,
) -> HistoryOut:
    chosen = resolve_history_period(period)
    hist = fetch_history(symbol, period=chosen)
    if hist.empty:
        return HistoryOut(symbol=symbol.upper(), period=chosen, points=[])
    closes = hist["Close"].dropna()
    daily = PERIOD_INTERVAL[chosen] == "1d"
    if daily:
        sma20 = closes.rolling(20, min_periods=20).mean()
        sma50 = closes.rolling(50, min_periods=50).mean()
    else:
        sma20 = pd.Series(index=closes.index, dtype=float)
        sma50 = pd.Series(index=closes.index, dtype=float)
    before: list[HistoryPoint] = []
    after: list[HistoryPoint] = []
    since_cmp = None
    if since is not None:
        since_cmp = since if since.tzinfo else since.replace(tzinfo=UTC)
    for idx, close in closes.items():
        ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx
        stamp = idx.isoformat() if hasattr(idx, "isoformat") else str(idx)
        s20 = sma20.loc[idx]
        s50 = sma50.loc[idx]
        point = HistoryPoint(
            date=stamp,
            close=float(close),
            sma_20=None if pd.isna(s20) else float(s20),
            sma_50=None if pd.isna(s50) else float(s50),
        )
        if since_cmp is None:
            after.append(point)
            continue
        cmp = ts
        if getattr(cmp, "tzinfo", None) is None:
            cmp = cmp.replace(tzinfo=UTC)
        if cmp < since_cmp:
            before.append(point)
        else:
            after.append(point)
    # Kauf am Wochenende / selben Tag: noch keine Kerze danach — letzte Kurse zeigen.
    points = after
    if since_cmp is not None and len(points) < 2:
        points = before[-10:] + after
    return HistoryOut(symbol=symbol.upper(), period=chosen, points=points)


def get_technicals(symbol: str, period: str = "6mo") -> TechnicalsOut:
    hist = fetch_history(symbol, period=period)
    if hist.empty:
        return TechnicalsOut(symbol=symbol)
    closes = hist["Close"].dropna()
    data = compute_technicals(closes)
    return TechnicalsOut(symbol=symbol, **data)


async def persist_quote(session: AsyncSession, quote: QuoteOut) -> Asset | None:
    asset = (
        await session.execute(select(Asset).where(Asset.symbol == quote.symbol))
    ).scalar_one_or_none()
    if asset is None:
        return None
    asset.last_price = quote.price
    asset.last_price_at = quote.as_of
    await session.flush()
    try:
        from app.services.alerts import check_alerts

        await check_alerts(
            session,
            symbol=quote.symbol,
            price=float(quote.price),
            change_pct=quote.change_pct,
        )
    except Exception:
        pass
    return asset


def benchmark_return_pct(period: str = "1y") -> float | None:
    """S&P 500 via VOO als Paper-Benchmark."""
    hist = fetch_history("VOO", period=period)
    if hist.empty or len(hist) < 2:
        return None
    first = float(hist["Close"].iloc[0])
    last = float(hist["Close"].iloc[-1])
    if first == 0:
        return None
    return (last - first) / first * 100