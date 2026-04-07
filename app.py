"""
StockFin — Live Market Dashboard
Run:  streamlit run app.py

CHANGES vs previous version:
  - Compliance page removed entirely.
  - Dashboard, Analytics, Portfolio, Screener, Calendar & Earnings removed
    from the sidebar nav (as requested). Remaining nav items have no emojis.
  - All emojis stripped from labels, buttons, messages.
  - Sidebar brand name changed from "StockFin" to "Dashboard".
  - Sidebar toggle always visible (fixed position in styling.py).
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time, io

st.set_page_config(
    page_title="StockFin",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils.styling import apply_css, DARK_LAYOUT
apply_css()

# ══════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_stock(symbol: str) -> dict | None:
    try:
        t     = yf.Ticker(symbol)
        intra = t.history(period="1d", interval="1m")
        price = float(intra["Close"].iloc[-1]) if not intra.empty else \
                t.info.get("regularMarketPrice", t.info.get("currentPrice", 0))
        hist  = t.history(period="1mo")
        if hist.empty: return None
        op = float(hist["Open"].iloc[-1])
        return dict(
            symbol=symbol, price=price, open=op,
            high=float(hist["High"].iloc[-1]),
            low=float(hist["Low"].iloc[-1]),
            volume=float(hist["Volume"].iloc[-1]),
            change=price - op,
            change_pct=((price - op) / op * 100) if op else 0.0,
            history=hist, info=t.info,
        )
    except Exception as e:
        st.warning(f"{symbol}: {e}")
        return None


@st.cache_data(ttl=300)
def get_many(symbols: tuple) -> dict:
    out = {}
    for s in symbols:
        d = get_stock(s)
        if d: out[s] = d
        time.sleep(0.3)
    return out


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    delta = df["Close"].diff()
    g = delta.where(delta > 0, 0.0).rolling(14).mean()
    l = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df["RSI"]    = (100 - 100 / (1 + g / l.replace(0, np.nan))).fillna(50)
    df["BB_M"]   = df["Close"].rolling(20).mean()
    s            = df["Close"].rolling(20).std()
    df["BB_U"]   = df["BB_M"] + 2 * s
    df["BB_L"]   = df["BB_M"] - 2 * s
    e1           = df["Close"].ewm(span=12, adjust=False).mean()
    e2           = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = e1 - e2
    df["MACD_sig"]= df["MACD"].ewm(span=9, adjust=False).mean()
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL", "NVDA"]
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:.6rem .4rem .2rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
          border-radius:10px;display:flex;align-items:center;justify-content:center;
          font-size:1rem;font-weight:700;color:white;font-family:'Syne',sans-serif">S</div>
        <div>
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;color:#f0f2f8">Dashboard</div>
          <span class="live-dot" style="font-size:.65rem">LIVE</span>
        </div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .6rem">
    """, unsafe_allow_html=True)

    # Nav — Compliance, Analytics, Portfolio, Screener, Calendar removed as requested
    page = st.radio("Navigate", [
        "Dashboard",
        "Watchlist & Alerts",
        "Sector Heatmap",
        "Backtesting",
        "Options Chain",
    ], label_visibility="collapsed")

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)

    DEFAULT_STOCKS = {
        "Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA", "Microsoft (MSFT)": "MSFT",
        "Google (GOOGL)": "GOOGL", "NVIDIA (NVDA)": "NVDA", "Meta (META)": "META",
        "Amazon (AMZN)": "AMZN", "Netflix (NFLX)": "NFLX",
    }
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .3rem">Select Stocks</div>', unsafe_allow_html=True)
    selected_stocks = [sym for name, sym in DEFAULT_STOCKS.items()
                       if st.checkbox(name, value=(sym in ["AAPL","TSLA","MSFT"]))]

    custom = st.text_input("Custom symbol", placeholder="INFY.NS, BTC-USD…")
    if custom and st.button("Add", use_container_width=True):
        s = custom.upper().strip()
        if s not in selected_stocks: selected_stocks.append(s)

    chart_period = st.selectbox("Chart Period", ["1mo","3mo","6mo","1y","2y"], index=0)
    total_inv    = st.number_input("Initial Investment ($)", value=10_000, step=1_000, min_value=0)

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    if st.button("Refresh All Data", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div style="font-size:.7rem;color:#4e5669;padding:.2rem .4rem">Data · Yahoo Finance · ~60s cache</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    h1, h2, h3 = st.columns([3, 1.4, .8])
    with h1:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .1rem">Live Market Dashboard</div><div style="font-size:.82rem;color:#8892a4">Real-time stock data &amp; analytics</div>', unsafe_allow_html=True)
    with h2:
        st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:.55rem 1rem;text-align:center;margin-top:.7rem"><div style="font-size:.65rem;color:#4e5669;text-transform:uppercase">Last Update</div><div style="font-size:.82rem;font-weight:600;color:#f0f2f8">{datetime.now().strftime("%b %d  %H:%M")}</div></div>', unsafe_allow_html=True)
    with h3:
        st.markdown("<div style='margin-top:.7rem'>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if not selected_stocks:
        st.info("Select stocks in the sidebar to get started.")
        st.stop()

    with st.spinner("Fetching live data…"):
        stocks = get_many(tuple(selected_stocks))

    if not stocks:
        st.error("No data fetched. Check your internet connection.")
        st.stop()

    # Ticker grid
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin:.8rem 0 .4rem">Market Overview</div>', unsafe_allow_html=True)
    cols = st.columns(min(4, len(stocks)))
    for i, (sym, d) in enumerate(list(stocks.items())[:8]):
        with cols[i % len(cols)]:
            up = d["change"] >= 0
            st.markdown(f'<div class="ticker-card"><div class="ticker-sym">{sym}</div><div class="ticker-price">${d["price"]:.2f}</div><div class="ticker-chg {"up" if up else "down"}">{"+" if up else ""}{d["change_pct"]:.2f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # Detailed analysis
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Detailed Analysis</div>', unsafe_allow_html=True)
    sel = st.selectbox("Symbol", list(stocks.keys()), label_visibility="collapsed")
    if sel:
        d    = stocks[sel]
        hist = add_indicators(d["history"])
        tab1, tab2, tab3, tab4 = st.tabs(["Chart","Indicators","Company","Alerts"])

        with tab1:
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.04,
                                row_heights=[.6,.2,.2], subplot_titles=("Price","Volume","RSI"))
            fig.add_trace(go.Candlestick(x=hist.index, open=hist.Open, high=hist.High,
                low=hist.Low, close=hist.Close, name="Price",
                increasing_line_color="#22d98a", decreasing_line_color="#f05252"), row=1, col=1)
            for c, lbl, col, dash in [
                ("MA20","MA20","#f5a623","solid"),("MA50","MA50","#7c6ff7","solid"),
                ("BB_U","BB+","rgba(255,255,255,.2)","dot"),("BB_L","BB-","rgba(255,255,255,.2)","dot"),
            ]:
                fig.add_trace(go.Scatter(x=hist.index, y=hist[c], name=lbl,
                                         line=dict(color=col,width=1,dash=dash)), row=1, col=1)
            bc = ["#22d98a" if hist.Close.iloc[i] >= hist.Open.iloc[i] else "#f05252"
                  for i in range(len(hist))]
            fig.add_trace(go.Bar(x=hist.index, y=hist.Volume, name="Vol",
                                  marker_color=bc, opacity=.7), row=2, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.RSI, name="RSI",
                                      line=dict(color="#4f8fff",width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=.5, row=3, col=1)
            fig.update_layout(height=620, showlegend=True, xaxis_rangeslider_visible=False,
                              title=f"{sel} Technical Chart",
                              title_font=dict(family="Syne",size=14,color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            rsi   = float(hist.RSI.iloc[-1])
            rsi_s = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
            rc    = "#f05252" if rsi > 70 else "#22d98a" if rsi < 30 else "#f5a623"
            macd_bull = float(hist.MACD.iloc[-1]) > float(hist.MACD_sig.iloc[-1])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="glass-card"><h4>Key Statistics</h4><table style="width:100%">
                <tr><td>Price</td><td><strong>${d['price']:.2f}</strong></td></tr>
                <tr><td>Open</td><td>${d['open']:.2f}</td></tr>
                <tr><td>High</td><td>${d['high']:.2f}</td></tr>
                <tr><td>Low</td><td>${d['low']:.2f}</td></tr>
                <tr><td>Volume</td><td>{d['volume']:,.0f}</td></tr>
                <tr><td>Change</td><td style="color:{'#22d98a' if d['change']>=0 else '#f05252'}">{d['change']:+.2f} ({d['change_pct']:+.2f}%)</td></tr>
                </table></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="glass-card"><h4>Technical Signals</h4><table style="width:100%">
                <tr><td>RSI 14</td><td><strong style="color:{rc}">{rsi:.1f} — {rsi_s}</strong></td></tr>
                <tr><td>MACD</td><td><strong style="color:{'#22d98a' if macd_bull else '#f05252'}">{'Bullish' if macd_bull else 'Bearish'}</strong></td></tr>
                <tr><td>MA20</td><td>${hist.MA20.iloc[-1]:.2f}</td></tr>
                <tr><td>MA50</td><td>${hist.MA50.iloc[-1]:.2f}</td></tr>
                <tr><td>BB Upper</td><td>${hist.BB_U.iloc[-1]:.2f}</td></tr>
                <tr><td>BB Lower</td><td>${hist.BB_L.iloc[-1]:.2f}</td></tr>
                </table></div>""", unsafe_allow_html=True)

        with tab3:
            info = d["info"]
            mc   = info.get("marketCap", 0)
            mcs  = f"${mc/1e12:.2f}T" if mc >= 1e12 else f"${mc/1e9:.1f}B" if mc >= 1e9 else f"${mc:,.0f}"
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="glass-card"><h4>Company Profile</h4><table style="width:100%">
                <tr><td>Name</td><td>{info.get('longName','N/A')}</td></tr>
                <tr><td>Sector</td><td>{info.get('sector','N/A')}</td></tr>
                <tr><td>Industry</td><td>{info.get('industry','N/A')}</td></tr>
                <tr><td>Country</td><td>{info.get('country','N/A')}</td></tr>
                <tr><td>Website</td><td><a href="{info.get('website','#')}" target="_blank" style="color:#4f8fff">{info.get('website','N/A')}</a></td></tr>
                </table></div>""", unsafe_allow_html=True)
            with c2:
                dy = (info.get("dividendYield") or 0) * 100
                st.markdown(f"""<div class="glass-card"><h4>Financials</h4><table style="width:100%">
                <tr><td>Market Cap</td><td>{mcs}</td></tr>
                <tr><td>P/E Ratio</td><td>{info.get('trailingPE','N/A')}</td></tr>
                <tr><td>EPS</td><td>{info.get('trailingEps','N/A')}</td></tr>
                <tr><td>52W High</td><td>${info.get('fiftyTwoWeekHigh',0):.2f}</td></tr>
                <tr><td>52W Low</td><td>${info.get('fiftyTwoWeekLow',0):.2f}</td></tr>
                <tr><td>Div Yield</td><td>{dy:.2f}%</td></tr>
                <tr><td>Beta</td><td>{info.get('beta','N/A')}</td></tr>
                </table></div>""", unsafe_allow_html=True)

        with tab4:
            rsi_v   = float(hist.RSI.iloc[-1])
            avgvol  = float(hist.Volume.rolling(20).mean().iloc[-1])
            alerts_found = []
            if d["change_pct"] > 3:  alerts_found.append(("!", f"<strong>{sel}</strong> surged <strong>+{d['change_pct']:.2f}%</strong>", "#f5a623"))
            if d["change_pct"] < -3: alerts_found.append(("!", f"<strong>{sel}</strong> dropped <strong>{d['change_pct']:.2f}%</strong>", "#f05252"))
            if rsi_v > 70: alerts_found.append(("RSI", f"Overbought at <strong>{rsi_v:.1f}</strong> — pullback zone", "#f05252"))
            if rsi_v < 30: alerts_found.append(("RSI", f"Oversold at <strong>{rsi_v:.1f}</strong> — bounce zone", "#22d98a"))
            if avgvol and d["volume"] > avgvol * 1.5:
                alerts_found.append(("Vol", f"Volume spike: <strong>{d['volume']:,.0f}</strong> vs avg {avgvol:,.0f}", "#4f8fff"))
            bbw = (float(hist.BB_U.iloc[-1]) - float(hist.BB_L.iloc[-1])) / float(hist.BB_M.iloc[-1])
            if bbw < 0.05: alerts_found.append(("BB", "Bollinger squeeze — breakout approaching", "#7c6ff7"))
            if alerts_found:
                for ico, msg, col in alerts_found:
                    st.markdown(f'<div style="background:var(--bg-elevated);border:1px solid {col}33;border-left:3px solid {col};border-radius:0 8px 8px 0;padding:.8rem 1rem;font-size:.83rem;color:#8892a4;margin-bottom:.4rem"><strong style="color:{col}">[{ico}]</strong> {msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:rgba(34,217,138,.07);border:1px solid rgba(34,217,138,.2);border-radius:14px;padding:1rem;font-size:.83rem;color:#22d98a">No significant alerts at this time</div>', unsafe_allow_html=True)

    # Session summary
    st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:1.2rem 0 .7rem'>", unsafe_allow_html=True)
    gainers = sum(1 for d in stocks.values() if d["change"] >= 0)
    losers  = len(stocks) - gainers
    avg_chg = sum(d["change_pct"] for d in stocks.values()) / max(len(stocks), 1)
    est_ret = total_inv * (1 + avg_chg / 100)
    for col, title, val, icon in zip(st.columns(4),
        ["Est. Portfolio","Avg Change","Gainers / Losers","Stocks Tracked"],
        [f"${est_ret:,.2f}", f"{avg_chg:+.2f}%", f"{gainers} up  {losers} dn", str(len(stocks))],
        ["$","~","G/L","#"]):
        color = "#22d98a" if avg_chg > 0 and "%" in val else "#f0f2f8"
        col.markdown(f'<div class="stat-card"><div class="stat-label">{title} <span style="opacity:.5;float:right">{icon}</span></div><div class="stat-value" style="font-size:1.4rem;color:{color}">{val}</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: WATCHLIST & ALERTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Watchlist & Alerts":
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .3rem">Watchlist &amp; Price Alerts</div>', unsafe_allow_html=True)

    wl_col, al_col = st.columns([1.4, 1])

    with wl_col:
        st.markdown("#### My Watchlist")
        add_sym = st.text_input("Add to watchlist", placeholder="AMZN, BABA…", key="wl_add")
        if st.button("Add Symbol") and add_sym:
            s = add_sym.upper().strip()
            if s not in st.session_state.watchlist:
                st.session_state.watchlist.append(s); st.rerun()

        to_remove = []
        for sym in st.session_state.watchlist:
            d = get_stock(sym)
            if d:
                up = d["change"] >= 0
                c1, c2, c3 = st.columns([2, 1, 0.4])
                with c1:
                    st.markdown(f'<div style="font-weight:600;color:#f0f2f8">{sym}</div><div style="font-size:.75rem;color:#8892a4">{d["info"].get("longName","")[:30]}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:#f0f2f8">${d["price"]:.2f}</div><div style="font-size:.75rem;color:{"#22d98a" if up else "#f05252"}">{d["change_pct"]:+.2f}%</div>', unsafe_allow_html=True)
                with c3:
                    if st.button("x", key=f"rm_{sym}"):
                        to_remove.append(sym)
                st.markdown("<hr style='border-color:rgba(255,255,255,.04);margin:.3rem 0'>", unsafe_allow_html=True)
        for s in to_remove:
            st.session_state.watchlist.remove(s)
        if to_remove: st.rerun()

    with al_col:
        st.markdown("#### Price Alerts")
        with st.form("alert_form"):
            a_sym  = st.text_input("Symbol", placeholder="AAPL")
            a_cond = st.selectbox("Condition", ["Price Above","Price Below"])
            a_price= st.number_input("Trigger Price ($)", min_value=0.01, step=0.01, value=150.0)
            if st.form_submit_button("Set Alert", use_container_width=True):
                if a_sym:
                    st.session_state.alerts.append({
                        "symbol": a_sym.upper(), "condition": a_cond,
                        "price": a_price, "triggered": False,
                    })
                    st.success(f"Alert set: {a_sym.upper()} {a_cond} ${a_price:.2f}")

        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.session_state.alerts:
            for i, al in enumerate(st.session_state.alerts):
                curr = get_stock(al["symbol"])
                triggered = False
                if curr:
                    if al["condition"] == "Price Above" and curr["price"] > al["price"]: triggered = True
                    if al["condition"] == "Price Below" and curr["price"] < al["price"]: triggered = True
                color = "#f05252" if triggered else "#4e5669"
                status= "TRIGGERED" if triggered else "Waiting"
                st.markdown(f'<div style="background:var(--bg-elevated);border:1px solid {color}33;border-left:3px solid {color};border-radius:0 8px 8px 0;padding:.7rem 1rem;font-size:.8rem;margin-bottom:.3rem"><strong style="color:#f0f2f8">{al["symbol"]}</strong> — {al["condition"]} <strong>${al["price"]:.2f}</strong> — <span style="color:{color}">{status}</span></div>', unsafe_allow_html=True)
            if st.button("Clear All Alerts"):
                st.session_state.alerts = []; st.rerun()
        else:
            st.info("No alerts set yet.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SECTOR HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Sector Heatmap":
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .3rem">Sector &amp; Market Heatmap</div>', unsafe_allow_html=True)

    SECTOR_ETF = {
        "Technology":"XLK","Healthcare":"XLV","Financials":"XLF",
        "Consumer Disc":"XLY","Industrials":"XLI","Energy":"XLE",
        "Utilities":"XLU","Materials":"XLB","Real Estate":"XLRE","Comm Svcs":"XLC",
    }
    SECTOR_STOCKS = {
        "Technology":["AAPL","MSFT","NVDA","AMD","INTC","ORCL","CRM","ADBE"],
        "Healthcare":["JNJ","PFE","ABBV","UNH","MRNA","CVS","LLY","BMY"],
        "Financials":["JPM","GS","BAC","WFC","MS","C","BLK","AXP"],
        "Consumer Disc":["AMZN","TSLA","HD","MCD","NKE","SBUX","LOW","TJX"],
    }

    tab_etf, tab_stocks = st.tabs(["Sector ETFs","Individual Stocks"])

    with tab_etf:
        with st.spinner("Fetching sector data…"):
            sector_data = []
            for sec, etf in SECTOR_ETF.items():
                d = get_stock(etf)
                if d: sector_data.append({"Sector": sec, "ETF": etf, "Price": d["price"], "Change": d["change_pct"]})

        if sector_data:
            df_s = pd.DataFrame(sector_data).sort_values("Change", ascending=False)
            fig  = px.bar(df_s, x="Sector", y="Change", color="Change",
                          color_continuous_scale=["#f05252","#1c2030","#22d98a"],
                          color_continuous_midpoint=0,
                          text=df_s["Change"].apply(lambda x: f"{x:+.2f}%"))
            fig.update_traces(textposition="outside", textfont=dict(color="#f0f2f8", size=11))
            fig.update_layout(height=400, title="Sector ETF Performance (Today)",
                              title_font=dict(family="Syne",size=14,color="#f0f2f8"),
                              showlegend=False, **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

            cols = st.columns(5)
            for i, row in df_s.iterrows():
                chg = row["Change"]
                intensity = min(abs(chg) / 5, 1)
                bg = f"rgba(34,217,138,{0.1+intensity*0.4})" if chg >= 0 else f"rgba(240,82,82,{0.1+intensity*0.4})"
                tc = "#22d98a" if chg >= 0 else "#f05252"
                with cols[list(df_s.index).index(i) % 5]:
                    st.markdown(f'<div class="heat-cell" style="background:{bg};color:{tc};margin-bottom:.5rem"><div style="font-size:.78rem;color:#f0f2f8;font-weight:600">{row["Sector"]}</div><div style="font-size:1rem;font-weight:700">{chg:+.2f}%</div><div style="font-size:.68rem;color:#8892a4">{row["ETF"]}</div></div>', unsafe_allow_html=True)

    with tab_stocks:
        sel_sec = st.selectbox("Select Sector", list(SECTOR_STOCKS.keys()))
        syms    = SECTOR_STOCKS[sel_sec]
        with st.spinner(f"Fetching {sel_sec}…"):
            sdata = [(s, get_stock(s)) for s in syms]
        sdata = [(s, d) for s, d in sdata if d]
        if sdata:
            labels = [s for s, _ in sdata]
            values = [d["change_pct"] for _, d in sdata]
            fig2   = go.Figure(go.Treemap(
                labels=labels, parents=[""] * len(labels),
                values=[abs(v) + 2 for v in values],
                customdata=[[d["price"], v] for (_, d), v in zip(sdata, values)],
                hovertemplate="<b>%{label}</b><br>Price: $%{customdata[0]:.2f}<br>Change: %{customdata[1]:+.2f}%<extra></extra>",
                marker=dict(colors=values,
                            colorscale=[[0,"#f05252"],[0.5,"#1c2030"],[1,"#22d98a"]],
                            cmid=0, line=dict(width=2,color="#0d0f14")),
                texttemplate="<b>%{label}</b><br>%{customdata[1]:+.1f}%",
                textfont=dict(color="#f0f2f8", size=13),
            ))
            fig2.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BACKTESTING
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Backtesting":
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .3rem">Strategy Backtester</div>', unsafe_allow_html=True)

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1: bt_sym    = st.text_input("Symbol", "AAPL", key="bt_sym")
    with bc2: bt_period = st.selectbox("Period", ["1y","2y","3y","5y"], index=1)
    with bc3: bt_strat  = st.selectbox("Strategy", ["SMA Crossover","RSI Mean Reversion","MACD Signal","Bollinger Reversion"])
    with bc4: bt_capital= st.number_input("Capital ($)", value=10_000, step=1_000)

    if bt_strat == "SMA Crossover":
        p1, p2 = st.columns(2)
        fast = p1.slider("Fast MA", 5, 50, 20)
        slow = p2.slider("Slow MA", 20, 200, 50)
    elif bt_strat == "RSI Mean Reversion":
        p1, p2 = st.columns(2)
        rsi_lo = p1.slider("Oversold", 10, 40, 30)
        rsi_hi = p2.slider("Overbought", 60, 90, 70)
    elif bt_strat == "Bollinger Reversion":
        bb_period = st.slider("BB Period", 10, 40, 20)

    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running backtest…"):
            @st.cache_data(ttl=3600)
            def get_hist(sym, period):
                return yf.Ticker(sym).history(period=period)

            df = get_hist(bt_sym.upper(), bt_period)
            if df is None or df.empty:
                st.error("Could not fetch data."); st.stop()

            df = df.copy()
            df["ret"] = df["Close"].pct_change()

            if bt_strat == "SMA Crossover":
                df["fast"]   = df["Close"].rolling(fast).mean()
                df["slow"]   = df["Close"].rolling(slow).mean()
                df["signal"] = np.where(df["fast"] > df["slow"], 1, -1)
            elif bt_strat == "RSI Mean Reversion":
                delta = df["Close"].diff()
                g_ = delta.where(delta > 0, 0).rolling(14).mean()
                l_ = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi_ = (100 - 100 / (1 + g_ / l_.replace(0, np.nan))).fillna(50)
                df["signal"] = np.where(rsi_ < rsi_lo, 1, np.where(rsi_ > rsi_hi, -1, 0))
                df["signal"] = df["signal"].replace(0, np.nan).ffill().fillna(0)
            elif bt_strat == "MACD Signal":
                e1_ = df["Close"].ewm(span=12, adjust=False).mean()
                e2_ = df["Close"].ewm(span=26, adjust=False).mean()
                macd_ = e1_ - e2_
                sig_  = macd_.ewm(span=9, adjust=False).mean()
                df["signal"] = np.where(macd_ > sig_, 1, -1)
            else:
                m_ = df["Close"].rolling(bb_period).mean()
                s_ = df["Close"].rolling(bb_period).std()
                df["signal"] = np.where(df["Close"] < m_ - 2*s_, 1, np.where(df["Close"] > m_ + 2*s_, -1, 0))
                df["signal"] = df["signal"].replace(0, np.nan).ffill().fillna(0)

            df["strat_ret"] = df["signal"].shift(1) * df["ret"]
            df["buy_hold"]  = (1 + df["ret"]).cumprod() * bt_capital
            df["strategy"]  = (1 + df["strat_ret"].fillna(0)).cumprod() * bt_capital
            df = df.dropna(subset=["buy_hold","strategy"])

            final_strat = float(df["strategy"].iloc[-1])
            final_bh    = float(df["buy_hold"].iloc[-1])
            total_r     = (final_strat / bt_capital - 1) * 100
            bh_r        = (final_bh / bt_capital - 1) * 100
            returns_s   = df["strat_ret"].dropna()
            sharpe      = (returns_s.mean() / returns_s.std() * np.sqrt(252)) if returns_s.std() > 0 else 0
            cum         = df["strategy"] / bt_capital
            mdd         = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100
            n_trades    = int(df["signal"].diff().abs().sum() // 2)

            m1, m2, m3, m4, m5 = st.columns(5)
            for col, lbl, val, color in [
                (m1, "Final Value",      f"${final_strat:,.0f}",  "#4f8fff"),
                (m2, "Strategy Return",  f"{total_r:+.1f}%",      "#22d98a" if total_r > 0 else "#f05252"),
                (m3, "Buy & Hold",       f"{bh_r:+.1f}%",         "#f5a623"),
                (m4, "Sharpe Ratio",     f"{sharpe:.2f}",          "#7c6ff7"),
                (m5, "Max Drawdown",     f"{mdd:.1f}%",            "#f05252"),
            ]:
                col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{color}">{val}</h2></div>', unsafe_allow_html=True)

            alpha_txt = f"{total_r - bh_r:+.1f}%"
            alpha_col = "#22d98a" if total_r > bh_r else "#f05252"
            st.markdown(f'<div style="margin:.5rem 0;font-size:.8rem;color:#8892a4">Trades executed: <strong style="color:#f0f2f8">{n_trades}</strong> &nbsp;·&nbsp; Alpha vs B&H: <strong style="color:{alpha_col}">{alpha_txt}</strong></div>', unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df["strategy"], name=bt_strat,
                                     line=dict(color="#4f8fff",width=2)))
            fig.add_trace(go.Scatter(x=df.index, y=df["buy_hold"], name="Buy & Hold",
                                     line=dict(color="#8892a4",width=1.5,dash="dot")))
            fig.update_layout(height=380, title=f"{bt_sym.upper()} — {bt_strat} vs Buy & Hold",
                              title_font=dict(family="Syne",size=14,color="#f0f2f8"),
                              yaxis_title="Portfolio Value ($)", **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

            export_df = df[["Close","signal","strat_ret","strategy","buy_hold"]].round(4)
            st.download_button("Export Backtest Data (CSV)",
                               export_df.to_csv().encode(),
                               file_name=f"backtest_{bt_sym}_{bt_strat.replace(' ','_')}.csv",
                               mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: OPTIONS CHAIN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Options Chain":
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .3rem">Options Chain Viewer</div>', unsafe_allow_html=True)

    oc1, oc2, oc3 = st.columns([1.5, 1, 1])
    with oc1: opt_sym  = st.text_input("Symbol", "AAPL", key="opt_sym")
    with oc2: opt_type = st.selectbox("Type", ["Calls","Puts","Both"])

    if st.button("Load Options Chain", type="primary"):
        with st.spinner("Fetching options…"):
            try:
                t    = yf.Ticker(opt_sym.upper())
                exps = t.options
                if not exps:
                    st.error("No options data available."); st.stop()

                with oc3:
                    exp_sel = st.selectbox("Expiry", exps)

                chain      = t.option_chain(exp_sel)
                curr_price = get_stock(opt_sym.upper())
                cp         = curr_price["price"] if curr_price else 0

                st.markdown(f'<div style="font-size:.82rem;color:#8892a4;margin-bottom:.6rem">Current Price: <strong style="color:#f0f2f8">${cp:.2f}</strong> &nbsp;·&nbsp; Expiry: <strong style="color:#f0f2f8">{exp_sel}</strong></div>', unsafe_allow_html=True)

                def style_chain(df_opt: pd.DataFrame) -> pd.DataFrame:
                    cols = ["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility","inTheMoney"]
                    df_opt = df_opt[[c for c in cols if c in df_opt.columns]].copy()
                    df_opt["impliedVolatility"] = (df_opt.get("impliedVolatility", 0) * 100).round(1).astype(str) + "%"
                    df_opt["inTheMoney"] = df_opt.get("inTheMoney", False).map({True: "ITM", False: "—"})
                    return df_opt

                if opt_type in ("Calls","Both"):
                    st.markdown("#### Calls")
                    st.dataframe(style_chain(chain.calls), use_container_width=True, hide_index=True)

                if opt_type in ("Puts","Both"):
                    st.markdown("#### Puts")
                    st.dataframe(style_chain(chain.puts), use_container_width=True, hide_index=True)

                st.markdown("#### Implied Volatility Smile")
                fig_iv = go.Figure()
                if opt_type in ("Calls","Both"):
                    c_iv = chain.calls[["strike","impliedVolatility"]].dropna()
                    fig_iv.add_trace(go.Scatter(x=c_iv.strike, y=c_iv.impliedVolatility * 100,
                                                name="Calls IV", line=dict(color="#22d98a",width=2)))
                if opt_type in ("Puts","Both"):
                    p_iv = chain.puts[["strike","impliedVolatility"]].dropna()
                    fig_iv.add_trace(go.Scatter(x=p_iv.strike, y=p_iv.impliedVolatility * 100,
                                                name="Puts IV", line=dict(color="#f05252",width=2)))
                if cp:
                    fig_iv.add_vline(x=cp, line_dash="dot", line_color="#f5a623",
                                     annotation_text=f"Spot ${cp:.0f}",
                                     annotation_font=dict(color="#f5a623"))
                fig_iv.update_layout(height=320, xaxis_title="Strike", yaxis_title="IV %", **DARK_LAYOUT)
                st.plotly_chart(fig_iv, use_container_width=True)

            except Exception as e:
                st.error(f"Options fetch error: {e}")

st.markdown('<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.72rem;color:#4e5669">Data · Yahoo Finance · For educational purposes only · Not financial advice</div>', unsafe_allow_html=True)
