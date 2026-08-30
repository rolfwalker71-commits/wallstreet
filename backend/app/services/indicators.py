from __future__ import annotations

import math

import pandas as pd


def sma(series: pd.Series, window: int) -> float | None:
    if len(series) < window:
        return None
    value = float(series.tail(window).mean())
    return None if math.isnan(value) else value


def ema(series: pd.Series, span: int) -> float | None:
    if len(series) < span:
        return None
    value = float(series.ewm(span=span, adjust=False).mean().iloc[-1])
    return None if math.isnan(value) else value


def rsi(series: pd.Series, period: int = 14) -> float | None:
    if len(series) < period + 1:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    last_gain = float(avg_gain.iloc[-1])
    last_loss = float(avg_loss.iloc[-1])
    if math.isnan(last_gain) or math.isnan(last_loss):
        return None
    if last_loss == 0:
        return 100.0 if last_gain > 0 else 50.0
    value = 100 - (100 / (1 + last_gain / last_loss))
    return None if math.isnan(value) else value


def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[float | None, float | None, float | None]:
    if len(series) < slow + signal:
        return None, None, None
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    line = ema_fast - ema_slow
    sig = line.ewm(span=signal, adjust=False).mean()
    hist = line - sig
    macd_v = float(line.iloc[-1])
    signal_v = float(sig.iloc[-1])
    hist_v = float(hist.iloc[-1])
    if any(math.isnan(v) for v in (macd_v, signal_v, hist_v)):
        return None, None, None
    return macd_v, signal_v, hist_v


def compute_technicals(closes: pd.Series) -> dict[str, float | None]:
    macd_line, macd_signal, macd_hist = macd(closes)
    return {
        "rsi_14": rsi(closes, 14),
        "sma_20": sma(closes, 20),
        "sma_50": sma(closes, 50),
        "ema_12": ema(closes, 12),
        "ema_26": ema(closes, 26),
        "macd": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "last_close": float(closes.iloc[-1]) if len(closes) else None,
    }