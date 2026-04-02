from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from src.utils.config import load_yaml, resolve_project_paths
from src.utils.logger import get_logger

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover
    LGBMClassifier = None

FEATURE_EXCLUDE = {
    'symbol', 'date', 'source', 'adjusted_flag', 'volume_anomaly_flag', 'market_trend_state', 'market_vol_state',
    'sector_name', 'label_3d', 'label_5d',
    'future_return_3d', 'future_return_5d'
}


def prepare_training_data(feature_df: pd.DataFrame, label_col: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    df = feature_df.copy()
    df = df.dropna(subset=[label_col])
    usable_features = [c for c in df.columns if c not in FEATURE_EXCLUDE and pd.api.types.is_numeric_dtype(df[c])]
    usable_features = [c for c in usable_features if not df[c].isna().all()]
    X = df[usable_features].copy()
    y = df[label_col].astype(int)
    return X, y, usable_features


def _make_imputer() -> SimpleImputer:
    imputer = SimpleImputer(strategy='median')
    if hasattr(imputer, 'set_output'):
        imputer = imputer.set_output(transform='pandas')
    return imputer


def _train_one(model_name: str, params: Dict, X_train: pd.DataFrame, y_train: pd.Series):
    if model_name == 'logistic_regression':
        model = LogisticRegression(**params)
    elif model_name == 'random_forest':
        model = RandomForestClassifier(**params)
    elif model_name == 'lightgbm':
        if LGBMClassifier is None:
            raise RuntimeError('lightgbm is not available')
        model = LGBMClassifier(**params)
    else:
        raise ValueError(f'Unsupported model: {model_name}')

    pipe = Pipeline([
        ('imputer', _make_imputer()),
        ('model', model),
    ])
    pipe.fit(X_train, y_train)
    return pipe


def _detect_suspicious_metrics(report_df: pd.DataFrame) -> list[str]:
    warnings = []
    if report_df.empty:
        return warnings
    for _, row in report_df.iterrows():
        auc = row.get('auc')
        precision = row.get('precision')
        model_name = row.get('model_name', 'unknown')
        if pd.notna(auc) and float(auc) >= 0.95:
            warnings.append(f"AUC bat thuong cao o {model_name}: {float(auc):.4f}. Can kiem tra leakage.")
        if pd.notna(precision) and float(precision) >= 0.90:
            warnings.append(f"Precision bat thuong cao o {model_name}: {float(precision):.4f}. Can kiem tra leakage.")
    return warnings


def _extract_feature_importance(pipe: Pipeline, features: List[str], model_name: str) -> pd.DataFrame:
    model = pipe.named_steps['model']
    values = None
    importance_type = 'unknown'

    if hasattr(model, 'feature_importances_'):
        values = np.asarray(model.feature_importances_, dtype=float)
        importance_type = 'feature_importances'
    elif hasattr(model, 'coef_'):
        coef = np.asarray(model.coef_, dtype=float)
        if coef.ndim == 2:
            coef = coef[0]
        values = np.abs(coef)
        importance_type = 'abs_coef'

    if values is None or len(values) != len(features):
        return pd.DataFrame(columns=['model_name', 'feature', 'importance', 'importance_norm', 'importance_type'])

    total = float(values.sum())
    norm = values / total if total > 0 else np.zeros_like(values)
    df = pd.DataFrame({
        'model_name': model_name,
        'feature': features,
        'importance': values,
        'importance_norm': norm,
        'importance_type': importance_type,
    })
    return df.sort_values(['importance', 'feature'], ascending=[False, True]).reset_index(drop=True)


def train_all_models(label_horizon: int = 5) -> Path:
    paths = resolve_project_paths('.')
    logger = get_logger('train', paths['log_dir'] / 'train.log')
    cfg = load_yaml('config/model_config.yaml')
    df = pd.read_parquet(paths['features_dir'] / 'features_daily.parquet')
    df['date'] = pd.to_datetime(df['date'])

    label_col = f'label_{label_horizon}d'
    X, y, features = prepare_training_data(df, label_col)
    split_1 = int(len(X) * (1 - cfg['training']['test_size_ratio']))
    X_train = X.iloc[:split_1]
    y_train = y.iloc[:split_1]
    X_test = X.iloc[split_1:]
    y_test = y.iloc[split_1:]

    model_dir = paths['artifacts_dir'] / 'models'
    model_dir.mkdir(parents=True, exist_ok=True)
    report_rows = []
    importance_frames = []

    for model_name, meta in cfg['models'].items():
        if not meta.get('enabled', False):
            continue
        try:
            pipe = _train_one(model_name, meta['params'], X_train, y_train)
            proba = pipe.predict_proba(X_test)[:, 1]
            pred = (proba >= 0.5).astype(int)
            precision = precision_score(y_test, pred, zero_division=0)
            auc = roc_auc_score(y_test, proba) if len(set(y_test)) > 1 else np.nan
            joblib.dump({'pipeline': pipe, 'features': features, 'label_col': label_col}, model_dir / f'{model_name}_{label_col}.joblib')
            report_rows.append({'model_name': model_name, 'precision': precision, 'auc': auc, 'n_features': len(features)})
            importance_df = _extract_feature_importance(pipe, features, model_name)
            if not importance_df.empty:
                importance_frames.append(importance_df)
            logger.info('Train xong %s | precision=%.4f | auc=%.4f | features=%s', model_name, precision, auc, len(features))
        except Exception as exc:
            logger.exception('Train loi %s: %s', model_name, exc)

    report_df = pd.DataFrame(report_rows)
    warnings = _detect_suspicious_metrics(report_df)
    report_path = paths['artifacts_dir'] / f'train_report_{label_col}.csv'
    report_df.to_csv(report_path, index=False)

    feature_importance_path = paths['artifacts_dir'] / f'feature_importance_{label_col}.csv'
    if importance_frames:
        pd.concat(importance_frames, ignore_index=True).to_csv(feature_importance_path, index=False)
    else:
        pd.DataFrame(columns=['model_name', 'feature', 'importance', 'importance_norm', 'importance_type']).to_csv(feature_importance_path, index=False)

    if warnings:
        warn_path = paths['artifacts_dir'] / f'train_warnings_{label_col}.txt'
        warn_path.write_text('\n'.join(warnings), encoding='utf-8')
        for msg in warnings:
            logger.warning(msg)
    return report_path
