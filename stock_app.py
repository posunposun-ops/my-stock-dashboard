import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import time

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇即時看板", layout="wide")

# 設定自動刷新：15000 毫秒 = 15 秒 (為了維持每分鐘 60 次 API 限制)
st_autorefresh(interval=15000, key="stock_refresh")

st.markdown("""
    <style>
    .stock-card {
        padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1); height: 130px;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 2px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 2px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 2px solid #D0D0D0; }
    .price { font-size: 26px; font-weight: bold; margin: 2px 0; }
    .delta { font-size: 14px; font-weight: bold; }
    .stock-name { font-size: 15px; color: #333; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 柏昇即時持股看板 (穩定更新版)")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 請在 Secrets 填入 FUGLE_KEY")
    st.stop()

# 3. 15 檔股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 顯示網格
symbols_list = list(my_portfolio.keys())
cols_per_row = 5

for i in range(0, len(symbols_list), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, sid in enumerate(symbols_list[i:i+cols_per_row]):
        with cols[j]:
            name = my_portfolio[sid]
            try:
                # 改用最穩定的單一抓取指令
                s = client.stock.intraday.quote(symbol=sid)
                
                if s and 'lastPrice' in s:
                    price = s.get('lastPrice', 0)
                    change = s.get('change', 0)
                    pct = s.get('changePercent', 0)
                    
                    if change > 0:
                        color_class, sign = "up", "+"
                    elif change < 0:
                        color_class, sign = "down", ""
                    else:
                        color_class, sign = "stable", ""
                    
                    st.markdown(f"""
                        <div class="stock-card {color_class}">
                            <div class="stock-name">{sid} {name}</div>
                            <div class="price">{price:.2f}</div>
                            <div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="stock-card stable"><div class="stock-name">{sid} {name}</div><br>未成交</div>""", unsafe_allow_html=True)
            except Exception as e:
                # 如果單次失敗，顯示錯誤原因（方便除錯）
                st.markdown(f"""<div class="stock-card stable"><div class="stock-name">{sid} {name}</div><br>API異常</div>""", unsafe_allow_html=True)

st.divider()
st.caption(f"🔄 每 15 秒同步一次 (API 限制守護中) | 目前時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
