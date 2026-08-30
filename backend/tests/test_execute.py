from decimal import Decimal
from types import SimpleNamespace

from app.models.enums import AssetClass, RecommendationAction, RecommendationStatus
from app.services.portfolio import default_qty, is_executable


def test_hold_is_not_executable() -> None:
    rec = SimpleNamespace(status=RecommendationStatus.OPEN, action=RecommendationAction.HOLD)
    assert is_executable(rec) is False


def test_open_buy_is_executable() -> None:
    rec = SimpleNamespace(status=RecommendationStatus.OPEN, action=RecommendationAction.BUY)
    assert is_executable(rec) is True


def test_executed_buy_is_not_executable() -> None:
    rec = SimpleNamespace(status=RecommendationStatus.EXECUTED, action=RecommendationAction.BUY)
    assert is_executable(rec) is False


def test_default_qty_prefers_proposal() -> None:
    rec = SimpleNamespace(
        proposed_qty=Decimal("3"),
        asset=SimpleNamespace(asset_class=AssetClass.STOCK),
    )
    assert default_qty(rec) == Decimal("3")


def test_apply_payload_optional() -> None:
    from app.schemas.portfolio import ApplyRecommendationIn

    empty = ApplyRecommendationIn()
    assert empty.quantity is None
    assert empty.price is None
    filled = ApplyRecommendationIn(quantity="2.5", price="120.5")
    assert filled.quantity is not None
    assert filled.price is not None


def test_default_qty_crypto_fallback() -> None:
    rec = SimpleNamespace(
        proposed_qty=None,
        asset=SimpleNamespace(asset_class=AssetClass.CRYPTO),
    )
    assert default_qty(rec) == Decimal("0.01")