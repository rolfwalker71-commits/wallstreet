from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from app.models.enums import AssetClass

# Regular cash session only (no pre/after).
VENUES: dict[str, tuple[str, str, time, time]] = {
    "US": ("Nasdaq / NYSE", "America/New_York", time(9, 30), time(16, 0)),
    "SIX": ("SIX Swiss Exchange", "Europe/Zurich", time(9, 0), time(17, 30)),
    "XETRA": ("Xetra", "Europe/Berlin", time(9, 0), time(17, 30)),
    "LSE": ("London Stock Exchange", "Europe/London", time(8, 0), time(16, 30)),
    "EPA": ("Euronext", "Europe/Paris", time(9, 0), time(17, 30)),
    "JPX": ("Tokyo", "Asia/Tokyo", time(9, 0), time(15, 0)),
    "HKEX": ("Hong Kong", "Asia/Hong_Kong", time(9, 30), time(16, 0)),
}

SUFFIX_VENUE = {
    "SW": "SIX",
    "DE": "XETRA",
    "F": "XETRA",
    "L": "LSE",
    "PA": "EPA",
    "AS": "EPA",
    "BR": "EPA",
    "MI": "EPA",
    "T": "JPX",
    "HK": "HKEX",
}


@dataclass(frozen=True)
class SessionInfo:
    venue_label: str
    market_open: bool
    session_label: str
    delayed: bool
    source: str
    freshness_label: str
    as_of_precision: str = "minute"


def venue_key(symbol: str, exchange: str | None = None) -> str:
    sym = (symbol or "").upper()
    if "." in sym:
        suffix = sym.rsplit(".", 1)[-1]
        if suffix in SUFFIX_VENUE:
            return SUFFIX_VENUE[suffix]
    ex = (exchange or "").upper()
    if ex in {"SWX", "SIX", "VTX"}:
        return "SIX"
    if ex in {"GER", "FRA", "XETRA"}:
        return "XETRA"
    if ex in {"LSE", "LON"}:
        return "LSE"
    return "US"


def session_info(
    symbol: str,
    asset_class: AssetClass | str | None = None,
    exchange: str | None = None,
    now: datetime | None = None,
    last_print: datetime | None = None,
    as_of_precision: str = "minute",
) -> SessionInfo:
    cls = asset_class.value if isinstance(asset_class, AssetClass) else (asset_class or "")
    if cls == "crypto" or (symbol or "").upper().endswith("-USD"):
        return SessionInfo(
            venue_label="Krypto (24h)",
            market_open=True,
            session_label="24h offen",
            delayed=False,
            source="CoinGecko",
            freshness_label="nahezu aktuell",
            as_of_precision="minute",
        )
    key = venue_key(symbol, exchange)
    label, tz_name, open_t, close_t = VENUES[key]
    tz = ZoneInfo(tz_name)
    local = (now or datetime.now(UTC)).astimezone(tz)
    weekday = local.weekday() < 5
    clock = local.timetz().replace(tzinfo=None)
    is_open = weekday and open_t <= clock < close_t
    if last_print is not None:
        last_local = last_print.astimezone(tz)
        if last_local.date() < local.date():
            is_open = False
            session_label = "kein Kurs von heute"
        else:
            session_label = "Handel läuft" if is_open else "Börse geschlossen"
    else:
        session_label = "Handel läuft" if is_open else "Börse geschlossen"
    if as_of_precision == "day":
        freshness = "letzter Schluss" if not is_open else "Tageskurs"
    else:
        freshness = "verzögert" if is_open else "letzter Schluss"
    return SessionInfo(
        venue_label=label,
        market_open=is_open,
        session_label=session_label,
        delayed=True,
        source="Yahoo Finance",
        freshness_label=freshness,
        as_of_precision=as_of_precision,
    )


def bar_as_of(index_value) -> datetime:
    ts = index_value.to_pydatetime() if hasattr(index_value, "to_pydatetime") else index_value
    if not isinstance(ts, datetime):
        return datetime.now(UTC)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def looks_like_daily_midnight(ts: datetime, tz_name: str) -> bool:
    local = ts.astimezone(ZoneInfo(tz_name))
    return local.hour == 0 and local.minute == 0


def session_close_as_of(ts: datetime, key: str) -> datetime:
    _label, tz_name, _open, close_t = VENUES[key]
    tz = ZoneInfo(tz_name)
    local = ts.astimezone(tz)
    return datetime.combine(local.date(), close_t, tzinfo=tz).astimezone(UTC)
