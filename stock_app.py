import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd

# 1. 網頁設定：使用寬版模式
st.set_page_config(page_title="我的持股即時儀表板", layout="wide")
st.title("📊 我的持股即時監控")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 請先在 Secrets 設定 FUGLE_KEY")
    st.stop()

# 3. 定義你的持股清單 (你可以隨時在這裡增減，湊滿 10 檔)
my_holdings = [
    "2330", "2317", "3711", "2454", "2308", 
    "0056", "00919", "00878", "00713", "0050"
]

# 4. 建立重新整理按鈕
if st.button("🔄 重新整理所有行情"):
    st.rerun()

st.divider()

# 5. 核心佈局：使用迴圈自動產生網格
# 我們設定一橫排顯示 4 支股票
cols_per_row = 4
rows = (len(my_holdings) + cols_per_row - 1) // cols_per_row

for r in range(rows):
    # 建立該排的欄位
    cols = st.columns(cols_per_row)
    for c in range(cols_per_row):
        index = r * cols_per_row + c
        if index < len(my_holdings):
            stock_id = my_holdings[index]
            with cols[c]:
                try:
                    # 抓取即時行情
                    quote = client.stock.intraday.quote(symbol=stock_id)
                    
                    if quote and 'lastPrice' in quote:
                        # 顯示小型數據卡片
                        # 漲跌判斷顏色
                        change_val = quote['change']
                        st.metric(
                            label=f"{stock_id}",
                            value=f"{quote['lastPrice']:.2f}",
                            delta=f"{change_val} ({quote['changePercent']}%)"
                        )
                    else:
                        st.caption(f"{stock_id} 暫無數據")
                except:
                    st.error(f"{stock_id} 讀取失敗")

st.divider()
st.caption("數據來源：富果即時行情 API | 畫面每排顯示 4 支持股")
