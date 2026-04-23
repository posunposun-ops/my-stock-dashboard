import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇專業看板", layout="wide")
# 設定 20 秒刷新一次 (現在非常安全，因為一分鐘只會用到 3 次額度)
st_autorefresh(interval=20000, key="stock_refresh")

# --- CSS：設定專業一體化佈局 ---
st.markdown("""
    <style>
    .stock-card {
        border-radius: 15px; padding: 18px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); height: 160px;
    }
    .up { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    
    .left-content { flex: 1; }
    .right-content { width: 220px; display: flex; justify-content: center; }
    
    .name-text { font-size: 26px; font-weight: 800; display: block; }
    .price-text { font-size: 56px; font-weight: 900; line-height: 1.1; display: block; margin: 5px 0; }
    .delta-text { font-size: 20px; font-weight: 700; display: block; }
    .id-tag { font-size: 14px; opacity: 0.6; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# SVG 繪圖器 (修正縮放邏輯)
def generate_svg(prices, l_up, l_down, color):
    if not prices or len(prices) < 2:
        return '<div style="color:gray; font-size:12px;">走勢讀取中...</div>'
    w, h = 200, 80
    # 避免除以零
    price_range = (l_up - l_down) if l_up != l_down else 1
    points = []
    for i, p in enumerate(prices):
        x = i * (w / (len(prices) - 1))
        y = h - ((p - l_down) / price_range * h)
        points.append(f"{x},{y}")
    return f'<svg width="{w}" height="{h}"><polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}"/></svg>'

st.title("🚀 柏昇即時看板：批次同步強韌版")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except:
    st.error("🔑 請檢查 Secrets 裡的 FUGLE_KEY")
    st.stop()

# 3. 15 檔指定股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

# 準備 Yahoo 代號
def to_yf(sid):
    return f"{sid}.TWO" if sid in ["3491", "6789", "3324", "8033"] else f"{sid}.TW"

# 4. 執行「批次」抓取 (解決連線異常的關鍵)
try:
    sids = list(my_portfolio.keys())
    # 富果批次抓取 (15 檔只花 1 個 API 額度)
    quotes = client.stock.intraday.tickers(symbols=sids)
    data_map = {item['symbol']: item for item in quotes if 'symbol' in item}
    
    # Yahoo 批次抓取走勢 (1 個請求抓 15 檔)
    yf_ids = [to_yf(s) for s in sids]
    yf_df = yf.download(yf_ids, period="1d", interval="2m", group_by='ticker', progress=False)

    # 5. 顯示網格 (一排 2 支，字體最霸氣)
    for i in range(0, len(sids), 2):
        cols = st.columns(2)
        for k, sid in enumerate(sids[i:i+2]):
            with cols[k]:
                name = my_portfolio[sid]
                q = data_map.get(sid)
                if q:
                    price, change, pct = q.get('lastPrice', 0), q.get('change', 0), q.get('changePercent', 0)
                    l_up, l_down = q.get('priceHighLimit', price*1.1), q.get('priceLowLimit', price*0.9)
                    
                    status = "up" if change > 0 else ("down" if change < 0 else "stable")
                    chart_col = "#FF0000" if change > 0 else ("#008000" if change < 0 else "#31333F")
                    
                    # 取得 Yahoo 走勢清單
                    try:
                        p_list = yf_df[to_yf(sid)]['Close'].dropna().tolist()
                    except:
                        p_list = []
                    
                    svg_chart = generate_svg(p_list, l_up, l_down, chart_col)

                    st.markdown(f"""
                        <div class="stock-card {status}">
                            <div class="left-content">
                                <span class="name-text">{name} <span class="id-tag">{sid}</span></span>
                                <span class="price-text">{price:.1f}</span>
                                <span class="delta-text">{"+" if change>0 else ""}{change:.2f} ({"+" if change>0 else ""}{pct:.2f}%)</span>
                            </div>
                            <div class="right-content">{svg_chart}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"{sid} 數據更新中...")

except Exception as e:
    st.error(f"📡 系統忙碌中，請稍候重整 (原因: {e})")

st.divider()
st.caption(f"🔄 批次連線模式：穩定不卡頓 | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
