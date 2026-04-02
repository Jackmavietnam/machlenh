from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import json
import joblib
import numpy as np
import pandas as pd

from src.models.model_selection import build_dynamic_weights
from src.models.quality_gate import evaluate_quality_gate
from src.regime.regime_engine import make_regime_label
from src.utils.config import load_yaml, resolve_project_paths
from src.utils.db import DatabaseManager
from src.utils.logger import get_logger

FEATURE_IMPORTANCE_PROXY = [
    'ret_5', 'ret_20', 'sma_20_ratio', 'breakout_20', 'rsi_14', 'vol_zscore_20',
    'value_zscore_20', 'rs_vs_vnindex_5', 'rs_vs_vnindex_20', 'rolling_vol_20', 'drawdown_20',
    'relative_breakout_20', 'trend_slope_20', 'pullback_from_20d_high'
]


def _build_explanation(row: pd.Series) -> str:
    reasons = []
    if row.get('breakout_20', np.nan) > 1.0:
        reasons.append('gia vuot dinh 20 phien')
    if row.get('relative_breakout_20', np.nan) > 0:
        reasons.append('manh hon thi truong chung')
    if row.get('vol_zscore_20', np.nan) > 1:
        reasons.append('volume tang bat thuong')
    if row.get('trend_slope_20', np.nan) > 0:
        reasons.append('duong trung binh dang huong len')
    if row.get('pullback_from_20d_high', np.nan) < 0.04 and row.get('rsi_14', np.nan) > 50:
        reasons.append('giu duoc vung manh gan dinh')
    if row.get('drawdown_20', np.nan) < -0.12:
        reasons.append('dang o vung rut manh')
    return '; '.join(reasons[:3]) if reasons else 'tin hieu tong hop tu nhieu feature'


def _score_to_direction(prob: float, cfg: dict) -> str:
    if prob >= cfg['alerts']['buy_threshold']:
        return 'BUY'
    if prob >= cfg['alerts']['watch_up_threshold']:
        return 'WATCH-UP'
    if prob <= cfg['alerts']['sell_threshold']:
        return 'SELL'
    if prob <= 1 - cfg['alerts']['watch_up_threshold']:
        return 'WATCH-DOWN'
    return 'NEUTRAL'


def _apply_regime_gate(prob: float, confidence: float, row: pd.Series, cfg: dict) -> tuple[float, float, list[str]]:
    regime_cfg = cfg.get('regime_gate', {})
    if not regime_cfg.get('enabled', True):
        return prob, confidence, []
    trend = row.get('market_trend_state', 'unknown')
    vol = row.get('market_vol_state', 'unknown')
    notes = []

    if trend == 'downtrend':
        if regime_cfg.get('block_buy_in_downtrend', True) and prob >= cfg['alerts']['buy_threshold']:
            prob = min(prob, 0.59)
            confidence *= 0.80
            notes.append('chan BUY do thi truong downtrend')
        elif regime_cfg.get('block_watchup_in_downtrend', True) and prob >= cfg['alerts']['watch_up_threshold']:
            prob = min(prob, 0.54)
            confidence *= 0.85
            notes.append('ha WATCH-UP do thi truong downtrend')
    if trend == 'sideway':
        penalty = float(regime_cfg.get('confidence_penalty_sideway', 0.05))
        confidence = max(0.0, confidence - penalty)
        notes.append('giam confidence do thi truong sideway')
    if vol == 'high_vol':
        penalty = float(regime_cfg.get('confidence_penalty_high_vol', 0.05))
        confidence = max(0.0, confidence - penalty)
        notes.append('giam confidence do bien dong cao')
    return prob, confidence, notes


def _confidence_band(confidence: float, cfg: dict) -> str:
    bands = cfg.get('alerts', {}).get('confidence_bands', {})
    if confidence >= float(bands.get('high', 0.75)):
        return 'HIGH'
    if confidence >= float(bands.get('medium', 0.60)):
        return 'MEDIUM'
    if confidence >= float(bands.get('low', 0.52)):
        return 'LOW'
    return 'VERY_LOW'


