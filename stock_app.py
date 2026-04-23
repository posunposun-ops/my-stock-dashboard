import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. 網頁設定
st.set_page_config(page_title="柏昇 15 檔全彩看板", layout="wide")

# 設定自動刷新 (10秒一次)
st_autorefresh(interval=10000, key="stock_refresh")

# CSS 設定：讓卡片更美、紅綠對比更明顯
st.markdown("""
    <style>
    .stock-card {
        padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 2px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 2px solid #008000; }
    .stable { color: #31333F; background-color: #F0F2F6; border: 2px solid #D0D0D0; }
    .price { font-size: 28px; font-weight: bold; margin: 2px 0; }
    .delta { font-size: 16px; font-weight: bold; }
    .stock-name { font-size: 14px; color: #333; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍎 柏昇即時持股監控 (15 檔全彩版)")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 請檢查 Streamlit Cloud 的 Secrets 是否正確填入 FUGLE_KEY")
    st.stop()

# 3. 你指定的 15 檔股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 執行批次抓取
try:
    symbols_str = ",".join(my_portfolio.keys())
    # 這裡加入一個檢查，確保抓到的是資料而不是錯誤字串
    results = client.stock.intraday.tickers(symbols=symbols_str)
    
    if isinstance(results, str):
        st.error(f"❌ API 回傳錯誤訊息: {results}。請檢查 API Key 是否正確或過期。")
        st.stop()

    # 5. 顯示網格 (一排 5 支，共三排)
    data_dict = {item['symbol']: item for item in results if 'symbol' in item}
    stock_ids = list(my_portfolio.keys())
    
    for i in range(0, len(stock_ids), 5):
        cols = st.columns(5)
        for j, sid in enumerate(stock_ids[i:i+5]):
            with cols[j]:
                name = my_portfolio[sid]
                # 檢查這支股票有沒有抓到資料
                if sid in data_dict:
                    s = data_dict[sid]
                    price = s.get('lastPrice', 0)
                    change = s.get('change', 0)
                    pct = s.get('changePercent', 0)
                    
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
                    st.markdown(f"""<div class="stock-card stable">{sid} {name}<br>讀取中...</div>""", unsafe_allow_html=True)

except Exception as e:
    st.error(f"📡 連線異常：{e}")
    st.info("提示：如果出現 string indices 錯誤，通常是 API Key 沒填對。")

st.caption(f"數據刷新：每 10 秒 | 狀態：{'🟢 正常' if 'results' in locals() else '🔴 異常'} | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
