import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

st.set_page_config(page_title="股票波浪斐波那契分析", layout="wide")
st.title("📈 智能股票技術分析系統 (Streamlit版)")

# 側邊欄設定
st.sidebar.header("參數設定")
ticker = st.sidebar.text_input("股票代碼 (例如: 09988.HK, AAPL)", "AAPL")
period = st.sidebar.selectbox("歷史數據週期", ["1y", "2y", "5y"], index=1)

if st.sidebar.button("開始分析"):
    with st.spinner('正在下載數據並計算...'):
        try:
            # 1. 下載數據
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
            if df.empty:
                st.error("❌ 無法獲取數據，請檢查股票代碼或網路連線。")
                st.stop()

            df = df.reset_index()

            # 🔧 核心修正：強健的欄位清洗邏輯（解決 close_aapl 問題）
            clean_cols = []
            for col in df.columns:
                # 處理 MultiIndex 或 tuple
                if isinstance(col, tuple):
                    col = col[0]
                col = str(col).lower()
                
                # 移除 yfinance 自動附加的代碼後綴 (例如 _aapl, _09988.hk)
                if col.startswith(('open_', 'high_', 'low_', 'close_', 'volume_', 'date_')):
                    col = col.split('_')[0]
                clean_cols.append(col)
            df.columns = clean_cols

            # 確保日期格式正確
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            if 'close' not in df.columns:
                st.error(f"❌ 找不到 'close' 列！實際欄位: {list(df.columns)}")
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

            # 3. 顯示結果
            st.success(f"✅ {ticker} 分析完成！")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("現價", f"{current_price:.2f}")
            col2.metric("期間最高", f"{high_price:.2f}")
            col3.metric("期間最低", f"{low_price:.2f}")
            col4.metric("K線數量", f"{len(df)}")

            # 4. 繪製圖表
            st.subheader("📊 技術走勢與斐波那契區間")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df['date'], df['close'], label='收盤價', linewidth=2)
            for lvl, price in fib_levels.items():
                ax.axhline(y=price, linestyle='--', alpha=0.5, label=f'{lvl}: {price:.2f}')
            ax.set_xlabel('日期')
            ax.set_ylabel('價格')
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

            # 5. 進出場價位參考（已補齊）
            st.subheader("🎯 進出場價位參考")
            c1, c2 = st.columns(2)
            with c1:
                st.info("📥 **進場支撐參考**\n"
                        f"- 斐波那契 38.2%: {fib_levels['38.2%']:.2f}\n"
                        f"- 斐波那契 50.0%: {fib_levels['50%']:.2f}\n"
                        f"- 斐波那契 61.8%: {fib_levels['61.8%']:.2f}")
            with c2:
                st.success("📤 **出場壓力參考**\n"
                           f"- 斐波那契 78.6%: {fib_levels['78.6%']:.2f}\n"
                           f"- 區間高點: {high_price:.2f}\n"
                           f"- 動態止損 (-5%): {current_price * 0.95:.2f}")

            # 6. 數據表格
            st.subheader("📋 最近 10 筆 K 線數據")
            st.dataframe(df.tail(10), use_container_width=True)

        except Exception as e:
            st.error(f" 執行錯誤: {e}")
else:
    st.info("👈 請在左側輸入股票代碼並點擊「開始分析」")
