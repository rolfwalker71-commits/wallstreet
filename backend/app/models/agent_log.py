from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AgentLogStatus, AgentName
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.recommendation import Recommendation


class AgentLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Transparenter Denkprozess eines Agenten-Laufs."""

    __tablename__ = "agent_logs"

    run_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), index=True)
    agent_name: Mapped[AgentName] = mapped_column(
        Enum(AgentName, name="agent_name", native_enum=True),
        index=True,
    )
    step: Mapped[str] = mapped_column(String(64))
    status: Mapped[AgentLogStatus] = mapped_column(
        Enum(AgentLogStatus, name="agent_log_status", native_enum=True),
        default=AgentLogStatus.STARTED,
    )
    input_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommendation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    recommendation: Mapped["Recommendation | None"] = relationship(
        back_populates="agent_logs",
    )