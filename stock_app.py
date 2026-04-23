import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import altair as alt

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")

# 設定自動刷新：20 秒一次 (穩定不卡頓)
st_autorefresh(interval=20000, key="stock_refresh")

# --- CSS 樣式：大字體與卡片設計 ---
st.markdown("""
    <style>
    .stock-card {
        border-radius: 15px; padding: 15px; margin-bottom: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); height: 180px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .up { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    
    .name-text { font-size: 24px; font-weight: 800; margin-bottom: 0px; display: block; }
    .price-text { font-size: 50px; font-weight: 900; line-height: 1; margin: 5px 0; display: block; }
    .delta-text { font-size: 18px; font-weight: 700; display: block; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 柏昇即時看板：左右佈局走勢版")

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔指定股票清單
my_portfolio = [
    {"sid": "2330", "yf_id": "2330.TW", "name": "台積電"},
    {"sid": "2317", "yf_id": "2317.TW", "name": "鴻海"},
    {"sid": "3711", "yf_id": "3711.TW", "name": "日月光投控"},
    {"sid": "2449", "yf_id": "2449.TW", "name": "京元電"},
    {"sid": "1711", "yf_id": "1711.TW", "name": "永光"},
    {"sid": "2337", "yf_id": "2337.TW", "name": "旺宏"},
    {"sid": "2454", "yf_id": "2454.TW", "name": "聯發科"},
    {"sid": "6285", "yf_id": "6285.TW", "name": "啟碁"},
    {"sid": "6789", "yf_id": "6789.TW", "name": "采鈺"},
    {"sid": "3324", "yf_id": "3324.TWO", "name": "雙鴻"},
    {"sid": "3491", "yf_id": "3491.TWO", "name": "昇達科"},
    {"sid": "3037", "yf_id": "3037.TW", "name": "欣興"},
    {"sid": "3189", "yf_id": "3189.TW", "name": "景碩"},
    {"sid": "8033", "yf_id": "8033.TWO", "name": "雷虎"},
    {"sid": "2344", "yf_id": "2344.TW", "name": "華邦電"}
]

# 4. 顯示網格 (一排 2 支在手機看最大，若在電腦看可改為 3)
cols_per_row = 3
for i in range(0, len(my_portfolio), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, stock in enumerate(my_portfolio[i:i+cols_per_row]):
        with cols[j]:
            sid = stock["sid"]
            yf_id = stock["yf_id"]
            name = stock["name"]
            try:
                # 抓取報價與走勢
                q = client.stock.intraday.quote(symbol=sid)
                df_yf = yf.download(yf_id, period="1d", interval="2m", progress=False)

                if q and 'lastPrice' in q:
                    price = q['lastPrice']
                    change = q['change']
                    pct = q['changePercent']
                    l_up = q.get('priceHighLimit', price * 1.1)
                    l_down = q.get('priceLowLimit', price * 0.9)
                    
                    box_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""

                    # --- 重點佈局：卡片內部左右分欄 ---
                    st.markdown(f'<div class="stock-card {box_class}">', unsafe_allow_html=True)
                    left, right = st.columns([1, 1.2])
                    
                    with left:
                        st.markdown(f'<span class="name-text">{name}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="price-text">{price:.1f}</span>', unsafe_allow_html=True)
                        st.markdown(f'<span class="delta-text">{sign}{change:.2f} ({sign}{pct:.2f}%)</span>', unsafe_allow_html=True)
                        st.caption(f"代碼: {sid}")

                    with right:
                        if not df_yf.empty:
                            chart_data = df_yf['Close'].dropna().reset_index()
                            chart_data.columns = ['Time', 'Price']
                            c = alt.Chart(chart_data).mark_line(color='blue', strokeWidth=2).encode(
                                x=alt.X('Time:T', axis=None),
                                y=alt.Y('Price:Q', scale=alt.Scale(domain=[l_down, l_up]), axis=None)
                            ).properties(height=120)
                            st.altair_chart(c, use_container_width=True)
                        else:
                            st.caption("走勢連線中...")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            except:
                st.error(f"{sid} 讀取失敗")

st.divider()
st.caption(f"🔄 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')} | Y軸：漲跌停自動鎖定")
