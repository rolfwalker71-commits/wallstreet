from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AgentLog, Asset, Recommendation
from app.models.enums import (
    AgentLogStatus,
    AgentName,
    RecommendationAction,
    RecommendationStatus,
)
from app.services.allocation import compute_allocation, size_order
from app.services.assets import AssetError, get_or_create_asset
from app.services.core_products import (
    CORE,
    CORE_BY_SLEEVE,
    SLEEVE_BOND,
    SLEEVE_COMMODITY,
    SLEEVE_STOCK,
    STARTER_SYMBOL,
    core_of,
)
from app.services.market import get_quote
from app.services.portfolio import decorate_portfolio, get_primary_portfolio
from app.services.swiss_tradable import is_swiss_buyable

PICKS_STEP = "buy_picks_gaps"
PICKS_TTL = timedelta(hours=6)


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def gap_rationale(
    *,
    symbol: str,
    sleeve_label: str,
    gap: dict,
    size: dict,
    currency: str,
    price: float | None,
    asset_ccy: str,
    empty: bool,
) -> str:
    core = core_of(symbol) or {}
    parts = [
        f"{core.get('name', symbol)} ({symbol}).",
        f"Sleeve {sleeve_label}: Ist {gap['current_pct']} %, Ziel {gap['target_pct']} %, Lücke {gap['gap_pct']} % ({gap['gap_value']:.2f} {currency}).",
    ]
    if empty and symbol == STARTER_SYMBOL:
        parts.append("Leeres Depot: erster Kauf ist der Welt-Aktien-UCITS, nicht Einzelaktien.")
    if core.get("isin"):
        parts.append(f"ISIN {core['isin']}.")
    if core.get("ter") is not None:
        parts.append(f"TER {core['ter']:.2f} % p.a.")
    if core.get("index_name"):
        parts.append(f"Index {core['index_name']}.")
    if core.get("duration_years"):
        parts.append(f"Effektive Duration ca. {core['duration_years']} Jahre (Emittenten-Factsheet).")
    if core.get("exchange"):
        parts.append(f"Börse {core['exchange']}.")
    parts.extend(core.get("notes") or [])
    if size.get("qty"):
        parts.append(
            f"Vorschlag {int(size['qty'])} Stück à {size['price']} {asset_ccy} "
            f"≈ {size['amount']} {currency} (Depotwährung, ohne FX-Umrechnung)."
        )
    elif price:
        parts.append(f"Letzter Kurs {price} {asset_ccy}; Betrag unter einem Stück.")
    if core.get("justetf"):
        parts.append(f"Factsheet: {core['justetf']}")
    parts.append("Keine Live-Prüfung beim Broker. ISIN im Broker suchen. Keine Kursprognose.")
    return " ".join(parts)


