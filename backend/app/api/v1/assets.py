from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Asset
from app.models.enums import AssetClass
from app.schemas.common import AssetCreateIn, AssetOut, AssetWatchIn, Paginated
from app.services.assets import AssetError, get_or_create_asset, set_watched

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


@router.get("/{symbol}", response_model=AssetOut)
async def get_asset(symbol: str, db: AsyncSession = Depends(get_db)) -> AssetOut:
    row = (
        await db.execute(select(Asset).where(Asset.symbol == symbol.upper()))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Titel nicht gefunden")
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
