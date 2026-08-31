from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Asset, Transaction
from app.models.enums import TransactionSource
from app.schemas.portfolio import ExecuteTradeIn, PortfolioOut, PortfolioTargetsIn, TransactionOut
from app.services.assets import AssetError, get_or_create_asset
from app.services.core_products import symbol_for_isin
from app.services.csv_trades import parse_trade_rows
from app.services.equity import portfolio_curve
from app.services.market import get_quote
from app.services.portfolio import (
    TradeError,
    decorate_portfolio,
    execute_trade,
    get_primary_portfolio,
)
from app.services.rebalance import propose_rebalance
from app.services.swiss_tradable import is_swiss_buyable

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


class CsvImportIn(BaseModel):
    csv: str


async def _resolve_import_symbol(db: AsyncSession, row: dict) -> str:
    if row.get("symbol"):
        return row["symbol"]
    isin = row.get("isin")
    if not isin:
        raise TradeError("ISIN oder Symbol fehlt.")
    existing = (
        await db.execute(select(Asset).where(Asset.isin == isin))
    ).scalar_one_or_none()
    if existing:
        return existing.symbol
    core = symbol_for_isin(isin)
    if core:
        return core
    raise TradeError(f"ISIN {isin} unbekannt — bitte Symbol in der Zeile setzen.")


@router.get("/curve")
async def equity_curve(db: AsyncSession = Depends(get_db)) -> dict:
    pf = await get_primary_portfolio(db)
    if pf is None:
        raise HTTPException(404, "Kein Depot vorhanden")
    return await portfolio_curve(pf)


@router.get("/rebalance")
async def rebalance_plan(db: AsyncSession = Depends(get_db)) -> dict:
    pf = await get_primary_portfolio(db)
    if pf is None:
        raise HTTPException(404, "Kein Depot vorhanden")
    data = await decorate_portfolio(db, pf)
    held = {
        (p["asset"].symbol if hasattr(p["asset"], "symbol") else p["asset"]["symbol"]).upper()
        for p in data["positions"]
    }
    quotes: dict = {}
    from app.services.picks import _plan_symbols

    for symbol, _gap in _plan_symbols(data["allocation"], held):
        try:
            asset = await get_or_create_asset(db, symbol, watched=True)
        except AssetError:
            continue
        try:
            quote = await get_quote(asset.symbol, db)
        except Exception:
            quote = None
        price = float(quote.price) if quote else (float(asset.last_price) if asset.last_price else None)
        quotes[symbol] = {
            "price": price,
            "currency": asset.currency,
            "name": asset.name,
            "asset_class": asset.asset_class,
            "exchange": asset.exchange,
            "swiss_buyable": is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange),
        }
    proposals = propose_rebalance(allocation=data["allocation"], held=held, quotes=quotes, limit=2)
    return {"items": proposals}


@router.post("/import")
async def import_csv(payload: CsvImportIn, db: AsyncSession = Depends(get_db)) -> dict:
    pf = await get_primary_portfolio(db)
    if pf is None:
        raise HTTPException(404, "Kein Depot vorhanden")
    rows, errors = parse_trade_rows(payload.csv)
    imported: list[dict] = []
    for row in rows:
        try:
            symbol = await _resolve_import_symbol(db, row)
            try:
                await get_or_create_asset(db, symbol, watched=True)
            except AssetError as exc:
                raise TradeError(str(exc)) from exc
            tx = await execute_trade(
                db,
                ExecuteTradeIn(
                    portfolio_id=pf.id,
                    symbol=symbol,
                    side=row["side"],
                    quantity=row["qty"],
                    price=row["price"],
                    source=TransactionSource.MANUAL,
                    note="CSV-Import",
                    executed_at=row["date"],
                ),
            )
            imported.append({"row": row["row"], "id": str(tx.id), "symbol": symbol})
        except (TradeError, AssetError) as exc:
            errors.append({"row": row["row"], "error": str(exc)})
    await db.commit()
    return {"imported": len(imported), "items": imported, "errors": errors}