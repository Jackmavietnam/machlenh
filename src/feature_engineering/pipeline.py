from __future__ import annotations

import json
import numpy as np
import pandas as pd

from src.feature_engineering.indicators import (
    atr,
    breakout_ratio,
    drawdown_from_peak,
    ema,
    macd,
    recovery_from_low,
    rolling_zscore,
    rsi,
    sma,
    stochastic_k,
)
from src.utils.config import load_yaml, resolve_project_paths
from src.utils.db import DatabaseManager
from src.utils.logger import get_logger

LABEL_COLS = ['label_3d', 'label_5d']


def _effective_value(df: pd.DataFrame) -> pd.Series:
    if 'value' not in df.columns:
        return df['close'] * df['volume']
    value = pd.to_numeric(df['value'], errors='coerce')
    fallback = df['close'] * df['volume']
    return value.fillna(fallback)


def _build_symbol_features(df: pd.DataFrame, market_df: pd.DataFrame | None = None, sector_name: str | None = None) -> pd.DataFrame:
    out = df.copy().sort_values('date')
    out['effective_value'] = _effective_value(out)
    out['ret_1'] = out['close'].pct_change(1)
    out['ret_3'] = out['close'].pct_change(3)
    out['ret_5'] = out['close'].pct_change(5)
    out['ret_10'] = out['close'].pct_change(10)
    out['ret_20'] = out['close'].pct_change(20)
    out['ret_60'] = out['close'].pct_change(60)
    out['sma_5'] = sma(out['close'], 5)
    out['sma_10'] = sma(out['close'], 10)
    out['sma_20'] = sma(out['close'], 20)
    out['sma_60'] = sma(out['close'], 60)
    out['ema_12'] = ema(out['close'], 12)
    out['ema_26'] = ema(out['close'], 26)
    out['sma_5_ratio'] = out['close'] / out['sma_5']
    out['sma_10_ratio'] = out['close'] / out['sma_10']
    out['sma_20_ratio'] = out['close'] / out['sma_20']
    out['sma_60_ratio'] = out['close'] / out['sma_60']
    out['ema_12_ratio'] = out['close'] / out['ema_12']
    out['ema_26_ratio'] = out['close'] / out['ema_26']
    out['dist_high_20'] = out['close'] / out['high'].rolling(20).max()
    out['dist_low_20'] = out['close'] / out['low'].rolling(20).min()
    out['trend_slope_20'] = out['sma_20'].pct_change(5)
    out['trend_slope_60'] = out['sma_60'].pct_change(10)
    out['rsi_14'] = rsi(out['close'], 14)
    out['stoch_k_14'] = stochastic_k(out, 14)
    out['atr_14'] = atr(out, 14)
    out['atr_pct_14'] = out['atr_14'] / out['close']
    out['range_pct'] = (out['high'] - out['low']) / out['close']
    out['rolling_vol_5'] = out['ret_1'].rolling(5).std()
    out['rolling_vol_20'] = out['ret_1'].rolling(20).std()
    out['vol_zscore_5'] = rolling_zscore(out['volume'], 5)
    out['vol_zscore_20'] = rolling_zscore(out['volume'], 20)
    out['value_zscore_20'] = rolling_zscore(out['effective_value'], 20)
    out['value_ratio_20'] = out['effective_value'] / out['effective_value'].rolling(20).mean()
    out['gap_pct'] = out['open'] / out['close'].shift(1) - 1
    out['close_to_high_5'] = out['close'] / out['high'].rolling(5).max()
    out['close_to_low_5'] = out['close'] / out['low'].rolling(5).min()
    out['breakout_20'] = breakout_ratio(out['close'], 20)
    out['breakout_60'] = breakout_ratio(out['close'], 60)
    out['drawdown_20'] = drawdown_from_peak(out['close'], 20)
    out['drawdown_60'] = drawdown_from_peak(out['close'], 60)
    out['recovery_20'] = recovery_from_low(out['close'], 20)
    out['recovery_60'] = recovery_from_low(out['close'], 60)
    out['volume_trend_5_20'] = out['volume'].rolling(5).mean() / out['volume'].rolling(20).mean()
    out['momentum_spread_20_60'] = out['ret_20'] - out['ret_60']
    out['pullback_from_20d_high'] = 1 - out['dist_high_20']
    out['bounce_from_20d_low'] = out['dist_low_20'] - 1
    macd_line, macd_signal, macd_hist = macd(out['close'])
    out['macd'] = macd_line
    out['macd_signal'] = macd_signal
    out['macd_hist'] = macd_hist
    if market_df is not None and not market_df.empty:
        out = out.merge(market_df[['date', 'market_ret_1', 'market_ret_5', 'market_ret_20', 'market_trend_state', 'market_vol_state', 'market_breakout_20']], on='date', how='left')
        out['rs_vs_vnindex_5'] = out['ret_5'] - out['market_ret_5']
        out['rs_vs_vnindex_20'] = out['ret_20'] - out['market_ret_20']
        out['stock_beta_60'] = out['ret_1'].rolling(60).cov(out['market_ret_1']) / out['market_ret_1'].rolling(60).var()
        out['relative_breakout_20'] = out['breakout_20'] - out['market_breakout_20']
    else:
        out['market_ret_1'] = np.nan
        out['market_ret_5'] = np.nan
        out['market_ret_20'] = np.nan
        out['market_trend_state'] = 'unknown'
        out['market_vol_state'] = 'unknown'
        out['market_breakout_20'] = np.nan
        out['rs_vs_vnindex_5'] = np.nan
        out['rs_vs_vnindex_20'] = np.nan
        out['stock_beta_60'] = np.nan
        out['relative_breakout_20'] = np.nan
    out['sector_name'] = sector_name or 'unknown'
    return out


