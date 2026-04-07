"""
StockFin — Live Market Intelligence Platform
Run:  streamlit run app.py

CHANGES IN THIS VERSION
────────────────────────
• App name everywhere → StockFin
• Sidebar collapse no longer leaves a black empty space — main content
  expands to fill full width automatically
• Wide gaps between every chart/section (chart-gap class + padding)
• Nav items styled with same Syne font as Analytics & Portfolio page titles
• Analytics and Portfolio added as nav items in sidebar
• Portfolio "Add Holding" form fixed (unique form key to avoid key collision
  when app.py runs alongside pages/)
• All pages reachable from one sidebar
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import time

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

# ═══════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════════════

def _gap(size: str = "lg") -> None:
    """Render a vertical spacer between sections / charts."""
    px_map = {"sm": ".8rem", "md": "1.4rem", "lg": "2.2rem", "xl": "3rem"}
    st.markdown(f"<div style='height:{px_map.get(size,size)}'></div>", unsafe_allow_html=True)

def _divider() -> None:
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,.06);margin:1.8rem 0'>",
                unsafe_allow_html=True)

def _section(title: str, sub: str = "") -> None:
    sub_html = f'<div style="font-size:.78rem;color:#8892a4;margin-top:.2rem">{sub}</div>' if sub else ""
    st.markdown(
        f'<div style="font-family:\'Syne\',sans-serif;font-size:1.55rem;font-weight:800;'
        f'color:#f0f2f8;padding:.4rem 0 .1rem">{title}</div>{sub_html}',
        unsafe_allow_html=True
    )

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
    g_ = delta.where(delta > 0, 0.0).rolling(14).mean()
    l_ = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df["RSI"]     = (100 - 100 / (1 + g_ / l_.replace(0, np.nan))).fillna(50)
    df["BB_M"]    = df["Close"].rolling(20).mean()
    s_            = df["Close"].rolling(20).std()
    df["BB_U"]    = df["BB_M"] + 2 * s_
    df["BB_L"]    = df["BB_M"] - 2 * s_
    e1 = df["Close"].ewm(span=12, adjust=False).mean()
    e2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]    = e1 - e2
    df["MACD_sig"]= df["MACD"].ewm(span=9, adjust=False).mean()
    return df


# ═══════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "MSFT", "GOOGL", "NVDA"]
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# Portfolio state (for the in-app Portfolio page)
import json, os
PORTFOLIO_FILE = str(pathlib.Path(__file__).parent / "data" / "portfolio_data.json")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}

def _save_portfolio() -> None:
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(st.session_state.portfolio, f, indent=2)

def _load_portfolio() -> None:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            st.session_state.portfolio = json.load(f)

_load_portfolio()


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
NAV_PAGES = [
    "Dashboard",
    "Watchlist & Alerts",
    "Sector Heatmap",
    "Analytics",
    "Portfolio",
    "Backtesting",
    "Options Chain",
]

with st.sidebar:
    # Brand header
    st.markdown("""
    <div style="padding:.6rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;
          background:linear-gradient(135deg,#4f8fff,#7c6ff7);
          border-radius:10px;display:flex;align-items:center;justify-content:center;
          font-family:'Syne',sans-serif;font-size:1rem;font-weight:800;color:white">S</div>
        <div>
          <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:1.05rem;
            color:#f0f2f8;letter-spacing:-.01em">StockFin</div>
          <span class="live-dot" style="font-size:.62rem">LIVE</span>
        </div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.1rem 0 .5rem">
    """, unsafe_allow_html=True)

    page = st.radio("Navigate", NAV_PAGES, label_visibility="collapsed")

    _divider()

    DEFAULT_STOCKS = {
        "Apple (AAPL)":     "AAPL",
        "Tesla (TSLA)":     "TSLA",
        "Microsoft (MSFT)": "MSFT",
        "Google (GOOGL)":   "GOOGL",
        "NVIDIA (NVDA)":    "NVDA",
        "Meta (META)":      "META",
        "Amazon (AMZN)":    "AMZN",
        "Netflix (NFLX)":   "NFLX",
    }
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;'
                'text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .3rem">Select Stocks</div>',
                unsafe_allow_html=True)
    selected_stocks = [sym for name, sym in DEFAULT_STOCKS.items()
                       if st.checkbox(name, value=(sym in ["AAPL", "TSLA", "MSFT"]))]

    custom = st.text_input("Custom symbol", placeholder="INFY.NS, BTC-USD…")
    if custom and st.button("Add Symbol", use_container_width=True):
        s = custom.upper().strip()
        if s not in selected_stocks:
            selected_stocks.append(s)

    chart_period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=0)
    total_inv    = st.number_input("Initial Investment ($)", value=10_000, step=1_000, min_value=0)

    # Portfolio quick-add (only shown when Portfolio page is active)
    if page == "Portfolio":
        _divider()
        st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;'
                    'text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .3rem">Add Holding</div>',
                    unsafe_allow_html=True)
        # KEY FIX: unique form key "pf_add_main" avoids collision with pages/2_Portfolio.py
        with st.form("pf_add_main", clear_on_submit=True):
            pf_sym   = st.text_input("Symbol", placeholder="AAPL…")
            pf_shrs  = st.number_input("Shares", min_value=0.01, step=0.01, value=1.0)
            pf_bp    = st.number_input("Buy Price ($)", min_value=0.01, step=0.01, value=100.0)
            pf_date  = st.date_input("Date", datetime.now())
            if st.form_submit_button("Add Holding", use_container_width=True):
                if pf_sym and pf_shrs > 0 and pf_bp > 0:
                    st.session_state.portfolio["holdings"].append({
                        "symbol":   pf_sym.upper().strip(),
                        "shares":   pf_shrs,
                        "buy_price": pf_bp,
                        "buy_date":  pf_date.strftime("%Y-%m-%d"),
                    })
                    _save_portfolio()
                    st.success(f"Added {pf_shrs} × {pf_sym.upper()}")
                    st.rerun()

        cash_in = st.number_input(
            "Cash Balance ($)",
            value=float(st.session_state.portfolio["cash_balance"]),
            step=100.0
        )
        if cash_in != st.session_state.portfolio["cash_balance"]:
            st.session_state.portfolio["cash_balance"] = cash_in
            _save_portfolio(); st.rerun()

        if st.button("Reset Portfolio", use_container_width=True):
            st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}
            _save_portfolio(); st.rerun()

    _divider()
    if st.button("Refresh All Data", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown('<div style="font-size:.7rem;color:#4e5669;padding:.2rem .4rem">'
                'StockFin · Data by Yahoo Finance · ~60s cache</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════
if page == "Dashboard":
    h1, h2, h3 = st.columns([3, 1.4, .8])
    with h1:
        _section("Live Market Dashboard", "Real-time prices, charts &amp; technical signals")
    with h2:
        st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border);'
                    f'border-radius:10px;padding:.55rem 1rem;text-align:center;margin-top:.7rem">'
                    f'<div style="font-size:.65rem;color:#4e5669;text-transform:uppercase">Last Update</div>'
                    f'<div style="font-size:.82rem;font-weight:600;color:#f0f2f8">'
                    f'{datetime.now().strftime("%b %d  %H:%M")}</div></div>', unsafe_allow_html=True)
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

    # ── Market Overview ticker grid ──────────────────────────────────────────
    _gap("md")
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;'
                'text-transform:uppercase;color:#4e5669;margin-bottom:.5rem">Market Overview</div>',
                unsafe_allow_html=True)
    cols = st.columns(min(4, len(stocks)))
    for i, (sym, d) in enumerate(list(stocks.items())[:8]):
        with cols[i % len(cols)]:
            up = d["change"] >= 0
            st.markdown(
                f'<div class="ticker-card">'
                f'<div class="ticker-sym">{sym}</div>'
                f'<div class="ticker-price">${d["price"]:.2f}</div>'
                f'<div class="ticker-chg {"up" if up else "down"}">'
                f'{"+" if up else ""}{d["change_pct"]:.2f}%</div></div>',
                unsafe_allow_html=True
            )

    # ── Detailed analysis ────────────────────────────────────────────────────
    _gap("xl")
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;'
                'text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Detailed Analysis</div>',
                unsafe_allow_html=True)
    sel = st.selectbox("Symbol", list(stocks.keys()), label_visibility="collapsed")

    if sel:
        d    = stocks[sel]
        hist = add_indicators(d["history"])
        tab1, tab2, tab3, tab4 = st.tabs(["Chart", "Indicators", "Company", "Alerts"])

        with tab1:
            _gap("sm")
            fig = make_subplots(
                rows=3, cols=1, shared_xaxes=True, vertical_spacing=.06,
                row_heights=[.6, .2, .2],
                subplot_titles=("Price & Bollinger Bands", "Volume", "RSI (14)")
            )
            fig.add_trace(go.Candlestick(
                x=hist.index, open=hist.Open, high=hist.High,
                low=hist.Low, close=hist.Close, name="Price",
                increasing_line_color="#22d98a", decreasing_line_color="#f05252"
            ), row=1, col=1)
            for c, lbl, col, dash in [
                ("MA20","MA20","#f5a623","solid"), ("MA50","MA50","#7c6ff7","solid"),
                ("BB_U","BB+","rgba(255,255,255,.2)","dot"), ("BB_L","BB−","rgba(255,255,255,.2)","dot"),
            ]:
                fig.add_trace(go.Scatter(x=hist.index, y=hist[c], name=lbl,
                                         line=dict(color=col, width=1, dash=dash)), row=1, col=1)
            bc = ["#22d98a" if hist.Close.iloc[i] >= hist.Open.iloc[i] else "#f05252"
                  for i in range(len(hist))]
            fig.add_trace(go.Bar(x=hist.index, y=hist.Volume, name="Vol",
                                  marker_color=bc, opacity=.7), row=2, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.RSI, name="RSI",
                                      line=dict(color="#4f8fff", width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=.5, row=3, col=1)
            fig.update_layout(height=660, showlegend=True, xaxis_rangeslider_visible=False,
                              title=f"{sel} — Technical Chart",
                              title_font=dict(family="Syne", size=14, color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            _gap("sm")
            rsi_v = float(hist.RSI.iloc[-1])
            rsi_s = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
            rc    = "#f05252" if rsi_v > 70 else "#22d98a" if rsi_v < 30 else "#f5a623"
            macd_bull = float(hist.MACD.iloc[-1]) > float(hist.MACD_sig.iloc[-1])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="glass-card"><h4>Key Statistics</h4><table style="width:100%">
                <tr><td>Price</td><td><strong>${d['price']:.2f}</strong></td></tr>
                <tr><td>Open</td><td>${d['open']:.2f}</td></tr>
                <tr><td>High</td><td>${d['high']:.2f}</td></tr>
                <tr><td>Low</td><td>${d['low']:.2f}</td></tr>
                <tr><td>Volume</td><td>{d['volume']:,.0f}</td></tr>
                <tr><td>Change</td><td style="color:{'#22d98a' if d['change']>=0 else '#f05252'}">
                {d['change']:+.2f} ({d['change_pct']:+.2f}%)</td></tr>
                </table></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class="glass-card"><h4>Technical Signals</h4><table style="width:100%">
                <tr><td>RSI 14</td><td><strong style="color:{rc}">{rsi_v:.1f} — {rsi_s}</strong></td></tr>
                <tr><td>MACD</td><td><strong style="color:{'#22d98a' if macd_bull else '#f05252'}">
                {'Bullish' if macd_bull else 'Bearish'}</strong></td></tr>
                <tr><td>MA20</td><td>${hist.MA20.iloc[-1]:.2f}</td></tr>
                <tr><td>MA50</td><td>${hist.MA50.iloc[-1]:.2f}</td></tr>
                <tr><td>BB Upper</td><td>${hist.BB_U.iloc[-1]:.2f}</td></tr>
                <tr><td>BB Lower</td><td>${hist.BB_L.iloc[-1]:.2f}</td></tr>
                </table></div>""", unsafe_allow_html=True)
            _gap()
            # MA chart
            fig2 = go.Figure()
            for c_, lbl_, col_ in [("Close","Price","#4f8fff"),("MA20","MA20","#f5a623"),("MA50","MA50","#7c6ff7")]:
                fig2.add_trace(go.Scatter(x=hist.index, y=hist[c_], name=lbl_,
                                          line=dict(color=col_, width=1.8 if c_=="Close" else 1.2)))
            fig2.update_layout(height=300, title="Price vs Moving Averages",
                               title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

        with tab3:
            _gap("sm")
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
                <tr><td>Website</td><td><a href="{info.get('website','#')}" target="_blank"
                style="color:#4f8fff">{info.get('website','N/A')}</a></td></tr>
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
            _gap("sm")
            rsi_v2  = float(hist.RSI.iloc[-1])
            avgvol  = float(hist.Volume.rolling(20).mean().iloc[-1])
            alerts_found = []
            if d["change_pct"] >  3: alerts_found.append(("!", f"<strong>{sel}</strong> surged <strong>+{d['change_pct']:.2f}%</strong>", "#f5a623"))
            if d["change_pct"] < -3: alerts_found.append(("!", f"<strong>{sel}</strong> dropped <strong>{d['change_pct']:.2f}%</strong>", "#f05252"))
            if rsi_v2 > 70: alerts_found.append(("RSI", f"Overbought at <strong>{rsi_v2:.1f}</strong> — pullback zone", "#f05252"))
            if rsi_v2 < 30: alerts_found.append(("RSI", f"Oversold at <strong>{rsi_v2:.1f}</strong> — bounce zone", "#22d98a"))
            if avgvol and d["volume"] > avgvol * 1.5:
                alerts_found.append(("Vol", f"Volume spike: <strong>{d['volume']:,.0f}</strong> vs avg {avgvol:,.0f}", "#4f8fff"))
            bbw = (float(hist.BB_U.iloc[-1]) - float(hist.BB_L.iloc[-1])) / max(float(hist.BB_M.iloc[-1]), 1)
            if bbw < 0.05: alerts_found.append(("BB", "Bollinger squeeze — breakout approaching", "#7c6ff7"))
            if alerts_found:
                for ico, msg, col_ in alerts_found:
                    st.markdown(
                        f'<div style="background:var(--bg-elevated);border:1px solid {col_}33;'
                        f'border-left:3px solid {col_};border-radius:0 8px 8px 0;'
                        f'padding:.8rem 1rem;font-size:.83rem;color:#8892a4;margin-bottom:.5rem">'
                        f'<strong style="color:{col_}">[{ico}]</strong> {msg}</div>',
                        unsafe_allow_html=True
                    )
            else:
                st.markdown('<div style="background:rgba(34,217,138,.07);border:1px solid rgba(34,217,138,.2);'
                            'border-radius:14px;padding:1rem;font-size:.83rem;color:#22d98a">'
                            'No significant alerts at this time</div>', unsafe_allow_html=True)

    # ── Session summary ──────────────────────────────────────────────────────
    _divider()
    gainers = sum(1 for d in stocks.values() if d["change"] >= 0)
    losers  = len(stocks) - gainers
    avg_chg = sum(d["change_pct"] for d in stocks.values()) / max(len(stocks), 1)
    est_ret = total_inv * (1 + avg_chg / 100)
    for col, title, val, icon in zip(
        st.columns(4),
        ["Est. Portfolio", "Avg Change", "Gainers / Losers", "Stocks Tracked"],
        [f"${est_ret:,.2f}", f"{avg_chg:+.2f}%", f"{gainers} up  {losers} dn", str(len(stocks))],
        ["$", "~", "G/L", "#"]
    ):
        color = "#22d98a" if "+" in val and "%" in val else "#f0f2f8"
        col.markdown(
            f'<div class="stat-card"><div class="stat-label">{title} '
            f'<span style="opacity:.5;float:right">{icon}</span></div>'
            f'<div class="stat-value" style="font-size:1.4rem;color:{color}">{val}</div></div>',
            unsafe_allow_html=True
        )


# ═══════════════════════════════════════════════════════════════════
# PAGE: WATCHLIST & ALERTS
# ═══════════════════════════════════════════════════════════════════
elif page == "Watchlist & Alerts":
    _section("Watchlist &amp; Price Alerts", "Track custom symbols and set automated price alerts")
    _gap("md")

    wl_col, al_col = st.columns([1.4, 1])

    with wl_col:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">My Watchlist</div>', unsafe_allow_html=True)
        add_sym = st.text_input("Add symbol", placeholder="AMZN, BABA…", key="wl_add")
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
                    st.markdown(f'<div style="font-weight:600;color:#f0f2f8">{sym}</div>'
                                f'<div style="font-size:.75rem;color:#8892a4">'
                                f'{d["info"].get("longName","")[:30]}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div style="font-size:1.1rem;font-weight:700;color:#f0f2f8">'
                                f'${d["price"]:.2f}</div>'
                                f'<div style="font-size:.75rem;color:{"#22d98a" if up else "#f05252"}">'
                                f'{d["change_pct"]:+.2f}%</div>', unsafe_allow_html=True)
                with c3:
                    if st.button("×", key=f"rm_{sym}"):
                        to_remove.append(sym)
                st.markdown("<hr style='border-color:rgba(255,255,255,.04);margin:.3rem 0'>",
                            unsafe_allow_html=True)
        for s in to_remove:
            st.session_state.watchlist.remove(s)
        if to_remove: st.rerun()

    with al_col:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">Price Alerts</div>', unsafe_allow_html=True)
        with st.form("alert_form"):
            a_sym   = st.text_input("Symbol", placeholder="AAPL")
            a_cond  = st.selectbox("Condition", ["Price Above", "Price Below"])
            a_price = st.number_input("Trigger Price ($)", min_value=0.01, step=0.01, value=150.0)
            if st.form_submit_button("Set Alert", use_container_width=True):
                if a_sym:
                    st.session_state.alerts.append({
                        "symbol": a_sym.upper(), "condition": a_cond,
                        "price": a_price, "triggered": False,
                    })
                    st.success(f"Alert set: {a_sym.upper()} {a_cond} ${a_price:.2f}")

        _gap("sm")
        if st.session_state.alerts:
            for al in st.session_state.alerts:
                curr = get_stock(al["symbol"])
                triggered = False
                if curr:
                    if al["condition"] == "Price Above" and curr["price"] > al["price"]: triggered = True
                    if al["condition"] == "Price Below" and curr["price"] < al["price"]: triggered = True
                color  = "#f05252" if triggered else "#4e5669"
                status = "TRIGGERED" if triggered else "Waiting"
                st.markdown(
                    f'<div style="background:var(--bg-elevated);border:1px solid {color}33;'
                    f'border-left:3px solid {color};border-radius:0 8px 8px 0;'
                    f'padding:.7rem 1rem;font-size:.8rem;margin-bottom:.3rem">'
                    f'<strong style="color:#f0f2f8">{al["symbol"]}</strong> — '
                    f'{al["condition"]} <strong>${al["price"]:.2f}</strong> — '
                    f'<span style="color:{color}">{status}</span></div>',
                    unsafe_allow_html=True
                )
            if st.button("Clear All Alerts"):
                st.session_state.alerts = []; st.rerun()
        else:
            st.info("No alerts set yet.")


# ═══════════════════════════════════════════════════════════════════
# PAGE: SECTOR HEATMAP
# ═══════════════════════════════════════════════════════════════════
elif page == "Sector Heatmap":
    _section("Sector &amp; Market Heatmap", "Real-time performance across all S&P 500 sectors")
    _gap("md")

    SECTOR_ETF = {
        "Technology":"XLK","Healthcare":"XLV","Financials":"XLF",
        "Consumer Disc":"XLY","Industrials":"XLI","Energy":"XLE",
        "Utilities":"XLU","Materials":"XLB","Real Estate":"XLRE","Comm Svcs":"XLC",
    }
    SECTOR_STOCKS = {
        "Technology":   ["AAPL","MSFT","NVDA","AMD","INTC","ORCL","CRM","ADBE"],
        "Healthcare":   ["JNJ","PFE","ABBV","UNH","MRNA","CVS","LLY","BMY"],
        "Financials":   ["JPM","GS","BAC","WFC","MS","C","BLK","AXP"],
        "Consumer Disc":["AMZN","TSLA","HD","MCD","NKE","SBUX","LOW","TJX"],
    }

    tab_etf, tab_stocks = st.tabs(["Sector ETFs", "Individual Stocks"])

    with tab_etf:
        with st.spinner("Fetching sector data…"):
            sector_data = []
            for sec, etf in SECTOR_ETF.items():
                d = get_stock(etf)
                if d: sector_data.append({"Sector": sec, "ETF": etf,
                                           "Price": d["price"], "Change": d["change_pct"]})
        if sector_data:
            df_s = pd.DataFrame(sector_data).sort_values("Change", ascending=False)
            _gap("sm")
            fig  = px.bar(df_s, x="Sector", y="Change", color="Change",
                          color_continuous_scale=["#f05252","#1c2030","#22d98a"],
                          color_continuous_midpoint=0,
                          text=df_s["Change"].apply(lambda x: f"{x:+.2f}%"))
            fig.update_traces(textposition="outside", textfont=dict(color="#f0f2f8", size=11))
            fig.update_layout(height=420, title="Sector ETF Performance (Today)",
                              title_font=dict(family="Syne", size=14, color="#f0f2f8"),
                              showlegend=False, **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

            _gap()
            cols = st.columns(5)
            for idx, (_, row) in enumerate(df_s.iterrows()):
                chg = row["Change"]
                intensity = min(abs(chg) / 5, 1)
                bg = (f"rgba(34,217,138,{0.1+intensity*0.4})" if chg >= 0
                      else f"rgba(240,82,82,{0.1+intensity*0.4})")
                tc = "#22d98a" if chg >= 0 else "#f05252"
                with cols[idx % 5]:
                    st.markdown(
                        f'<div class="heat-cell" style="background:{bg};color:{tc};margin-bottom:.5rem">'
                        f'<div style="font-size:.78rem;color:#f0f2f8;font-weight:600">{row["Sector"]}</div>'
                        f'<div style="font-size:1rem;font-weight:700">{chg:+.2f}%</div>'
                        f'<div style="font-size:.68rem;color:#8892a4">{row["ETF"]}</div></div>',
                        unsafe_allow_html=True
                    )

    with tab_stocks:
        sel_sec = st.selectbox("Select Sector", list(SECTOR_STOCKS.keys()))
        with st.spinner(f"Fetching {sel_sec}…"):
            sdata = [(s, get_stock(s)) for s in SECTOR_STOCKS[sel_sec]]
        sdata = [(s, d) for s, d in sdata if d]
        if sdata:
            _gap("sm")
            labels = [s for s, _ in sdata]
            values = [d["change_pct"] for _, d in sdata]
            fig2   = go.Figure(go.Treemap(
                labels=labels, parents=[""] * len(labels),
                values=[abs(v) + 2 for v in values],
                customdata=[[d["price"], v] for (_, d), v in zip(sdata, values)],
                hovertemplate="<b>%{label}</b><br>Price: $%{customdata[0]:.2f}<br>Change: %{customdata[1]:+.2f}%<extra></extra>",
                marker=dict(colors=values,
                            colorscale=[[0,"#f05252"],[0.5,"#1c2030"],[1,"#22d98a"]],
                            cmid=0, line=dict(width=2, color="#0d0f14")),
                texttemplate="<b>%{label}</b><br>%{customdata[1]:+.1f}%",
                textfont=dict(color="#f0f2f8", size=13),
            ))
            fig2.update_layout(height=420, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS (inline — mirrors pages/1_Analytics.py structure)
# ═══════════════════════════════════════════════════════════════════
elif page == "Analytics":
    _section("Advanced Analytics", "Technical indicators · Risk metrics · ML predictions · Benchmark")
    _gap("md")

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1: an_sym   = st.text_input("Symbol", "AAPL", key="an_sym").upper().strip()
    with ac2: an_period= st.selectbox("Period", ["6mo","1y","2y","3y","5y"], index=1, key="an_period")
    with ac3: an_bench = st.text_input("Benchmark", "SPY", key="an_bench").upper().strip()
    with ac4: an_strat = st.selectbox("Chart Type", ["Candlestick","Line"], key="an_strat")

    if an_sym:
        with st.spinner(f"Fetching {an_sym}…"):
            an_data = get_stock(an_sym)

        if an_data is None:
            st.error(f"Could not fetch {an_sym}."); st.stop()

        hist = add_indicators(an_data["history"])
        cur  = an_data["price"]
        chgp = an_data["change_pct"]

        # Metrics row
        _gap("sm")
        for col_, lbl_, val_, d_ in zip(
            st.columns(5),
            ["Price","Volume","Day High","Day Low","Change"],
            [f"${cur:.2f}", f"{an_data['volume']:,.0f}",
             f"${an_data['high']:.2f}", f"${an_data['low']:.2f}", f"{chgp:+.2f}%"],
            [f"{chgp:+.2f}%", None, None, None, None]
        ):
            with col_: st.metric(lbl_, val_, d_)

        _gap()
        an_tab1, an_tab2 = st.tabs(["Technical Chart", "Key Metrics"])

        with an_tab1:
            _gap("sm")
            fig = make_subplots(
                rows=4, cols=1, shared_xaxes=True, vertical_spacing=.06,
                row_heights=[.45, .2, .18, .17],
                subplot_titles=("Price", "Volume", "RSI (14)", "MACD")
            )
            if an_strat == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist.Open, high=hist.High,
                    low=hist.Low, close=hist.Close, name="Price",
                    increasing_line_color="#22d98a", decreasing_line_color="#f05252"
                ), row=1, col=1)
            else:
                fig.add_trace(go.Scatter(x=hist.index, y=hist.Close, name="Price",
                                          line=dict(color="#4f8fff", width=2)), row=1, col=1)
            for c_, lbl_, col_, dash_ in [
                ("MA20","MA20","#f5a623","solid"),("MA50","MA50","#7c6ff7","solid"),
                ("BB_U","BB+","rgba(255,255,255,.2)","dot"),("BB_L","BB−","rgba(255,255,255,.2)","dot"),
            ]:
                fig.add_trace(go.Scatter(x=hist.index, y=hist[c_], name=lbl_,
                                          line=dict(color=col_, width=1, dash=dash_)), row=1, col=1)
            bc = ["#22d98a" if hist.Close.iloc[i] >= hist.Open.iloc[i] else "#f05252"
                  for i in range(len(hist))]
            fig.add_trace(go.Bar(x=hist.index, y=hist.Volume, marker_color=bc, opacity=.7, name="Vol"),
                          row=2, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.RSI, name="RSI",
                                      line=dict(color="#4f8fff", width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=.5, row=3, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.MACD, name="MACD",
                                      line=dict(color="#4f8fff", width=1.2)), row=4, col=1)
            fig.add_trace(go.Scatter(x=hist.index, y=hist.MACD_sig, name="Signal",
                                      line=dict(color="#f5a623", width=1.2)), row=4, col=1)
            fig.update_layout(height=780, showlegend=True, xaxis_rangeslider_visible=False,
                              title=f"{an_sym} — Technical Dashboard",
                              title_font=dict(family="Syne", size=14, color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with an_tab2:
            _gap("sm")
            r_ = hist.Close.pct_change().dropna()
            ar = r_.mean() * 252 * 100
            av = r_.std() * np.sqrt(252) * 100
            sr = ar / av if av else 0
            cum = (1 + r_).cumprod()
            mdd = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100

            m1, m2, m3, m4 = st.columns(4)
            for col_, lbl_, val_ in [
                (m1,"Annual Return",f"{ar:+.1f}%"),
                (m2,"Volatility",f"{av:.1f}%"),
                (m3,"Sharpe Ratio",f"{sr:.2f}"),
                (m4,"Max Drawdown",f"{mdd:.1f}%"),
            ]:
                col_.markdown(f'<div class="metric-box"><h4>{lbl_}</h4><h2>{val_}</h2></div>',
                              unsafe_allow_html=True)

            _gap()
            rsi_v = float(hist.RSI.iloc[-1])
            rsi_s = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
            rc_   = "#f05252" if rsi_v > 70 else "#22d98a" if rsi_v < 30 else "#f5a623"
            st.markdown(
                f'<div class="glass-card"><h4>Quick Signal Summary</h4>'
                f'<table style="width:100%">'
                f'<tr><td>RSI (14)</td><td><strong style="color:{rc_}">{rsi_v:.1f} — {rsi_s}</strong></td></tr>'
                f'<tr><td>MACD</td><td><strong style="color:{"#22d98a" if hist.MACD.iloc[-1]>hist.MACD_sig.iloc[-1] else "#f05252"}">'
                f'{"Bullish" if hist.MACD.iloc[-1]>hist.MACD_sig.iloc[-1] else "Bearish"}</strong></td></tr>'
                f'<tr><td>Price vs MA20</td><td>{"Above" if cur>hist.MA20.iloc[-1] else "Below"} (${hist.MA20.iloc[-1]:.2f})</td></tr>'
                f'<tr><td>Price vs MA50</td><td>{"Above" if cur>hist.MA50.iloc[-1] else "Below"} (${hist.MA50.iloc[-1]:.2f})</td></tr>'
                f'</table></div>',
                unsafe_allow_html=True
            )


# ═══════════════════════════════════════════════════════════════════
# PAGE: PORTFOLIO
# ═══════════════════════════════════════════════════════════════════
elif page == "Portfolio":
    _section("Portfolio Tracker", "Real-time P&amp;L · Allocation · Risk overview")
    _gap("md")

    @st.cache_data(ttl=60)
    def _pf_price(sym: str) -> float | None:
        try: return float(yf.Ticker(sym).history(period="1d")["Close"].iloc[-1])
        except: return None

    def _calc_portfolio(holdings: list) -> tuple:
        cash = st.session_state.portfolio["cash_balance"]
        tv, ti, rows = cash, 0.0, []
        for h in holdings:
            p = _pf_price(h["symbol"])
            if not p: continue
            cur = h["shares"] * p; inv = h["shares"] * h["buy_price"]; pnl = cur - inv
            rows.append({**h, "current_price": p, "current_value": cur,
                         "invested": inv, "pnl": pnl,
                         "pnl_pct": (pnl / inv * 100) if inv else 0, "allocation": 0})
            tv += cur; ti += inv
        for r in rows:
            r["allocation"] = (r["current_value"] / tv * 100) if tv else 0
        base = ti + cash; total_pnl = tv - base
        return rows, tv, total_pnl, (total_pnl / base * 100) if base else 0

    holdings = st.session_state.portfolio["holdings"]

    if not holdings:
        st.markdown("""
        <div style="background:#13161e;border:1px dashed rgba(255,255,255,.12);
            border-radius:20px;padding:3rem 2rem;text-align:center;margin-top:1rem">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8">
                Portfolio is empty</div>
            <div style="font-size:.84rem;color:#8892a4;margin-top:.4rem">
                Use the sidebar Add Holding form to get started</div>
        </div>""", unsafe_allow_html=True)
    else:
        metrics, tv, total_pnl, total_pnl_pct = _calc_portfolio(holdings)
        ti_ = sum(m["invested"] for m in metrics)
        pnl_color = "#22d98a" if total_pnl >= 0 else "#f05252"
        pnl_arrow = "▲" if total_pnl >= 0 else "▼"

        # Stat cards
        for col_, lbl_, val_, color_ in zip(
            st.columns(4),
            ["Total Value", "Total P&L", "Total Invested", "Cash Balance"],
            [f"${tv:,.2f}",
             f"{pnl_arrow} ${abs(total_pnl):,.2f} ({total_pnl_pct:+.2f}%)",
             f"${ti_:,.2f}",
             f"${st.session_state.portfolio['cash_balance']:,.2f}"],
            ["#4f8fff", pnl_color, "#f5a623", "#22d98a"]
        ):
            with col_:
                st.markdown(
                    f'<div class="stat-card"><div class="stat-label">{lbl_}</div>'
                    f'<div class="stat-value" style="color:{color_};font-size:1.4rem">{val_}</div></div>',
                    unsafe_allow_html=True
                )

        _gap("xl")

        # Charts
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                        'color:#f0f2f8;margin-bottom:.5rem">Portfolio Allocation</div>', unsafe_allow_html=True)
            alloc_df = pd.DataFrame([{"Symbol": m["symbol"], "Allocation": m["allocation"]}
                                      for m in metrics if m["allocation"] > 0])
            if not alloc_df.empty:
                fig_pie = px.pie(alloc_df, values="Allocation", names="Symbol", hole=0.55,
                                  color_discrete_sequence=["#4f8fff","#7c6ff7","#22d98a","#f5a623","#f05252","#ec4899"])
                fig_pie.update_traces(textfont=dict(size=10, color="#000000"),
                                      marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)))
                fig_pie.update_layout(height=300, **DARK_LAYOUT)
                st.plotly_chart(fig_pie, use_container_width=True)

        with cc2:
            st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                        'color:#f0f2f8;margin-bottom:.5rem">P&amp;L by Stock (%)</div>', unsafe_allow_html=True)
            pf_df = pd.DataFrame([{"Symbol": m["symbol"], "Return %": m["pnl_pct"]} for m in metrics])
            colors_ = ["#22d98a" if x >= 0 else "#f05252" for x in pf_df["Return %"]]
            fig_bar = go.Figure(go.Bar(x=pf_df["Symbol"], y=pf_df["Return %"],
                                       marker_color=colors_, marker_line_width=0))
            fig_bar.update_layout(height=300, yaxis_title="Return (%)", **DARK_LAYOUT)
            st.plotly_chart(fig_bar, use_container_width=True)

        _gap("xl")

        # Holdings table
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                    'color:#f0f2f8;margin-bottom:.5rem">Holdings</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
            font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
            color:#4e5669;padding:.4rem .5rem;border-bottom:1px solid rgba(255,255,255,.06)">
            <span>Symbol</span><span>Shares</span><span>Buy $</span><span>Now $</span>
            <span>Invested</span><span>Value</span><span>P&L $</span><span>P&L %</span><span>Alloc</span>
        </div>""", unsafe_allow_html=True)
        for m in metrics:
            cls_ = "up" if m["pnl"] >= 0 else "down"
            st.markdown(f"""
            <div class="holding-row" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
                font-size:.8rem;align-items:center">
                <span style="font-weight:600;color:#f0f2f8">{m['symbol']}</span>
                <span style="color:#8892a4">{m['shares']:.2f}</span>
                <span style="color:#8892a4">${m['buy_price']:.2f}</span>
                <span style="color:#f0f2f8">${m['current_price']:.2f}</span>
                <span style="color:#8892a4">${m['invested']:,.0f}</span>
                <span style="color:#f0f2f8">${m['current_value']:,.0f}</span>
                <span class="{cls_}">${m['pnl']:,.0f}</span>
                <span class="{cls_}">{m['pnl_pct']:+.1f}%</span>
                <span style="color:#8892a4">{m['allocation']:.1f}%</span>
            </div>""", unsafe_allow_html=True)

        _gap("xl")

        # Allocation bars
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                    'color:#f0f2f8;margin-bottom:.5rem">Allocation Breakdown</div>', unsafe_allow_html=True)
        for m in sorted(metrics, key=lambda x: x["allocation"], reverse=True)[:8]:
            st.markdown(f"""
            <div style="margin-bottom:.7rem">
                <div style="display:flex;justify-content:space-between;margin-bottom:.2rem">
                    <span style="font-size:.8rem;font-weight:600;color:#f0f2f8">{m['symbol']}</span>
                    <span style="font-size:.78rem;color:#8892a4">{m['allocation']:.1f}%</span>
                </div>
                <div class="alloc-bar">
                    <div class="alloc-fill" style="width:{min(m['allocation'],100):.1f}%"></div>
                </div>
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# PAGE: BACKTESTING
# ═══════════════════════════════════════════════════════════════════
elif page == "Backtesting":
    _section("Strategy Backtester", "Test technical strategies against historical data")
    _gap("md")

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1: bt_sym    = st.text_input("Symbol", "AAPL", key="bt_sym")
    with bc2: bt_period = st.selectbox("Period", ["1y","2y","3y","5y"], index=1)
    with bc3: bt_strat  = st.selectbox("Strategy", ["SMA Crossover","RSI Mean Reversion","MACD Signal","Bollinger Reversion"])
    with bc4: bt_capital= st.number_input("Capital ($)", value=10_000, step=1_000)

    _gap("sm")
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

    _gap("sm")
    if st.button("Run Backtest", type="primary"):
        with st.spinner("Running backtest…"):
            @st.cache_data(ttl=3600)
            def _get_hist(sym, period):
                return yf.Ticker(sym).history(period=period)

            bt_df = _get_hist(bt_sym.upper(), bt_period)
            if bt_df is None or bt_df.empty:
                st.error("Could not fetch data."); st.stop()

            bt_df = bt_df.copy()
            bt_df["ret"] = bt_df["Close"].pct_change()

            if bt_strat == "SMA Crossover":
                bt_df["fast"]   = bt_df["Close"].rolling(fast).mean()
                bt_df["slow"]   = bt_df["Close"].rolling(slow).mean()
                bt_df["signal"] = np.where(bt_df["fast"] > bt_df["slow"], 1, -1)
            elif bt_strat == "RSI Mean Reversion":
                delta_ = bt_df["Close"].diff()
                g_ = delta_.where(delta_ > 0, 0).rolling(14).mean()
                l_ = (-delta_.where(delta_ < 0, 0)).rolling(14).mean()
                rsi_ = (100 - 100 / (1 + g_ / l_.replace(0, np.nan))).fillna(50)
                bt_df["signal"] = np.where(rsi_ < rsi_lo, 1, np.where(rsi_ > rsi_hi, -1, 0))
                bt_df["signal"] = bt_df["signal"].replace(0, np.nan).ffill().fillna(0)
            elif bt_strat == "MACD Signal":
                e1_ = bt_df["Close"].ewm(span=12, adjust=False).mean()
                e2_ = bt_df["Close"].ewm(span=26, adjust=False).mean()
                macd_ = e1_ - e2_
                sig_  = macd_.ewm(span=9, adjust=False).mean()
                bt_df["signal"] = np.where(macd_ > sig_, 1, -1)
            else:
                m_ = bt_df["Close"].rolling(bb_period).mean()
                s_ = bt_df["Close"].rolling(bb_period).std()
                bt_df["signal"] = np.where(bt_df["Close"] < m_ - 2*s_, 1,
                                           np.where(bt_df["Close"] > m_ + 2*s_, -1, 0))
                bt_df["signal"] = bt_df["signal"].replace(0, np.nan).ffill().fillna(0)

            bt_df["strat_ret"] = bt_df["signal"].shift(1) * bt_df["ret"]
            bt_df["buy_hold"]  = (1 + bt_df["ret"]).cumprod() * bt_capital
            bt_df["strategy"]  = (1 + bt_df["strat_ret"].fillna(0)).cumprod() * bt_capital
            bt_df = bt_df.dropna(subset=["buy_hold","strategy"])

            final_s = float(bt_df["strategy"].iloc[-1])
            final_b = float(bt_df["buy_hold"].iloc[-1])
            total_r = (final_s / bt_capital - 1) * 100
            bh_r    = (final_b / bt_capital - 1) * 100
            rets_s  = bt_df["strat_ret"].dropna()
            sharpe  = (rets_s.mean() / rets_s.std() * np.sqrt(252)) if rets_s.std() > 0 else 0
            cum     = bt_df["strategy"] / bt_capital
            mdd     = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100
            n_trades= int(bt_df["signal"].diff().abs().sum() // 2)

        _gap("md")
        m1, m2, m3, m4, m5 = st.columns(5)
        for col_, lbl_, val_, color_ in [
            (m1,"Final Value",     f"${final_s:,.0f}",   "#4f8fff"),
            (m2,"Strategy Return", f"{total_r:+.1f}%",   "#22d98a" if total_r > 0 else "#f05252"),
            (m3,"Buy & Hold",      f"{bh_r:+.1f}%",      "#f5a623"),
            (m4,"Sharpe Ratio",    f"{sharpe:.2f}",       "#7c6ff7"),
            (m5,"Max Drawdown",    f"{mdd:.1f}%",         "#f05252"),
        ]:
            col_.markdown(f'<div class="metric-box"><h4>{lbl_}</h4>'
                          f'<h2 style="color:{color_}">{val_}</h2></div>', unsafe_allow_html=True)

        alpha_txt = f"{total_r - bh_r:+.1f}%"
        alpha_col = "#22d98a" if total_r > bh_r else "#f05252"
        st.markdown(f'<div style="margin:.6rem 0;font-size:.8rem;color:#8892a4">'
                    f'Trades: <strong style="color:#f0f2f8">{n_trades}</strong> &nbsp;·&nbsp; '
                    f'Alpha vs B&H: <strong style="color:{alpha_col}">{alpha_txt}</strong></div>',
                    unsafe_allow_html=True)

        _gap()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bt_df.index, y=bt_df["strategy"], name=bt_strat,
                                 line=dict(color="#4f8fff", width=2)))
        fig.add_trace(go.Scatter(x=bt_df.index, y=bt_df["buy_hold"], name="Buy & Hold",
                                 line=dict(color="#8892a4", width=1.5, dash="dot")))
        fig.update_layout(height=420, title=f"{bt_sym.upper()} — {bt_strat} vs Buy & Hold",
                          title_font=dict(family="Syne", size=14, color="#f0f2f8"),
                          yaxis_title="Portfolio Value ($)", **DARK_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)

        export_df = bt_df[["Close","signal","strat_ret","strategy","buy_hold"]].round(4)
        st.download_button("Export Backtest CSV",
                           export_df.to_csv().encode(),
                           file_name=f"backtest_{bt_sym}_{bt_strat.replace(' ','_')}.csv",
                           mime="text/csv")


