from __future__ import annotations

import pandas as pd

from src.alerts.engine import _filter_alerts
from src.models.predict import _build_symbol_ranking
from src.utils.config import load_yaml


def test_ranking_and_alert_filter_v12() -> None:
    cfg = load_yaml('config/model_config.yaml')
    latest = pd.DataFrame({
        'symbol': ['AAA', 'BBB', 'CCC'],
        'date': pd.to_datetime(['2026-01-01'] * 3),
        'close': [10, 20, 30],
    })
    ensemble = pd.DataFrame({
        'symbol': ['AAA', 'BBB', 'CCC'],
        'p_up_5d': [0.72, 0.48, 0.22],
        'confidence': [0.66, 0.10, 0.70],
        'regime': ['uptrend', 'sideway', 'downtrend'],
        'reason_text': ['a', 'b', 'c'],
    })
    ranking = _build_symbol_ranking(latest, ensemble, cfg)
    assert 'ranking_score' in ranking.columns
    assert ranking.iloc[0]['symbol'] in {'AAA', 'CCC'}

    grouped = ranking[['symbol', 'date', 'p_up_5d', 'confidence', 'regime']].copy()
    grouped['feature_contrib_json'] = '{}'
    grouped['reason_text'] = 'ly do'
    grouped['direction'] = grouped['p_up_5d'].apply(lambda p: 'BUY' if p >= 0.65 else ('SELL' if p <= 0.35 else 'NEUTRAL'))
    grouped['direction_score'] = grouped['direction'].map({'BUY': 5, 'SELL': 1, 'NEUTRAL': 3})
    filtered = _filter_alerts(grouped, cfg)
    assert len(filtered) >= 1
    assert 'BBB' not in filtered['symbol'].tolist()
