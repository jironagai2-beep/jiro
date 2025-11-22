"""
7通貨ペア監視システム - リアルタイムダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.insert(0, '/home/user/jiro/src')

from data_loader import DataLoader
from backtest_engine import BacktestEngine
from trading_system import TradingConfig

# ページ設定
st.set_page_config(
    page_title="7通貨ペア監視システム",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .main {background-color: #0e1117;}
    .stMetric {background-color: #1e2130; padding: 15px; border-radius: 5px;}
    h1 {color: #4da6ff;}
    .status-connected {color: #00ff00; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# タイトル
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📊 7通貨ペア監視システム")
with col2:
    st.markdown('<p class="status-connected">🟢 Server: Connected</p>', unsafe_allow_html=True)

# 通貨ペア定義（デモデータ）
pairs = [
    {"name": "BTC/USD", "price": 84186.040, "signals": 0, "winrate": 0},
    {"name": "USD/JPY", "price": 150.433, "signals": 0, "winrate": 0},
    {"name": "EUR/USD", "price": 1.498, "signals": 0, "winrate": 0},
    {"name": "GBP/JPY", "price": 150.229, "signals": 0, "winrate": 0},
    {"name": "AUD/USD", "price": 1.499, "signals": 0, "winrate": 0},
    {"name": "AUD/JPY", "price": 150.389, "signals": 0, "winrate": 0},
    {"name": "EUR/JPY", "price": 150.411, "signals": 0, "winrate": 0},
]

# 通貨ペア一覧（左側）
st.subheader("通貨ペア一覧")

# 2列レイアウト
col_left, col_right = st.columns([1, 2])

with col_left:
    # 各通貨ペアのカード表示（4列2行）
    cols = st.columns(2)

    for idx, pair in enumerate(pairs):
        col = cols[idx % 2]

        with col:
            with st.container():
                st.markdown(f"### {pair['name']}")
                st.metric(
                    label="現在価格",
                    value=f"{pair['price']:.3f}" if pair['price'] > 100 else f"{pair['price']:.4f}",
                    delta=None
                )

                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    st.metric("運勝数", pair['signals'])
                with subcol2:
                    st.metric("勝率", f"{pair['winrate']}%")

                if st.button(f"詳細", key=f"detail_{idx}"):
                    st.session_state.selected_pair = pair['name']

# チャート表示（右側）
with col_right:
    st.subheader("📈 チャート (USD/JPY)")

    try:
        # 実データを読み込み
        loader = DataLoader()
        df = loader.load_ohlcv('USDJPY_1m.csv')

        # バックテスト実行
        config = TradingConfig()
        engine = BacktestEngine(config)
        result = engine.run(df)

        # ローソク足チャート作成
        fig = go.Figure()

        # ローソク足
        fig.add_trace(go.Candlestick(
            x=result.index,
            open=result['open'],
            high=result['high'],
            low=result['low'],
            close=result['close'],
            name='Price'
        ))

        # MA
        fig.add_trace(go.Scatter(
            x=result.index,
            y=result['ma_fast'],
            name='MA Fast',
            line=dict(color='yellow', width=1)
        ))

        fig.add_trace(go.Scatter(
            x=result.index,
            y=result['ma_mid'],
            name='MA Mid',
            line=dict(color='orange', width=1)
        ))

        fig.add_trace(go.Scatter(
            x=result.index,
            y=result['ma_slow'],
            name='MA Slow',
            line=dict(color='red', width=1)
        ))

        # レイアウト
        fig.update_layout(
            height=500,
            xaxis_title="時刻",
            yaxis_title="価格",
            template="plotly_dark",
            showlegend=True,
            legend=dict(x=0.01, y=0.99),
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # 統計情報
        st.markdown("---")
        stat_cols = st.columns(4)

        with stat_cols[0]:
            st.metric("データ行数", len(result))
        with stat_cols[1]:
            st.metric("Buy シグナル", result['final_buy_signal'].sum())
        with stat_cols[2]:
            st.metric("Sell シグナル", result['final_sell_signal'].sum())
        with stat_cols[3]:
            price_range = result['close'].max() - result['close'].min()
            st.metric("価格変動", f"{price_range:.3f}")

    except Exception as e:
        st.error(f"データ読み込みエラー: {str(e)}")
        st.info("デモチャートを表示中")

# フッター
st.markdown("---")
st.caption(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
