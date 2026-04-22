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
            df = yf.download(ticker, period=period, interval="1d")
            if df.empty:
                st.error("無法獲取數據，請檢查代碼是否正確。")
                st.stop()
            
            # 重置索引
            df.reset_index(inplace=True)
            
            # 處理列名 - 支援 MultiIndex 和普通索引
            if isinstance(df.columns, pd.MultiIndex):
                # 展平 MultiIndex
                df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns]
            
            # 統一轉為小寫
            df.columns = [col.lower() if isinstance(col, str) else '_'.join(map(str, col)).lower() if isinstance(col, tuple) else str(col).lower() for col in df.columns]
            
            # 刪除不需要的列
            if 'adj_close' in df.columns:
                df.drop(columns=['adj_close'], inplace=True)

            # 2. 初始化分析器 (這裡需要您將之前的類代碼複製過來或導入)
            # analyzer = 波浪斐波那契分析器(df, 觀察週期=200) 
            # result = analyzer.執行分析()
            
            # --- 模擬結果展示 (實際使用時請替換為真實調用) ---
            st.success(f"✅ {ticker} 分析完成！")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("現價", f"{df['close'].iloc[-1]:.2f}")
            col2.metric("趨勢判斷", "多頭回調")  # 替換為 result['波浪週期']['趨勢']
            col3.metric("操作建議", "分批加倉")  # 替換為 result['最終指示']

            # 3. 顯示圖表
            st.subheader("技術走勢與斐波那契區間")
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['date'], df['close'], label='Close Price')
            ax.axhline(y=df['close'].mean(), color='r', linestyle='--', label='Mean Line')
            ax.legend()
            st.pyplot(fig)
            
            # 4. 顯示詳細數據表格
            st.subheader("進出場價位參考")
            st.dataframe(df.tail(10), use_container_width=True)
            # st.json(result['動態進出場']) # 如果用了真實類
            
        except Exception as e:
            st.error(f"發生錯誤: {str(e)}")
else:
    st.info("👈 請在左側輸入股票代碼並點擊「開始分析」")
