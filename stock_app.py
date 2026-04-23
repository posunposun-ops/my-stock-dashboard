import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. 網頁設定
st.set_page_config(page_title="柏昇即時看板", layout="wide")

# 設定自動刷新：10 秒一次 (非常安全，絕對不會爆)
st_autorefresh(interval=10000, key="stock_refresh")

# CSS 樣式：維持你要求的大字體
st.markdown("""
    <style>
    .stock-card {
        padding: 20px 10px; border-radius: 15px; margin-bottom: 15px; text-align: center;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.1); height: 160px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 3px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 3px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 3px solid #D0D0D0; }
    .stock-name { font-size: 24px; color: #333; font-weight: 800; margin-bottom: 5px; }
    .price { font-size: 44px; font-weight: 900; line-height: 1.1; margin: 5px 0; }
    .delta { font-size: 18px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 柏昇即時持股監控 (穩定大字版)")

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔指定股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 執行「超級批次」抓取 (15 檔只花 1 個 API 額度)
try:
    # 將所有代號串起來
    sym_list = list(my_portfolio.keys())
    results = client.stock.intraday.tickers(symbols=sym_list)
    
    # 建立數據搜尋字典
    data_map = {}
    if isinstance(results, list):
        for item in results:
            if 'symbol' in item:
                data_map[item['symbol']] = item

    # 5. 顯示網格 (一排 5 支)
    for i in range(0, len(sym_list), 5):
        cols = st.columns(5)
        for j, sid in enumerate(sym_list[i:i+5]):
            with cols[j]:
                name = my_portfolio[sid]
                if sid in data_map:
                    s = data_map[sid]
                    price = s.get('lastPrice') or 0
                    change = s.get('change', 0)
                    pct = s.get('changePercent', 0)
                    
                    color_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""
                    
                    st.markdown(f"""
                        <div class="stock-card {color_class}">
                            <div class="stock-name">{name}</div>
                            <div class="price">{price:.1f}</div>
                            <div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>
                            <div style="font-size:12px; color:gray;">{sid}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # 如果抓不到資料，顯示具體的代號方便 debug
                    st.error(f"{sid} 無資料")

except Exception as e:
    st.error(f"📡 API 連線失敗，請檢查密鑰或網路。錯誤碼: {e}")

st.divider()
st.caption(f"🔄 10 秒自動更新 | API 消耗：極低 (每分鐘 6 次) | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
