from __future__ import annotations

from pathlib import Path
from typing import List
import pandas as pd

from src.ingest.adapters import VnstockAdapter
from src.utils.config import load_yaml, resolve_project_paths
from src.utils.db import DatabaseManager
from src.utils.logger import get_logger


def run_ingest(start: str, end: str) -> None:
    paths = resolve_project_paths('.')
    logger = get_logger('ingest', paths['log_dir'] / 'ingest.log')
    universe_cfg = load_yaml('config/universe.yaml')
    db = DatabaseManager(paths['db_path'])
    db.initialize(Path('db/schema.sql'))
    adapter = VnstockAdapter()

    symbol_rows: List[dict] = []
    for item in universe_cfg['universe']:
        symbol_rows.append({'symbol': item['symbol'], 'sector': item.get('sector', ''), 'subgroup': ''})
    db.write_dataframe('symbol_info', pd.DataFrame(symbol_rows), if_exists='append')

    for item in universe_cfg['universe']:
        symbol = item['symbol']
        result = adapter.fetch_stock_daily(symbol=symbol, start=start, end=end)
        raw_path = paths['raw_daily_dir'] / f'{symbol}.csv'
        if result.error:
            logger.warning('Loi ingest %s: %s', symbol, result.error)
            continue
        result.df.to_csv(raw_path, index=False)
        db.upsert_prices_daily(result.df)
        logger.info('Da ingest %s: %s dong', symbol, len(result.df))

    index_symbol = universe_cfg.get('index_symbol', 'VNINDEX')
    index_result = adapter.fetch_index_daily(index_symbol=index_symbol, start=start, end=end)
    if not index_result.error and not index_result.df.empty:
        idx_df = index_result.df.rename(columns={'symbol': 'index_symbol'})
        idx_df['index_symbol'] = index_symbol
        idx_df.to_csv(paths['raw_index_dir'] / f'{index_symbol}.csv', index=False)
        db.upsert_index_daily(idx_df[['index_symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'value', 'source']])
        logger.info('Da ingest index %s: %s dong', index_symbol, len(idx_df))
    else:
        logger.warning('Khong ingest duoc index %s: %s', index_symbol, index_result.error)
