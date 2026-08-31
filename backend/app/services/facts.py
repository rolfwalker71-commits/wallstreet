"""Nur belegte Zahlen und wörtliche Schlagzeilen — keine Deutung, keine erfundenen Events."""

from __future__ import annotations

from typing import Any

ACTION_LABEL = {"buy": "Kauf", "hold": "Halten", "sell": "Verkauf"}

FACTS_ONLY_RULE = """
Harte Regeln:
- Keine Halluzination. Keine Interpretation. Keine Prognose. Keine Motive.
- Nur Zahlen und Texte, die in den übergebenen Daten stehen.
- Keine Unternehmensnews, Deals, Quartalszahlen oder Personen, die nicht wörtlich in den Schlagzeilen stehen.
- Fehlende News heisst: «Keine Meldung, die den Titel namentlich nennt.» Nicht durch Allgemeinwissen ersetzen.
- Keine Wörter wie «könnte», «dürfte», «Positionierung», «These», «Underdog», «Potenzial».
"""


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_num(value: Any, digits: int = 2) -> str | None:
    n = as_float(value)
    if n is None:
        return None
    return f"{n:.{digits}f}"


def headlines_from_sources(sources: Any) -> list[str]:
    """Nur echte Titel aus gespeicherten News-Quellen, kein LLM-Summary."""
    if not sources:
        return []
    if isinstance(sources, str):
        text = sources.strip()
        return [text] if text else []
    if not isinstance(sources, list):
        return []
    out: list[str] = []
    for row in sources:
        if isinstance(row, str) and row.strip():
            out.append(row.strip())
            continue
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "").strip()
        source = str(row.get("source") or "").strip()
        if not title:
            continue
        out.append(f"{title} ({source})" if source else title)
    return out[:8]


def technical_fact_lines(technicals: dict[str, Any] | None, *, price: float | None = None, currency: str = "") -> list[str]:
    tech = technicals or {}
    lines: list[str] = []
    close = as_float(tech.get("last_close")) or price
    if close is not None:
        cur = f" {currency}" if currency else ""
        lines.append(f"Kurs: {fmt_num(close, 2)}{cur}")
    rsi = as_float(tech.get("rsi_14"))
    if rsi is not None:
        lines.append(f"RSI-14: {fmt_num(rsi, 1)}")
    sma20 = as_float(tech.get("sma_20"))
    sma50 = as_float(tech.get("sma_50"))
    if sma20 is not None:
        lines.append(f"SMA-20: {fmt_num(sma20, 2)}")
    if sma50 is not None:
        lines.append(f"SMA-50: {fmt_num(sma50, 2)}")
    if sma20 is not None and sma50 is not None:
        rel = "über" if sma20 > sma50 else "unter" if sma20 < sma50 else "gleich"
        lines.append(f"SMA-20 liegt {rel} SMA-50.")
    if close is not None and sma50 is not None:
        rel = "über" if close > sma50 else "unter" if close < sma50 else "auf"
        lines.append(f"Kurs liegt {rel} dem SMA-50.")
    macd = as_float(tech.get("macd"))
    signal = as_float(tech.get("macd_signal"))
    if macd is not None:
        lines.append(f"MACD: {fmt_num(macd, 3)}")
    if signal is not None:
        lines.append(f"MACD-Signal: {fmt_num(signal, 3)}")
    if macd is not None and signal is not None:
        rel = "über" if macd > signal else "unter" if macd < signal else "auf"
        lines.append(f"MACD liegt {rel} dem Signal.")
    return lines


def news_fact_lines(headlines: list[str] | None) -> list[str]:
    titles = [h.strip() for h in (headlines or []) if h and h.strip()]
    if not titles:
        return ["News: keine Meldung, die den Titel namentlich nennt."]
    lines = ["News (wörtlich, nur Treffer zum Titel):"]
    lines.extend(f"- {title}" for title in titles[:6])
    return lines


def action_from_technicals(technicals: dict[str, Any] | None) -> tuple[str, float]:
    """Regelwerk auf gemessenen Indikatoren, keine Marktmeinung."""
    rsi = as_float((technicals or {}).get("rsi_14"))
    if rsi is not None and rsi <= 32:
        return "buy", 0.58
    if rsi is not None and rsi >= 72:
        return "sell", 0.56
    return "hold", 0.45


def build_fact_rationale(
    *,
    symbol: str,
    name: str,
    currency: str = "",
    price: float | None = None,
    technicals: dict[str, Any] | None = None,
    headlines: list[str] | None = None,
    last_action: str | None = None,
    last_confidence: float | None = None,
    action: str | None = None,
) -> str:
    parts = [f"{name} ({symbol})."]
    parts.extend(technical_fact_lines(technicals, price=price, currency=currency))
    if last_action:
        label = ACTION_LABEL.get(last_action, last_action)
        if last_confidence is not None:
            parts.append(f"Letzte gespeicherte Aktion: {label}, Konfidenz {last_confidence:.0%}.")
        else:
            parts.append(f"Letzte gespeicherte Aktion: {label}.")
    parts.extend(news_fact_lines(headlines))
    if action:
        rsi = as_float((technicals or {}).get("rsi_14"))
        rsi_txt = f"RSI-14={fmt_num(rsi, 1)}" if rsi is not None else "RSI-14 fehlt"
        if action == "buy":
            parts.append(f"Regel: Kauf, weil {rsi_txt} ≤ 32.")
        elif action == "sell":
            parts.append(f"Regel: Verkauf, weil {rsi_txt} ≥ 72.")
        else:
            parts.append(f"Regel: Halten, weil {rsi_txt} zwischen 32 und 72 liegt oder fehlt.")
    return " ".join(parts)


def quant_fact_brief(technicals: dict[str, Any] | None) -> str:
    lines = technical_fact_lines(technicals)
    return " ".join(lines) if lines else "Keine ausreichende Kursreihe für Indikatoren."
