import enum


class AssetClass(str, enum.Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"
    BOND = "bond"
    FUND = "fund"
    COMMODITY = "commodity"
    FOREX = "forex"


class RecommendationAction(str, enum.Enum):
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"


class RecommendationStatus(str, enum.Enum):
    OPEN = "open"
    EXECUTED = "executed"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class AgentName(str, enum.Enum):
    RESEARCH = "research"
    QUANT = "quant"
    STRATEGIST = "strategist"
    EDUCATOR = "educator"


class AgentLogStatus(str, enum.Enum):
    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TransactionSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class TransactionSource(str, enum.Enum):
    MANUAL = "manual"
    AGENT = "agent"
    LIVE_BROKER = "live_broker"


class Sentiment(str, enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"