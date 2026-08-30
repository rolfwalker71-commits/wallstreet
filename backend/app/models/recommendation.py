from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RecommendationAction, RecommendationStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.agent_log import AgentLog
    from app.models.asset import Asset
    from app.models.transaction import Transaction


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Finale Handlungsempfehlung des Senior-Strategist-Agenten."""

    __tablename__ = "recommendations"

    asset_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        index=True,
    )
    run_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    action: Mapped[RecommendationAction] = mapped_column(
        Enum(RecommendationAction, name="recommendation_action", native_enum=True),
        index=True,
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    risk_reward_ratio: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4),
        nullable=True,
    )
    rationale: Mapped[str] = mapped_column(Text)
    news_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    news_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    technicals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proposed_qty: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    proposed_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", native_enum=True),
        default=RecommendationStatus.OPEN,
        index=True,
    )
    glossary_terms: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    suggested_symbols: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    asset: Mapped["Asset"] = relationship(back_populates="recommendations")
    agent_logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="recommendation",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="recommendation",
    )