from __future__ import annotations

from pathlib import Path
import pandas as pd

from src.cleaning.daily_cleaner import clean_daily_prices
from src.utils.config import resolve_project_paths
from src.utils.logger import get_logger


def run_cleaning() -> None:
    paths = resolve_project_paths('.')
    logger = get_logger('cleaning', paths['log_dir'] / 'cleaning.log')
    frames = []
    for csv_path in sorted(paths['raw_daily_dir'].glob('*.csv')):
        df = pd.read_csv(csv_path)
        frames.append(df)
    if not frames:
        logger.warning('Khong co file raw daily de cleaning')
        return
    all_df = pd.concat(frames, ignore_index=True)
    cleaned = clean_daily_prices(all_df)
    out_path = paths['processed_dir'] / 'prices_daily_cleaned.parquet'
    cleaned.to_parquet(out_path, index=False)
    logger.info('Da cleaning xong %s dong -> %s', len(cleaned), out_path)
