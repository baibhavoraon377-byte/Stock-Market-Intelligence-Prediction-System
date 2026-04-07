"""
StockFin — Live Market Dashboard  (app.py)
Run:  streamlit run app.py

Changes vs original:
  - Compliance removed; replaced by ML Prediction, Watchlist & Screener pages
  - Sidebar toggle always visible (fixed CSS in utils/styling.py)
  - Price/Volume/RSI chart: increased vertical_spacing and row_heights for breathing room
  - Shared CSS imported from utils/styling — no more duplicated inline styles
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import time

st.set_page_config(
    page_title="StockFin",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from utils.styling import apply_css, DARK_LAYOUT
apply_css()


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_stock(symbol: str) -> dict | None:
    try:
        t     = yf.Ticker(symbol)
        intra = t.history(period="1d", interval="1m")
        price = (float(intra["Close"].iloc[-1]) if not intra.empty
                 else t.info.get("regularMarketPrice", t.info.get("currentPrice", 0)))
        hist  = t.history(period="1mo")
        if hist.empty: return None
        op = float(hist["Open"].iloc[-1])
        info = t.info
        return dict(
            symbol=symbol, price=price, open=op,
            high=float(hist["High"].iloc[-1]), low=float(hist["Low"].iloc[-1]),
            volume=float(hist["Volume"].iloc[-1]),
            change=price - op,
            change_pct=((price - op) / op * 100) if op else 0.0,
            history=hist, info=info,
            market_cap=info.get("marketCap", 0),
            pe=info.get("trailingPE"),
            week52_hi=info.get("fiftyTwoWeekHigh", 0),
            week52_lo=info.get("fiftyTwoWeekLow", 0),
            beta=info.get("beta"),
            analyst_target=info.get("targetMeanPrice"),
            sector=info.get("sector", "N/A"),
        )
    except Exception as e:
        st.warning(f"Could not fetch {symbol}: {e}")
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
    e1 = df["Close"].ewm(span=12, adjust=False).mean()
    e2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = e1 - e2
    df["MACD_S"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df


def fmt_cap(n):
    if not n: return "N/A"
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.1f}B"
    return f"${n/1e6:.0f}M"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem .4rem .3rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">📈</div>
        <div>
          <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;color:#f0f2f8">StockFin</div>
          <span class="live-dot" style="font-size:.62rem">LIVE</span>
        </div>
      </div>
      <div class="nav-group">Platform</div>
      <div class="nav-item active">Dashboard</div>
      <div class="nav-group" style="margin-top:.4rem">Feature Pages</div>
      <div class="nav-item">Analytics (page 1)</div>
      <div class="nav-item">Portfolio (page 2)</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.5rem 0 .8rem">
    """, unsafe_allow_html=True)

    DEFAULT = {
        "Apple (AAPL)": "AAPL", "Tesla (TSLA)": "TSLA",
        "Microsoft (MSFT)": "MSFT", "Google (GOOGL)": "GOOGL",
        "NVIDIA (NVDA)": "NVDA", "Meta (META)": "META",
        "Amazon (AMZN)": "AMZN", "Netflix (NFLX)": "NFLX",
    }
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .3rem">Select Stocks</div>', unsafe_allow_html=True)
    selected = [sym for name, sym in DEFAULT.items()
                if st.checkbox(name, value=(sym in ["AAPL", "TSLA", "MSFT"]))]

    custom = st.text_input("Custom symbol", placeholder="INFY.NS, BTC-USD…")
    if custom and st.button("Add", use_container_width=True):
        s = custom.upper().strip()
        if s not in selected: selected.append(s)

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    total_inv = st.number_input("Initial Investment ($)", value=10_000, step=1_000, min_value=0)
    if st.button("↺ Refresh", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div style="font-size:.7rem;color:#4e5669;padding:.3rem .4rem">Data · Yahoo Finance · ~60 s cache</div>', unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3, 1.4, 0.8])
with c1:
    st.markdown('<div style="padding:.6rem 0 .2rem"><div style="font-family:\'Syne\',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">Live Market Dashboard</div><div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">Real-time prices · Technical analysis · Portfolio insights</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:.55rem 1rem;text-align:center;margin-top:.7rem"><div style="font-size:.62rem;color:#4e5669;text-transform:uppercase">Last Update</div><div style="font-size:.82rem;font-weight:600;color:#f0f2f8">{datetime.now().strftime("%b %d, %Y  %H:%M")}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown("<div style='margin-top:.7rem'>", unsafe_allow_html=True)
    if st.button("↺ Refresh", use_container_width=True, key="hdr_refresh"):
        st.cache_data.clear(); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

if not selected:
    st.info("Select stocks from the sidebar to get started.")
    st.stop()

with st.spinner("Fetching live market data…"):
    stocks = get_many(tuple(selected))

if not stocks:
    st.error("No data fetched. Check your internet connection.")
    st.stop()


# ── Ticker grid ───────────────────────────────────────────────────────────────
st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.5rem">Market Overview</div>', unsafe_allow_html=True)
n_cols = min(4, len(stocks))
cols   = st.columns(n_cols)
for i, (sym, d) in enumerate(list(stocks.items())[:8]):
    up = d["change"] >= 0
    # 52-week position bar
    rng = d["week52_hi"] - d["week52_lo"]
    pos = int((d["price"] - d["week52_lo"]) / rng * 100) if rng > 0 else 50
    with cols[i % n_cols]:
        st.markdown(f"""
        <div class="ticker-card">
            <div class="ticker-sym">{sym}</div>
            <div class="ticker-price">${d['price']:.2f}</div>
            <div class="ticker-chg {'up' if up else 'down'}">{'▲' if up else '▼'} {abs(d['change_pct']):.2f}%</div>
            <div style="height:3px;background:rgba(255,255,255,.06);border-radius:6px;margin-top:.5rem;overflow:hidden">
              <div style="width:{pos}%;height:100%;background:{'#22d98a' if up else '#f05252'};border-radius:6px"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:.58rem;color:#4e5669;margin-top:.15rem"><span>52W Lo</span><span>52W Hi</span></div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)


# ── Quick Insights strip ──────────────────────────────────────────────────────
st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.5rem">Quick Insights</div>', unsafe_allow_html=True)
qi_cols = st.columns(min(4, len(stocks)))
for i, (sym, d) in enumerate(list(stocks.items())[:4]):
    target = d.get("analyst_target")
    price  = d["price"]
    upside = (target - price) / price * 100 if target and price else None
    pe_str = f"{d['pe']:.1f}x" if d.get("pe") else "N/A"
    beta_str = f"{d['beta']:.2f}" if d.get("beta") else "N/A"
    mc_str = fmt_cap(d.get("market_cap", 0))
    with qi_cols[i]:
        up_color = "#22d98a" if (upside and upside > 0) else "#f05252"
        upside_html = (f'<div style="font-family:\'Syne\',sans-serif;font-size:1rem;font-weight:700;color:{up_color}">'
                       f'{"▲" if upside > 0 else "▼"} {abs(upside):.1f}% upside</div>'
                       f'<div style="font-size:.7rem;color:#8892a4">Target: ${target:.0f}</div>'
                       if upside is not None else
                       '<div style="font-size:.82rem;color:#4e5669">No analyst target</div>')
        st.markdown(f"""
        <div class="glass-card" style="padding:.9rem 1rem">
          <div style="font-size:.62rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669">{sym} · {d.get('sector','N/A')}</div>
          {upside_html}
          <div style="font-size:.7rem;color:#8892a4;margin-top:.3rem">P/E {pe_str} · Beta {beta_str} · Cap {mc_str}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:.9rem'></div>", unsafe_allow_html=True)


# ── Detailed analysis ─────────────────────────────────────────────────────────
st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.5rem">Detailed Analysis</div>', unsafe_allow_html=True)
sel = st.selectbox("", list(stocks.keys()), label_visibility="collapsed")

if sel and sel in stocks:
    d    = stocks[sel]
    hist = add_indicators(d["history"])

    tab1, tab2, tab3, tab4 = st.tabs(["Price Chart", "Indicators", "Company Info", "Alerts"])

    # ── Price Chart ───────────────────────────────────────────────────────────
    with tab1:
        # Increased vertical_spacing (0.04→0.07) and row_heights give more gap
        # between Price, Volume, and RSI panels as requested
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.07,
            row_heights=[0.58, 0.21, 0.21],
            subplot_titles=("Price & Bands", "Volume", "RSI (14)"),
        )
        fig.add_trace(go.Candlestick(
            x=hist.index, open=hist["Open"], high=hist["High"],
            low=hist["Low"], close=hist["Close"],
            increasing_line_color="#22d98a", decreasing_line_color="#f05252", name="Price",
        ), row=1, col=1)
        for col_n, lbl, clr, dash in [
            ("MA20","MA20","#f5a623","solid"), ("MA50","MA50","#7c6ff7","solid"),
            ("BB_U","BB+","rgba(255,255,255,.22)","dot"), ("BB_L","BB-","rgba(255,255,255,.22)","dot"),
        ]:
            fig.add_trace(go.Scatter(x=hist.index, y=hist[col_n], name=lbl,
                line=dict(color=clr, width=1, dash=dash)), row=1, col=1)
        bc = ["#22d98a" if hist["Close"].iloc[i] >= hist["Open"].iloc[i] else "#f05252"
              for i in range(len(hist))]
        fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume",
                             marker_color=bc, opacity=0.7), row=2, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist["RSI"], name="RSI",
                                  line=dict(color="#4f8fff", width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=0.5, row=3, col=1)
        fig.update_layout(
            height=700, showlegend=True, xaxis_rangeslider_visible=False,
            title=f"{sel} Technical Chart",
            title_font=dict(family="Syne", size=14, color="#f0f2f8"), **DARK_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Indicators ────────────────────────────────────────────────────────────
    with tab2:
        rsi_v  = float(hist["RSI"].iloc[-1])
        rsi_s  = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
        rsi_c  = "#f05252" if rsi_v > 70 else "#22d98a" if rsi_v < 30 else "#f5a623"
        bull   = float(hist["MACD"].iloc[-1]) > float(hist["MACD_S"].iloc[-1])
        w52rng = d["week52_hi"] - d["week52_lo"]
        pos_pct= ((d["price"] - d["week52_lo"]) / w52rng * 100) if w52rng > 0 else 0

        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown(f"""<div class="glass-card"><h4>Key Statistics</h4><table style="width:100%">
            <tr><td>Price</td><td><strong>${d['price']:.2f}</strong></td></tr>
            <tr><td>Open</td><td>${d['open']:.2f}</td></tr>
            <tr><td>High</td><td>${d['high']:.2f}</td></tr>
            <tr><td>Low</td><td>${d['low']:.2f}</td></tr>
            <tr><td>Volume</td><td>{d['volume']:,.0f}</td></tr>
            <tr><td>Market Cap</td><td>{fmt_cap(d['market_cap'])}</td></tr>
            <tr><td>52W Position</td><td>{pos_pct:.0f}% of range</td></tr>
            </table></div>""", unsafe_allow_html=True)
        with ic2:
            tgt = d.get("analyst_target")
            tgt_str = f"${tgt:.2f} ({(tgt-d['price'])/d['price']*100:+.1f}%)" if tgt else "N/A"
            st.markdown(f"""<div class="glass-card"><h4>Technical Signals</h4><table style="width:100%">
            <tr><td>RSI (14)</td><td><strong style="color:{rsi_c}">{rsi_v:.1f} — {rsi_s}</strong></td></tr>
            <tr><td>MACD</td><td><strong style="color:{'#22d98a' if bull else '#f05252'}">{'Bullish ▲' if bull else 'Bearish ▼'}</strong></td></tr>
            <tr><td>MA 20</td><td>${hist['MA20'].iloc[-1]:.2f}</td></tr>
            <tr><td>MA 50</td><td>${hist['MA50'].iloc[-1]:.2f}</td></tr>
            <tr><td>BB Upper</td><td>${hist['BB_U'].iloc[-1]:.2f}</td></tr>
            <tr><td>BB Lower</td><td>${hist['BB_L'].iloc[-1]:.2f}</td></tr>
            <tr><td>Analyst Target</td><td>{tgt_str}</td></tr>
            </table></div>""", unsafe_allow_html=True)

        fig2 = go.Figure()
        for cn, lbl, clr in [("Close","Close","#4f8fff"),("MA20","MA20","#f5a623"),("MA50","MA50","#7c6ff7")]:
            fig2.add_trace(go.Scatter(x=hist.index, y=hist[cn], name=lbl,
                line=dict(color=clr, width=1.8 if cn=="Close" else 1.2)))
        fig2.update_layout(height=300, title="Price vs Moving Averages",
                           title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Company Info ──────────────────────────────────────────────────────────
    with tab3:
        info = d["info"]
        ci1, ci2 = st.columns(2)
        with ci1:
            st.markdown(f"""<div class="glass-card"><h4>Company Profile</h4><table style="width:100%">
            <tr><td>Name</td><td>{info.get('longName','N/A')}</td></tr>
            <tr><td>Sector</td><td>{info.get('sector','N/A')}</td></tr>
            <tr><td>Industry</td><td>{info.get('industry','N/A')}</td></tr>
            <tr><td>Country</td><td>{info.get('country','N/A')}</td></tr>
            <tr><td>Employees</td><td>{info.get('fullTimeEmployees','N/A'):,}</td></tr>
            <tr><td>Website</td><td><a href="{info.get('website','#')}" target="_blank" style="color:#4f8fff">{info.get('website','N/A')}</a></td></tr>
            </table></div>""", unsafe_allow_html=True)
        with ci2:
            rev = info.get("totalRevenue", 0)
            st.markdown(f"""<div class="glass-card"><h4>Financial Metrics</h4><table style="width:100%">
            <tr><td>Market Cap</td><td>{fmt_cap(info.get('marketCap',0))}</td></tr>
            <tr><td>Revenue</td><td>{fmt_cap(rev)}</td></tr>
            <tr><td>P/E Ratio</td><td>{info.get('trailingPE','N/A')}</td></tr>
            <tr><td>EPS (TTM)</td><td>{info.get('trailingEps','N/A')}</td></tr>
            <tr><td>52W High</td><td>${info.get('fiftyTwoWeekHigh',0):.2f}</td></tr>
            <tr><td>52W Low</td><td>${info.get('fiftyTwoWeekLow',0):.2f}</td></tr>
            <tr><td>Div Yield</td><td>{(info.get('dividendYield') or 0)*100:.2f}%</td></tr>
            <tr><td>Beta</td><td>{info.get('beta','N/A')}</td></tr>
            </table></div>""", unsafe_allow_html=True)

    # ── Alerts ────────────────────────────────────────────────────────────────
    with tab4:
        rsi_v   = float(hist["RSI"].iloc[-1])
        avg_vol = float(hist["Volume"].rolling(20).mean().iloc[-1])
        alerts  = []

        if d["change_pct"] > 3:
            alerts.append(("⚡", f"{sel} surged <strong>+{d['change_pct']:.2f}%</strong> today", "#f5a623"))
        elif d["change_pct"] < -3:
            alerts.append(("⚡", f"{sel} dropped <strong>{d['change_pct']:.2f}%</strong> today", "#f05252"))
        if rsi_v > 70:
            alerts.append(("📊", f"RSI overbought — <strong>{rsi_v:.1f}</strong>", "#f05252"))
        elif rsi_v < 30:
            alerts.append(("📊", f"RSI oversold — <strong>{rsi_v:.1f}</strong>", "#22d98a"))
        if avg_vol and d["volume"] > avg_vol * 1.5:
            alerts.append(("📢", f"Volume spike — <strong>{d['volume']:,.0f}</strong> vs avg {avg_vol:,.0f}", "#4f8fff"))
        tgt = d.get("analyst_target")
        if tgt:
            up = (tgt - d["price"]) / d["price"] * 100
            if abs(up) > 15:
                c = "#22d98a" if up > 0 else "#f05252"
                alerts.append(("🎯", f"Analyst target <strong>${tgt:.0f}</strong> implies <strong style='color:{c}'>{up:+.1f}%</strong>", c))

        if alerts:
            for ico, msg, col in alerts:
                st.markdown(f'<div style="background:var(--bg-elevated);border:1px solid {col}33;border-left:3px solid {col};border-radius:0 8px 8px 0;padding:.8rem 1rem;font-size:.83rem;color:#8892a4;margin-bottom:.4rem">{ico} {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:rgba(34,217,138,.07);border:1px solid rgba(34,217,138,.2);border-radius:14px;padding:1rem;font-size:.83rem;color:#22d98a">✅ No significant alerts at this time</div>', unsafe_allow_html=True)


# ── Portfolio summary strip ───────────────────────────────────────────────────
st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:1.2rem 0 .7rem'>", unsafe_allow_html=True)
st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.6rem">Portfolio Summary</div>', unsafe_allow_html=True)

pv = float(total_inv)
for sym, d in stocks.items():
    if d and d["open"]:
        alloc = total_inv / max(len(stocks), 1)
        pv    = pv - alloc + alloc * d["price"] / d["open"]
pct_ret = ((pv - total_inv) / total_inv * 100) if total_inv else 0.0

best  = max(stocks.items(), key=lambda x: x[1]["change_pct"])
worst = min(stocks.items(), key=lambda x: x[1]["change_pct"])

for col, title, value, color in zip(st.columns(6),
    ["Est. Value","Return","Holdings","Risk","Best Today","Worst Today"],
    [f"${pv:,.2f}", f"{pct_ret:+.2f}%", str(len(stocks)), "Medium",
     f"{best[0]} {best[1]['change_pct']:+.1f}%", f"{worst[0]} {worst[1]['change_pct']:+.1f}%"],
    ["#4f8fff",
     "#22d98a" if pct_ret >= 0 else "#f05252",
     "#f0f2f8", "#f5a623",
     "#22d98a", "#f05252"]):
    with col:
        col.markdown(f'<div class="stat-card"><div class="stat-label">{title}</div><div class="stat-value" style="color:{color};font-size:1.3rem">{value}</div></div>', unsafe_allow_html=True)

st.markdown('<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.73rem;color:#4e5669">Data · Yahoo Finance · Educational purposes only · Not financial advice</div>', unsafe_allow_html=True)
