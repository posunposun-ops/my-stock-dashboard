import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")

# 設定自動刷新：20 秒一次 (安全且穩定)
st_autorefresh(interval=20000, key="stock_refresh")

# CSS 樣式：大字體 + 走勢圖排版
st.markdown("""
    <style>
    .stock-container {
        border-radius: 15px; padding: 15px; margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); height: 200px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 3px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 3px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 2px solid #D0D0D0; }
    
    .stock-name { font-size: 24px; font-weight: 800; margin-bottom: 0px; }
    .price { font-size: 48px; font-weight: 900; line-height: 1; margin: 5px 0; }
    .delta { font-size: 18px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 柏昇即時看板：富果價格 + Yahoo 走勢")

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔指定股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 判斷上市或上櫃 (yfinance 專用)
def get_yf_symbol(sid):
    # 簡單判斷：常用的上櫃代號 (3491, 6789 等)，若不確定可預設為 .TW
    otc_list = ["3491", "6789", "3189", "3324"]
    return f"{sid}.TWO" if sid in otc_list else f"{sid}.TW"

# 4. 批次抓取 Yahoo 走勢圖數據 (一次抓全部，效率最高)
yf_symbols = [get_yf_symbol(sid) for sid in my_portfolio.keys()]
try:
    # 抓取今天 (1d) 每 2 分鐘 (2m) 的數據
    yf_data = yf.download(yf_symbols, period="1d", interval="2m", group_by='ticker', progress=False)
except:
    yf_data = pd.DataFrame()

# 5. 顯示網格 (一排 3 支)
symbols = list(my_portfolio.keys())
for i in range(0, len(symbols), 3):
    cols = st.columns(3)
    for j, sid in enumerate(symbols[i:i+3]):
        with cols[j]:
            name = my_portfolio[sid]
            yf_sid = get_yf_symbol(sid)
            try:
                # 抓取富果即時報價 (保證價格最快)
                q = client.stock.intraday.quote(symbol=sid)
                
                if q and 'lastPrice' in q:
                    price = q['lastPrice']
                    change = q['change']
                    pct = q['changePercent']
                    color_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""

                    # 準備 Yahoo 走勢數據
                    try:
                        chart_data = yf_data[yf_sid]['Close'].dropna()
                    except:
                        chart_data = pd.Series()

                    # 佈局：左邊文字，右邊圖
                    st.markdown(f'<div class="stock-container {color_class}">', unsafe_allow_html=True)
                    t_col, g_col = st.columns([1, 1.2])
                    
                    with t_col:
                        st.markdown(f'<div class="stock-name">{name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="price">{price:.1f}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>', unsafe_allow_html=True)
                    
                    with g_col:
                        if not chart_data.empty:
                            # 繪製極簡走勢圖
                            st.line_chart(chart_data, height=120, use_container_width=True)
                        else:
                            st.caption("走勢加載中...")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error(f"{sid} 無報價資料")
            except:
                st.error(f"{sid} 連線中...")

st.divider()
st.caption(f"數據來源：富果 (價格) & Yahoo (走勢) | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