# ═══════════════════════════════════════════════════════════════════
# PAGE: OPTIONS CHAIN
# ═══════════════════════════════════════════════════════════════════
elif page == "Options Chain":
    _section("Options Chain Viewer", "Live calls &amp; puts data with IV smile visualisation")
    _gap("md")

    oc1, oc2, oc3 = st.columns([1.5, 1, 1])
    with oc1: opt_sym  = st.text_input("Symbol", "AAPL", key="opt_sym")
    with oc2: opt_type = st.selectbox("Type", ["Calls","Puts","Both"])

    _gap("sm")
    if st.button("Load Options Chain", type="primary"):
        with st.spinner("Fetching options…"):
            try:
                t    = yf.Ticker(opt_sym.upper())
                exps = t.options
                if not exps:
                    st.error("No options data available."); st.stop()

                with oc3:
                    exp_sel = st.selectbox("Expiry", exps)

                chain = t.option_chain(exp_sel)
                cp    = (get_stock(opt_sym.upper()) or {}).get("price", 0)

                st.markdown(f'<div style="font-size:.82rem;color:#8892a4;margin-bottom:.6rem">'
                            f'Current Price: <strong style="color:#f0f2f8">${cp:.2f}</strong>'
                            f' &nbsp;·&nbsp; Expiry: <strong style="color:#f0f2f8">{exp_sel}</strong></div>',
                            unsafe_allow_html=True)

                def style_chain(df_opt: pd.DataFrame) -> pd.DataFrame:
                    cols = ["strike","lastPrice","bid","ask","volume","openInterest","impliedVolatility","inTheMoney"]
                    df_opt = df_opt[[c for c in cols if c in df_opt.columns]].copy()
                    df_opt["impliedVolatility"] = (df_opt.get("impliedVolatility", 0) * 100).round(1).astype(str) + "%"
                    df_opt["inTheMoney"] = df_opt.get("inTheMoney", False).map({True:"ITM", False:"—"})
                    return df_opt

                _gap("sm")
                if opt_type in ("Calls","Both"):
                    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;'
                                'font-weight:700;color:#22d98a;margin-bottom:.4rem">Calls</div>',
                                unsafe_allow_html=True)
                    st.dataframe(style_chain(chain.calls), use_container_width=True, hide_index=True)

                _gap("md")
                if opt_type in ("Puts","Both"):
                    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;'
                                'font-weight:700;color:#f05252;margin-bottom:.4rem">Puts</div>',
                                unsafe_allow_html=True)
                    st.dataframe(style_chain(chain.puts), use_container_width=True, hide_index=True)

                _gap("xl")
                fig_iv = go.Figure()
                if opt_type in ("Calls","Both"):
                    c_iv = chain.calls[["strike","impliedVolatility"]].dropna()
                    fig_iv.add_trace(go.Scatter(x=c_iv.strike, y=c_iv.impliedVolatility * 100,
                                                name="Calls IV", line=dict(color="#22d98a", width=2)))
                if opt_type in ("Puts","Both"):
                    p_iv = chain.puts[["strike","impliedVolatility"]].dropna()
                    fig_iv.add_trace(go.Scatter(x=p_iv.strike, y=p_iv.impliedVolatility * 100,
                                                name="Puts IV", line=dict(color="#f05252", width=2)))
                if cp:
                    fig_iv.add_vline(x=cp, line_dash="dot", line_color="#f5a623",
                                     annotation_text=f"Spot ${cp:.0f}",
                                     annotation_font=dict(color="#f5a623"))
                fig_iv.update_layout(height=360, title="Implied Volatility Smile",
                                     title_font=dict(family="Syne", size=14, color="#f0f2f8"),
                                     xaxis_title="Strike", yaxis_title="IV %", **DARK_LAYOUT)
                st.plotly_chart(fig_iv, use_container_width=True)

            except Exception as e:
                st.error(f"Options fetch error: {e}")


# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════
_divider()
st.markdown(
    '<div style="text-align:center;padding:.6rem 0 .4rem;font-size:.72rem;color:#4e5669">'
    'StockFin &nbsp;·&nbsp; Data by Yahoo Finance &nbsp;·&nbsp; For educational purposes only &nbsp;·&nbsp; Not financial advice'
    '</div>',
    unsafe_allow_html=True
)
