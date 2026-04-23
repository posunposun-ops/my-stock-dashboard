import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇即時看板", layout="wide")

# --- 自動刷新設定：10000 毫秒 = 10 秒 ---
st_autorefresh(interval=10000, key="stock_refresh")

# CSS 樣式：美化全彩卡片
st.markdown("""
    <style>
    .stock-card {
        padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1); height: 130px;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 2px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 2px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 2px solid #D0D0D0; }
    .price { font-size: 28px; font-weight: bold; margin: 2px 0; }
    .delta { font-size: 16px; font-weight: bold; }
    .stock-name { font-size: 15px; color: #333; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 柏昇即時持股看板 (10秒更新版)")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 請在 Streamlit Cloud 的 Secrets 填入正確的 FUGLE_KEY")
    st.stop()

# 3. 指定的 15 檔股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 執行批次抓取邏輯
try:
    symbols_list = list(my_portfolio.keys())
    # 嘗試抓取批次資料
    results = client.stock.intraday.tickers(symbols=symbols_list)
    
    # 資料轉換為字典方便顯示
    data_dict = {}
    if isinstance(results, list):
        for item in results:
            if 'symbol' in item:
                data_dict[item['symbol']] = item
    
    # 5. 顯示 15 檔網格 (一排 5 支，共 3 排)
    for i in range(0, len(symbols_list), 5):
        cols = st.columns(5)
        for j, sid in enumerate(symbols_list[i:i+5]):
            with cols[j]:
                name = my_portfolio[sid]
                if sid in data_dict:
                    s = data_dict[sid]
                    # 有些標的可能還沒成交，給予預設值 0
                    price = s.get('lastPrice') or s.get('closePrice') or 0
                    change = s.get('change', 0)
                    pct = s.get('changePercent', 0)
                    
                    # 顏色判斷：紅漲綠跌
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
                    # 備用顯示
                    st.markdown(f"""<div class="stock-card stable"><div class="stock-name">{sid} {name}</div><br>連線中...</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"📡 抓取異常：{e}")

st.divider()
st.caption(f"🔄 每 10 秒自動刷新一次 | 目前時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
