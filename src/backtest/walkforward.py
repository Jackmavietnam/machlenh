from __future__ import annotations

from pathlib import Path
import pandas as pd
from sklearn.metrics import precision_score, roc_auc_score

from src.models.train import prepare_training_data, _train_one
from src.utils.config import load_yaml, resolve_project_paths
from src.utils.logger import get_logger


def _calc_alert_quality(raw_test: pd.DataFrame, futret_col: str, top_n: int) -> dict:
    ordered = raw_test.sort_values('proba', ascending=False).head(top_n).copy()
    if ordered.empty:
        return {
            'top_n': top_n,
            'alert_precision': 0.0,
            'alert_avg_return': 0.0,
            'alert_win_rate': 0.0,
            'alert_count': 0,
        }
    truth = (ordered[futret_col] > 0).astype(int)
    pred = pd.Series([1] * len(ordered), index=ordered.index)
    return {
        'top_n': top_n,
        'alert_precision': float(precision_score(truth, pred, zero_division=0)),
        'alert_avg_return': float(ordered[futret_col].mean()),
        'alert_win_rate': float((ordered[futret_col] > 0).mean()),
        'alert_count': int(len(ordered)),
    }


def run_walkforward_backtest(label_horizon: int = 5) -> Path:
    paths = resolve_project_paths('.')
    logger = get_logger('backtest', paths['log_dir'] / 'backtest.log')
    cfg = load_yaml('config/model_config.yaml')
    df = pd.read_parquet(paths['features_dir'] / 'features_daily.parquet')
    df['date'] = pd.to_datetime(df['date'])
    label_col = f'label_{label_horizon}d'
    futret_col = f'future_return_{label_horizon}d'
    train_df = df.dropna(subset=[label_col]).copy().reset_index(drop=True)
    X, y, features = prepare_training_data(train_df, label_col)
    window = max(250, int(len(X) * 0.5))
    step = max(60, int(len(X) * 0.1))
    rows = []
    signal_threshold = float(cfg.get('backtest', {}).get('signal_threshold', 0.55))
    alert_top_n_list = list(cfg.get('backtest', {}).get('alert_top_n_list', [3, 5]))

    enabled_models = {k: v for k, v in cfg['models'].items() if v.get('enabled', False)}
    for model_name, model_meta in enabled_models.items():
        for start in range(0, max(1, len(X) - window - step), step):
            train_end = start + window
            test_end = min(train_end + step, len(X))
            X_train, y_train = X.iloc[start:train_end], y.iloc[start:train_end]
            X_test, y_test = X.iloc[train_end:test_end], y.iloc[train_end:test_end]
            raw_test = train_df.iloc[train_end:test_end].copy()
            if len(X_test) == 0 or len(set(y_train)) < 2:
                continue
            model = _train_one(model_name, model_meta['params'], X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
            pred = (proba >= 0.5).astype(int)
            precision = precision_score(y_test, pred, zero_division=0)
            auc = roc_auc_score(y_test, proba) if len(set(y_test)) > 1 else None
            raw_test['proba'] = proba
            trades = raw_test[raw_test['proba'] >= signal_threshold].copy()
            avg_return = float(trades[futret_col].mean()) if not trades.empty else 0.0
            win_rate = float((trades[futret_col] > 0).mean()) if not trades.empty else 0.0
            trade_count = int(len(trades))
            base_row = {
                'model_name': model_name,
                'window_start': start,
                'train_end': train_end,
                'test_end': test_end,
                'precision': precision,
                'auc': auc,
                'rows_test': len(X_test),
                'trade_count': trade_count,
                'avg_return': avg_return,
                'win_rate': win_rate,
                'n_features': len(features),
            }
            for top_n in alert_top_n_list:
                quality = _calc_alert_quality(raw_test, futret_col, int(top_n))
                row = dict(base_row)
                row.update(quality)
                rows.append(row)

    report = pd.DataFrame(rows)
    out_path = paths['artifacts_dir'] / f'walkforward_report_label_{label_horizon}d.csv'
    report.to_csv(out_path, index=False)

    summary_cols = ['model_name', 'precision_bt', 'auc_bt', 'avg_return', 'win_rate', 'trade_count', 'windows']
    if not report.empty:
        summary = report.groupby('model_name', as_index=False).agg(
            precision_bt=('precision', 'mean'),
            auc_bt=('auc', 'mean'),
            avg_return=('avg_return', 'mean'),
            win_rate=('win_rate', 'mean'),
            trade_count=('trade_count', 'mean'),
            windows=('window_start', 'nunique'),
        )
        summary.to_csv(paths['artifacts_dir'] / f'backtest_summary_label_{label_horizon}d.csv', index=False)

        alert_quality = report.groupby(['model_name', 'top_n'], as_index=False).agg(
            alert_precision=('alert_precision', 'mean'),
            alert_avg_return=('alert_avg_return', 'mean'),
            alert_win_rate=('alert_win_rate', 'mean'),
            alert_count=('alert_count', 'mean'),
            windows=('window_start', 'nunique'),
        )
        alert_quality.to_csv(paths['artifacts_dir'] / f'alert_quality_summary_label_{label_horizon}d.csv', index=False)
    else:
        pd.DataFrame(columns=summary_cols).to_csv(paths['artifacts_dir'] / f'backtest_summary_label_{label_horizon}d.csv', index=False)
        pd.DataFrame(columns=['model_name', 'top_n', 'alert_precision', 'alert_avg_return', 'alert_win_rate', 'alert_count', 'windows']).to_csv(
            paths['artifacts_dir'] / f'alert_quality_summary_label_{label_horizon}d.csv', index=False
        )

    if not report.empty and ((report['auc'].fillna(0) >= 0.95).any() or (report['precision'].fillna(0) >= 0.90).any()):
        logger.warning('Backtest co dau hieu metric bat thuong cao. Can kiem tra leakage truoc khi dung thuc chien.')
    logger.info('Backtest V1.5 xong | so window=%s | so model=%s | co alert_quality=%s', len(report), len(enabled_models), True)
    return out_path
