import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")
st_autorefresh(interval=20000, key="stock_refresh")

# --- CSS：設定專業看板樣式 ---
st.markdown("""
    <style>
    .stock-card {
        border-radius: 15px; padding: 20px; margin-bottom: 15px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); height: 160px;
    }
    .up { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    
    .left-content { flex: 1; }
    .right-content { width: 220px; text-align: right; }
    
    .name-text { font-size: 24px; font-weight: 800; display: block; margin-bottom: 2px; }
    .price-text { font-size: 56px; font-weight: 900; line-height: 1; display: block; margin: 8px 0; }
    .delta-text { font-size: 20px; font-weight: 700; display: block; }
    .id-tag { font-size: 14px; opacity: 0.6; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SVG 走勢圖生成器 ---
def generate_svg_chart(prices, limit_up, limit_down, color):
    if not prices or len(prices) < 2:
        return '<div style="color:gray; font-size:12px;">走勢載入中...</div>'
    
    w, h = 200, 80
    points = []
    for i, p in enumerate(prices):
        x = i * (w / (len(prices) - 1))
        # 根據漲跌停縮放 Y 軸
        y = h - ((p - limit_down) / (limit_up - limit_down) * h)
        points.append(f"{x},{y}")
    
    path_data = " ".join(points)
    return f"""
    <svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">
        <polyline fill="none" stroke="{color}" stroke-width="3" points="{path_data}" />
    </svg>
    """

st.title("⚡ 柏昇即時看板：專業走勢一體版")

# 3. 安全讀取 API Key 與持股清單
FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
client = RestClient(api_key=FUGLE_API_KEY)

my_portfolio = [
    {"sid": "2330", "yf_id": "2330.TW", "name": "台積電"},
    {"sid": "2317", "yf_id": "2317.TW", "name": "鴻海"},
    {"sid": "3711", "yf_id": "3711.TW", "name": "日月光"},
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

# 4. 顯示網格 (一排 2 支在手機上看字最大最霸氣)
cols_per_row = 2
for i in range(0, len(my_portfolio), cols_per_row):
    cols = st.columns(cols_per_row)
    for j, stock in enumerate(my_portfolio[i:i+cols_per_row]):
        with cols[j]:
            sid, ysid, name = stock["sid"], stock["yf_id"], stock["name"]
            try:
                # 抓取富果即時價格
                q = client.stock.intraday.quote(symbol=sid)
                # 抓取 Yahoo 今日走勢
                df_yf = yf.download(ysid, period="1d", interval="2m", progress=False)

                if q and 'lastPrice' in q:
                    price, change, pct = q['lastPrice'], q['change'], q['changePercent']
                    l_up = q.get('priceHighLimit', price * 1.1)
                    l_down = q.get('priceLowLimit', price * 0.9)
                    
                    status = "up" if change > 0 else ("down" if change < 0 else "stable")
                    chart_color = "#FF0000" if change > 0 else ("#008000" if change < 0 else "#31333F")
                    sign = "+" if change > 0 else ""

                    # 準備走勢數據
                    price_list = df_yf['Close'].dropna().tolist() if not df_yf.empty else []
                    svg_chart = generate_svg_chart(price_list, l_up, l_down, chart_color)

                    # --- 渲染一體化 HTML 卡片 ---
                    st.markdown(f"""
                        <div class="stock-card {status}">
                            <div class="left-content">
                                <span class="name-text">{name} <span class="id-tag">{sid}</span></span>
                                <span class="price-text">{price:.1f}</span>
                                <span class="delta-text">{sign}{change:.2f} ({sign}{pct:.2f}%)</span>
                            </div>
                            <div class="right-content">
                                {svg_chart}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"{sid} 數據更新中")
            except:
                st.error(f"{sid} 連線異常")

st.divider()
st.caption(f"🔄 最後更新：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')} | 走勢 Y 軸：漲跌停區間")
