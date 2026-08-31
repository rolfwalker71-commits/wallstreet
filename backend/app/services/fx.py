from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import Any

import httpx
import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSetting

FX_CACHE_KEY = "fx_rates_json"
BENCHMARK_CCY = "CHF"


def convert(amount: float | None, from_ccy: str | None, to_ccy: str | None, rates: dict[str, float]) -> float | None:
    """Wandle Betrag anhand täglicher Kurse (Einheiten je 1 EUR) um."""
    if amount is None:
        return None
    src = (from_ccy or "USD").upper()
    dst = (to_ccy or src).upper()
    if dst == "NATIVE" or src == dst:
        return float(amount)
    if src == "EUR":
        src_per_eur = 1.0
    else:
        src_per_eur = rates.get(src)
    if dst == "EUR":
        dst_per_eur = 1.0
    else:
        dst_per_eur = rates.get(dst)
    if not src_per_eur or not dst_per_eur:
        return None
    return float(amount) / src_per_eur * dst_per_eur


def _parse_ecb(xml: str) -> dict[str, float]:
    rates: dict[str, float] = {"EUR": 1.0}
    for part in xml.split("<Cube"):
        if 'currency="' not in part or 'rate="' not in part:
            continue
        try:
            ccy = part.split('currency="', 1)[1].split('"', 1)[0]
            rate = float(part.split('rate="', 1)[1].split('"', 1)[0])
        except (IndexError, ValueError):
            continue
        rates[ccy.upper()] = rate
    return rates


def fetch_ecb_rates() -> dict[str, float]:
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    with httpx.Client(timeout=12) as client:
        resp = client.get(url)
        resp.raise_for_status()
        rates = _parse_ecb(resp.text)
    if "CHF" not in rates or "USD" not in rates:
        raise ValueError("ECB-Kurse unvollständig.")
    return rates


def fetch_yahoo_chf_rates() -> dict[str, float]:
    """Fallback: CHF=X = CHF je USD, EURCHF=X = CHF je EUR → auf EUR-Basis."""
    usdchf = yf.Ticker("CHF=X").history(period="5d")
    eurchf = yf.Ticker("EURCHF=X").history(period="5d")
    if usdchf is None or usdchf.empty or eurchf is None or eurchf.empty:
        raise ValueError("Yahoo-Devisen nicht verfügbar.")
    chf_per_usd = float(usdchf["Close"].dropna().iloc[-1])
    chf_per_eur = float(eurchf["Close"].dropna().iloc[-1])
    if chf_per_usd <= 0 or chf_per_eur <= 0:
        raise ValueError("Yahoo-Devisen ungültig.")
    usd_per_eur = chf_per_eur / chf_per_usd
    return {"EUR": 1.0, "CHF": chf_per_eur, "USD": usd_per_eur}


def _today() -> str:
    return date.today().isoformat()


async def get_fx_bundle(session: AsyncSession | None = None, *, refresh: bool = False) -> dict[str, Any]:
    cached: dict[str, Any] | None = None
    if session is not None and not refresh:
        row = (
            await session.execute(select(AppSetting).where(AppSetting.key == FX_CACHE_KEY))
        ).scalar_one_or_none()
        if row:
            try:
                cached = json.loads(row.value)
            except json.JSONDecodeError:
                cached = None
        if cached and cached.get("as_of") == _today() and cached.get("rates"):
            return cached

    rates: dict[str, float] | None = None
    source = "ECB"
    try:
        rates = fetch_ecb_rates()
    except Exception:
        try:
            rates = fetch_yahoo_chf_rates()
            source = "Yahoo"
        except Exception:
            rates = None
    if rates is None:
        if cached and cached.get("rates"):
            return cached
        rates = {"EUR": 1.0, "CHF": 0.94, "USD": 1.08}
        source = "fallback"

    bundle = {
        "as_of": _today(),
        "source": source,
        "base": "EUR",
        "rates": {k: float(v) for k, v in rates.items()},
        "fetched_at": datetime.now(UTC).isoformat(),
    }
    if session is not None:
        row = (
            await session.execute(select(AppSetting).where(AppSetting.key == FX_CACHE_KEY))
        ).scalar_one_or_none()
        payload = json.dumps(bundle)
        if row:
            row.value = payload
        else:
            session.add(AppSetting(key=FX_CACHE_KEY, value=payload))
        await session.flush()
    return bundle
