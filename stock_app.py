import streamlit as st
from fugle_marketdata import RestClient
import pandas as pd
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
import time

# 1. 網頁基本設定
st.set_page_config(page_title="柏昇操盤監控", layout="wide")
# 設定 30 秒刷新一次，這是最穩定的頻率
st_autorefresh(interval=30000, key="stock_refresh")

# --- CSS：設定專業一體化佈局 ---
st.markdown("""
    <style>
    .stock-card {
        border-radius: 15px; padding: 15px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1); height: 160px;
    }
    .up { background-color: #FFF0F0; border: 3px solid #FF0000; color: #FF0000; }
    .down { background-color: #F0FFF0; border: 3px solid #008000; color: #008000; }
    .stable { background-color: #F8F9FA; border: 3px solid #D0D0D0; color: #31333F; }
    
    .left-content { flex: 1.2; }
    .right-content { width: 220px; display: flex; justify-content: flex-end; }
    
    .name-text { font-size: 26px; font-weight: 800; display: block; }
    .price-text { font-size: 56px; font-weight: 900; line-height: 1; display: block; margin: 5px 0; }
    .delta-text { font-size: 20px; font-weight: 700; display: block; }
    .id-tag { font-size: 14px; opacity: 0.6; font-weight: 400; }
    </style>
    """, unsafe_allow_html=True)

# SVG 走勢圖生成器
def generate_svg(prices, l_up, l_down, color):
    if not prices or len(prices) < 2:
        return '<div style="color:gray; font-size:12px;">走勢載入中...</div>'
    w, h = 200, 80
    p_range = (l_up - l_down) if l_up != l_down else 1
    points = [f"{i*(w/(len(prices)-1))},{h-((p-l_down)/p_range*h)}" for i, p in enumerate(prices)]
    return f'<svg width="{w}" height="{h}"><polyline fill="none" stroke="{color}" stroke-width="4" points="{" ".join(points)}"/></svg>'

st.title("⚡ 柏昇即時看板：單點穩定一體版")

# 2. 安全讀取 API Key
try:
    FUGLE_API_KEY = st.secrets["FUGLE_KEY"]
    client = RestClient(api_key=FUGLE_API_KEY)
except:
    st.error("🔑 Secrets 設定錯誤")
    st.stop()

# 3. 15 檔股票清單
my_portfolio = {
    "2330": "台積電", "2317": "鴻海", "3711": "日月光", "2449": "京元電", "1711": "永光",
    "2337": "旺宏", "2454": "聯發科", "6285": "啟碁", "6789": "采鈺", "3324": "雙鴻",
    "3491": "昇達科", "3037": "欣興", "3189": "景碩", "8033": "雷虎", "2344": "華邦電"
}

def to_yf(sid):
    return f"{sid}.TWO" if sid in ["3491", "6789", "3324", "8033"] else f"{sid}.TW"

# 4. 批次抓取 Yahoo 數據 (Yahoo 很穩，可以用批次)
yf_ids = [to_yf(s) for s in my_portfolio.keys()]
try:
    yf_df = yf.download(yf_ids, period="1d", interval="2m", group_by='ticker', progress=False)
except:
    yf_df = pd.DataFrame()

# 5. 顯示網格 (一排 2 支，確保畫面霸氣)
sids = list(my_portfolio.keys())
for i in range(0, len(sids), 2):
    cols = st.columns(2)
    for k, sid in enumerate(sids[i:i+2]):
        with cols[k]:
            name = my_portfolio[sid]
            try:
                # 重點：逐一抓取富果價格，並給予 0.2 秒間隔保護 API
                q = client.stock.intraday.quote(symbol=sid)
                time.sleep(0.2) 

                if q and 'lastPrice' in q:
                    price, change, pct = q['lastPrice'], q['change'], q['changePercent']
                    l_up, l_down = q.get('priceHighLimit', price*1.1), q.get('priceLowLimit', price*0.9)
                    
                    status = "up" if change > 0 else ("down" if change < 0 else "stable")
                    chart_col = "#FF0000" if change > 0 else ("#008000" if change < 0 else "#31333F")
                    
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
                    st.warning(f"{sid} 無數據")
            except Exception as e:
                st.error(f"{sid} 連線異常")

st.divider()
st.caption(f"🔄 30 秒週期更新 | 模式：逐一抓取 (API 守護者) | 更新時間：{pd.Timestamp.now(tz='Asia/Taipei').strftime('%H:%M:%S')}")
