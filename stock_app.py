import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd

# --- 1. 網頁設定 ---
st.set_page_config(page_title="柏昇即時看盤", layout="wide")
st.title("⚡ 台股即時報價 (零延遲)")

# --- 2. 安全地讀取 API KEY (這行很重要) ---
# 我們要從 Streamlit Cloud 的 Secrets 抓取你剛才那組 dab7... 的密鑰
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 密鑰錯誤：請確認 Streamlit Cloud 的 Secrets 設定中是否有 FUGLE_KEY")
    st.stop()

# --- 3. 側邊欄設定 ---
with st.sidebar:
    st.header("搜尋股票")
    stock_id = st.text_input("輸入台股代號 (如: 2330)", "2330")
    if st.button("🔄 點擊刷新即時報價"):
        st.rerun()

# --- 4. 抓取即時數據 ---
try:
    # 獲取即時行情
    stock = client.stock.intraday.quote(symbol=stock_id)
    
    # 顯示頂部卡片
    if stock and 'lastPrice' in stock:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("成交價", f"{stock['lastPrice']:.2f}")
        c2.metric("漲跌", f"{stock['change']}", f"{stock['changePercent']}%")
        c3.metric("成交量", f"{stock['total']['tradeVolume']} 張")
        c4.metric("最高/最低", f"{stock['highPrice']} / {stock['lowPrice']}")

        st.divider()

        # --- 5. 顯示最佳五檔 ---
        st.subheader(f"📊 {stock_id} 最佳五檔報價")
        
        bids = stock.get('bids', [])
        asks = stock.get('asks', [])

        col_ask, col_bid = st.columns(2)

        with col_ask:
            st.write("🔴 賣出報價 (Asks)")
            df_asks = pd.DataFrame(asks).sort_values('price', ascending=False)
            st.table(df_asks.rename(columns={'price': '賣價', 'volume': '張數'}))

        with col_bid:
            st.write("🟢 買進報價 (Bids)")
            df_bids = pd.DataFrame(bids).sort_values('price', ascending=False)
            st.table(df_bids.rename(columns={'price': '買價', 'volume': '張數'}))
    else:
        st.warning("目前暫無即時數據，請確認現在是否為開盤時間。")

except Exception as e:
    st.error(f"讀取失敗。錯誤訊息: {e}")

st.caption("數據來源：富果即時行情 API (零延遲)")
