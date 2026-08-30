from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import AssetClass, Sentiment


class QuoteOut(BaseModel):
    symbol: str
    name: str | None = None
    asset_class: AssetClass | None = None
    price: Decimal
    change_pct: float | None = None
    currency: str = "USD"
    as_of: datetime
    volume: float | None = None


class TechnicalsOut(BaseModel):
    symbol: str
    rsi_14: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    last_close: float | None = None


class HistoryPoint(BaseModel):
    date: str
    close: float
    sma_20: float | None = None
    sma_50: float | None = None


class HistoryOut(BaseModel):
    symbol: str
    period: str
    points: list[HistoryPoint]


class NewsOut(BaseModel):
    title: str
    url: str
    source: str
    published_at: datetime | None = None
    summary: str | None = None
    sentiment: Sentiment | None = None
    symbol: str | None = None