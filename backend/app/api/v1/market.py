from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Asset, Recommendation
from app.schemas.market import HistoryOut, NewsOut, QuoteOut, TechnicalsOut
from app.services.dossier import build_dossier, fetch_yahoo_facts
from app.services.market import get_history_series, get_quote, get_technicals, persist_quote
from app.services.news import fetch_rss, filter_for_symbol
from app.services.outcomes import outcome_to_dict

router = APIRouter()


@router.get("/quote/{symbol}", response_model=QuoteOut)
async def quote(symbol: str, db: AsyncSession = Depends(get_db)) -> QuoteOut:
    q = await get_quote(symbol.upper(), db)
    if q is None:
        raise HTTPException(404, "Kein Kurs gefunden")
    await persist_quote(db, q)
    return q


@router.get("/technicals/{symbol}", response_model=TechnicalsOut)
async def technicals(symbol: str) -> TechnicalsOut:
    return get_technicals(symbol.upper())


@router.get("/history/{symbol}", response_model=HistoryOut)
async def history(
    symbol: str,
    period: str = Query(default="6mo"),
    since: datetime | None = Query(default=None),
) -> HistoryOut:
    return get_history_series(symbol.upper(), period, since=since)


@router.get("/news", response_model=list[NewsOut])
async def news(symbol: str | None = Query(default=None)) -> list[NewsOut]:
    items = fetch_rss()
    if symbol:
        items = filter_for_symbol(items, symbol.upper()) or items[:8]
    return items[:40]


async def _compare_side(db: AsyncSession, symbol: str) -> dict:
    sym = symbol.upper()
    asset = (await db.execute(select(Asset).where(Asset.symbol == sym))).scalar_one_or_none()
    quote = await get_quote(sym, db)
    if quote:
        await persist_quote(db, quote)
    tech = get_technicals(sym)
    yahoo = fetch_yahoo_facts(sym)
    dossier = build_dossier(asset, yahoo) if asset else None
    rec = None
    if asset:
        rec = (
            await db.execute(
                select(Recommendation)
                .options(selectinload(Recommendation.outcome))
                .where(Recommendation.asset_id == asset.id)
                .order_by(Recommendation.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    return {
        "symbol": sym,
        "name": asset.name if asset else (quote.name if quote else sym),
        "currency": asset.currency if asset else (quote.currency if quote else "USD"),
        "price": str(quote.price) if quote else (str(asset.last_price) if asset and asset.last_price else None),
        "change_pct": quote.change_pct if quote else None,
        "as_of": quote.as_of.isoformat() if quote else None,
        "ter": dossier.get("ter") if dossier else None,
        "dividend_yield": dossier.get("dividend_yield") if dossier else None,
        "sma_20": tech.sma_20,
        "sma_50": tech.sma_50,
        "last_signal": (
            {
                "id": str(rec.id),
                "action": rec.action.value,
                "confidence": str(rec.confidence),
                "created_at": rec.created_at.isoformat(),
                "outcome": outcome_to_dict(rec.outcome),
            }
            if rec
            else None
        ),
    }


@router.get("/compare")
async def compare_titles(
    a: str = Query(min_length=1),
    b: str = Query(min_length=1),
    db: AsyncSession = Depends(get_db),
) -> dict:
    left = await _compare_side(db, a)
    right = await _compare_side(db, b)
    await db.commit()
    return {"left": left, "right": right}