async def cached_picks(session: AsyncSession) -> list[Recommendation] | None:
    log = (
        await session.execute(
            select(AgentLog)
            .where(AgentLog.step == PICKS_STEP, AgentLog.status == AgentLogStatus.SUCCEEDED)
            .order_by(AgentLog.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if log is None:
        return None
    created = log.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    if datetime.now(UTC) - created > PICKS_TTL:
        return None
    def _query(*, with_outcome: bool):
        opts = [
            selectinload(Recommendation.asset),
            selectinload(Recommendation.agent_logs),
        ]
        if with_outcome:
            opts.append(selectinload(Recommendation.outcome))
        return (
            select(Recommendation)
            .options(*opts)
            .where(Recommendation.run_id == log.run_id)
            .order_by(Recommendation.created_at.asc())
        )

    try:
        rows = (await session.execute(_query(with_outcome=True))).scalars().all()
    except Exception:
        await session.rollback()
        rows = (await session.execute(_query(with_outcome=False))).scalars().all()
    return list(rows) or None


async def _ensure_core(session: AsyncSession, symbol: str) -> Asset | None:
    try:
        return await get_or_create_asset(session, symbol, watched=True)
    except AssetError:
        row = (
            await session.execute(select(Asset).where(Asset.symbol == symbol))
        ).scalar_one_or_none()
        return row


def _plan_symbols(allocation: dict, symbols_held: set[str]) -> list[tuple[str, dict]]:
    empty = len(symbols_held) == 0
    has_world = STARTER_SYMBOL in symbols_held
    has_equity = has_world or any(
        s["sleeve"] == SLEEVE_STOCK and s["current_pct"] >= 5 for s in allocation["sleeves"]
    )
    planned: list[tuple[str, dict]] = []
    by_sleeve = {s["sleeve"]: s for s in allocation["sleeves"]}
    stock = by_sleeve[SLEEVE_STOCK]
    if stock["gap_pct"] >= 1 or empty:
        planned.append((STARTER_SYMBOL, stock))
    if not empty and has_equity:
        comm = by_sleeve[SLEEVE_COMMODITY]
        if comm["gap_pct"] >= 1:
            planned.append((CORE_BY_SLEEVE[SLEEVE_COMMODITY], comm))
        bond = by_sleeve[SLEEVE_BOND]
        if bond["gap_pct"] >= 1 and has_world:
            planned.append((CORE_BY_SLEEVE[SLEEVE_BOND], bond))
    return planned


async def generate_buy_picks(session: AsyncSession) -> list[Recommendation]:
    started = time.perf_counter()
    pf = await get_primary_portfolio(session)
    if pf is None:
        return []
    decorated = await decorate_portfolio(session, pf)
    allocation = decorated["allocation"]
    held = {
        (p["asset"].symbol if hasattr(p["asset"], "symbol") else p["asset"]["symbol"]).upper()
        for p in decorated["positions"]
    }
    empty = len(held) == 0
    planned = _plan_symbols(allocation, held)
    run_id = uuid4()
    recs: list[Recommendation] = []
    cash_left = float(allocation["cash"])
    equity = float(allocation["equity"])
    max_single = float(allocation["max_single_position_pct"])

    for symbol, gap in planned:
        asset = await _ensure_core(session, symbol)
        if asset is None:
            continue
        meta = core_of(symbol) or {}
        if asset.isin is None and meta.get("isin"):
            asset.isin = meta["isin"]
        if not is_swiss_buyable(asset.symbol, asset.asset_class, asset.exchange):
            continue
        quote = None
        try:
            quote = await get_quote(asset.symbol, session)
        except Exception:
            quote = None
        price = float(quote.price) if quote else (float(asset.last_price) if asset.last_price else None)
        is_core = meta.get("role") == "core"
        size = size_order(
            gap_value=float(gap["gap_value"]),
            equity=equity,
            cash=cash_left,
            price=price,
            is_core=is_core,
            max_single=max_single,
        )
        if not size.get("qty"):
            continue
        cash_left -= float(size["amount"] or 0)
        sleeve_label = gap["label"]
        rec = Recommendation(
            asset_id=asset.id,
            run_id=run_id,
            action=RecommendationAction.BUY,
            confidence=Decimal("0.70") if symbol == STARTER_SYMBOL else Decimal("0.55"),
            risk_reward_ratio=None,
            rationale=gap_rationale(
                symbol=symbol,
                sleeve_label=sleeve_label,
                gap=gap,
                size=size,
                currency=allocation["currency"],
                price=price,
                asset_ccy=asset.currency,
                empty=empty,
            ),
            news_summary=None,
            news_sources=[{"title": n} for n in (meta.get("notes") or [])] or None,
            technicals=None,
            proposed_qty=_dec(size["qty"]),
            proposed_price=_dec(size["price"]),
            status=RecommendationStatus.OPEN,
            glossary_terms=["TER", "PRIIPs", "UCITS", "ISIN"],
            suggested_symbols=list(meta.get("peers") or []),
        )
        session.add(rec)
        recs.append(rec)

    await session.flush()
    for rec in recs:
        await session.refresh(rec, attribute_names=["asset", "agent_logs"])

    elapsed = int((time.perf_counter() - started) * 1000)
    session.add(
        AgentLog(
            run_id=run_id,
            agent_name=AgentName.STRATEGIST,
            step=PICKS_STEP,
            status=AgentLogStatus.SUCCEEDED,
            reasoning=f"{len(recs)} Lücken-Käufe, leer={empty}",
            output_payload={"symbols": [r.asset.symbol for r in recs if r.asset]},
            duration_ms=elapsed,
        )
    )
    await session.flush()
    return recs


async def list_buy_picks(session: AsyncSession, *, refresh: bool = False) -> list[Recommendation]:
    if not refresh:
        cached = await cached_picks(session)
        if cached:
            return cached
    return await generate_buy_picks(session)
