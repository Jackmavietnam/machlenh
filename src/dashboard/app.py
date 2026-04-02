from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st

from src.utils.config import resolve_project_paths

st.set_page_config(page_title='Mạch Lệnh V1.2', layout='wide')
paths = resolve_project_paths('.')
artifacts = paths['artifacts_dir']
reports_dir = paths['report_dir']

st.title('Mạch Lệnh - Dashboard V1.2')
st.caption('Bang xep hang, alert da loc, backtest va bao cao van hanh local')


def safe_read(path: Path) -> pd.DataFrame:
    if path.exists() and path.stat().st_size > 0:
        if path.suffix == '.parquet':
            return pd.read_parquet(path)
        return pd.read_csv(path)
    return pd.DataFrame()

ranking = safe_read(artifacts / 'ranking_latest_label_5d.csv')
alerts = safe_read(artifacts / 'alerts_latest_label_5d.csv')
train = safe_read(artifacts / 'train_report_label_5d.csv')
walk = safe_read(artifacts / 'walkforward_report_label_5d.csv')
features = safe_read(paths['features_dir'] / 'features_daily.parquet')

col1, col2, col3, col4 = st.columns(4)
col1.metric('So ma xep hang', len(ranking))
col2.metric('So alert sau loc', len(alerts))
col3.metric('So model train', len(train))
col4.metric('So window backtest', len(walk))

tab1, tab2, tab3, tab4 = st.tabs(['Bang xep hang', 'Alerts', 'Backtest', 'Du lieu ma'])

with tab1:
    st.subheader('Bang xep hang tong hop')
    if ranking.empty:
        st.warning('Chua co ranking. Hay chay run_daily.py')
    else:
        st.dataframe(ranking, use_container_width=True)
        st.download_button('Tai ranking CSV', ranking.to_csv(index=False).encode('utf-8-sig'), file_name='ranking_latest_label_5d.csv', mime='text/csv')

with tab2:
    st.subheader('Alert sau khi loc')
    if alerts.empty:
        st.warning('Chua co alert.')
    else:
        st.dataframe(alerts, use_container_width=True)
        st.download_button('Tai alerts CSV', alerts.to_csv(index=False).encode('utf-8-sig'), file_name='alerts_latest_label_5d.csv', mime='text/csv')

with tab3:
    st.subheader('Ket qua backtest')
    if walk.empty:
        st.warning('Chua co backtest.')
    else:
        st.dataframe(walk, use_container_width=True)
        if 'precision' in walk.columns:
            st.line_chart(walk.set_index('window_start')['precision'])
        if 'auc' in walk.columns and walk['auc'].notna().any():
            st.line_chart(walk[['auc']])

with tab4:
    st.subheader('Xem du lieu tung ma')
    if features.empty:
        st.warning('Chua co features.')
    else:
        features['date'] = pd.to_datetime(features['date'])
        symbols = sorted(features['symbol'].dropna().unique().tolist())
        symbol = st.selectbox('Chon ma', symbols)
        df = features[features['symbol'] == symbol].sort_values('date').tail(250)
        st.line_chart(df.set_index('date')['close'])
        cols = ['date', 'close', 'rsi_14', 'sma_20_ratio', 'breakout_20', 'drawdown_20', 'rs_vs_vnindex_20']
        show_cols = [c for c in cols if c in df.columns]
        st.dataframe(df[show_cols].tail(30), use_container_width=True)
