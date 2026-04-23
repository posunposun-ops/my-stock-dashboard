import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd

# --- 1. 網頁設定 ---
st.set_page_config(page_title="柏昇即時看盤", layout="wide")
st.title("⚡ 台股即時報價 (零延遲)")

# --- 2. 安全地讀取 API KEY ---
# 正式部署後要改用 st.secrets，本地測試先直接填入
FUGLE_API_KEY = "這裡貼上你的富果API_KEY"
client = RestClient(api_key=FUGLE_API_KEY)

# --- 3. 側邊欄設定 ---
with st.sidebar:
    st.header("搜尋股票")
    stock_id = st.text_input("輸入台股代號 (不需要加 .TW)", "2330")
    refresh_btn = st.button("🔄 點擊刷新即時報價")

# --- 4. 抓取即時數據 ---
try:
    # 獲取即時行情 (Quote)
    stock = client.stock.intraday.quote(symbol=stock_id)
    
    # 顯示頂部卡片
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("成交價", stock['lastPrice'])
    c2.metric("漲跌", f"{stock['change']}", f"{stock['changePercent']}%")
    c3.metric("成交量", stock['total']['tradeVolume'])
    c4.metric("最高/最低", f"{stock['highPrice']} / {stock['lowPrice']}")

    st.divider()

    # --- 5. 顯示最佳五檔 ---
    st.subheader(f"📊 {stock_id} 最佳五檔報價")
    
    # 取得五檔數據
    bids = stock.get('bids', []) # 買進
    asks = stock.get('asks', []) # 賣出

    col_ask, col_bid = st.columns(2)

    with col_ask:
        st.write("🔴 賣出報價 (Asks)")
        df_asks = pd.DataFrame(asks).sort_values('price', ascending=False)
        st.table(df_asks.rename(columns={'price': '賣價', 'volume': '張數'}))

    with col_bid:
        st.write("🟢 買進報價 (Bids)")
        df_bids = pd.DataFrame(bids).sort_values('price', ascending=False)
        st.table(df_bids.rename(columns={'price': '買價', 'volume': '張數'}))

except Exception as e:
    st.error(f"讀取失敗，請確認代號是否正確或 API Key 是否有效。錯誤訊息: {e}")

st.caption("數據來源：富果即時行情 API (零延遲)")