from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Asset
from app.models.enums import AssetClass
from app.schemas.common import (
    AssetCreateIn,
    AssetNoteIn,
    AssetOut,
    AssetWatchIn,
    Paginated,
    TitleSearchHit,
)
from app.services.calendar import upcoming_events
from app.services.assets import AssetError, get_or_create_asset, set_watched
from app.services.core_products import core_of
from app.services.dossier import build_dossier, fetch_yahoo_facts, persist_isin
from app.services.title_search import search_titles

router = APIRouter()


@router.get("", response_model=Paginated[AssetOut])
async def list_assets(
    asset_class: AssetClass | None = None,
    watched: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> Paginated[AssetOut]:
    stmt = select(Asset).order_by(Asset.watched.desc(), Asset.symbol)
    if asset_class:
        stmt = stmt.where(Asset.asset_class == asset_class)
    if watched is not None:
        stmt = stmt.where(Asset.watched.is_(watched))
    rows = (await db.execute(stmt)).scalars().all()
    return Paginated(items=[AssetOut.model_validate(r) for r in rows], total=len(rows))


@router.get("/calendar")
async def watchlist_calendar(days: int = Query(default=14, ge=1, le=60), db: AsyncSession = Depends(get_db)) -> list[dict]:
    return await upcoming_events(db, days=days)


@router.get("/search", response_model=list[TitleSearchHit])
async def search_assets(
    q: str = Query(min_length=2, max_length=80),
    db: AsyncSession = Depends(get_db),
) -> list[TitleSearchHit]:
    return await search_titles(db, q)


@router.post("", response_model=AssetOut)
async def create_asset(
    payload: AssetCreateIn,
    db: AsyncSession = Depends(get_db),
) -> AssetOut:
    try:
        asset = await get_or_create_asset(db, payload.symbol, watched=payload.watched)
        if payload.watched:
            asset.watched = True
    except AssetError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    await db.refresh(asset)
    return AssetOut.model_validate(asset)


@router.get("/{symbol}/dossier")
async def get_dossier(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    row = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Titel nicht gefunden")
    yahoo = fetch_yahoo_facts(row.symbol)
    persist_isin(row, yahoo.get("isin") or (core_of(row.symbol) or {}).get("isin"))
    extra = dict(row.extra or {})
    for key in ("pe_ratio", "dividend_yield", "ter", "earnings_date", "ex_dividend_date"):
        if yahoo.get(key) is not None:
            extra[key] = yahoo[key]
    row.extra = extra or None
    await db.commit()
    await db.refresh(row)
    return build_dossier(row, yahoo)


@router.get("/{symbol}", response_model=AssetOut)
async def get_asset(symbol: str, db: AsyncSession = Depends(get_db)) -> AssetOut:
    row = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Titel nicht gefunden")
    return AssetOut.model_validate(row)


@router.patch("/{symbol}/note", response_model=AssetOut)
async def patch_note(
    symbol: str,
    payload: AssetNoteIn,
    db: AsyncSession = Depends(get_db),
) -> AssetOut:
    row = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Titel nicht gefunden")
    text = (payload.user_note or "").strip()
    row.user_note = text or None
    await db.commit()
    await db.refresh(row)
    return AssetOut.model_validate(row)


@router.patch("/{symbol}/watch", response_model=AssetOut)
async def patch_watch(
    symbol: str,
    payload: AssetWatchIn,
    db: AsyncSession = Depends(get_db),
) -> AssetOut:
    try:
        asset = await set_watched(db, symbol, payload.watched)
    except AssetError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.commit()
    await db.refresh(asset)
    return AssetOut.model_validate(asset)
