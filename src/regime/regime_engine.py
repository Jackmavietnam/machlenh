from __future__ import annotations

import pandas as pd


def make_regime_label(row: pd.Series) -> str:
    trend = row.get('market_trend_state', 'unknown')
    vol = row.get('market_vol_state', 'unknown')
    return f'{trend}|{vol}'
