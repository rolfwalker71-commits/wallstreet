from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Transaction
from app.schemas.portfolio import ExecuteTradeIn, PortfolioOut, PortfolioTargetsIn, TransactionOut
from app.services.portfolio import (
    TradeError,
    decorate_portfolio,
    execute_trade,
    get_primary_portfolio,
)

router = APIRouter()


@router.get("", response_model=PortfolioOut)
async def get_portfolio(db: AsyncSession = Depends(get_db)) -> PortfolioOut:
    pf = await get_primary_portfolio(db)
    if pf is None:
        raise HTTPException(404, "Kein Depot vorhanden")
    data = await decorate_portfolio(db, pf)
    return PortfolioOut.model_validate(data)


@router.patch("/targets", response_model=PortfolioOut)
async def patch_targets(
    payload: PortfolioTargetsIn,
    db: AsyncSession = Depends(get_db),
) -> PortfolioOut:
    pf = await get_primary_portfolio(db)
    if pf is None:
        raise HTTPException(404, "Kein Depot vorhanden")
    total = (
        payload.target_stock_pct
        + payload.target_bond_pct
        + payload.target_commodity_pct
        + payload.target_crypto_pct
        + payload.target_cash_pct
    )
    if abs(float(total) - 100) > 0.6:
        raise HTTPException(400, "Zielquoten müssen zusammen 100 % ergeben.")
    pf.target_stock_pct = payload.target_stock_pct
    pf.target_bond_pct = payload.target_bond_pct
    pf.target_commodity_pct = payload.target_commodity_pct
    pf.target_crypto_pct = payload.target_crypto_pct
    pf.target_cash_pct = payload.target_cash_pct
    pf.max_single_position_pct = payload.max_single_position_pct
    await db.commit()
    pf = await get_primary_portfolio(db)
    data = await decorate_portfolio(db, pf)
    return PortfolioOut.model_validate(data)


@router.get("/transactions", response_model=list[TransactionOut])
async def list_transactions(db: AsyncSession = Depends(get_db)) -> list[TransactionOut]:
    pf = await get_primary_portfolio(db)
    if pf is None:
        return []
    rows = (
        await db.execute(
            select(Transaction)
            .options(selectinload(Transaction.asset))
            .where(Transaction.portfolio_id == pf.id)
            .order_by(Transaction.executed_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return [TransactionOut.model_validate(r) for r in rows]


@router.post("/trades", response_model=TransactionOut)
async def place_trade(
    payload: ExecuteTradeIn,
    db: AsyncSession = Depends(get_db),
) -> TransactionOut:
    try:
        tx = await execute_trade(db, payload)
    except TradeError as exc:
        raise HTTPException(400, str(exc)) from exc
    await db.refresh(tx, attribute_names=["asset"])
    return TransactionOut.model_validate(tx)