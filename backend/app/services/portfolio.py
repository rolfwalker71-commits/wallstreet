from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Asset, AssetClass, Portfolio, Position, Recommendation, Transaction
from app.models.enums import (
    RecommendationAction,
    RecommendationStatus,
    TransactionSide,
    TransactionSource,
)
from app.schemas.portfolio import ExecuteTradeIn
from app.services.allocation import compute_allocation
from app.services.market import benchmark_return_pct, get_quote


class TradeError(ValueError):
    pass


async def get_primary_portfolio(session: AsyncSession) -> Portfolio | None:
    result = await session.execute(
        select(Portfolio)
        .options(
            selectinload(Portfolio.positions).selectinload(Position.asset),
            selectinload(Portfolio.transactions).selectinload(Transaction.asset),
        )
        .order_by(Portfolio.created_at.asc())
        .limit(1)
    )
    return result.scalars().first()


async def execute_trade(session: AsyncSession, payload: ExecuteTradeIn) -> Transaction:
    portfolio = await session.get(Portfolio, payload.portfolio_id)
    if portfolio is None:
        raise TradeError("Depot nicht gefunden.")

    asset = (
        await session.execute(select(Asset).where(Asset.symbol == payload.symbol.upper()))
    ).scalar_one_or_none()
    if asset is None:
        raise TradeError(f"Asset {payload.symbol} unbekannt.")

    try:
        quote = await get_quote(asset.symbol, session)
    except Exception:
        quote = None
    if payload.price is not None:
        price = payload.price
        if quote:
            asset.last_price = quote.price
            asset.last_price_at = quote.as_of
    elif quote is not None:
        price = quote.price
        asset.last_price = quote.price
        asset.last_price_at = quote.as_of
    elif asset.last_price is not None:
        price = asset.last_price
    else:
        raise TradeError("Kein Kurs — bitte Kaufpreis manuell eintragen.")
    notional = price * payload.quantity

    realized = None
    if payload.side == TransactionSide.BUY:
        if portfolio.cash_balance < notional:
            raise TradeError("Nicht genug Cash im Paper-Depot.")
        portfolio.cash_balance -= notional
        await _upsert_position(session, portfolio, asset, payload.quantity, price, buy=True)
    elif payload.side == TransactionSide.SELL:
        position = (
            await session.execute(
                select(Position).where(
                    Position.portfolio_id == portfolio.id,
                    Position.asset_id == asset.id,
                )
            )
        ).scalar_one_or_none()
        if position is None or position.quantity < payload.quantity:
            raise TradeError("Position reicht für den Verkauf nicht aus.")
        realized = (price - position.avg_cost) * payload.quantity
        portfolio.cash_balance += notional
        await _upsert_position(session, portfolio, asset, payload.quantity, price, buy=False)
    else:
        raise TradeError("Nur Kauf und Verkauf sind hier manuell erlaubt.")

    tx = Transaction(
        portfolio_id=portfolio.id,
        asset_id=asset.id,
        recommendation_id=payload.recommendation_id,
        side=payload.side,
        source=payload.source,
        quantity=payload.quantity,
        price=price,
        fee=Decimal("0"),
        realized_pnl=realized,
        currency=asset.currency,
        executed_at=payload.executed_at or datetime.now(UTC),
        note=payload.note,
    )
    session.add(tx)

    if payload.recommendation_id:
        rec = await session.get(Recommendation, payload.recommendation_id)
        if rec:
            rec.status = RecommendationStatus.EXECUTED

    await session.flush()
    await session.refresh(tx)
    return tx


async def _upsert_position(
    session: AsyncSession,
    portfolio: Portfolio,
    asset: Asset,
    qty: Decimal,
    price: Decimal,
    *,
    buy: bool,
) -> None:
    position = (
        await session.execute(
            select(Position).where(
                Position.portfolio_id == portfolio.id,
                Position.asset_id == asset.id,
            )
        )
    ).scalar_one_or_none()

    if buy:
        if position is None:
            session.add(
                Position(
                    portfolio_id=portfolio.id,
                    asset_id=asset.id,
                    quantity=qty,
                    avg_cost=price,
                )
            )
            return
        total_cost = position.avg_cost * position.quantity + price * qty
        position.quantity += qty
        position.avg_cost = total_cost / position.quantity
        return

    if position is None:
        return
    position.quantity -= qty
    if position.quantity <= 0:
        await session.delete(position)


