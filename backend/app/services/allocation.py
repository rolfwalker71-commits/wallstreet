from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.core_products import (
    DEFAULT_TARGETS,
    SLEEVE_BOND,
    SLEEVE_CASH,
    SLEEVE_COMMODITY,
    SLEEVE_CRYPTO,
    SLEEVE_LABEL,
    SLEEVE_STOCK,
    sleeve_for,
)

SLEEVES = (SLEEVE_STOCK, SLEEVE_BOND, SLEEVE_COMMODITY, SLEEVE_CRYPTO, SLEEVE_CASH)


def _dec(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def _pct(value: Any, fallback: float) -> float:
    if value is None:
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def targets_from_portfolio(portfolio) -> dict[str, float]:
    return {
        SLEEVE_STOCK: _pct(getattr(portfolio, "target_stock_pct", None), DEFAULT_TARGETS[SLEEVE_STOCK]),
        SLEEVE_BOND: _pct(getattr(portfolio, "target_bond_pct", None), DEFAULT_TARGETS[SLEEVE_BOND]),
        SLEEVE_COMMODITY: _pct(
            getattr(portfolio, "target_commodity_pct", None), DEFAULT_TARGETS[SLEEVE_COMMODITY]
        ),
        SLEEVE_CRYPTO: _pct(getattr(portfolio, "target_crypto_pct", None), DEFAULT_TARGETS[SLEEVE_CRYPTO]),
        SLEEVE_CASH: _pct(getattr(portfolio, "target_cash_pct", None), DEFAULT_TARGETS[SLEEVE_CASH]),
    }


def max_single_pct(portfolio) -> float:
    return _pct(getattr(portfolio, "max_single_position_pct", None), 5.0)


def compute_allocation(portfolio, positions_out: list[dict]) -> dict[str, Any]:
    targets = targets_from_portfolio(portfolio)
    cash = _dec(portfolio.cash_balance)
    holdings = Decimal("0")
    by_sleeve: dict[str, Decimal] = {s: Decimal("0") for s in SLEEVES}
    by_sleeve[SLEEVE_CASH] = cash
    for pos in positions_out:
        mv = pos.get("market_value")
        if mv is None:
            continue
        value = _dec(mv)
        holdings += value
        asset = pos.get("asset")
        cls = getattr(asset, "asset_class", None)
        symbol = getattr(asset, "symbol", None)
        if isinstance(asset, dict):
            cls = asset.get("asset_class")
            symbol = asset.get("symbol")
        sleeve = sleeve_for(cls, symbol)
        if sleeve == SLEEVE_CASH:
            continue
        by_sleeve[sleeve] = by_sleeve.get(sleeve, Decimal("0")) + value
    equity = cash + holdings
    if equity <= 0:
        equity = Decimal("1")
    current_pct = {s: float(by_sleeve.get(s, Decimal("0")) / equity * 100) for s in SLEEVES}
    gaps = []
    for sleeve in SLEEVES:
        target = targets[sleeve]
        current = current_pct[sleeve]
        gap_pct = target - current
        gap_value = float(equity) * gap_pct / 100
        gaps.append(
            {
                "sleeve": sleeve,
                "label": SLEEVE_LABEL[sleeve],
                "target_pct": target,
                "current_pct": round(current, 2),
                "gap_pct": round(gap_pct, 2),
                "gap_value": round(gap_value, 2),
                "current_value": float(by_sleeve.get(sleeve, Decimal("0"))),
            }
        )
    return {
        "equity": float(cash + holdings),
        "cash": float(cash),
        "holdings": float(holdings),
        "currency": portfolio.base_currency,
        "max_single_position_pct": max_single_pct(portfolio),
        "targets": targets,
        "sleeves": gaps,
    }


def size_order(
    *,
    gap_value: float,
    equity: float,
    cash: float,
    price: float | None,
    is_core: bool,
    max_single: float,
) -> dict[str, float | int | None]:
    if price is None or price <= 0 or gap_value <= 0 or cash <= 0:
        return {"amount": 0, "qty": 0, "price": price}
    cap_pct = 40.0 if is_core else max_single
    cap = equity * cap_pct / 100
    amount = min(gap_value, cap, cash)
    qty = int(amount // price)
    if qty < 1 and amount >= price:
        qty = 1
    spent = qty * price
    return {
        "amount": round(spent, 2),
        "qty": qty,
        "price": price,
        "cap_pct": cap_pct,
    }
