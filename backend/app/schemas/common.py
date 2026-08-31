from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AssetClass

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
    llm_enabled: bool = False
    llm_model: str | None = None
    llm_mini_model: str | None = None


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int


class AssetCreateIn(BaseModel):
    symbol: str
    watched: bool = True


class AssetWatchIn(BaseModel):
    watched: bool


class AssetNoteIn(BaseModel):
    user_note: str | None = None


class TitleSearchHit(BaseModel):
    symbol: str
    name: str
    exchange: str | None = None
    exchange_label: str | None = None
    quote_type: str | None = None
    asset_class: AssetClass
    swiss_buyable: bool
    watched: bool = False
    in_library: bool = False
    score: int = 0


class AssetOut(ORMModel):
    id: UUID
    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str | None
    currency: str
    last_price: Decimal | None
    last_price_at: datetime | None
    sector: str | None
    isin: str | None = None
    watched: bool = True
    notes: str | None = None
    user_note: str | None = None


class GlossaryTermOut(ORMModel):
    id: UUID
    term: str
    slug: str
    short_definition: str
    long_explanation: str | None
    related_terms: list[str] | None
    chart_hint: str | None