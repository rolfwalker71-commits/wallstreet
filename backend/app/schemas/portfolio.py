from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import TransactionSide, TransactionSource
from app.schemas.common import AssetOut, ORMModel


class PositionOut(ORMModel):
    id: UUID
    quantity: Decimal
    avg_cost: Decimal
    cost_basis: Decimal | None = None
    current_price: Decimal | None = None
    opened_at: datetime | None = None
    asset: AssetOut
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    unrealized_pnl_pct: float | None = None


class TransactionOut(ORMModel):
    id: UUID
    side: TransactionSide
    source: TransactionSource
    quantity: Decimal
    price: Decimal
    fee: Decimal
    realized_pnl: Decimal | None = None
    currency: str
    executed_at: datetime
    note: str | None
    asset: AssetOut | None = None


class PortfolioOut(ORMModel):
    id: UUID
    name: str
    base_currency: str
    cash_balance: Decimal
    initial_capital: Decimal
    is_paper: bool
    broker_adapter: str | None
    equity: Decimal | None = None
    invested_cost: Decimal | None = None
    holdings_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    total_return_pct: float | None = None
    positions: list[PositionOut] = []
    benchmark_return_pct: float | None = None
    vs_benchmark_pct: float | None = None


class ExecuteTradeIn(BaseModel):
    portfolio_id: UUID
    symbol: str
    side: TransactionSide
    quantity: Decimal = Field(gt=0)
    price: Decimal | None = Field(default=None, gt=0)
    recommendation_id: UUID | None = None
    source: TransactionSource = TransactionSource.MANUAL
    note: str | None = None


class ApplyRecommendationIn(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, gt=0)