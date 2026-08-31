"""Belegte Stammdaten für CH-kaufbare Kernprodukte (JustETF / Emittent)."""

from __future__ import annotations

from app.models.enums import AssetClass

SLEEVE_STOCK = "stock"
SLEEVE_BOND = "bond"
SLEEVE_COMMODITY = "commodity"
SLEEVE_CRYPTO = "crypto"
SLEEVE_CASH = "cash"

SLEEVE_LABEL = {
    SLEEVE_STOCK: "Aktien / Aktien-ETFs",
    SLEEVE_BOND: "Obligationen",
    SLEEVE_COMMODITY: "Rohstoffe",
    SLEEVE_CRYPTO: "Crypto",
    SLEEVE_CASH: "Cash",
}

DEFAULT_TARGETS = {
    SLEEVE_STOCK: 60.0,
    SLEEVE_BOND: 20.0,
    SLEEVE_COMMODITY: 5.0,
    SLEEVE_CRYPTO: 0.0,
    SLEEVE_CASH: 15.0,
}

# Quellen: JustETF / BlackRock / Vanguard, Stand Recherche Aug 2026.
CORE: dict[str, dict] = {
    "VWCE.DE": {
        "name": "Vanguard FTSE All-World UCITS ETF",
        "asset_class": AssetClass.ETF,
        "exchange": "XETRA",
        "currency": "EUR",
        "isin": "IE00BK5BQT80",
        "ter": 0.14,
        "sleeve": SLEEVE_STOCK,
        "role": "core",
        "replication": "physisch (Sampling)",
        "distribution": "thesaurierend",
        "domicile": "Irland",
        "index_name": "FTSE All-World",
        "kid": True,
        "justetf": "https://www.justetf.com/ch-de/etf-profile.html?isin=IE00BK5BQT80",
        "issuer": "https://www.justetf.com/ch-de/etf-profile.html?isin=IE00BK5BQT80",
        "peers": ["CSSMI.SW"],
        "notes": [
            "UCITS, PRIIPs-KID üblich bei CH-Brokern.",
            "Kern für ein leeres Depot: zuerst dieses Papier.",
        ],
    },
    "CSSMI.SW": {
        "name": "iShares SMI (CH)",
        "asset_class": AssetClass.ETF,
        "exchange": "SIX",
        "currency": "CHF",
        "isin": "CH0008899764",
        "ter": 0.35,
        "sleeve": SLEEVE_STOCK,
        "role": "satellite",
        "replication": "physisch (voll)",
        "distribution": "ausschüttend",
        "domicile": "Schweiz",
        "index_name": "SMI",
        "kid": True,
        "justetf": "https://www.justetf.com/ch-de/etf-profile.html?isin=CH0008899764",
        "issuer": "https://www.blackrock.com/ch/individual/en/products/261154/ishares-smi-ch-fund",
        "peers": ["VWCE.DE"],
        "notes": [
            "20 Schweizer Titel. Überlappt mit VWCE.",
            "Nur zusätzlich, wenn extra Schweiz-Quote gewollt ist.",
        ],
    },
    "IDTL.L": {
        "name": "iShares $ Treasury Bond 20+yr UCITS ETF",
        "asset_class": AssetClass.BOND,
        "exchange": "LSE",
        "currency": "USD",
        "isin": "IE00BSKRJZ44",
        "ter": 0.07,
        "sleeve": SLEEVE_BOND,
        "role": "satellite",
        "replication": "physisch (Sampling)",
        "distribution": "ausschüttend",
        "domicile": "Irland",
        "index_name": "ICE U.S. Treasury 20+ Year",
        "duration_years": 15.34,
        "kid": True,
        "justetf": "https://www.justetf.com/ch-de/etf-profile.html?isin=IE00BSKRJZ44",
        "issuer": "https://www.ishares.com/ch/individual/en/products/258304/",
        "peers": [],
        "notes": [
            "Effektive Duration ca. 15, Restlaufzeit 20+ Jahre, USD.",
            "Nicht der Einstieg: hoher Zinsänderungs- und Währungseffekt.",
        ],
    },
    "ZGLD.SW": {
        "name": "Swisscanto (CH) Gold ETF EA CHF",
        "asset_class": AssetClass.COMMODITY,
        "exchange": "SIX",
        "currency": "CHF",
        "isin": "CH0139101593",
        "ter": 0.40,
        "sleeve": SLEEVE_COMMODITY,
        "role": "satellite",
        "replication": "physisch (Gold)",
        "distribution": "ausschüttend",
        "domicile": "Schweiz",
        "index_name": "Gold",
        "kid": True,
        "justetf": "https://www.justetf.com/ch-de/etf-profile.html?isin=CH0139101593",
        "issuer": "https://www.justetf.com/ch-de/etf-profile.html?isin=CH0139101593",
        "peers": [],
        "notes": ["Physisch hinterlegtes Gold in CHF. Kein Unternehmen."],
    },
}

STARTER_SYMBOL = "VWCE.DE"
CORE_BY_SLEEVE = {
    SLEEVE_STOCK: "VWCE.DE",
    SLEEVE_BOND: "IDTL.L",
    SLEEVE_COMMODITY: "ZGLD.SW",
}


def sleeve_for(asset_class: str | AssetClass | None, symbol: str | None = None) -> str:
    if symbol and symbol.upper() in CORE:
        return CORE[symbol.upper()]["sleeve"]
    raw = asset_class.value if hasattr(asset_class, "value") else str(asset_class or "")
    raw = raw.lower()
    if raw in {"bond"}:
        return SLEEVE_BOND
    if raw in {"commodity"}:
        return SLEEVE_COMMODITY
    if raw in {"crypto"}:
        return SLEEVE_CRYPTO
    if raw in {"forex"}:
        return SLEEVE_CASH
    return SLEEVE_STOCK


def core_of(symbol: str) -> dict | None:
    return CORE.get(symbol.strip().upper())


def peers_of(symbol: str) -> list[str]:
    row = core_of(symbol)
    return list(row["peers"]) if row else []
