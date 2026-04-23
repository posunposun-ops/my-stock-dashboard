import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="柏昇即時全彩看板", layout="wide")

# 1. 自動刷新設定 (2秒一次)
st_autorefresh(interval=2000, key="stock_refresh")

# CSS 設定保持不變...
st.markdown("""
    <style>
    .stock-card { padding: 20px; border-radius: 10px; margin-bottom: 10px; text-align: center; border: 1px solid #f0f2f6; }
    .up { color: #FF0000; background-color: #FFF5F5; }
    .down { color: #008000; background-color: #F5FFF5; }
    .stable { color: #31333F; background-color: #F0F2F6; }
    .price { font-size: 32px; font-weight: bold; margin: 5px 0; }
    .delta { font-size: 18px; font-weight: 500; }
    .stock-name { font-size: 16px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔持股清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

st.title("🚀 即時持股全彩看板 (批次抓取版)")

# 4. 執行批次抓取 (關鍵：一次把所有代號傳過去)
try:
    symbols_str = ",".join(my_portfolio.keys())
    # 使用 tickers 指令一次抓全部
    results = client.stock.intraday.tickers(symbols=symbols_str)
    
    # 將結果轉換為方便查詢的字典
    data_dict = {item['symbol']: item for item in results}

    # 5. 顯示網格
    cols_per_row = 5
    stock_ids = list(my_portfolio.keys())
    for i in range(0, len(stock_ids), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, sid in enumerate(stock_ids[i:i+cols_per_row]):
            with cols[j]:
                stock_data = data_dict.get(sid)
                if stock_data:
                    name = my_portfolio[sid]
                    price = stock_data['lastPrice']
                    change = stock_data['change']
                    pct = stock_data['changePercent']
                    
                    # 判斷顏色
                    color_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""
                    
                    st.markdown(f"""
                        <div class="stock-card {color_class}">
                            <div class="stock-name">{sid} {name}</div>
                            <div class="price">{price:.2f}</div>
                            <div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write(f"{sid} 讀取中...")

except Exception as e:
    st.error(f"連線異常: {e}")

st.caption(f"數據刷新：每 2 秒 | API 消耗：每分鐘 30/60 次 (安全)")
