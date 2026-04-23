import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇即時看板", layout="wide")

# 設定自動刷新：15 秒一次 (15 檔股票 x 每分鐘 4 次 = 60 次 API 剛好滿額)
st_autorefresh(interval=15000, key="stock_refresh")

# --- 樣式調整重點：加大字體 ---
st.markdown("""
    <style>
    .stock-card {
        padding: 20px 10px; border-radius: 15px; margin-bottom: 15px; text-align: center;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1); height: 180px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 3px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 3px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 3px solid #D0D0D0; }
    
    /* 股票名稱：大字體 */
    .stock-name { font-size: 22px; color: #333; font-weight: 800; margin-bottom: 5px; }
    
    /* 現價：最大字體 */
    .price { font-size: 42px; font-weight: 900; line-height: 1.1; margin: 5px 0; }
    
    /* 漲跌幅：中字體 */
    .delta { font-size: 18px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 柏昇即時持股看板 (大字體版)")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 Secrets 設定錯誤")
    st.stop()

# 3. 15 檔股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 顯示網格 (維持一排 5 支)
symbols_list = list(my_portfolio.keys())
cols_per_row = 5

for r in range(0, len(symbols_list), cols_per_row):
    cols = st.columns(cols_per_row)
    for c, sid in enumerate(symbols_list[r:r+cols_per_row]):
        with cols[c]:
            name = my_portfolio[sid]
            try:
                # 逐一抓取以確保 100% 成功率
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
                            <div class="stock-name">{name}</div>
                            <div class="price">{price:.2f}</div>
                            <div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>
                            <div style="font-size:12px; color:gray;">{sid}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="stock-card stable"><div class="stock-name">{name}</div><br>未成交</div>""", unsafe_allow_html=True)
            except:
                st.markdown(f"""<div class="stock-card stable"><div class="stock-name">{name}</div><br>連線中</div>""", unsafe_allow_html=True)

st.divider()
st.caption(f"🔄 自動同步中 | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
