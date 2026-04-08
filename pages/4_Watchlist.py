"""
Watchlist & Price Alerts  ·  pages/5_Watchlist.py
Live watchlist with configurable price alerts and notifications.
DO NOT call st.set_page_config() here — it lives only in app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import time

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{--bg-base:#0d0f14;--bg-card:#13161e;--bg-elevated:#1c2030;
    --border:rgba(255,255,255,.07);--border-active:rgba(255,255,255,.14);
    --accent-blue:#4f8fff;--accent-violet:#7c6ff7;--accent-green:#22d98a;
    --accent-red:#f05252;--accent-amber:#f5a623;
    --text-primary:#f0f2f8;--text-secondary:#8892a4;--text-muted:#4e5669;
    --radius-sm:8px;--radius-md:14px;--radius-lg:20px;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--text-primary)!important;}
.stApp{background:var(--bg-base)!important;}
section[data-testid="stSidebar"]{background:var(--bg-card)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text-secondary)!important;}
#MainMenu,footer,header{visibility:hidden;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--text-primary)!important;}
.stMarkdown p{color:var(--text-secondary);font-size:.84rem;}
.watch-row{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:1rem 1.2rem;margin-bottom:.5rem;display:flex;align-items:center;
    justify-content:space-between;transition:border-color .2s;}
.watch-row:hover{border-color:var(--border-active);}
.watch-sym{font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#f0f2f8;}
.watch-name{font-size:.72rem;color:#4e5669;margin-top:1px;}
.watch-price{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;}
.watch-chg{font-size:.75rem;font-weight:600;margin-top:2px;}
.up{color:#22d98a;} .down{color:#f05252;}
.alert-triggered{background:rgba(240,82,82,.08);border-color:rgba(240,82,82,.35)!important;
    border-left:3px solid #f05252!important;}
.alert-triggered-up{background:rgba(34,217,138,.06);border-color:rgba(34,217,138,.3)!important;
    border-left:3px solid #22d98a!important;}
.alert-badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;
    font-size:.68rem;font-weight:600;}
.badge-red{background:rgba(240,82,82,.15);color:#f05252;}
.badge-green{background:rgba(34,217,138,.12);color:#22d98a;}
.badge-blue{background:rgba(79,143,255,.12);color:#4f8fff;}
.badge-amber{background:rgba(245,166,35,.12);color:#f5a623;}
.alert-card{background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:.9rem 1rem;margin-bottom:.4rem;border-left:3px solid;}
.sparkline-wrap{overflow:hidden;border-radius:6px;}
.nav-group{font-size:.62rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text-muted)!important;padding:.5rem .4rem .2rem;}
.nav-item{display:flex;align-items:center;gap:9px;padding:.5rem .8rem;border-radius:var(--radius-sm);
    font-size:.83rem;font-weight:500;color:var(--text-secondary)!important;cursor:pointer;margin:2px 0;}
.nav-item:hover{background:rgba(255,255,255,.05);}
.nav-item.active{background:rgba(79,143,255,.15);color:var(--accent-blue)!important;font-weight:600;}
.live-dot{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;font-weight:600;color:#22d98a;}
.live-dot::before{content:'';width:7px;height:7px;background:#22d98a;border-radius:50%;animation:pdot 2s infinite;}
@keyframes pdot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(1.3);}}
.stButton>button{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;border-radius:var(--radius-sm)!important;font-size:.8rem!important;transition:all .15s!important;}
.stButton>button:hover{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stButton>button[kind="primary"]{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stTextInput>div>div>input,.stNumberInput>div>div>input{background:var(--bg-elevated)!important;
    border:1px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;}
.stSelectbox>div>div{background:var(--bg-elevated)!important;border:1px solid var(--border)!important;
    border-radius:var(--radius-sm)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--bg-card)!important;border-radius:var(--radius-md)!important;
    gap:4px;padding:4px;border:1px solid var(--border)!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--text-secondary)!important;
    border-radius:var(--radius-sm)!important;font-size:.8rem!important;padding:6px 14px!important;}
.stTabs [aria-selected="true"]{background:var(--bg-elevated)!important;color:var(--text-primary)!important;font-weight:600!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:10px;}
</style>
""", unsafe_allow_html=True)

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(28,32,48,0.5)",
    font=dict(family="DM Sans", color="#8892a4", size=10),
    xaxis=dict(gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.05)", showticklabels=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.03)", linecolor="rgba(255,255,255,0.05)"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=4, r=4, t=4, b=4),
)