def _build_market_features(index_df: pd.DataFrame) -> pd.DataFrame:
    m = index_df.copy().sort_values('date')
    m['market_ret_1'] = m['close'].pct_change(1)
    m['market_ret_5'] = m['close'].pct_change(5)
    m['market_ret_20'] = m['close'].pct_change(20)
    m['market_sma20'] = m['close'].rolling(20).mean()
    m['market_sma50'] = m['close'].rolling(50).mean()
    up_cond = (m['close'] > m['market_sma20']) & (m['market_sma20'] > m['market_sma50'])
    down_cond = (m['close'] < m['market_sma20']) & (m['market_sma20'] < m['market_sma50'])
    m['market_trend_state'] = np.where(up_cond, 'uptrend', np.where(down_cond, 'downtrend', 'sideway'))
    market_vol_20 = m['market_ret_1'].rolling(20).std()
    q70 = market_vol_20.quantile(0.7)
    q30 = market_vol_20.quantile(0.3)
    m['market_vol_state'] = np.where(market_vol_20 > q70, 'high_vol', np.where(market_vol_20 < q30, 'low_vol', 'mid_vol'))
    m['market_breakout_20'] = breakout_ratio(m['close'], 20)
    return m


def run_feature_engineering() -> None:
    paths = resolve_project_paths('.')
    logger = get_logger('feature_engineering', paths['log_dir'] / 'feature_engineering.log')
    db = DatabaseManager(paths['db_path'])
    universe_cfg = load_yaml('config/universe.yaml')
    model_cfg = load_yaml('config/model_config.yaml')
    prices = pd.read_parquet(paths['processed_dir'] / 'prices_daily_cleaned.parquet')
    prices['date'] = pd.to_datetime(prices['date'])
    index_path = paths['raw_index_dir'] / f"{universe_cfg.get('index_symbol', 'VNINDEX')}.csv"
    market_df = pd.DataFrame()
    if index_path.exists():
        idx = pd.read_csv(index_path)
        idx['date'] = pd.to_datetime(idx['date'])
        market_df = _build_market_features(idx)
    symbol_infos = {item['symbol']: item.get('sector', '') for item in universe_cfg['universe']}
    all_frames = []
    for symbol, g in prices.groupby('symbol'):
        f = _build_symbol_features(g, market_df=market_df, sector_name=symbol_infos.get(symbol))
        for horizon in model_cfg['labels']['horizon_days']:
            threshold = model_cfg['labels']['threshold_return'][horizon]
            future_ret = f['close'].shift(-horizon) / f['close'] - 1
            f[f'future_return_{horizon}d'] = future_ret
            f[f'label_{horizon}d'] = (future_ret >= threshold).astype('float')
        f['symbol'] = symbol
        all_frames.append(f)
    final_df = pd.concat(all_frames, ignore_index=True).sort_values(['symbol', 'date'])
    feature_path = paths['features_dir'] / 'features_daily.parquet'
    final_df.to_parquet(feature_path, index=False)
    logger.info('Da tao feature V1.3: %s dong | %s cot', len(final_df), len(final_df.columns))
    minimal_feature_cols = [c for c in final_df.columns if c not in LABEL_COLS]
    records = []
    for _, row in final_df.iterrows():
        payload = {k: (None if pd.isna(row[k]) else row[k]) for k in minimal_feature_cols if k not in ['date']}
        records.append({'symbol': row['symbol'], 'date': pd.to_datetime(row['date']).strftime('%Y-%m-%d'), 'data_json': json.dumps(payload, ensure_ascii=False, default=str), 'label_3d': None if pd.isna(row.get('label_3d')) else int(row['label_3d']), 'label_5d': None if pd.isna(row.get('label_5d')) else int(row['label_5d'])})
    db.write_dataframe('features_daily', pd.DataFrame(records), if_exists='replace')
