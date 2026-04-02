from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable
import pandas as pd


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        clean = df.copy()
        for col in clean.columns:
            if pd.api.types.is_datetime64_any_dtype(clean[col]):
                clean[col] = pd.to_datetime(clean[col], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        clean = clean.astype(object)
        clean = clean.where(pd.notna(clean), None)
        return clean

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def initialize(self, schema_path: Path) -> None:
        with self.connect() as conn:
            conn.executescript(schema_path.read_text(encoding='utf-8'))
            conn.commit()

    def write_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = 'append') -> None:
        if df.empty:
            return
        clean = self._sanitize_dataframe(df)
        with self.connect() as conn:
            clean.to_sql(table_name, conn, if_exists=if_exists, index=False)

    def upsert_prices_daily(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        query = '''
        INSERT OR REPLACE INTO prices_daily
        (symbol, date, open, high, low, close, volume, value, source, adjusted_flag)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        clean = self._sanitize_dataframe(df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'value', 'source', 'adjusted_flag']])
        rows: Iterable[tuple] = clean.itertuples(index=False, name=None)
        with self.connect() as conn:
            conn.executemany(query, rows)
            conn.commit()

    def upsert_index_daily(self, df: pd.DataFrame) -> None:
        if df.empty:
            return
        query = '''
        INSERT OR REPLACE INTO index_daily
        (index_symbol, date, open, high, low, close, volume, value, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        clean = self._sanitize_dataframe(df[['index_symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'value', 'source']])
        rows: Iterable[tuple] = clean.itertuples(index=False, name=None)
        with self.connect() as conn:
            conn.executemany(query, rows)
            conn.commit()

    def read_sql(self, query: str) -> pd.DataFrame:
        with self.connect() as conn:
            return pd.read_sql_query(query, conn)
