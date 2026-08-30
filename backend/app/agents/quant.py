from __future__ import annotations

from app.agents.state import AgentState
from app.services.market import get_technicals


def _signal_text(tech: dict) -> str:
    parts: list[str] = []
    rsi = tech.get("rsi_14")
    if rsi is not None:
        if rsi >= 70:
            parts.append(f"RSI {rsi:.1f} überkauft")
        elif rsi <= 30:
            parts.append(f"RSI {rsi:.1f} überverkauft")
        else:
            parts.append(f"RSI {rsi:.1f} neutral")
    sma20, sma50 = tech.get("sma_20"), tech.get("sma_50")
    close = tech.get("last_close")
    if close and sma50:
        parts.append("Kurs über SMA-50" if close > sma50 else "Kurs unter SMA-50")
    if sma20 and sma50:
        parts.append("SMA-20 über SMA-50 (Aufwärtstrend)" if sma20 > sma50 else "SMA-20 unter SMA-50")
    macd, signal = tech.get("macd"), tech.get("macd_signal")
    if macd is not None and signal is not None:
        parts.append("MACD über Signal" if macd > signal else "MACD unter Signal")
    return "; ".join(parts) if parts else "Unzureichende Kursreihe für Indikatoren."


def quant_node(state: AgentState) -> AgentState:
    symbol = state["symbol"]
    tech = get_technicals(symbol)
    payload = tech.model_dump()
    return {
        "technicals": payload,
        "quant_brief": _signal_text(payload),
    }