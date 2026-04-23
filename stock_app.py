import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")

# --- 設定自動刷新：30 秒一次 (保護 API 額度) ---
st_autorefresh(interval=30000, key="stock_refresh")

# CSS 樣式：針對大字體與圖表排版
st.markdown("""
    <style>
    .stock-container {
        border-radius: 15px; padding: 15px; margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.08); height: 220px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .up { color: #FF0000; background-color: #FFF0F0; border: 3px solid #FF0000; }
    .down { color: #008000; background-color: #F0FFF0; border: 3px solid #008000; }
    .stable { color: #31333F; background-color: #F8F9FA; border: 3px solid #D0D0D0; }
    
    .stock-name { font-size: 24px; font-weight: 800; margin-bottom: 0px; }
    .price { font-size: 48px; font-weight: 900; line-height: 1; margin: 5px 0; }
    .delta { font-size: 20px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 柏昇持股監控：大字體 + 當日走勢")

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔指定股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 4. 顯示網格 (一排 3 支，給圖表足夠空間)
symbols = list(my_portfolio.keys())
for i in range(0, len(symbols), 3):
    cols = st.columns(3)
    for j, sid in enumerate(symbols[i:i+3]):
        with cols[j]:
            name = my_portfolio[sid]
            try:
                # A. 抓取即時報價
                q = client.stock.intraday.quote(symbol=sid)
                # B. 抓取今日走勢 (1分鐘 K 線)
                c = client.stock.intraday.candles(symbol=sid)
                
                if q and 'lastPrice' in q:
                    price = q['lastPrice']
                    change = q['change']
                    pct = q['changePercent']
                    color_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""

                    # 準備圖表數據
                    df_chart = pd.DataFrame(c)
                    
                    # 建立左右佈局：左邊放文字，右邊放小圖
                    st.markdown(f'<div class="stock-container {color_class}">', unsafe_allow_html=True)
                    t_col, g_col = st.columns([1.2, 1])
                    
                    with t_col:
                        st.markdown(f'<div class="stock-name">{name}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="price">{price:.1f}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="delta">{sign}{change:.2f} ({sign}{pct:.2f}%)</div>', unsafe_allow_html=True)
                        st.caption(f"代號: {sid}")
                    
                    with g_col:
                        if not df_chart.empty:
                            # 顯示極簡線圖
                            st.line_chart(df_chart['close'], height=120, use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.error(f"{sid} {name} 讀取中...")

st.divider()
st.caption(f"🔄 每 30 秒自動更新一次 (保護 API) | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
