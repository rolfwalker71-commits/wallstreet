from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.market import HistoryOut, NewsOut, QuoteOut, TechnicalsOut
from app.services.market import get_history_series, get_quote, get_technicals, persist_quote
from app.services.news import fetch_rss, filter_for_symbol

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