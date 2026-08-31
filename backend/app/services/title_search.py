from __future__ import annotations

import unicodedata
from typing import Any

import yfinance as yf
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset
from app.models.enums import AssetClass
from app.schemas.common import TitleSearchHit
from app.services.classify import infer_asset_class
from app.services.swiss_tradable import _EU_EXCHANGES, _EU_SUFFIXES, is_swiss_buyable

_SKIP_TYPES = {"CURRENCY", "FUTURE", "OPTION", "INDEX", "ECNQUOTE"}
_SWISS_EX = {"EBS", "SIX", "VTX"}


def fold_query(value: str) -> str:
    text = (value or "").strip().lower()
    for src, dst in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(src, dst)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def query_variants(query: str) -> list[str]:
    raw = (query or "").strip()
    if not raw:
        return []
    table = str.maketrans(
        {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "Ä": "Ae",
            "Ö": "Oe",
            "Ü": "Ue",
            "ß": "ss",
        }
    )
    folded = fold_query(raw)
    out: list[str] = []
    for item in (raw, raw.translate(table), folded):
        item = item.strip()
        if item and item not in out:
            out.append(item)
    return out


def _skip_quote(quote_type: str, symbol: str) -> bool:
    qt = (quote_type or "").upper()
    sym = (symbol or "").upper()
    if qt in _SKIP_TYPES:
        return True
    if sym.endswith("=X") or sym.endswith("=F"):
        return True
    return False


def score_hit(
    *,
    symbol: str,
    name: str,
    exchange: str | None,
    query: str,
    swiss_buyable: bool,
) -> int:
    needle = fold_query(query)
    sym = fold_query(symbol)
    title = fold_query(name)
    score = 0
    base = sym.split(".")[0]
    if needle and (sym == needle or base == needle):
        score += 80
    if needle and title.startswith(needle):
        score += 50
    elif needle and needle in title:
        score += 35
    exch = (exchange or "").upper()
    if symbol.upper().endswith(".SW") or exch in _SWISS_EX:
        score += 40
    elif any(symbol.upper().endswith(sfx) for sfx in _EU_SUFFIXES) or exch in _EU_EXCHANGES:
        score += 15
    if swiss_buyable:
        score += 8
    return score


def _hit_from_yahoo(row: dict[str, Any], query: str, local: dict[str, Asset]) -> TitleSearchHit | None:
    symbol = str(row.get("symbol") or "").strip().upper()
    if not symbol:
        return None
    quote_type = str(row.get("quoteType") or "")
    if _skip_quote(quote_type, symbol):
        return None
    name = (
        row.get("longname")
        or row.get("shortname")
        or row.get("longName")
        or row.get("shortName")
        or symbol
    )
    exchange = row.get("exchange") or None
    cls = infer_asset_class(symbol, quote_type)
    buyable = is_swiss_buyable(symbol, cls, exchange)
    existing = local.get(symbol)
    return TitleSearchHit(
        symbol=symbol,
        name=str(name),
        exchange=exchange,
        exchange_label=row.get("exchDisp") or exchange,
        quote_type=quote_type or None,
        asset_class=cls,
        swiss_buyable=buyable,
        watched=bool(existing.watched) if existing else False,
        in_library=existing is not None,
        score=score_hit(
            symbol=symbol,
            name=str(name),
            exchange=exchange,
            query=query,
            swiss_buyable=buyable,
        ),
    )


def yahoo_quotes(query: str) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for variant in query_variants(query):
        try:
            found = yf.Search(
                variant,
                max_results=20,
                news_count=0,
                lists_count=0,
                include_cb=False,
                recommended=0,
                raise_errors=False,
            )
        except Exception:
            continue
        for row in found.quotes or []:
            symbol = str(row.get("symbol") or "").strip().upper()
            if symbol and symbol not in merged:
                merged[symbol] = row
    return list(merged.values())


def _like_fragment(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def search_titles(session: AsyncSession, query: str) -> list[TitleSearchHit]:
    q = (query or "").strip()
    if len(q) < 2:
        return []
    likes = [f"%{_like_fragment(v)}%" for v in query_variants(q)]
    local_rows = (
        await session.execute(
            select(Asset).where(
                or_(
                    *[Asset.symbol.ilike(pat, escape="\\") for pat in likes],
                    *[Asset.name.ilike(pat, escape="\\") for pat in likes],
                )
            )
        )
    ).scalars().all()
    local = {row.symbol.upper(): row for row in local_rows}
    hits: dict[str, TitleSearchHit] = {}
    for row in yahoo_quotes(q):
        hit = _hit_from_yahoo(row, q, local)
        if hit:
            hits[hit.symbol] = hit
    for row in local_rows:
        if row.symbol.upper() in hits:
            continue
        if _skip_quote("", row.symbol):
            continue
        buyable = is_swiss_buyable(row.symbol, row.asset_class, row.exchange)
        hits[row.symbol.upper()] = TitleSearchHit(
            symbol=row.symbol,
            name=row.name,
            exchange=row.exchange,
            exchange_label=row.exchange,
            quote_type=None,
            asset_class=row.asset_class,
            swiss_buyable=buyable,
            watched=row.watched,
            in_library=True,
            score=score_hit(
                symbol=row.symbol,
                name=row.name,
                exchange=row.exchange,
                query=q,
                swiss_buyable=buyable,
            ),
        )
    return sorted(hits.values(), key=lambda h: (-h.score, h.symbol))
