from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Asset, Recommendation
from app.models.enums import AssetClass, RecommendationAction, RecommendationStatus
from app.schemas.portfolio import ApplyRecommendationIn, TransactionOut
from app.schemas.recommendation import RecommendationOut
from app.services.outcomes import ensure_outcome, summarize_outcomes
from app.services.picks import list_buy_picks
from app.services.portfolio import TradeError, execute_recommendation
from app.services.rec_out import recommendation_out
from app.services.swiss_tradable import is_swiss_buyable

router = APIRouter()


@router.get("/picks", response_model=list[RecommendationOut])
async def list_buy_now_picks(
    refresh: bool = False,
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    rows = await list_buy_picks(db, refresh=refresh)
    await db.commit()
    for row in rows:
        await db.refresh(row, attribute_names=["asset", "agent_logs"])
    return [recommendation_out(r) for r in rows]


@router.post("/picks/refresh", response_model=list[RecommendationOut])
async def refresh_buy_now_picks(
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    rows = await list_buy_picks(db, refresh=True)
    await db.commit()
    for row in rows:
        await db.refresh(row, attribute_names=["asset", "agent_logs"])
    return [recommendation_out(r) for r in rows]


@router.get("", response_model=list[RecommendationOut])
async def list_recommendations(
    asset_class: AssetClass | None = None,
    action: RecommendationAction | None = None,
    status: RecommendationStatus | None = None,
    watched: bool | None = None,
    symbol: str | None = None,
    latest: bool = True,
    limit: int = Query(default=80, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[RecommendationOut]:
    stmt = (
        select(Recommendation)
        .join(Asset)
        .options(
            selectinload(Recommendation.asset),
            selectinload(Recommendation.agent_logs),
            selectinload(Recommendation.outcome),
        )
        .order_by(Recommendation.created_at.desc())
        .limit(200 if latest else limit)
    )
    if action:
        stmt = stmt.where(Recommendation.action == action)
    if status:
        stmt = stmt.where(Recommendation.status == status)
    if watched is not None:
        stmt = stmt.where(Asset.watched.is_(watched))
    if asset_class:
        stmt = stmt.where(Asset.asset_class == asset_class)
    if symbol:
        stmt = stmt.where(Asset.symbol == symbol.upper())
    rows = (await db.execute(stmt)).scalars().all()
    rows = [
        row
        for row in rows
        if is_swiss_buyable(row.asset.symbol, row.asset.asset_class, row.asset.exchange)
    ]
    if latest:
        seen: set = set()
        uniq: list[Recommendation] = []
        for row in rows:
            if row.asset_id in seen:
                continue
            seen.add(row.asset_id)
            uniq.append(row)
            if len(uniq) >= limit:
                break
        rows = uniq
    return [recommendation_out(r) for r in rows]


@router.get("/outcomes/summary")
async def outcome_summary(db: AsyncSession = Depends(get_db)) -> dict:
    return await summarize_outcomes(db)


@router.get("/{rec_id}", response_model=RecommendationOut)
async def get_recommendation(
    rec_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> RecommendationOut:
    rec = (
        await db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.asset),
                selectinload(Recommendation.agent_logs),
                selectinload(Recommendation.outcome),
            )
            .where(Recommendation.id == rec_id)
        )
    ).scalar_one_or_none()
    if rec is None:
        raise HTTPException(404, "Empfehlung nicht gefunden")
    try:
        await ensure_outcome(db, rec)
        await db.commit()
    except Exception:
        await db.rollback()
    rec = (
        await db.execute(
            select(Recommendation)
            .options(
                selectinload(Recommendation.asset),
                selectinload(Recommendation.agent_logs),
                selectinload(Recommendation.outcome),
            )
            .where(Recommendation.id == rec_id)
        )
    ).scalar_one()
    return recommendation_out(rec)


@router.post("/{rec_id}/execute", response_model=TransactionOut)
async def apply_to_wallet(
    rec_id: UUID,
    payload: ApplyRecommendationIn | None = None,
    db: AsyncSession = Depends(get_db),
) -> TransactionOut:
    rec = (
        await db.execute(
            select(Recommendation)
            .options(selectinload(Recommendation.asset))
            .where(Recommendation.id == rec_id)
        )
    ).scalar_one_or_none()
    if rec is None:
        raise HTTPException(404, "Empfehlung nicht gefunden")
    body = payload or ApplyRecommendationIn()
    try:
        tx = await execute_recommendation(db, rec, quantity=body.quantity, price=body.price)
    except TradeError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.refresh(tx, attribute_names=["asset"])
    return TransactionOut.model_validate(tx)