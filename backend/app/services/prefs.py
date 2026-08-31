from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.settings import AppSetting

DISPLAY_CURRENCIES = ("CHF", "USD", "EUR", "native")
AGENT_INTERVALS = (30, 60, 240)


@dataclass
class AppPrefs:
    display_currency: str = "CHF"
    push_min_confidence: float = 0.0
    push_digest: bool = False
    calendar_push: bool = False
    agent_interval_minutes: int = 30
    agent_watchlist_only: bool = False
    agent_mini_only: bool = False

    def as_public(self) -> dict:
        return asdict(self)


KEYS = {
    "display_currency": "CHF",
    "push_min_confidence": "0",
    "push_digest": "false",
    "calendar_push": "false",
    "agent_interval_minutes": "",
    "agent_watchlist_only": "false",
    "agent_mini_only": "false",
}


def _bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float(raw: str | None, default: float = 0.0) -> float:
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _int(raw: str | None, default: int) -> int:
    if raw is None or raw == "":
        return default
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def prefs_from_map(values: dict[str, str]) -> AppPrefs:
    env = get_settings()
    interval = _int(values.get("agent_interval_minutes"), env.agent_cron_minutes)
    if interval not in AGENT_INTERVALS:
        interval = env.agent_cron_minutes if env.agent_cron_minutes in AGENT_INTERVALS else 30
    currency = (values.get("display_currency") or "CHF").upper()
    if currency not in DISPLAY_CURRENCIES:
        currency = "CHF"
    conf = max(0.0, min(1.0, _float(values.get("push_min_confidence"), 0.0)))
    return AppPrefs(
        display_currency=currency,
        push_min_confidence=conf,
        push_digest=_bool(values.get("push_digest")),
        calendar_push=_bool(values.get("calendar_push")),
        agent_interval_minutes=interval,
        agent_watchlist_only=_bool(values.get("agent_watchlist_only")),
        agent_mini_only=_bool(values.get("agent_mini_only")),
    )


def normalize_patch(payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    if "display_currency" in payload:
        ccy = str(payload["display_currency"] or "CHF").upper()
        if ccy not in DISPLAY_CURRENCIES:
            raise ValueError("Anzeige-Währung muss CHF, USD, EUR oder native sein.")
        out["display_currency"] = ccy
    if "push_min_confidence" in payload:
        conf = max(0.0, min(1.0, float(payload["push_min_confidence"])))
        out["push_min_confidence"] = str(conf)
    if "push_digest" in payload:
        out["push_digest"] = "true" if bool(payload["push_digest"]) else "false"
    if "calendar_push" in payload:
        out["calendar_push"] = "true" if bool(payload["calendar_push"]) else "false"
    if "agent_interval_minutes" in payload:
        minutes = int(payload["agent_interval_minutes"])
        if minutes not in AGENT_INTERVALS:
            raise ValueError("Intervall: 30, 60 oder 240 Minuten.")
        out["agent_interval_minutes"] = str(minutes)
    if "agent_watchlist_only" in payload:
        out["agent_watchlist_only"] = "true" if bool(payload["agent_watchlist_only"]) else "false"
    if "agent_mini_only" in payload:
        out["agent_mini_only"] = "true" if bool(payload["agent_mini_only"]) else "false"
    return out


async def load_pref_map(session: AsyncSession) -> dict[str, str]:
    rows = (
        await session.execute(select(AppSetting).where(AppSetting.key.in_(list(KEYS))))
    ).scalars().all()
    values = dict(KEYS)
    for row in rows:
        values[row.key] = row.value
    return values


async def get_prefs(session: AsyncSession) -> AppPrefs:
    return prefs_from_map(await load_pref_map(session))


async def set_pref(session: AsyncSession, key: str, value: str) -> None:
    row = (
        await session.execute(select(AppSetting).where(AppSetting.key == key))
    ).scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(AppSetting(key=key, value=value))
    await session.flush()


async def update_prefs(session: AsyncSession, payload: dict) -> AppPrefs:
    patch = normalize_patch(payload)
    for key, value in patch.items():
        await set_pref(session, key, value)
    return await get_prefs(session)