# ── Session state ─────────────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN"]
if "alerts" not in st.session_state:
    # each alert: {symbol, condition, price, note, triggered}
    st.session_state["alerts"] = []

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem 0.4rem 0.4rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">📈</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;color:#f0f2f8!important">StockFin</div>
                <span class="live-dot" style="font-size:.65rem">LIVE</span>
            </div>
        </div>
        <div class="nav-group">Platform</div>
        <div class="nav-item">⬛ Dashboard</div>
        <div class="nav-group" style="margin-top:.5rem">Pages</div>
        <div class="nav-item">📊 Analytics</div>
        <div class="nav-item">💼 Portfolio</div>
        <div class="nav-item">🤖 ML Predictions</div>
        <div class="nav-item active">🔔 Watchlist & Alerts</div>
        <div class="nav-item">⚙️ Backtesting</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:0.8rem 0">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.3rem .4rem .1rem">Add to Watchlist</div>', unsafe_allow_html=True)
    new_sym = st.text_input("Symbol", placeholder="e.g. GOOG, BTC-USD", label_visibility="collapsed")
    if st.button("➕ Add Symbol", use_container_width=True):
        sym_up = new_sym.upper().strip()
        if sym_up and sym_up not in st.session_state["watchlist"]:
            st.session_state["watchlist"].append(sym_up)
            st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.7rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.3rem .4rem .1rem">Create Alert</div>', unsafe_allow_html=True)
    alert_sym  = st.text_input("Symbol for Alert", placeholder="AAPL", key="al_sym")
    alert_cond = st.selectbox("Condition", ["Price ≥", "Price ≤", "Change% ≥", "Change% ≤", "RSI ≥", "RSI ≤"])
    alert_val  = st.number_input("Threshold", value=0.0, step=0.5, format="%.2f")
    alert_note = st.text_input("Note (optional)", placeholder="Support level breach…", key="al_note")
    if st.button("🔔 Set Alert", use_container_width=True, type="primary"):
        if alert_sym.strip():
            st.session_state["alerts"].append({
                "symbol":    alert_sym.upper().strip(),
                "condition": alert_cond,
                "value":     alert_val,
                "note":      alert_note,
                "triggered": False,
                "created":   datetime.now().strftime("%b %d %H:%M"),
            })
            st.success("Alert set!", icon="🔔")
            st.rerun()

    if st.button("↺ Refresh Prices", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Fetch helpers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_quote(sym: str) -> dict | None:
    try:
        t = yf.Ticker(sym)
        hist = t.history(period="5d", interval="1d")
        intra = t.history(period="1d", interval="5m")
        if hist.empty:
            return None
        price = float(intra["Close"].iloc[-1]) if not intra.empty else float(hist["Close"].iloc[-1])
        prev  = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else float(hist["Open"].iloc[-1])
        chg   = price - prev
        chg_p = (chg / prev * 100) if prev else 0.0
        info  = t.fast_info
        delta = hist["Close"].diff()
        gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rsi_s = 100 - (100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)
        rsi   = float(rsi_s.iloc[-1])
        sparkline = intra["Close"].values.tolist() if not intra.empty else hist["Close"].values.tolist()
        return dict(symbol=sym, price=price, prev=prev, change=chg, change_pct=chg_p, rsi=rsi,
                    sparkline=sparkline, volume=float(hist["Volume"].iloc[-1]),
                    market_cap=getattr(info, "market_cap", 0) or 0,
                    name=t.info.get("shortName", sym))
    except Exception:
        return None

def make_sparkline(values: list, color: str) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=list(range(len(values))), y=values,
        mode="lines", line=dict(color=color, width=1.5),
        fill="tozeroy", fillcolor=color.replace(")", ",0.08)").replace("rgb", "rgba") if "rgb" in color else color + "15",
    ))
    fig.update_layout(height=45, width=120, showlegend=False, **DARK_LAYOUT)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">
        🔔 Watchlist & Price Alerts
    </div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">
        Monitor your symbols and get triggered alerts when conditions are met
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📋 Watchlist", "🔔 Active Alerts"])

