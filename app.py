import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# === 設置頁面配置 ===
st.set_page_config(page_title="智能股票波浪分析", layout="wide", page_icon="📈")

# === 核心分析類 (完整內建，無需額外文件) ===
class 波浪斐波那契分析器:
    FIB_LEVELS = {'回撤支撐': [0.236, 0.382, 0.5, 0.618, 0.786], '擴展目標': [1.272, 1.414, 1.618, 2.0]}
    
    def __init__(self, df):
        self.df = df.copy()
        self.ATR值 = None
        self.斐波區間 = {}
        
    def _計算均線(self):
        for name, span in [('MA10',10), ('MA20',20), ('MA50',50), ('EMA120',120)]:
            if 'MA' in name: self.df[name] = self.df['Close'].rolling(span).mean()
            else: self.df[name] = self.df['Close'].ewm(span=span, adjust=False).mean()

    def _計算量價(self):
        df = self.df
        amp = (df['High'] - df['Low']).replace(0, np.nan)
        df['VAR6'] = (np.abs(df['Open'] - df['Close']) / amp) * df['Volume']
        df['VAR7'] = ((df['High'] - np.where(df['Close']>df['Open'], df['Close'], df['Open'])) / amp) * df['Volume']
        df['VAR8'] = ((np.where(df['Close']>df['Open'], df['Open'], df['Close']) - df['Low']) / amp) * df['Volume']
        df['量價信號'] = np.select([(df['VAR6']>=df['VAR7'])&(df['VAR6']>=df['VAR8'])&(df['Close']>df['Open']),
                                    (df['VAR8']>df['VAR6'])&(df['VAR8']>df['VAR7'])], ['加倉', '洗盤'], default='觀望')

    def _計算ATR(self):
        high, low, close = self.df['High'], self.df['Low'], self.df['Close']
        tr = pd.concat([high-low, abs(high-close.shift(1)), abs(low-close.shift(1))], axis=1).max(axis=1)
        self.ATR值 = tr.rolling(14).mean().iloc[-1]

    def _識別波段(self):
        highs = argrelextrema(self.df['High'].values, np.greater, order=8)[0]
        lows = argrelextrema(self.df['Low'].values, np.less, order=8)[0]
        return self.df.iloc[highs]['High'].tail(3), self.df.iloc[lows]['Low'].tail(3)

    def _計算斐波那契(self, start_idx, end_idx, direction):
        s_p, e_p = self.df.iloc[start_idx]['Low'], self.df.iloc[end_idx]['High'] if direction=='up' else (self.df.iloc[start_idx]['High'], self.df.iloc[end_idx]['Low'])
        range_p = abs(e_p - s_p)
        base = e_p if direction=='up' else s_p
        self.斐波區間['回撤'] = {l: base - range_p*l if direction=='up' else base + range_p*l for l in self.FIB_LEVELS['回撤支撐']}
        self.斐波區間['擴展'] = {l: base + range_p*(l-1) if direction=='up' else base - range_p*(l-1) for l in self.FIB_LEVELS['擴展目標']}

    def 執行分析(self):
        self._計算均線()
        self._計算量價()
        self._計算ATR()
        highs, lows = self._識別波段()
        if len(highs)<2 or len(lows)<2: return {'狀態': '數據不足'}
        
        curr_p = self.df['Close'].iloc[-1]
        last_h, prev_h = highs.iloc[-1], highs.iloc[-2]
        last_l, prev_l = lows.iloc[-1], lows.iloc[-2]
        
        is_up = (last_h > prev_h) and (last_l > prev_l)
        if is_up:
            self._計算斐波那契(lows.index[-2], highs.index[-1], 'up')
            state = "延伸浪" if curr_p > last_h else ("強勢回調" if curr_p >= self.斐波區間['回撤'][0.382] else "深度回調")
            action = "持有/減倉" if curr_p > last_h else ("逢低加倉" if curr_p >= self.斐波區間['回撤'][0.382] else "分批建倉")
        else:
            self._計算斐波那契(highs.index[-2], lows.index[-1], 'down')
            state = "延伸下跌" if curr_p < last_l else "弱勢反彈"
            action = "觀望" if curr_p < last_l else "反彈減倉"
            
        return {'現價': curr_p, '趨勢': '多頭' if is_up else '空頭', '週期': state, '操作': action, 'ATR': self.ATR值}

    def 繪圖(self):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(self.df['Date'], self.df['Close'], label='Price', color='black')
        ax.plot(self.df['Date'], self.df['MA20'], label='MA20', linestyle='--', alpha=0.5)
        if self.斐波區間:
            for l, p in self.斐波區間.get('回撤', {}).items():
                ax.axhline(p, color='green', linestyle=':', alpha=0.3)
        ax.legend(loc='upper left')
        return fig

# === Streamlit 界面邏輯 ===
@st.cache_data(ttl=3600)
def get_data(ticker, period):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df.empty: return None
        df.reset_index(inplace=True)
        df.columns = [c.lower() for c in df.columns]
        if 'adj close' in df.columns: df.drop(columns=['adj close'], inplace=True)
        return df
    except: return None

st.title("📈 股票波浪斐波那契分析系統")
with st.sidebar:
    ticker = st.text_input("股票代碼 (例: 09988.HK)", "09988.HK")
    period = st.selectbox("時間範圍", ["1y", "2y"], index=0)
    btn = st.button("開始分析", type="primary")

if btn:
    with st.spinner('雲端計算中...'):
        df = get_data(ticker, period)
        if df is not None:
            analyzer = 波浪斐波那契分析器(df)
            res = analyzer.執行分析()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("現價", f"{res['現價']:.2f}")
            c2.metric("趨勢", res['趨勢'])
            c3.metric("建議", res['操作'])
            
            st.info(f"**詳細狀態:** {res['週期']} | **ATR波動率:** {res['ATR']:.2f}")
            
            tab1, tab2 = st.tabs(["走勢圖", "詳細價位"])
            with tab1:
                st.pyplot(analyzer.繪圖())
            with tab2:
                st.json({"斐波那契回撤": analyzer.斐波區間.get('回撤', {})})
        else:
            st.error("無法獲取數據，請檢查代碼。")
