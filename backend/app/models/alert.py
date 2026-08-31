from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AlertKind
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.asset import Asset


class PriceAlert(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Kursalarm ohne LLM: unter/über Preis oder ±X % heute."""

    __tablename__ = "price_alerts"

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[AlertKind] = mapped_column(
        Enum(
            AlertKind,
            name="alert_kind",
            native_enum=True,
            values_callable=lambda members: [item.value for item in members],
        ),
        index=True,
    )
    threshold: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    fired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="price_alerts")
