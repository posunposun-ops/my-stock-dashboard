import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import altair as alt

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")

# 設定自動刷新：20 秒一次 (安全且穩定)
st_autorefresh(interval=20000, key="stock_refresh")

# --- CSS 修正：確保文字與顏色合一，名字大、價格最大 ---
st.markdown("""
    <style>
    .stock-card {
        padding: 20px; border-radius: 15px; margin-bottom: 10px; text-align: left;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .up { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    
    .name-text { font-size: 26px; font-weight: 800; margin-bottom: 0px; display: block; }
    .price-text { font-size: 52px; font-weight: 900; line-height: 1; margin: 10px 0; display: block; }
    .delta-text { font-size: 20px; font-weight: 700; display: block; }
    .id-text { font-size: 14px; color: #666; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 柏昇即時看板：大字全彩走勢版")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except:
    st.error("🔑 請檢查 Secrets 裡的 FUGLE_KEY")
    st.stop()

# 3. 指定的 15 檔指定股票清單與 yfinance 對應代號
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

# 4. 顯示網格 (一排 3 支，共 5 排)
for i in range(0, len(my_portfolio), 3):
    cols = st.columns(3)
    for j, stock_info in enumerate(my_portfolio[i:i+3]):
        with cols[j]:
            sid = stock_info["sid"]
            yf_id = stock_info["yf_id"]
            name = stock_info["name"]
            try:
                # A. 抓取富果即時價格
                q = client.stock.intraday.quote(symbol=sid)
                
                # B. 抓取 Yahoo 走勢圖數據 (今日 1 分鐘 K 線)
                try:
                    df_yf = yf.download(yf_id, period="1d", interval="2m", progress=False)
                except:
                    df_yf = pd.DataFrame()

                if q and 'lastPrice' in q:
                    price = q['lastPrice']
                    change = q['change']
                    pct = q['changePercent']
                    # 抓取漲跌停價，設為預設值避免為 None
                    limit_up = q.get('priceHighLimit', price * 1.1)
                    limit_down = q.get('priceLowLimit', price * 0.9)

                    # 決定卡片顏色樣式
                    box_class = "up" if change > 0 else ("down" if change < 0 else "stable")
                    sign = "+" if change > 0 else ""

                    # 渲染彩色文字卡片
                    st.markdown(f"""
                        <div class="stock-card {box_class}">
                            <span class="name-text">{name} <span class="id-text">{sid}</span></span>
                            <span class="price-text">{price:.1f}</span>
                            <span class="delta-text">{sign}{change:.2f} ({sign}{pct:.2f}%)</span>
                        </div>
                    """, unsafe_allow_html=True)

                    # 渲染精確縮放的走勢圖 (緊接在下方)
                    if not df_yf.empty and not df_yf['Close'].dropna().empty:
                        # 整理數據用於 Altair
                        chart_data = df_yf['Close'].dropna().reset_index()
                        chart_data.columns = ['Datetime', 'Close']
                        
                        # 使用 Altair 指定 Y 軸範圍從 跌停 到 漲停
                        c = alt.Chart(chart_data).mark_line(color='blue').encode(
                            x=alt.X('Datetime:T', axis=None, title=None),
                            y=alt.Y('Close:Q', scale=alt.Scale(domain=[limit_down, limit_up]), title=None)
                        ).properties(height=120, use_container_width=True)
                        st.altair_chart(c)
                    else:
                        st.caption("今天走勢數據連線中...")
                else:
                    st.error(f"{sid} 無數據資料")
            except:
                st.error(f"{sid} 連線異常")

st.divider()
st.caption(f"數據來源：富果 (價格) & Yahoo (走勢) | Y軸範圍：漲停 ↔ 跌停 | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
