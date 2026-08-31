from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from app.models.enums import TransactionSide

SIDE_ALIASES = {
    "buy": TransactionSide.BUY,
    "kauf": TransactionSide.BUY,
    "kaufen": TransactionSide.BUY,
    "long": TransactionSide.BUY,
    "sell": TransactionSide.SELL,
    "verkauf": TransactionSide.SELL,
    "verkaufen": TransactionSide.SELL,
    "short": TransactionSide.SELL,
}

HEADER_ALIASES = {
    "date": "date",
    "datum": "date",
    "isin": "isin",
    "symbol": "symbol",
    "ticker": "symbol",
    "titel": "symbol",
    "qty": "qty",
    "quantity": "qty",
    "menge": "qty",
    "anzahl": "qty",
    "price": "price",
    "preis": "price",
    "kurs": "price",
    "side": "side",
    "seite": "side",
    "typ": "side",
    "aktion": "side",
}


def _norm_header(name: str) -> str | None:
    key = name.strip().lower().replace(" ", "_")
    return HEADER_ALIASES.get(key)


def parse_trade_date(raw: str) -> datetime:
    text = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            dt = datetime.strptime(text[:10] if fmt.startswith("%Y") and "-" in text else text, fmt)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue
    raise ValueError(f"Datum «{raw}» nicht lesbar (YYYY-MM-DD oder TT.MM.JJJJ).")


def parse_side(raw: str) -> TransactionSide:
    key = (raw or "").strip().lower()
    if key not in SIDE_ALIASES:
        raise ValueError(f"Seite «{raw}» unbekannt — erlaubt: buy/sell oder Kauf/Verkauf.")
    return SIDE_ALIASES[key]


def parse_decimal(raw: str, field: str) -> Decimal:
    text = (raw or "").strip().replace("'", "").replace(" ", "")
    if text.count(",") == 1 and text.count(".") == 0:
        text = text.replace(",", ".")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{field} «{raw}» ist keine Zahl.") from exc
    if value <= 0:
        raise ValueError(f"{field} muss grösser als 0 sein.")
    return value


def parse_trade_rows(text: str) -> tuple[list[dict], list[dict]]:
    """Parst CSV mit Datum, ISIN oder Symbol, Menge, Preis, Seite. Fehler pro Zeile."""
    if not text or not text.strip():
        return [], [{"row": 0, "error": "Datei ist leer."}]
    sample = text.lstrip()
    dialect = csv.Sniffer().sniff(sample[:400], delimiters=",;\t")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return [], [{"row": 0, "error": "Keine Spaltenköpfe gefunden."}]
    mapping: dict[str, str] = {}
    for raw in reader.fieldnames:
        canon = _norm_header(raw or "")
        if canon:
            mapping[canon] = raw
    if "date" not in mapping or "qty" not in mapping or "price" not in mapping or "side" not in mapping:
        return [], [
            {
                "row": 0,
                "error": "Spalten fehlen. Erwartet: date, qty, price, side und isin oder symbol.",
            }
        ]
    if "isin" not in mapping and "symbol" not in mapping:
        return [], [{"row": 0, "error": "Spalte isin oder symbol fehlt."}]

    rows: list[dict] = []
    errors: list[dict] = []
    for index, raw in enumerate(reader, start=2):
        try:
            ident = ""
            if "isin" in mapping:
                ident = (raw.get(mapping["isin"]) or "").strip()
            symbol = (raw.get(mapping["symbol"]) or "").strip() if "symbol" in mapping else ""
            if not ident and not symbol:
                raise ValueError("ISIN oder Symbol fehlt.")
            rows.append(
                {
                    "row": index,
                    "date": parse_trade_date(raw.get(mapping["date"]) or ""),
                    "isin": ident.upper() if ident else None,
                    "symbol": symbol.upper() if symbol else None,
                    "qty": parse_decimal(raw.get(mapping["qty"]) or "", "Menge"),
                    "price": parse_decimal(raw.get(mapping["price"]) or "", "Preis"),
                    "side": parse_side(raw.get(mapping["side"]) or ""),
                }
            )
        except ValueError as exc:
            errors.append({"row": index, "error": str(exc)})
    return rows, errors