# ── Watchlist tab ─────────────────────────────────────────────────────────────
with tab1:
    watchlist = st.session_state["watchlist"]
    if not watchlist:
        st.info("Your watchlist is empty. Add symbols from the sidebar.")
    else:
        with st.spinner("Fetching live quotes…"):
            quotes = {sym: fetch_quote(sym) for sym in watchlist}

        # Summary strip
        total_up   = sum(1 for q in quotes.values() if q and q["change_pct"] >= 0)
        total_down = len([q for q in quotes.values() if q]) - total_up
        avg_chg    = np.mean([q["change_pct"] for q in quotes.values() if q])

        sc1, sc2, sc3 = st.columns(3)
        for col, label, val, cls in [
            (sc1, "Watching",    str(len(watchlist)),   "badge-blue"),
            (sc2, "Advancing",   f"{total_up} symbols", "badge-green"),
            (sc3, "Declining",   f"{total_down} symbols","badge-red"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);
                    padding:.8rem 1rem;text-align:center;">
                    <div style="font-size:.65rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669">{label}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:700;color:#f0f2f8;margin:.2rem 0">{val}</div>
                    <span class="alert-badge {cls}">{'+' if cls=='badge-green' else ''}{avg_chg:.2f}% avg</span>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        # Watchlist rows
        for sym in list(watchlist):
            q = quotes.get(sym)
            if q is None:
                st.markdown(f"""
                <div class="watch-row">
                    <div><div class="watch-sym">{sym}</div>
                    <div class="watch-name">Could not fetch data</div></div>
                </div>
                """, unsafe_allow_html=True)
                continue

            up    = q["change_pct"] >= 0
            color = "#22d98a" if up else "#f05252"
            arrow = "▲" if up else "▼"
            rsi_cls = "badge-red" if q["rsi"] > 70 else "badge-green" if q["rsi"] < 30 else "badge-amber"
            rsi_lbl = "Overbought" if q["rsi"] > 70 else "Oversold" if q["rsi"] < 30 else "Neutral"

            col_info, col_spark, col_stats, col_del = st.columns([3, 2, 3, 1])
            with col_info:
                st.markdown(f"""
                <div style="padding:.6rem 0">
                    <div class="watch-sym">{sym}</div>
                    <div class="watch-name">{q['name'][:30]}</div>
                    <div class="watch-price" style="color:{color}">${q['price']:.2f}</div>
                    <div class="watch-chg {'up' if up else 'down'}">{arrow} {abs(q['change_pct']):.2f}% ({q['change']:+.2f})</div>
                </div>
                """, unsafe_allow_html=True)
            with col_spark:
                spark = make_sparkline(q["sparkline"][-40:], color)
                st.plotly_chart(spark, use_container_width=False, config={"displayModeBar": False})
            with col_stats:
                st.markdown(f"""
                <div style="padding:.6rem 0;font-size:.8rem;color:#8892a4">
                    <div>Vol: <span style="color:#f0f2f8">{q['volume']:,.0f}</span></div>
                    <div>MCap: <span style="color:#f0f2f8">${q['market_cap']:,.0f}</span></div>
                    <div>RSI: <span class="alert-badge {rsi_cls}" style="padding:1px 6px">{q['rsi']:.1f} {rsi_lbl}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with col_del:
                if st.button("✕", key=f"del_{sym}", help=f"Remove {sym}"):
                    st.session_state["watchlist"].remove(sym)
                    st.rerun()

            st.markdown('<hr style="border-color:rgba(255,255,255,.04);margin:.1rem 0">', unsafe_allow_html=True)

# ── Alerts tab ────────────────────────────────────────────────────────────────
with tab2:
    alerts = st.session_state["alerts"]
    if not alerts:
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:20px;
            padding:2rem;text-align:center;margin-top:1rem">
            <div style="font-size:2rem;margin-bottom:.6rem">🔔</div>
            <div style="font-family:'Syne',sans-serif;font-size:1rem;font-weight:700;color:#f0f2f8;margin-bottom:.3rem">No Alerts Set</div>
            <div style="font-size:.82rem;color:#8892a4">Use the sidebar form to create price, change%, or RSI alerts.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Check alert conditions
        alert_syms = list({a["symbol"] for a in alerts})
        with st.spinner("Checking alert conditions…"):
            live = {s: fetch_quote(s) for s in alert_syms}

        triggered_count = 0
        for i, al in enumerate(alerts):
            q   = live.get(al["symbol"])
            if q is None:
                continue
            val = al["value"]
            cond = al["condition"]
            check_val = {
                "Price ≥":   q["price"],
                "Price ≤":   q["price"],
                "Change% ≥": q["change_pct"],
                "Change% ≤": q["change_pct"],
                "RSI ≥":     q["rsi"],
                "RSI ≤":     q["rsi"],
            }.get(cond, 0)
            triggered = (
                (cond.endswith("≥") and check_val >= val) or
                (cond.endswith("≤") and check_val <= val)
            )
            st.session_state["alerts"][i]["triggered"] = triggered
            if triggered:
                triggered_count += 1

        # Stats
        total_alerts = len(alerts)
        ac1, ac2, ac3 = st.columns(3)
        for col, lbl, v, cls in [
            (ac1, "Total Alerts",  str(total_alerts),    "badge-blue"),
            (ac2, "Triggered",     str(triggered_count), "badge-red" if triggered_count else "badge-amber"),
            (ac3, "Pending",       str(total_alerts - triggered_count), "badge-blue"),
        ]:
            with col:
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);
                    padding:.8rem 1rem;text-align:center;">
                    <div style="font-size:.65rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669">{lbl}</div>
                    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:#f0f2f8;margin:.2rem 0">{v}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        for i, al in enumerate(alerts):
            q          = live.get(al["symbol"])
            triggered  = al.get("triggered", False)
            border_col = "#f05252" if triggered else "#4e5669"
            bg_cls     = "alert-triggered" if triggered else ""
            status_lbl = "🔴 TRIGGERED" if triggered else "⏳ Pending"
            status_cls = "badge-red" if triggered else "badge-blue"
            price_str  = f"${q['price']:.2f}" if q else "N/A"
            chg_str    = f"{q['change_pct']:+.2f}%" if q else "N/A"

            col_info, col_del2 = st.columns([11, 1])
            with col_info:
                st.markdown(f"""
                <div class="alert-card {bg_cls}" style="border-left-color:{border_col}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start">
                        <div>
                            <span style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">{al['symbol']}</span>
                            <span style="font-size:.75rem;color:#4e5669;margin-left:.5rem">created {al.get('created','—')}</span>
                        </div>
                        <span class="alert-badge {status_cls}">{status_lbl}</span>
                    </div>
                    <div style="margin-top:.5rem;font-size:.83rem;color:#8892a4">
                        <strong style="color:#f0f2f8">{al['condition']} {al['value']}</strong>
                        &nbsp;·&nbsp; Current: <strong style="color:#f0f2f8">{price_str}</strong> ({chg_str})
                        {f"&nbsp;·&nbsp; <em>{al['note']}</em>" if al.get('note') else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_del2:
                if st.button("✕", key=f"aldel_{i}", help="Delete alert"):
                    st.session_state["alerts"].pop(i)
                    st.rerun()

        if st.button("🗑 Clear All Alerts", use_container_width=True):
            st.session_state["alerts"] = []
            st.rerun()

st.markdown("""
<div style="text-align:center;padding:1rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Data provided by Yahoo Finance &nbsp;·&nbsp; Alerts are session-only &nbsp;·&nbsp; Not financial advice
</div>
""", unsafe_allow_html=True)
