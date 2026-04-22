import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 導入您之前寫的類 (假設保存為 wave_fib.py)
# from wave_fib import 波浪斐波那契分析器

st.set_page_config(page_title="股票波浪斐波那契分析", layout="wide")
st.title("📈 智能股票技術分析系統 (Streamlit版)")

# 側邊欄設定
st.sidebar.header("參數設定")
ticker = st.sidebar.text_input("股票代碼 (例如: 09988.HK, AAPL)", "AAPL")

timeframe = st.sidebar.selectbox(
    "分析週期 (K線級別)",
    ["日線 (1d)", "周線 (1wk)", "月線 (1mo)", "小時線 (1h)"],
    index=0
)
period = st.sidebar.selectbox("歷史數據範圍", ["1y", "2y", "5y"], index=1)

interval_map = {
    "日線 (1d)": "1d", "周線 (1wk)": "1wk",
    "月線 (1mo)": "1mo", "小時線 (1h)": "1h"
}

# 主邏輯
if st.sidebar.button("開始分析"):
    with st.spinner(f'正在下載 {timeframe} 數據並計算...'):
        try:
            # 1. 下載數據 (auto_adjust=True 可避免 MultiIndex 欄位問題)
            interval = interval_map[timeframe]
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            
            if df.empty:
                st.error("❌ 無法獲取數據，請檢查股票代碼或 Yahoo Finance 連線。")
                st.stop()

            df = df.reset_index()
            # 安全轉換欄名為小寫
            df.columns = [col.lower() if isinstance(col, str) else "_".join(map(str, col)).lower() for col in df.columns]
            
            if 'close' not in df.columns:
                st.error(f"❌ 找不到 'close' 欄位。可用欄位: {list(df.columns)}")
                st.stop()

            # 2. 計算斐波那契回撤位
            high_price = df['high'].max()
            low_price = df['low'].min()
            current_price = df['close'].iloc[-1]
            fib_levels = {f"{p}%": low_price + (high_price - low_price) * p / 100 for p in [0, 23.6, 38.2, 50, 61.8, 78.6, 100]}

            # 3. 顯示狀態與指標
            st.success(f"✅ {ticker} ({timeframe}) 分析完成！")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("現價", f"{current_price:.2f}")
            col2.metric("期間最高", f"{high_price:.2f}")
            col3.metric("期間最低", f"{low_price:.2f}")
            col4.metric("K線數量", f"{len(df)}")

            # 4. 繪製圖表
            st.subheader("📊 技術走勢與斐波那契回撤區間")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df['date'], df['close'], label='收盤價', linewidth=2, color='#1f77b4')
            for lvl, price in fib_levels.items():
                ax.axhline(y=price, linestyle='--', alpha=0.6, label=f'{lvl}: {price:.2f}')
            ax.set_xlabel('日期')
            ax.set_ylabel('價格')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            # 5. 進出場價位參考
            st.subheader("🎯 進出場價位參考 (基於斐波那契與波動率)")
            c1, c2 = st.columns(2)
            with c1:
                st.info(" **進場 / 支撐參考**")
                st.write(f"• 斐波那契 38.2%: {fib_levels['38.2%']:.2f}")
                st.write(f"• 斐波那契 50.0%: {fib_levels['50%']:.2f}")
                st.write(f"• 斐波那契 61.8%: {fib_levels['61.8%']:.2f}")
                st.write(f"• 近期支撐 (區間低點): {low_price:.2f}")
            with c2:
                st.success("📤 **出場 / 壓力參考**")
                st.write(f"• 斐波那契 78.6%: {fib_levels['78.6%']:.2f}")
                st.write(f"• 近期壓力 (區間高點): {high_price:.2f}")
                st.write(f"• 動態止損位: {current_price * 0.95:.2f} (-5%)")
                st.write(f"• 第一目標價: {current_price * 1.05:.2f} (+5%)")

            # 6. 原始數據表格
            st.subheader(" 最近 10 筆 K 線數據")
            st.dataframe(df.tail(10), use_container_width=True)

        except Exception as e:
            st.error(f"❌ 執行錯誤: {e}")
else:
    st.info("👈 請在左側設定參數並點擊「開始分析」")
