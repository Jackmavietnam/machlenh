from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def true_range(df: pd.DataFrame) -> pd.Series:
    prev_close = df['close'].shift(1)
    ranges = pd.concat([
        df['high'] - df['low'],
        (df['high'] - prev_close).abs(),
        (df['low'] - prev_close).abs(),
    ], axis=1)
    return ranges.max(axis=1)


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    return true_range(df).rolling(window).mean()


def macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast = ema(series, 12)
    slow = ema(series, 26)
    line = fast - slow
    signal = ema(line, 9)
    hist = line - signal
    return line, signal, hist


def rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window).mean()
    std = series.rolling(window).std().replace(0, np.nan)
    return (series - mean) / std


def breakout_ratio(series: pd.Series, window: int) -> pd.Series:
    highest = series.shift(1).rolling(window).max()
    return series / highest


def drawdown_from_peak(series: pd.Series, window: int) -> pd.Series:
    rolling_peak = series.rolling(window).max()
    return series / rolling_peak - 1


def recovery_from_low(series: pd.Series, window: int) -> pd.Series:
    rolling_low = series.rolling(window).min()
    return series / rolling_low - 1


def stochastic_k(df: pd.DataFrame, window: int = 14) -> pd.Series:
    lowest_low = df['low'].rolling(window).min()
    highest_high = df['high'].rolling(window).max()
    denom = (highest_high - lowest_low).replace(0, np.nan)
    return 100 * (df['close'] - lowest_low) / denom
