from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

from src.models.predict import _build_symbol_ranking
from src.models.train import _extract_feature_importance
from src.utils.config import load_yaml


def test_v15_ranking_has_confidence_band() -> None:
    cfg = load_yaml('config/model_config.yaml')
    latest = pd.DataFrame({
        'symbol': ['AAA', 'BBB'],
        'date': pd.to_datetime(['2026-01-01', '2026-01-01']),
        'close': [10, 20],
    })
    ensemble = pd.DataFrame({
        'symbol': ['AAA', 'BBB'],
        'p_up_5d': [0.72, 0.41],
        'confidence': [0.80, 0.58],
        'regime': ['uptrend', 'sideway'],
        'reason_text': ['a', 'b'],
        'gate_notes': ['', ''],
    })
    ranking = _build_symbol_ranking(latest, ensemble, cfg)
    assert 'confidence_band' in ranking.columns
    assert ranking.loc[ranking['symbol'] == 'AAA', 'confidence_band'].iloc[0] == 'HIGH'


def test_v15_extract_feature_importance_logistic() -> None:
    X = pd.DataFrame({'a': [0, 1, 0, 1], 'b': [1, 1, 0, 0]})
    y = pd.Series([0, 1, 0, 1])
    pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median').set_output(transform='pandas')),
        ('model', LogisticRegression(max_iter=1000)),
    ])
    pipe.fit(X, y)
    importance = _extract_feature_importance(pipe, ['a', 'b'], 'logistic_regression')
    assert not importance.empty
    assert set(importance.columns) >= {'model_name', 'feature', 'importance', 'importance_norm'}
