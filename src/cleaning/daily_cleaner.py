from __future__ import annotations

import pandas as pd


def clean_daily_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out['date'] = pd.to_datetime(out['date'])
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'value']
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors='coerce')
    out = out.dropna(subset=['date', 'close'])
    out = out.sort_values(['symbol', 'date']).drop_duplicates(['symbol', 'date'], keep='last')
    out = out[(out['high'] >= out['low']) | out['high'].isna() | out['low'].isna()]
    out['volume_anomaly_flag'] = ((out['volume'] <= 0) | out['volume'].isna()).astype(int)
    return out
