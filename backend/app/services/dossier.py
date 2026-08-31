from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import yfinance as yf

from app.models import Asset
from app.services.core_products import CORE, core_of, peers_of, sleeve_for
from app.services.facts import as_float
from app.services.swiss_tradable import is_swiss_buyable


def _ts(value: Any) -> str | None:
    if value is None or value == "":
        return None
    try:
        n = float(value)
        if n > 10_000:
            return datetime.fromtimestamp(n, tz=UTC).date().isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        pass
    text = str(value)
    return text[:10] if len(text) >= 10 and text[4] == "-" else text


def fetch_yahoo_facts(symbol: str) -> dict[str, Any]:
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        return {}
    if not isinstance(info, dict):
        return {}
    out: dict[str, Any] = {}
    mapping = {
        "isin": "isin",
        "trailingPE": "pe_ratio",
        "dividendYield": "dividend_yield",
        "yield": "fund_yield",
        "netExpenseRatio": "ter",
        "annualReportExpenseRatio": "ter",
        "fiftyTwoWeekHigh": "week52_high",
        "fiftyTwoWeekLow": "week52_low",
        "marketCap": "market_cap",
        "fundFamily": "fund_family",
        "category": "category",
        "earningsTimestamp": "earnings_date",
        "exDividendDate": "ex_dividend_date",
        "website": "website",
    }
    for src, dest in mapping.items():
        raw = info.get(src)
        if raw is None or raw == "":
            continue
        if dest in {"earnings_date", "ex_dividend_date"}:
            out[dest] = _ts(raw)
        elif dest in {"pe_ratio", "dividend_yield", "fund_yield", "ter", "week52_high", "week52_low", "market_cap"}:
            num = as_float(raw)
            if num is None:
                continue
            if dest in {"dividend_yield", "fund_yield", "ter"} and num > 1:
                num = num / 100 if num > 5 else num
            if dest == "ter" and num > 1:
                num = num / 100
            out[dest] = num
        else:
            out[dest] = raw
    return out


def persist_isin(asset: Asset, isin: str | None) -> None:
    if isin and not asset.isin:
        asset.isin = isin[:16]


def build_dossier(asset: Asset, yahoo: dict[str, Any] | None = None) -> dict[str, Any]:
    core = core_of(asset.symbol) or {}
    yahoo = yahoo or {}
    extra = asset.extra if isinstance(asset.extra, dict) else {}
    isin = asset.isin or core.get("isin") or yahoo.get("isin")
    ter = core.get("ter") if core.get("ter") is not None else yahoo.get("ter") or extra.get("ter")
    buyable = is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange)
    justetf = core.get("justetf")
    if not justetf and isin:
        justetf = f"https://www.justetf.com/ch-de/etf-profile.html?isin={isin}"
    calendar = []
    if yahoo.get("earnings_date"):
        calendar.append({"kind": "earnings", "date": yahoo["earnings_date"], "source": "Yahoo Finance"})
    if extra.get("earnings_date") and not yahoo.get("earnings_date"):
        calendar.append({"kind": "earnings", "date": extra["earnings_date"], "source": "gespeichert"})
    if yahoo.get("ex_dividend_date"):
        calendar.append({"kind": "ex_dividend", "date": yahoo["ex_dividend_date"], "source": "Yahoo Finance"})
    peers = []
    for sym in peers_of(asset.symbol):
        peer = CORE.get(sym)
        if not peer:
            continue
        peers.append(
            {
                "symbol": sym,
                "name": peer["name"],
                "isin": peer.get("isin"),
                "ter": peer.get("ter"),
                "exchange": peer.get("exchange"),
                "currency": peer.get("currency"),
                "justetf": peer.get("justetf"),
            }
        )
    return {
        "symbol": asset.symbol,
        "name": asset.name,
        "asset_class": asset.asset_class.value if hasattr(asset.asset_class, "value") else str(asset.asset_class),
        "exchange": asset.exchange,
        "currency": asset.currency,
        "isin": isin,
        "sleeve": sleeve_for(asset.asset_class, asset.symbol),
        "swiss_buyable": buyable,
        "broker_rule": (
            "Regel: EU/SIX-Listing oder Einzelaktie; kein US-ETF/Fonds ohne PRIIPs-KID, kein Forex/Future. "
            "Keine Live-Prüfung beim Broker — ISIN im Broker suchen."
            if buyable
            else "Nach Regel nicht als CH-Privatanleger-Kauf behandelt (US-Verpackung ohne KID, Forex oder Future)."
        ),
        "ter": ter,
        "pe_ratio": yahoo.get("pe_ratio") or extra.get("pe_ratio"),
        "dividend_yield": yahoo.get("dividend_yield") or extra.get("dividend_yield"),
        "week52_high": yahoo.get("week52_high"),
        "week52_low": yahoo.get("week52_low"),
        "index_name": core.get("index_name"),
        "replication": core.get("replication"),
        "distribution": core.get("distribution"),
        "domicile": core.get("domicile"),
        "kid": bool(core.get("kid")) if core else None,
        "justetf_url": justetf
        if str(getattr(asset.asset_class, "value", asset.asset_class)).lower()
        in {"etf", "bond", "fund", "commodity"}
        else None,
        "issuer_url": core.get("issuer"),
        "yahoo_url": f"https://finance.yahoo.com/quote/{asset.symbol}",
        "notes": list(core.get("notes") or []),
        "calendar": calendar,
        "peers": peers,
        "as_of": datetime.now(UTC).isoformat(),
    }