async def decorate_portfolio(session: AsyncSession, portfolio: Portfolio) -> dict:
    positions_out: list[dict] = []
    holdings = Decimal("0")
    invested = Decimal("0")
    unrealized = Decimal("0")
    first_buy: dict[str, datetime] = {}
    for tx in portfolio.transactions:
        if tx.side == TransactionSide.BUY and tx.asset_id and tx.executed_at:
            key = str(tx.asset_id)
            if key not in first_buy or tx.executed_at < first_buy[key]:
                first_buy[key] = tx.executed_at

    for pos in portfolio.positions:
        quote = None
        try:
            quote = await get_quote(pos.asset.symbol, session)
        except Exception:
            quote = None
        price = quote.price if quote else pos.asset.last_price
        cost = pos.avg_cost * pos.quantity
        invested += cost
        mv = (price * pos.quantity) if price is not None else None
        pnl = (mv - cost) if mv is not None else None
        pnl_pct = (
            float(pnl / cost * 100) if pnl is not None and cost != 0 else None
        )
        if mv is not None:
            holdings += mv
        if pnl is not None:
            unrealized += pnl
        positions_out.append(
            {
                "id": pos.id,
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "cost_basis": cost,
                "current_price": price,
                "opened_at": first_buy.get(str(pos.asset_id), pos.created_at),
                "asset": pos.asset,
                "market_value": mv,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": pnl_pct,
                "quote_as_of": quote.as_of if quote else pos.asset.last_price_at,
                "delayed": quote.delayed if quote else None,
                "market_open": quote.market_open if quote else None,
                "session_label": quote.session_label if quote else None,
                "freshness_label": quote.freshness_label if quote else None,
                "as_of_precision": quote.as_of_precision if quote else None,
            }
        )

    realized = sum((tx.realized_pnl or Decimal("0")) for tx in portfolio.transactions)
    equity = portfolio.cash_balance + holdings
    total_return = None
    if portfolio.initial_capital:
        total_return = float((equity - portfolio.initial_capital) / portfolio.initial_capital * 100)
    bench = _safe_benchmark()
    vs_bench = None
    if total_return is not None and bench is not None:
        vs_bench = total_return - bench

    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "base_currency": portfolio.base_currency,
        "cash_balance": portfolio.cash_balance,
        "initial_capital": portfolio.initial_capital,
        "is_paper": portfolio.is_paper,
        "broker_adapter": portfolio.broker_adapter,
        "equity": equity,
        "invested_cost": invested,
        "holdings_value": holdings,
        "unrealized_pnl": unrealized,
        "realized_pnl": realized,
        "total_return_pct": total_return,
        "positions": positions_out,
        "benchmark_return_pct": bench,
        "vs_benchmark_pct": vs_bench,
        "target_stock_pct": getattr(portfolio, "target_stock_pct", None),
        "target_bond_pct": getattr(portfolio, "target_bond_pct", None),
        "target_commodity_pct": getattr(portfolio, "target_commodity_pct", None),
        "target_crypto_pct": getattr(portfolio, "target_crypto_pct", None),
        "target_cash_pct": getattr(portfolio, "target_cash_pct", None),
        "max_single_position_pct": getattr(portfolio, "max_single_position_pct", None),
        "allocation": compute_allocation(portfolio, positions_out),
    }


def _safe_benchmark() -> float | None:
    try:
        return benchmark_return_pct("1y")
    except Exception:
        return None


def is_executable(recommendation: Recommendation) -> bool:
    return (
        recommendation.status == RecommendationStatus.OPEN
        and recommendation.action in {RecommendationAction.BUY, RecommendationAction.SELL}
    )


def default_qty(recommendation: Recommendation) -> Decimal:
    if recommendation.proposed_qty and recommendation.proposed_qty > 0:
        return recommendation.proposed_qty
    if recommendation.asset.asset_class == AssetClass.CRYPTO:
        return Decimal("0.01")
    return Decimal("1")


async def execute_recommendation(
    session: AsyncSession,
    recommendation: Recommendation,
    quantity: Decimal | None = None,
    price: Decimal | None = None,
) -> Transaction:
    if recommendation.status != RecommendationStatus.OPEN:
        raise TradeError("Diese Empfehlung ist nicht mehr offen.")
    if recommendation.action not in {RecommendationAction.BUY, RecommendationAction.SELL}:
        raise TradeError("Nur Kauf- oder Verkaufssignale können ins Depot.")
    portfolio = await get_primary_portfolio(session)
    if portfolio is None:
        raise TradeError("Kein Paper-Depot vorhanden.")
    qty = quantity if quantity and quantity > 0 else default_qty(recommendation)
    fill = price if price and price > 0 else None
    payload = ExecuteTradeIn(
        portfolio_id=portfolio.id,
        symbol=recommendation.asset.symbol,
        side=TransactionSide(recommendation.action.value),
        quantity=qty,
        price=fill,
        recommendation_id=recommendation.id,
        source=TransactionSource.MANUAL,
        note="Empfehlung manuell ins Paper-Depot übernommen",
    )
    return await execute_trade(session, payload)