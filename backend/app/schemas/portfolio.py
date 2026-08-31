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
    quote_as_of: datetime | None = None
    delayed: bool | None = None
    market_open: bool | None = None
    session_label: str | None = None
    freshness_label: str | None = None
    as_of_precision: str | None = None


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
    target_stock_pct: Decimal | None = None
    target_bond_pct: Decimal | None = None
    target_commodity_pct: Decimal | None = None
    target_crypto_pct: Decimal | None = None
    target_cash_pct: Decimal | None = None
    max_single_position_pct: Decimal | None = None
    allocation: dict | None = None


class PortfolioTargetsIn(BaseModel):
    target_stock_pct: Decimal = Field(ge=0, le=100)
    target_bond_pct: Decimal = Field(ge=0, le=100)
    target_commodity_pct: Decimal = Field(ge=0, le=100)
    target_crypto_pct: Decimal = Field(ge=0, le=100)
    target_cash_pct: Decimal = Field(ge=0, le=100)
    max_single_position_pct: Decimal = Field(default=Decimal("5"), ge=1, le=40)


class ExecuteTradeIn(BaseModel):
    portfolio_id: UUID
    symbol: str
    side: TransactionSide
    quantity: Decimal = Field(gt=0)
    price: Decimal | None = Field(default=None, gt=0)
    recommendation_id: UUID | None = None
    source: TransactionSource = TransactionSource.MANUAL
    note: str | None = None
    executed_at: datetime | None = None


class ApplyRecommendationIn(BaseModel):
    quantity: Decimal | None = Field(default=None, gt=0)
    price: Decimal | None = Field(default=None, gt=0)