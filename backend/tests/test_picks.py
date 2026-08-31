from app.services.core_products import STARTER_SYMBOL, sleeve_for
from app.services.picks import gap_rationale


def test_vwce_is_stock_sleeve() -> None:
    assert sleeve_for("etf", "VWCE.DE") == "stock"
    assert sleeve_for("bond", "IDTL.L") == "bond"


def test_gap_rationale_is_factual() -> None:
    text = gap_rationale(
        symbol=STARTER_SYMBOL,
        sleeve_label="Aktien / Aktien-ETFs",
        gap={"current_pct": 0, "target_pct": 60, "gap_pct": 60, "gap_value": 60000},
        size={"qty": 10, "price": 140, "amount": 1400},
        currency="USD",
        price=140,
        asset_ccy="EUR",
        empty=True,
    )
    assert "IE00BK5BQT80" in text
    assert "TER 0.14" in text
    assert "Leeres Depot" in text
    assert "könnte" not in text.lower()
