from types import SimpleNamespace

from app.services.allocation import compute_allocation, size_order
from app.services.picks import _plan_symbols
from app.services.core_products import SLEEVE_STOCK, STARTER_SYMBOL


def test_empty_portfolio_is_all_cash() -> None:
    pf = SimpleNamespace(
        cash_balance=100_000,
        base_currency="USD",
        target_stock_pct=60,
        target_bond_pct=20,
        target_commodity_pct=5,
        target_crypto_pct=0,
        target_cash_pct=15,
        max_single_position_pct=5,
    )
    alloc = compute_allocation(pf, [])
    cash = next(s for s in alloc["sleeves"] if s["sleeve"] == "cash")
    stock = next(s for s in alloc["sleeves"] if s["sleeve"] == SLEEVE_STOCK)
    assert cash["current_pct"] == 100
    assert stock["gap_pct"] == 60
    assert stock["gap_value"] == 60_000


def test_empty_plan_is_only_vwce() -> None:
    pf = SimpleNamespace(
        cash_balance=10_000,
        base_currency="CHF",
        target_stock_pct=60,
        target_bond_pct=20,
        target_commodity_pct=5,
        target_crypto_pct=0,
        target_cash_pct=15,
        max_single_position_pct=5,
    )
    alloc = compute_allocation(pf, [])
    planned = _plan_symbols(alloc, set())
    assert [s for s, _ in planned] == [STARTER_SYMBOL]


def test_size_core_uses_gap_and_cash() -> None:
    out = size_order(
        gap_value=6000,
        equity=10_000,
        cash=10_000,
        price=120,
        is_core=True,
        max_single=5,
    )
    assert out["qty"] == 33
    assert out["amount"] == 3960


def test_size_skips_when_cannot_afford_one_share() -> None:
    out = size_order(
        gap_value=50,
        equity=10_000,
        cash=50,
        price=120,
        is_core=True,
        max_single=5,
    )
    assert out["qty"] == 0
