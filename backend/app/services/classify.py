from app.models.enums import AssetClass

COINGECKO_IDS = {
    "BTC-USD": "bitcoin",
    "ETH-USD": "ethereum",
    "SOL-USD": "solana",
}

ETF_TICKERS = {
    "VOO",
    "SPY",
    "QQQ",
    "IWDA",
    "VWCE",
    "VWCE.DE",
    "VXUS",
    "VTI",
    "SXR8.DE",
    "CSPX.L",
    "CSSMI.SW",
    "CHSPI.SW",
}

BOND_TICKERS = {
    "TLT",
    "BND",
    "BNDX",
    "SHY",
    "IEF",
    "AGG",
    "LQD",
    "HYG",
    "TIP",
    "GOVT",
    "IDTL.L",
    "IDTL",
}

COMMODITY_TICKERS = {
    "GLD",
    "IAU",
    "SLV",
    "ZGLD.SW",
    "4GLD.DE",
    "SGLD.L",
    "USO",
    "UNG",
    "DBC",
    "PDBC",
}

FUND_TICKERS = {"VTSAX", "VTIAX", "VBTLX", "FXAIX", "SWTSX"}


def infer_asset_class(symbol: str, quote_type: str = "") -> AssetClass:
    sym = symbol.strip().upper()
    qt = (quote_type or "").upper()
    if qt in {"CRYPTOCURRENCY", "CRYPTO"} or sym.endswith("-USD") or sym in COINGECKO_IDS:
        return AssetClass.CRYPTO
    if qt == "CURRENCY" or sym.endswith("=X"):
        return AssetClass.FOREX
    if qt in {"FUTURE", "COMMODITY"} or sym.endswith("=F") or sym in COMMODITY_TICKERS:
        return AssetClass.COMMODITY
    if qt == "MUTUALFUND" or sym in FUND_TICKERS:
        return AssetClass.FUND
    if qt == "BOND" or sym in BOND_TICKERS:
        return AssetClass.BOND
    if qt == "ETF" or sym in ETF_TICKERS:
        return AssetClass.ETF
    return AssetClass.STOCK
