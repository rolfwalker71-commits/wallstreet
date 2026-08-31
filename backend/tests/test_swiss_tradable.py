from app.models.enums import AssetClass
from app.services.swiss_tradable import filter_swiss_symbols, is_swiss_buyable


def test_swiss_buyable_rules() -> None:
    assert is_swiss_buyable("AAPL", AssetClass.STOCK)
    assert is_swiss_buyable("NESN.SW", AssetClass.STOCK)
    assert is_swiss_buyable("VWCE.DE", AssetClass.ETF)
    assert is_swiss_buyable("IDTL.L", AssetClass.BOND)
    assert is_swiss_buyable("ZGLD.SW", AssetClass.COMMODITY)
    assert is_swiss_buyable("BTC-USD", AssetClass.CRYPTO)
    assert not is_swiss_buyable("VOO", AssetClass.ETF)
    assert not is_swiss_buyable("TLT", AssetClass.BOND)
    assert not is_swiss_buyable("GLD", AssetClass.COMMODITY)
    assert not is_swiss_buyable("VTSAX", AssetClass.FUND)
    assert not is_swiss_buyable("EURUSD=X", AssetClass.FOREX)
    assert filter_swiss_symbols(["AAPL", "VOO", "VWCE.DE"]) == ["AAPL", "VWCE.DE"]
