from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class GlossaryTerm(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Börsen-Fachbegriff, gepflegt vom Finance-Educator-Agenten."""

    __tablename__ = "glossary_terms"
    __table_args__ = (UniqueConstraint("slug", name="uq_glossary_slug"),)

    term: Mapped[str] = mapped_column(String(128), index=True)
    slug: Mapped[str] = mapped_column(String(128), index=True)
    short_definition: Mapped[str] = mapped_column(Text)
    long_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_terms: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    chart_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)