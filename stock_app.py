import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd

# 1. 網頁設定
st.set_page_config(page_title="即時持股監控", layout="wide")

# 自定義 CSS 讓介面更精美
st.markdown("""
    <style>
    .stock-card {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        border: 1px solid #f0f2f6;
    }
    .up { color: #FF0000; background-color: #FFF5F5; }
    .down { color: #008000; background-color: #F5FFF5; }
    .stable { color: #31333F; background-color: #F0F2F6; }
    .price { font-size: 32px; font-weight: bold; margin: 5px 0; }
    .delta { font-size: 18px; font-weight: 500; }
    .stock-name { font-size: 16px; color: #555; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 即時持股全彩看板")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except Exception:
    st.error("🔑 請先在 Streamlit Secrets 設定 FUGLE_KEY")
    st.stop()

# 3. 指定的 15 檔股票清單
my_portfolio = {
    "2330": "台積電",
    "2317": "鴻海",
    "3711": "日月光",
    "2449": "京元電",
    "1711": "永光",
    "2337": "旺宏",
    "2454": "聯發科",
    "6285": "啟碁",
    "6789": "采鈺",
    "3324": "雙鴻",
    "3491": "昇達科",
    "3037": "欣興",
    "3189": "景碩",
    "8033": "雷虎",
    "2344": "華邦電"
}

# 4. 側邊欄與更新功能
if st.sidebar.button("🔄 立即刷新行情"):
    st.rerun()

# 5. 定義彩色卡片函數
def render_stock_card(sid, name, price, change, pct):
    if change > 0:
        color_class = "up"
        sign = "+"
    elif change < 0:
        color_class = "down"
        sign = ""
    else:
        color_class = "stable"
        sign = ""
    
    html_content = f"""
    <div class="stock-card {color_class}">
        <div class="stock-name">{sid} {name}</div>
        <div class="price">{price:.2f}</div>
        <div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

# 6. 建立網格 (一排顯示 5 支，畫面最平衡)
cols_per_row = 5
stock_ids = list(my_portfolio.keys())
rows = (len(stock_ids) + cols_per_row - 1) // cols_per_row

for r in range(rows):
    cols = st.columns(cols_per_row)
    for c in range(cols_per_row):
        index = r * cols_per_row + c
        if index < len(stock_ids):
            sid = stock_ids[index]
            sname = my_portfolio[sid]
            
            with cols[c]:
                try:
                    quote = client.stock.intraday.quote(symbol=sid)
                    if quote and 'lastPrice' in quote:
                        render_stock_card(
                            sid, sname, 
                            quote['lastPrice'], 
                            quote['change'], 
                            quote['changePercent']
                        )
                    else:
                        st.info(f"{sid} {sname}\n讀取中...")
                except:
                    st.error(f"{sid} 連結中斷")

st.divider()
st.caption(f"最後更新：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')} | 台灣股市紅漲綠跌標準設定")
