from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AssetClass
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.news import NewsItem
    from app.models.portfolio import Position
    from app.models.recommendation import Recommendation
    from app.models.transaction import Transaction


class Asset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Handelbares Instrument: Aktie, ETF, Crypto oder Obligation."""

    __tablename__ = "assets"

    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(AssetClass, name="asset_class", native_enum=True),
        index=True,
    )
    exchange: Mapped[str | None] = mapped_column(String(64), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    isin: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    coingecko_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_price: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 8),
        nullable=True,
    )
    last_price_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    watched: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="asset",
    )
    positions: Mapped[list["Position"]] = relationship(
        back_populates="asset",
    )
    news_items: Mapped[list["NewsItem"]] = relationship(
        back_populates="asset",
    )