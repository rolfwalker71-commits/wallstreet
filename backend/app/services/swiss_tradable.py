from app.models.enums import AssetClass

# EU/CH-Börsen: typisch mit PRIIPs-KID / SIX handelbar.
_EU_SUFFIXES = (
    ".SW",
    ".DE",
    ".L",
    ".MI",
    ".PA",
    ".AS",
    ".VI",
    ".BR",
    ".HE",
    ".ST",
    ".CO",
    ".OL",
    ".LS",
    ".IR",
)

_EU_EXCHANGES = {
    "SIX",
    "EBS",
    "GER",
    "XETR",
    "FRA",
    "LSE",
    "AMS",
    "PAR",
    "MIL",
    "MCE",
    "VIE",
}

# US-Retail-Vehikel ohne KID — Schweizer Broker lehnen sie meist ab.
_US_PACKAGED = {
    "VOO",
    "SPY",
    "QQQ",
    "VTI",
    "VXUS",
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
    "GLD",
    "IAU",
    "SLV",
    "USO",
    "UNG",
    "DBC",
    "PDBC",
    "VTSAX",
    "VTIAX",
    "VBTLX",
    "FXAIX",
    "SWTSX",
}


def _eu_listed(symbol: str, exchange: str | None = None) -> bool:
    sym = symbol.strip().upper()
    if any(sym.endswith(sfx) for sfx in _EU_SUFFIXES):
        return True
    if exchange and exchange.upper() in _EU_EXCHANGES:
        return True
    return False


def is_swiss_buyable(
    symbol: str,
    asset_class: AssetClass | str | None = None,
    exchange: str | None = None,
) -> bool:
    """True, wenn ein CH-Privatanleger das typischerweise kaufen kann."""
    sym = (symbol or "").strip().upper()
    if not sym:
        return False
    if sym.endswith("=X") or sym.endswith("=F"):
        return False

    cls = asset_class
    if isinstance(cls, str):
        raw = cls.strip()
        try:
            cls = AssetClass(raw.lower())
        except ValueError:
            try:
                cls = AssetClass[raw.upper()]
            except KeyError:
                cls = None

    if cls == AssetClass.FOREX:
        return False
    if sym in _US_PACKAGED:
        return False
    if cls in {AssetClass.ETF, AssetClass.BOND, AssetClass.COMMODITY, AssetClass.FUND}:
        return _eu_listed(sym, exchange)
    if cls == AssetClass.CRYPTO or sym.endswith("-USD"):
        return True
    return True


def filter_swiss_symbols(symbols: list[str] | None) -> list[str]:
    return [s for s in (symbols or []) if is_swiss_buyable(s)]
