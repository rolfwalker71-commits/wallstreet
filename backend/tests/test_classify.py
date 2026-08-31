from app.models.enums import AssetClass
from app.services.classify import infer_asset_class


def test_infer_new_classes() -> None:
    assert infer_asset_class("TLT") == AssetClass.BOND
    assert infer_asset_class("IDTL.L") == AssetClass.BOND
    assert infer_asset_class("GLD") == AssetClass.COMMODITY
    assert infer_asset_class("ZGLD.SW") == AssetClass.COMMODITY
    assert infer_asset_class("EURUSD=X") == AssetClass.FOREX
    assert infer_asset_class("VTSAX") == AssetClass.FUND
    assert infer_asset_class("GC=F") == AssetClass.COMMODITY
    assert infer_asset_class("AAPL") == AssetClass.STOCK
    assert infer_asset_class("NESN.SW") == AssetClass.STOCK
    assert infer_asset_class("VOO") == AssetClass.ETF
    assert infer_asset_class("VWCE.DE") == AssetClass.ETF
    assert infer_asset_class("CSSMI.SW") == AssetClass.ETF
    assert infer_asset_class("FOO", "MUTUALFUND") == AssetClass.FUND
    assert infer_asset_class("FOO", "CURRENCY") == AssetClass.FOREX
