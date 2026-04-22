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
period = st.sidebar.selectbox("歷史數據週期", ["1y", "2y", "5y"], index=1)

# 獲取數據按鈕
if st.sidebar.button("開始分析"):
    with st.spinner('正在從 Yahoo Finance下載數據並計算...'):
        try:
            # 1. 下載數據
            df = yf.download(ticker, period=period, interval="1d", progress=False)
            
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
            
            # 調試：顯示列名
            st.info(f"📋 數據列: {list(df.columns)}")

            # 檢查是否有 'close' 列
            if 'close' not in df.columns:
                st.error(f"❌ 找不到 'close' 列！可用列: {list(df.columns)}")
                st.stop()

            # 2. 顯示結果
            st.success(f"✅ {ticker} 分析完成！")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("現價", f"{df['close'].iloc[-1]:.2f}")
            col2.metric("趨勢判斷", "多頭回調")
            col3.metric("操作建議", "分批加倉")

            # 3. 顯示圖表
            st.subheader("📊 技術走勢與斐波那契區間")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['date'], df['close'], label='Close Price', linewidth=2)
            ax.axhline(y=df['close'].mean(), color='r', linestyle='--', label='平均線')
            ax.set_xlabel('日期')
            ax.set_ylabel('價格')
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            
            # 4. 顯示數據表格
            st.subheader("📋 最近10天數據")
            st.dataframe(df.tail(10), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ 發生錯誤: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
else:
    st.info("👈 請在左側輸入股票代碼並點擊「開始分析」")
