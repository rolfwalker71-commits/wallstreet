from __future__ import annotations

from app.services.allocation import size_order
from app.services.core_products import core_of
from app.services.picks import _plan_symbols, gap_rationale
from app.services.swiss_tradable import is_swiss_buyable


def propose_rebalance(
    *,
    allocation: dict,
    held: set[str],
    quotes: dict[str, dict],
    limit: int = 2,
) -> list[dict]:
    """Nächste 1–2 Käufe aus Lücken, gleiche Logik wie Empfehlungen."""
    planned = _plan_symbols(allocation, held)
    cash_left = float(allocation.get("cash") or 0)
    equity = float(allocation.get("equity") or 0)
    max_single = float(allocation.get("max_single_position_pct") or 5)
    currency = allocation.get("currency") or "CHF"
    empty = len(held) == 0
    out: list[dict] = []
    for symbol, gap in planned:
        meta = quotes.get(symbol) or {}
        price = meta.get("price")
        asset_ccy = meta.get("currency") or "EUR"
        swiss = meta.get("swiss_buyable")
        if swiss is False:
            continue
        if swiss is None and not is_swiss_buyable(symbol, meta.get("asset_class"), meta.get("exchange")):
            continue
        is_core = (core_of(symbol) or {}).get("role") == "core"
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
        out.append(
            {
                "symbol": symbol,
                "name": meta.get("name") or symbol,
                "sleeve": gap["sleeve"],
                "sleeve_label": gap["label"],
                "qty": int(size["qty"]),
                "price": size["price"],
                "amount": size["amount"],
                "currency": currency,
                "asset_currency": asset_ccy,
                "rationale": gap_rationale(
                    symbol=symbol,
                    sleeve_label=gap["label"],
                    gap=gap,
                    size=size,
                    currency=currency,
                    price=price,
                    asset_ccy=asset_ccy,
                    empty=empty,
                ),
            }
        )
        if len(out) >= limit:
            break
    return out