def _build_symbol_ranking(latest: pd.DataFrame, ensemble_df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    base = latest[['symbol', 'date', 'close']].copy().reset_index(drop=True)
    work = ensemble_df.copy()
    if 'gate_notes' not in work.columns:
        work['gate_notes'] = ''
    merged = base.merge(
        work[['symbol', 'p_up_5d', 'confidence', 'regime', 'reason_text', 'gate_notes']],
        on='symbol', how='left'
    )
    merged['direction'] = merged['p_up_5d'].apply(lambda x: _score_to_direction(float(x), cfg))
    merged['signal_strength'] = (merged['p_up_5d'] - 0.5).abs() * 2
    merged['confidence_band'] = merged['confidence'].apply(lambda x: _confidence_band(float(x), cfg))
    merged['ranking_score'] = np.where(
        merged['p_up_5d'] >= 0.5,
        merged['p_up_5d'] * (1 + merged['confidence']),
        (1 - merged['p_up_5d']) * (1 + merged['confidence']),
    )
    return merged.sort_values(['ranking_score', 'confidence'], ascending=[False, False]).reset_index(drop=True)


def _export_rankings(ranking_df: pd.DataFrame, label_horizon: int, paths: dict, cfg: dict) -> None:
    top_n = int(cfg.get('reporting', {}).get('ranking_top_n', 12))
    out_csv = paths['artifacts_dir'] / f'ranking_latest_label_{label_horizon}d.csv'
    ranking_df.to_csv(out_csv, index=False)
    if cfg.get('reporting', {}).get('export_excel', True):
        out_xlsx = paths['artifacts_dir'] / f'ranking_latest_label_{label_horizon}d.xlsx'
        with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
            ranking_df.to_excel(writer, sheet_name='tong_hop', index=False)
            ranking_df.head(top_n).to_excel(writer, sheet_name='top_xep_hang', index=False)
            ranking_df.sort_values('p_up_5d', ascending=False).head(top_n).to_excel(writer, sheet_name='top_tang', index=False)
            ranking_df.sort_values('p_up_5d', ascending=True).head(top_n).to_excel(writer, sheet_name='top_giam', index=False)


def generate_predictions(label_horizon: int = 5) -> Path:
    paths = resolve_project_paths('.')
    logger = get_logger('predict', paths['log_dir'] / 'predict.log')
    cfg = load_yaml('config/model_config.yaml')
    db = DatabaseManager(paths['db_path'])
    df = pd.read_parquet(paths['features_dir'] / 'features_daily.parquet')
    df['date'] = pd.to_datetime(df['date'])
    latest_date = df['date'].max()
    latest = df[df['date'] == latest_date].copy().reset_index(drop=True)
    per_model = []
    ensemble_store: Dict[str, np.ndarray] = {}
    static_weights = cfg.get('ensemble', {}).get('weights', {})
    dynamic_weights, scorecard = build_dynamic_weights(paths['artifacts_dir'], static_weights, cfg)
    quality_gate = evaluate_quality_gate(paths['artifacts_dir'], cfg)

    for model_path in sorted((paths['artifacts_dir'] / 'models').glob(f'*label_{label_horizon}d.joblib')):
        payload = joblib.load(model_path)
        pipeline = payload['pipeline']
        features: List[str] = payload['features']
        model_name = model_path.stem.replace(f'_label_{label_horizon}d', '')
        X = latest[features].copy()
        proba = pipeline.predict_proba(X)[:, 1]
        ensemble_store[model_name] = proba
        for i, row in latest.iterrows():
            contrib = {k: row.get(k) for k in FEATURE_IMPORTANCE_PROXY if k in row.index}
            per_model.append({
                'symbol': row['symbol'],
                'date': row['date'].strftime('%Y-%m-%d'),
                'model_name': model_name,
                'p_up_3d': None,
                'p_up_5d': float(proba[i]),
                'regime': make_regime_label(row),
                'confidence': float(abs(proba[i] - 0.5) * 2),
                'alert_level': None,
                'feature_contrib_json': json.dumps(contrib, ensure_ascii=False, default=str),
                'reason_text': _build_explanation(row),
            })
    if not per_model:
        logger.warning('Chua co model nao de sinh predictions')
        return paths['artifacts_dir'] / 'predictions_empty.csv'

    pred_df = pd.DataFrame(per_model)
    ensemble_rows = []
    for i, row in latest.iterrows():
        weighted_sum = 0.0
        total_weight = 0.0
        for model_name, probs in ensemble_store.items():
            w = float(dynamic_weights.get(model_name, static_weights.get(model_name, 0.0)))
            if w <= 0:
                continue
            weighted_sum += w * float(probs[i])
            total_weight += w
        ensemble_p = weighted_sum / total_weight if total_weight > 0 else float(pred_df[pred_df['symbol'] == row['symbol']]['p_up_5d'].mean())
        confidence = float(abs(ensemble_p - 0.5) * 2)
        ensemble_p, confidence, gate_notes = _apply_regime_gate(ensemble_p, confidence, row, cfg)
        ensemble_rows.append({
            'symbol': row['symbol'],
            'date': row['date'].strftime('%Y-%m-%d'),
            'model_name': 'ensemble',
            'p_up_3d': None,
            'p_up_5d': ensemble_p,
            'regime': make_regime_label(row),
            'confidence': confidence,
            'alert_level': None,
            'feature_contrib_json': json.dumps({k: row.get(k) for k in FEATURE_IMPORTANCE_PROXY if k in row.index}, ensure_ascii=False, default=str),
            'reason_text': _build_explanation(row),
            'gate_notes': '; '.join(gate_notes),
            'quality_gate_passed': quality_gate.get('passed', True),
        })
    ensemble_df = pd.DataFrame(ensemble_rows)
    ranking_df = _build_symbol_ranking(latest, ensemble_df, cfg)
    final_df = pd.concat([pred_df, ensemble_df], ignore_index=True)
    db.write_dataframe('predictions_daily', final_df, if_exists='replace')
    db.write_dataframe('ranking_daily', ranking_df, if_exists='replace')
    out = paths['artifacts_dir'] / f'predictions_latest_label_{label_horizon}d.csv'
    final_df.to_csv(out, index=False)
    _export_rankings(ranking_df, label_horizon, paths, cfg)
    logger.info(
        'Da sinh predictions V1.4 cho %s dong | symbol=%s | ranking=%s | quality_gate=%s',
        len(final_df), latest['symbol'].nunique(), len(ranking_df), quality_gate.get('passed', True)
    )
    return out
