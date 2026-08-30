from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _APP_DIR.parent
_ROOT_DIR = _BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_ROOT_DIR / ".env", _BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Wallstreet"
    app_env: str = "development"
    app_port: int = 4499
    backend_port: int = 8000
    log_level: str = "info"
    cors_origins: str = "http://localhost:4499,http://127.0.0.1:4499"

    database_url: str = (
        "postgresql+asyncpg://wallstreet:wallstreet@localhost:5432/wallstreet"
    )
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_mini_model: str = "gpt-4o-mini"

    default_cash: float = 100_000
    default_currency: str = "USD"

    agent_cron_minutes: int = 30
    watchlist: str = "AAPL,MSFT,NVDA,VOO,BTC-USD,ETH-USD"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def watchlist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.watchlist.split(",") if s.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()