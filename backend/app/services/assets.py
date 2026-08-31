from __future__ import annotations

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, AssetClass
from app.services.classify import COINGECKO_IDS, infer_asset_class
from app.services.market import get_quote, persist_quote


class AssetError(ValueError):
    pass


def lookup_meta(symbol: str) -> dict:
    sym = symbol.strip().upper()
    if not sym:
        raise AssetError("Symbol fehlt.")
    if sym in COINGECKO_IDS:
        return {
            "symbol": sym,
            "name": COINGECKO_IDS[sym].replace("-", " ").title(),
            "asset_class": AssetClass.CRYPTO,
            "coingecko_id": COINGECKO_IDS[sym],
            "exchange": None,
        }
    ticker = yf.Ticker(sym)
    try:
        hist = ticker.history(period="5d")
    except Exception as exc:
        raise AssetError(f"{sym} nicht gefunden.") from exc
    if hist is None or hist.empty:
        raise AssetError(f"{sym} nicht gefunden.")
    try:
        info = ticker.info or {}
    except Exception:
        info = {}
    name = info.get("shortName") or info.get("longName") or sym
    qtype = str(info.get("quoteType") or "")
    cls = infer_asset_class(sym, qtype)
    return {
        "symbol": sym,
        "name": name,
        "asset_class": cls,
        "coingecko_id": COINGECKO_IDS.get(sym),
        "exchange": info.get("exchange"),
    }


async def get_or_create_asset(
    session: AsyncSession,
    symbol: str,
    *,
    watched: bool | None = None,
) -> Asset:
    sym = symbol.strip().upper()
    asset = (
        await session.execute(select(Asset).where(Asset.symbol == sym))
    ).scalar_one_or_none()
    if asset:
        if watched is True:
            asset.watched = True
        await session.flush()
        return asset
    meta = lookup_meta(sym)
    asset = Asset(
        symbol=meta["symbol"],
        name=meta["name"],
        asset_class=meta["asset_class"],
        exchange=meta.get("exchange"),
        coingecko_id=meta.get("coingecko_id"),
        currency="USD",
        watched=True if watched is None else watched,
    )
    session.add(asset)
    await session.flush()
    try:
        quote = await get_quote(asset.symbol, session)
        if quote:
            await persist_quote(session, quote)
    except Exception:
        pass
    return asset


async def set_watched(session: AsyncSession, symbol: str, watched: bool) -> Asset:
    asset = await get_or_create_asset(session, symbol, watched=watched)
    asset.watched = watched
    await session.flush()
    return asset