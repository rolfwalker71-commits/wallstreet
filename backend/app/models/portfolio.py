from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.transaction import Transaction


class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Paper-Trading-Depot (später um Live-Broker erweiterbar)."""

    __tablename__ = "portfolios"

    name: Mapped[str] = mapped_column(String(128))
    base_currency: Mapped[str] = mapped_column(String(8), default="USD")
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
    broker_adapter: Mapped[str | None] = mapped_column(String(64), nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="portfolio",
        cascade="all, delete-orphan",
    )


class Position(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Aktuelle Bestandshaltung in einem Depot."""

    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "asset_id", name="uq_position_portfolio_asset"),
    )

    portfolio_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
    )
    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        index=True,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    avg_cost: Mapped[Decimal] = mapped_column(Numeric(20, 8))

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")
    asset: Mapped["Asset"] = relationship(back_populates="positions")