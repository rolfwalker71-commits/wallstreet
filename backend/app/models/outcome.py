from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


class SignalOutcome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Gespeicherte Rendite eines Signals nach 5 / 20 / 60 Handelstagen."""

    __tablename__ = "signal_outcomes"
    __table_args__ = (UniqueConstraint("recommendation_id", name="uq_signal_outcome_rec"),)

    recommendation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        index=True,
    )
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    ret_5d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    ret_20d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    ret_60d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    bench_5d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    bench_20d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    bench_60d: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    computed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    recommendation: Mapped["Recommendation"] = relationship(back_populates="outcome")
