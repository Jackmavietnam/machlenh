from __future__ import annotations

from pathlib import Path
import json
import pandas as pd


def _normalize(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors='coerce').fillna(0.0)
    if s.nunique() <= 1:
        return pd.Series([1.0] * len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


def _pick_col(df: pd.DataFrame, candidates: list[str], default: float = 0.0) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return pd.to_numeric(df[col], errors='coerce').fillna(default)
    return pd.Series([default] * len(df), index=df.index, dtype='float64')


def build_dynamic_weights(artifacts_dir: Path, static_weights: dict, cfg: dict) -> tuple[dict, pd.DataFrame]:
    mode = cfg.get('model_selection', {}).get('mode', 'static')
    min_model_weight = float(cfg.get('model_selection', {}).get('min_model_weight', 0.10))
    if mode != 'dynamic':
        return static_weights, pd.DataFrame()

    train_path = artifacts_dir / 'train_report_label_5d.csv'
    bt_path = artifacts_dir / 'backtest_summary_label_5d.csv'
    if not train_path.exists() or not bt_path.exists():
        return static_weights, pd.DataFrame()

    train_df = pd.read_csv(train_path)
    bt_df = pd.read_csv(bt_path)
    if train_df.empty or bt_df.empty:
        return static_weights, pd.DataFrame()

    merged = train_df.merge(bt_df, on='model_name', how='inner', suffixes=('_train', '_bt'))
    if merged.empty:
        return static_weights, pd.DataFrame()

    auc_train = _pick_col(merged, ['auc_train', 'auc'])
    precision_train = _pick_col(merged, ['precision_train', 'precision'])
    auc_bt = _pick_col(merged, ['auc_bt'])
    precision_bt = _pick_col(merged, ['precision_bt'])
    avg_return = _pick_col(merged, ['avg_return'])
    win_rate = _pick_col(merged, ['win_rate'])

    merged['train_score'] = 0.6 * _normalize(auc_train) + 0.4 * _normalize(precision_train)
    merged['backtest_score'] = (
        0.35 * _normalize(auc_bt) +
        0.25 * _normalize(precision_bt) +
        0.25 * _normalize(avg_return) +
        0.15 * _normalize(win_rate)
    )

    tw = float(cfg.get('model_selection', {}).get('train_weight', 0.35))
    bw = float(cfg.get('model_selection', {}).get('backtest_weight', 0.65))
    merged['final_score'] = tw * merged['train_score'] + bw * merged['backtest_score']

    score_sum = float(merged['final_score'].sum())
    if score_sum <= 0:
        return static_weights, merged

    weights = {row['model_name']: max(float(row['final_score']) / score_sum, min_model_weight) for _, row in merged.iterrows()}
    total = sum(weights.values())
    weights = {k: v / total for k, v in weights.items()}

    out_json = artifacts_dir / 'ensemble_weights_used_label_5d.json'
    out_json.write_text(json.dumps(weights, ensure_ascii=False, indent=2), encoding='utf-8')
    merged.to_csv(artifacts_dir / 'model_selection_scorecard_label_5d.csv', index=False)
    return weights, merged
