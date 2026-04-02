from __future__ import annotations

import json
import uuid
from pathlib import Path
import pandas as pd

from src.models.quality_gate import evaluate_quality_gate
from src.utils.config import load_yaml, resolve_project_paths
from src.utils.db import DatabaseManager
from src.utils.logger import get_logger

DIRECTION_SCORE = {
    'BUY': 5,
    'WATCH-UP': 4,
    'NEUTRAL': 3,
    'WATCH-DOWN': 2,
    'SELL': 1,
}


def _classify(prob: float, cfg: dict) -> str:
    if prob >= cfg['alerts']['buy_threshold']:
        return 'BUY'
    if prob >= cfg['alerts']['watch_up_threshold']:
        return 'WATCH-UP'
    if prob <= cfg['alerts']['sell_threshold']:
        return 'SELL'
    if prob <= 1 - cfg['alerts']['watch_up_threshold']:
        return 'WATCH-DOWN'
    return 'NEUTRAL'


def _filter_alerts(df: pd.DataFrame, cfg: dict, quality_gate: dict | None = None) -> pd.DataFrame:
    quality_gate = quality_gate or {}
    min_conf = float(cfg['alerts'].get('confidence_threshold', 0.52))
    min_strength = float(cfg['alerts'].get('min_signal_strength', 0.05))
    allow_neutral = bool(cfg['alerts'].get('allow_neutral_alerts', False))
    top_n_each_side = int(cfg['alerts'].get('top_n_each_side', 6))
    max_total = int(cfg['alerts'].get('max_total_alerts', 14))
    adaptive_min_alerts = int(cfg['alerts'].get('adaptive_min_alerts', 4))
    fallback_top_n = int(cfg['alerts'].get('fallback_top_n', 6))

    if quality_gate.get('max_alerts_override'):
        max_total = min(max_total, int(quality_gate['max_alerts_override']))
        top_n_each_side = min(top_n_each_side, max_total)
        min_conf = max(min_conf, 0.55)

    work = df.copy()
    work['signal_strength'] = (work['p_up_5d'] - 0.5).abs() * 2
    strict = work[(work['confidence'] >= min_conf) & (work['signal_strength'] >= min_strength)]
    if not allow_neutral:
        strict = strict[strict['direction'] != 'NEUTRAL']
    selected = strict
    if len(selected) < adaptive_min_alerts:
        relaxed = work.copy()
        if not allow_neutral:
            relaxed = relaxed[relaxed['direction'] != 'NEUTRAL']
        relaxed = relaxed.sort_values(['signal_strength', 'confidence'], ascending=[False, False]).head(max(fallback_top_n, adaptive_min_alerts))
        selected = relaxed
    up_side = selected[selected['direction'].isin(['BUY', 'WATCH-UP'])].sort_values(['direction_score', 'confidence'], ascending=[False, False]).head(top_n_each_side)
    down_side = selected[selected['direction'].isin(['SELL', 'WATCH-DOWN'])].sort_values(['direction_score', 'confidence'], ascending=[False, False]).head(top_n_each_side)
    final = pd.concat([up_side, down_side], ignore_index=True)
    return final.sort_values(['signal_strength', 'confidence'], ascending=[False, False]).head(max_total).reset_index(drop=True)


def build_alerts(label_horizon: int = 5) -> Path:
    paths = resolve_project_paths('.')
    cfg = load_yaml('config/model_config.yaml')
    logger = get_logger('alerts', paths['log_dir'] / 'alerts.log')
    db = DatabaseManager(paths['db_path'])
    pred_df = db.read_sql('SELECT * FROM predictions_daily')
    quality_gate = evaluate_quality_gate(paths['artifacts_dir'], cfg)
    if pred_df.empty:
        logger.warning('Khong co prediction de build alert')
        out = paths['artifacts_dir'] / 'alerts_empty.csv'
        pd.DataFrame().to_csv(out, index=False)
        return out
    work = pred_df.copy()
    if 'model_name' in work.columns and (work['model_name'] == 'ensemble').any():
        grouped = work[work['model_name'] == 'ensemble'].copy()
    else:
        grouped = work.groupby(['symbol', 'date'], as_index=False).agg({'p_up_5d': 'mean', 'confidence': 'mean', 'regime': 'first', 'feature_contrib_json': 'first', 'reason_text': 'first'})
    grouped['direction'] = grouped['p_up_5d'].astype(float).apply(lambda x: _classify(x, cfg))
    grouped['direction_score'] = grouped['direction'].map(DIRECTION_SCORE)
    grouped['signal_strength'] = (grouped['p_up_5d'] - 0.5).abs() * 2
    filtered = _filter_alerts(grouped, cfg, quality_gate)
    alerts = []
    for _, row in filtered.iterrows():
        q_note = 'quality_gate_pass' if quality_gate.get('passed', True) else 'quality_gate_degraded'
        gate_note = row.get('gate_notes', '')
        confidence_band = row.get('confidence_band', 'UNKNOWN')
        rationale = (
            f"Regime={row['regime']} | P_up_5d={float(row['p_up_5d']):.3f} | Confidence={float(row['confidence']):.3f} "
            f"| Band={confidence_band} | Strength={float(row['signal_strength']):.3f} | Quality={q_note} | Gate={gate_note} | Ly do={row.get('reason_text', '')}"
        )
        invalidation = 'Vo SMA20, xac suat suy yeu, hoac mat vung breakout gan nhat'
        alerts.append({
            'alert_id': str(uuid.uuid4()),
            'symbol': row['symbol'],
            'ts': f"{row['date']} 15:00:00",
            'direction': row['direction'],
            'direction_score': int(row['direction_score']),
            'confidence': float(row['confidence']),
            'signal_strength': float(row['signal_strength']),
            'confidence_band': confidence_band,
            'rationale': rationale,
            'invalidation_rule': invalidation,
            'status': 'OPEN',
            'meta_json': json.dumps({'feature_contrib': row.get('feature_contrib_json'), 'quality_gate': quality_gate}, ensure_ascii=False),
        })
    alert_df = pd.DataFrame(alerts).sort_values(['direction_score', 'confidence'], ascending=[False, False]) if alerts else pd.DataFrame()
    db.write_dataframe('alerts', alert_df, if_exists='replace')
    out = paths['artifacts_dir'] / f'alerts_latest_label_{label_horizon}d.csv'
    alert_df.to_csv(out, index=False)
    logger.info('Da build %s alerts V1.4 | sau loc con %s alerts | quality_gate=%s', len(grouped), len(alert_df), quality_gate.get('passed', True))
    return out
