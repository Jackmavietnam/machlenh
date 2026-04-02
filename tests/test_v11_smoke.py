from __future__ import annotations

import pandas as pd

from src.feature_engineering.pipeline import _build_market_features, _build_symbol_features
from src.models.train import prepare_training_data


def test_feature_pipeline_v11_smoke() -> None:
    dates = pd.date_range('2024-01-01', periods=120, freq='B')
    base = pd.DataFrame({
        'date': dates,
        'open': range(100, 220),
        'high': range(101, 221),
        'low': range(99, 219),
        'close': range(100, 220),
        'volume': [1_000_000 + i * 1000 for i in range(120)],
        'value': [100_000_000 + i * 100_000 for i in range(120)],
        'symbol': ['AAA'] * 120,
    })
    market = base[['date', 'open', 'high', 'low', 'close', 'volume', 'value']].copy()
    market_features = _build_market_features(market)
    out = _build_symbol_features(base, market_features, 'Test')
    assert 'breakout_20' in out.columns
    assert 'drawdown_20' in out.columns
    assert 'rs_vs_vnindex_20' in out.columns

    out['label_5d'] = ((out['close'].shift(-5) / out['close'] - 1) >= 0.03).astype(float)
    X, y, features = prepare_training_data(out, 'label_5d')
    assert len(features) > 10
    assert len(X) == len(y)
