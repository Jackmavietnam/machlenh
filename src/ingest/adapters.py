from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
import pandas as pd


@dataclass
class DataFetchResult:
    symbol: str
    df: pd.DataFrame
    source: str
    error: Optional[str] = None


class BaseMarketDataAdapter:
    source_name = 'base'

    def fetch_stock_daily(self, symbol: str, start: str, end: str) -> DataFetchResult:
        raise NotImplementedError

    def fetch_index_daily(self, index_symbol: str, start: str, end: str) -> DataFetchResult:
        raise NotImplementedError


class VnstockAdapter(BaseMarketDataAdapter):
    source_name = 'vnstock'

    def __init__(self) -> None:
        try:
            from vnstock import Vnstock  # type: ignore
            self._Vnstock = Vnstock
        except Exception as exc:  # pragma: no cover
            self._Vnstock = None
            self._import_error = str(exc)

    def _normalize(self, raw: pd.DataFrame, symbol: str) -> pd.DataFrame:
        rename_map = {
            'time': 'date',
            'date': 'date',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'value': 'value',
        }
        df = raw.rename(columns=rename_map).copy()
        needed = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in needed:
            if col not in df.columns:
                df[col] = pd.NA
        if 'value' not in df.columns:
            df['value'] = pd.NA
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'value']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['symbol'] = symbol
        df['source'] = self.source_name
        df['adjusted_flag'] = 0
        return df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'value', 'source', 'adjusted_flag']]

    def fetch_stock_daily(self, symbol: str, start: str, end: str) -> DataFetchResult:
        if self._Vnstock is None:
            return DataFetchResult(symbol=symbol, df=pd.DataFrame(), source=self.source_name, error=getattr(self, '_import_error', 'vnstock import failed'))
        try:
            stock = self._Vnstock().stock(symbol=symbol, source='VCI')
            raw = stock.quote.history(start=start, end=end, interval='1D')
            df = self._normalize(raw, symbol=symbol)
            return DataFetchResult(symbol=symbol, df=df, source=self.source_name)
        except Exception as exc:
            return DataFetchResult(symbol=symbol, df=pd.DataFrame(), source=self.source_name, error=str(exc))

    def fetch_index_daily(self, index_symbol: str, start: str, end: str) -> DataFetchResult:
        # fallback: index handled through same method if data provider supports it.
        return self.fetch_stock_daily(index_symbol, start, end)
