import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 導入您之前寫的類 (假設保存為 wave_fib.py)
# from wave_fib import 波浪斐波那契分析器

st.set_page_config(page_title="股票波浪斐波那契分析", layout="wide")
st.title("📈 智能股票技術分析系統 (Streamlit版)")

# 側邊欄輸入
st.sidebar.header("參數設定")
ticker = st.sidebar.text_input("股票代碼 (例如: 09988.HK, AAPL)", "09988.HK")

# 新增：时间周期选择
timeframe = st.sidebar.selectbox(
    "K線級別",
    ["日線 (1d)", "周線 (1wk)", "月線 (1mo)", "小时线 (1h)"],
    index=0
)

period = st.sidebar.selectbox("歷史數據範圍", ["1y", "2y", "5y"], index=1)

interval_map = {
    "日線 (1d)": "1d",
    "周線 (1wk)": "1wk",
    "月線 (1mo)": "1mo",
    "小时线 (1h)": "1h"
}

# 獲取數據按鈕
if st.sidebar.button("開始分析"):
    with st.spinner(f'正在下載 {timeframe} 數據並計算...'):
        try:
            # 1. 下載數據
            interval = interval_map[timeframe]
            df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
            
            if df.empty:
                st.error("❌ 無法獲取數據，請檢查股票代碼是否正確。")
                st.stop()
            
            # 重置索引
            df = df.reset_index()
            
            # 處理列名 - 支援 MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip().lower() for col in df.columns]
            else:
                df.columns = [col.lower() if isinstance(col, str) else str(col).lower() for col in df.columns]
            
            # 刪除不需要的列
            if 'adj_close' in df.columns:
                df.drop(columns=['adj_close'], inplace=True)
            
            # 檢查是否有 'close' 列
            if 'close' not in df.columns:
                st.error(f"❌ 找不到 'close' 列！可用列: {list(df.columns)}")
                st.stop()

            # 2. 計算斐波那契回撤位
            high_price = df['high'].max()
            low_price = df['low'].min()
            current_price = df['close'].iloc[-1]
            
            fib_levels = {
                '0%': low_price,
                '23.6%': low_price + (high_price - low_price) * 0.236,
                '38.2%': low_price + (high_price - low_price) * 0.382,
                '50%': low_price + (high_price - low_price) * 0.5,
                '61.8%': low_price + (high_price - low_price) * 0.618,
                '78.6%': low_price + (high_price - low_price) * 0.786,
                '100%': high_price
            }
            
            # 計算進出場位
            support_level = fib_levels['38.2%']
            resistance_level = fib_levels['61.8%']
            stop_loss = current_price * 0.95
            take_profit_1 = current_price * 1.05
            take_profit_2 = current_price * 1.10

            # 3. 顯示結果
            st.success(f"✅ {ticker} ({timeframe}) 分析完成！")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("現價", f"{current_price:.2f}")
            col2.metric("期間最高", f"{high_price:.2f}")
            col3.metric("期間最低", f"{low_price:.2f}")
            col4.metric("K線數量", f"{len(df)}")

            # 4. 顯示圖表
            st.subheader(f"📊 {timeframe}技術走勢與斐波那契區間")
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 繪製價格線
            ax.plot(df['date'], df['close'], label='收盤價', linewidth=2, color='#1f77b4')
            
            # 繪製斐波那契回撤位
            for level, price in fib_levels.items():
                ax.axhline(y=price, linestyle='--', alpha=0.5, label=f'{level}: {price:.2f}')
            
            ax.set_xlabel('日期')
            ax.set_ylabel('價格')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
            # 5. 進出場價位參考
            st.subheader("🎯 進出場價位參考")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("📥 **進場建議**")
                st.write(f"- 斐波那契 38.2%: {fib_levels['38.2%']:.2f}")
                st.write(f"- 斐波那契 50%: {fib_levels['50%']:.2f}")
                st.write(f"- 斐波那契 61.8%: {fib_levels['61.8%']:.2f}")
                st.write(f"- 近期支撐: {low_price:.2f}")
            
            with col2:
                st.success("📤 **出場建議**")
                st.write(f"- 斐波那契 78.6%: {fib_levels['78.6%']:.2f}")
                st.write(f"- 近期阻力: {high_price:.2f}")
                st.write(f"- 止損位: {stop_loss:.2f} (-5%)")
                st.write(f"- 目標價1: {take_profit_1:.2f} (+5%)")
                st.write(f"- 目標價2: {take_profit_2:.2f} (+10%)")
            
            # 6. 顯示詳細數據表格
            st.subheader("📋 最近10根K線數據")
            st.dataframe(df.tail(10), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ 發生錯誤: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
else:
    st.info("👈 請在左側輸入股票代碼並點擊「開始分析」")
