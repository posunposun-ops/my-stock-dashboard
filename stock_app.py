import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import altair as alt

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")
st_autorefresh(interval=20000, key="stock_refresh")

# CSS：維持你的大字體風格
st.markdown("""
    <style>
    .stock-box {
        border-radius: 15px; padding: 20px; margin-bottom: 10px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); text-align: left;
    }
    .up-box { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down-box { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable-box { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    .name-text { font-size: 26px; font-weight: 800; display: block; }
    .price-text { font-size: 52px; font-weight: 900; line-height: 1.1; margin: 5px 0; display: block; }
    .delta-text { font-size: 20px; font-weight: 700; display: block; }
    .id-text { font-size: 14px; color: #666; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 柏昇即時看板：漲跌停自動縮放")

# 2. 安全讀取 API Key
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

# 3. 15 檔指定股票
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

def get_yf_symbol(sid):
    otc_list = ["3491", "6789", "3189", "3324"]
    return f"{sid}.TWO" if sid in otc_list else f"{sid}.TW"

# 4. 批次抓取 Yahoo 走勢 (2分鐘 K 線)
yf_symbols = [get_yf_symbol(sid) for sid in my_portfolio.keys()]
try:
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
                q = client.stock.intraday.quote(symbol=sid)
                if q and 'lastPrice' in q:
                    price = q['lastPrice']
                    change = q['change']
                    pct = q['changePercent']
                    
                    # 關鍵：抓取漲跌停價
                    limit_up = q.get('priceHighLimit')
                    limit_down = q.get('priceLowLimit')
                    
                    box_class = "up-box" if change > 0 else ("down-box" if change < 0 else "stable-box")
                    sign = "+" if change > 0 else ""

                    # 渲染大字體卡片
                    st.markdown(f"""
                        <div class="stock-box {box_class}">
                            <span class="name-text">{name} <span class="id-text">{sid}</span></span>
                            <span class="price-text">{price:.1f}</span>
                            <span class="delta-text">{sign}{change:.2f} ({sign}{pct:.2f}%)</span>
                        </div>
                    """, unsafe_allow_html=True)

                    # 繪製「精確縮放」的走勢圖
                    try:
                        chart_series = yf_data[yf_sid]['Close'].dropna()
                        if not chart_series.empty:
                            df_chart = chart_series.reset_index()
                            df_chart.columns = ['Time', 'Price']
                            
                            # 使用 Altair 指定 Y 軸範圍從 跌停 到 漲停
                            c = alt.Chart(df_chart).mark_line(color='blue').encode(
                                x=alt.X('Time:T', axis=None),
                                y=alt.Y('Price:Q', scale=alt.Scale(domain=[limit_down, limit_up]), title=None)
                            ).properties(height=120)
                            st.altair_chart(c, use_container_width=True)
                    except:
                        st.caption("走勢圖連線中...")
                else:
                    st.error(f"{sid} 無報價")
            except:
                st.error(f"{sid} 讀取中")

st.divider()
st.caption(f"🔄 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')} | Y軸範圍：漲停 ↔ 跌停")
