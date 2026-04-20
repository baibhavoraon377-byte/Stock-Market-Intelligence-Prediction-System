"""
StockFin — Live Market Dashboard
Entry point for the Streamlit multi-page app.
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import time
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import streamlit.components.v1 as components

# ── Page config (ONLY in the root app.py, never in pages/) ─────────────────
st.set_page_config(
    page_title="StockFin — Live Dashboard",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Dark premium CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {
    --bg-base:#0d0f14; --bg-card:#13161e; --bg-card-hover:#181c27;
    --bg-elevated:#1c2030; --border:rgba(255,255,255,0.07);
    --border-active:rgba(255,255,255,0.14);
    --accent-blue:#4f8fff; --accent-violet:#7c6ff7;
    --accent-green:#22d98a; --accent-red:#f05252; --accent-amber:#f5a623;
    --text-primary:#f0f2f8; --text-secondary:#8892a4; --text-muted:#4e5669;
    --radius-sm:8px; --radius-md:14px; --radius-lg:20px;
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--text-primary)!important;}
.stApp{background:var(--bg-base)!important;}
section[data-testid="stSidebar"]{background:var(--bg-card)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text-secondary)!important;}
#MainMenu,footer,header{visibility:hidden;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--text-primary)!important;}
p,span{color:var(--text-primary);}
.stMarkdown p{color:var(--text-secondary);font-size:.84rem;}
.fin-card,.stat-card,.ticker-card,.glass-card,.metric-card,.alert-item{
    background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.3rem 1.5rem;
    transition:border-color .2s,transform .2s;}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet));opacity:.7;}
.stat-card{position:relative;overflow:hidden;}
.stat-card:hover,.fin-card:hover{border-color:var(--border-active);transform:translateY(-2px);}
.stat-label{font-size:.7rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
    color:var(--text-secondary);margin-bottom:.4rem;}
.stat-value{font-family:'Syne',sans-serif!important;font-size:1.9rem;font-weight:700;
    color:var(--text-primary);line-height:1.1;}
.stat-badge{display:inline-flex;align-items:center;gap:4px;font-size:.7rem;font-weight:600;
    padding:3px 8px;border-radius:20px;margin-top:.4rem;}
.badge-up{background:rgba(34,217,138,.12);color:var(--accent-green);}
.badge-down{background:rgba(240,82,82,.12);color:var(--accent-red);}
.badge-info{background:rgba(79,143,255,.12);color:var(--accent-blue);}
.ticker-card{border-radius:var(--radius-md);text-align:center;padding:.9rem;}
.ticker-card:hover{border-color:var(--accent-blue);transform:translateY(-3px);
    box-shadow:0 8px 24px rgba(79,143,255,.12);}
.ticker-sym{font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--text-secondary);}
.ticker-price{font-family:'Syne',sans-serif;font-size:1.25rem;font-weight:700;color:var(--text-primary);margin:.3rem 0;}
.ticker-chg{font-size:.75rem;font-weight:600;}
.up{color:var(--accent-green);} .down{color:var(--accent-red);}
.nav-group{font-size:.62rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text-muted)!important;padding:.5rem .4rem .2rem;}
.nav-item{display:flex;align-items:center;gap:9px;padding:.5rem .8rem;border-radius:var(--radius-sm);
    font-size:.83rem;font-weight:500;color:var(--text-secondary)!important;cursor:pointer;transition:background .15s;margin:2px 0;}
.nav-item:hover{background:rgba(255,255,255,.05);}
.nav-item.active{background:rgba(79,143,255,.15);color:var(--accent-blue)!important;font-weight:600;}
.live-dot{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;font-weight:600;color:var(--accent-green);}
.live-dot::before{content:'';width:7px;height:7px;background:var(--accent-green);border-radius:50%;animation:pdot 2s infinite;}
@keyframes pdot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(1.3);}}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input{
    background:var(--bg-elevated)!important;border:1px solid var(--border)!important;
    border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;font-size:.84rem!important;}
.stButton>button{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;border-radius:var(--radius-sm)!important;
    font-size:.8rem!important;font-weight:500!important;transition:all .15s!important;}
.stButton>button:hover{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stButton>button[kind="primary"]{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--bg-card)!important;border-radius:var(--radius-md)!important;
    gap:4px;padding:4px;border:1px solid var(--border)!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--text-secondary)!important;
    border-radius:var(--radius-sm)!important;font-size:.8rem!important;font-weight:500!important;padding:6px 14px!important;}
.stTabs [aria-selected="true"]{background:var(--bg-elevated)!important;color:var(--text-primary)!important;font-weight:600!important;}
div[data-testid="stMetric"]{background:var(--bg-card);border:1px solid var(--border);
    border-radius:var(--radius-md);padding:.8rem 1rem;}
div[data-testid="stMetric"] label{color:var(--text-secondary)!important;font-size:.7rem!important;
    letter-spacing:.06em;text-transform:uppercase;}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;
    color:var(--text-primary)!important;font-size:1.5rem!important;}
[data-testid="stDataFrameContainer"]{border:1px solid var(--border)!important;border-radius:var(--radius-md)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:10px;}
.glass-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.2rem 1.4rem;}
.glass-card h4{font-family:'Syne',sans-serif;font-size:.8rem;font-weight:600;letter-spacing:.07em;
    text-transform:uppercase;color:var(--text-secondary);margin-bottom:.6rem;}
.glass-card table td{padding:.28rem .4rem;font-size:.82rem;color:var(--text-secondary);}
.glass-card table td:last-child{color:var(--text-primary);}
.alert-item{border-left:3px solid;border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    padding:.75rem 1rem;background:var(--bg-elevated)!important;}
.metric-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:1rem;text-align:center;}
.metric-value{font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text-primary);margin:.3rem 0;}
.positive{color:var(--accent-green);} .negative{color:var(--accent-red);}
</style>
""", unsafe_allow_html=True)

# ── Session state for sidebar ─────────────────────────────────────────────────
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = False

# ── Custom overlay sidebar injected into parent document via components.html ──
components.html("""
<script>
(function() {
    const doc = window.parent.document;

    // ── Inject only once ──────────────────────────────────────────────────────
    if (doc.getElementById('sf-sidebar')) return;

    // ── CSS ───────────────────────────────────────────────────────────────────
    const style = doc.createElement('style');
    style.textContent = `
        /* Hide Streamlit native sidebar controls */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] { display:none!important; }

        /* Backdrop */
        #sf-backdrop {
            position:fixed; inset:0;
            background:rgba(0,0,0,0.6);
            backdrop-filter:blur(4px);
            z-index:99998;
            opacity:0; pointer-events:none;
            transition:opacity 0.35s ease;
        }
        #sf-backdrop.sf-open { opacity:1; pointer-events:all; }

        /* Sidebar panel */
        #sf-sidebar {
            position:fixed; top:0; left:0; bottom:0;
            width:272px;
            background:#13161e;
            border-right:1px solid rgba(255,255,255,0.08);
            box-shadow:8px 0 40px rgba(0,0,0,0.55);
            z-index:99999;
            transform:translateX(-100%);
            transition:transform 0.38s cubic-bezier(0.4,0,0.2,1);
            display:flex; flex-direction:column;
            overflow-y:auto; overflow-x:hidden;
            font-family:'DM Sans',sans-serif;
        }
        #sf-sidebar.sf-open { transform:translateX(0); }
        #sf-sidebar::-webkit-scrollbar { width:4px; }
        #sf-sidebar::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.08); border-radius:4px; }

        /* Header */
        .sf-hdr {
            display:flex; align-items:center; justify-content:space-between;
            padding:1.1rem 1rem 0.9rem;
            border-bottom:1px solid rgba(255,255,255,0.06);
            flex-shrink:0;
        }
        .sf-logo { display:flex; align-items:center; gap:10px; }
        .sf-logo-box {
            width:34px; height:34px;
            background:linear-gradient(135deg,#4f8fff,#7c6ff7);
            border-radius:10px;
            display:flex; align-items:center; justify-content:center;
            font-weight:700; font-size:.85rem; color:white;
            font-family:'Syne',sans-serif; flex-shrink:0;
        }
        .sf-brand { font-family:'Syne',sans-serif; font-weight:700; font-size:.98rem; color:#f0f2f8; }
        .sf-live {
            display:inline-flex; align-items:center; gap:5px;
            font-size:.6rem; font-weight:600; color:#22d98a; margin-top:1px;
        }
        .sf-live::before {
            content:''; width:6px; height:6px;
            background:#22d98a; border-radius:50%;
            animation:sfpulse 2s infinite;
        }
        @keyframes sfpulse {
            0%,100%{opacity:1;transform:scale(1);}
            50%{opacity:.3;transform:scale(1.4);}
        }
        .sf-close {
            background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:8px; width:30px; height:30px;
            cursor:pointer; color:#8892a4;
            display:flex; align-items:center; justify-content:center;
            font-size:.95rem; transition:background .2s, color .2s;
        }
        .sf-close:hover { background:rgba(240,82,82,0.15); color:#f05252; }

        /* Section labels */
        .sf-lbl {
            font-size:.59rem; font-weight:600; letter-spacing:.13em;
            text-transform:uppercase; color:#4e5669;
            padding:.95rem 1rem .3rem;
        }

        /* Nav items */
        .sf-item {
            display:flex; align-items:center; gap:10px;
            padding:.5rem .9rem; border-radius:8px;
            margin:2px 8px; font-size:.82rem; font-weight:500;
            color:#8892a4; cursor:pointer;
            transition:background .15s, color .15s;
            text-decoration:none; user-select:none;
        }
        .sf-item:hover { background:rgba(255,255,255,0.05); color:#d0d6e8; }
        .sf-item.sf-active { background:rgba(79,143,255,0.13); color:#4f8fff; font-weight:600; }
        .sf-item svg { flex-shrink:0; opacity:.85; }

        /* Divider */
        .sf-div { border:none; border-top:1px solid rgba(255,255,255,0.06); margin:.6rem .9rem; }

        /* Footer */
        .sf-foot {
            margin-top:auto; padding:.85rem 1rem;
            border-top:1px solid rgba(255,255,255,0.06);
            font-size:.69rem; color:#4e5669; flex-shrink:0;
        }

        /* Hamburger toggle button */
        #sf-toggle {
            position:fixed; top:14px; left:14px; z-index:99997;
            background:#13161e; border:1px solid rgba(255,255,255,0.14);
            border-radius:10px; width:40px; height:40px;
            cursor:pointer; color:#f0f2f8;
            display:flex; align-items:center; justify-content:center;
            box-shadow:0 4px 16px rgba(0,0,0,0.4);
            transition:border-color .2s, background .2s, transform .2s;
        }
        #sf-toggle:hover {
            border-color:#4f8fff;
            background:rgba(79,143,255,0.1);
            transform:translateY(-1px);
        }
    `;
    doc.head.appendChild(style);

    // ── Backdrop ──────────────────────────────────────────────────────────────
    const backdrop = doc.createElement('div');
    backdrop.id = 'sf-backdrop';
    backdrop.onclick = () => sfClose();
    doc.body.appendChild(backdrop);

    // ── Sidebar HTML ──────────────────────────────────────────────────────────
    const sidebar = doc.createElement('div');
    sidebar.id = 'sf-sidebar';
    sidebar.innerHTML = `
        <div class="sf-hdr">
            <div class="sf-logo">
                <div class="sf-logo-box">S</div>
                <div>
                    <div class="sf-brand">StockFin</div>
                    <div class="sf-live">LIVE</div>
                </div>
            </div>
            <button class="sf-close" onclick="sfClose()" title="Close">✕</button>
        </div>

        <div class="sf-lbl">Platform</div>
        <div class="sf-item sf-active">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            Dashboard
        </div>

        <hr class="sf-div">
        <div class="sf-lbl">Pages</div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            Analytics
        </div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            Portfolio
        </div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
            ML Predictions
        </div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            Watchlist & Alerts
        </div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
            Backtesting
        </div>

        <hr class="sf-div">
        <div class="sf-lbl">Settings</div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>
            Preferences
        </div>
        <div class="sf-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>
            Account
        </div>

        <div class="sf-foot">📡 Data · Yahoo Finance · ~60s refresh</div>
    `;
    doc.body.appendChild(sidebar);

    // ── Hamburger toggle button ───────────────────────────────────────────────
    const toggle = doc.createElement('button');
    toggle.id = 'sf-toggle';
    toggle.title = 'Toggle menu';
    toggle.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`;
    toggle.onclick = () => sfToggle();
    doc.body.appendChild(toggle);

    // ── Toggle functions (attached to parent window) ──────────────────────────
    window.parent.sfOpen  = function() {
        sidebar.classList.add('sf-open');
        backdrop.classList.add('sf-open');
    };
    window.parent.sfClose = function() {
        sidebar.classList.remove('sf-open');
        backdrop.classList.remove('sf-open');
    };
    window.parent.sfToggle = function() {
        sidebar.classList.contains('sf-open') ? window.parent.sfClose() : window.parent.sfOpen();
    };

    // Also expose locally for onclick handlers in the injected HTML
    window.sfClose  = window.parent.sfClose;
    window.sfToggle = window.parent.sfToggle;

})();
</script>
""", height=0, width=0)


# ── Stock catalogue ───────────────────────────────────────────────────────────
STOCK_CATALOGUE = {
    "Apple (AAPL)":               "AAPL",
    "Microsoft (MSFT)":           "MSFT",
    "NVIDIA (NVDA)":              "NVDA",
    "Alphabet / Google (GOOGL)":  "GOOGL",
    "Meta Platforms (META)":      "META",
    "Amazon (AMZN)":              "AMZN",
    "Tesla (TSLA)":               "TSLA",
    "Netflix (NFLX)":             "NFLX",
    "AMD (AMD)":                  "AMD",
    "Intel (INTC)":               "INTC",
    "Qualcomm (QCOM)":            "QCOM",
    "Broadcom (AVGO)":            "AVGO",
    "Salesforce (CRM)":           "CRM",
    "Oracle (ORCL)":              "ORCL",
    "Adobe (ADBE)":               "ADBE",
    "Shopify (SHOP)":             "SHOP",
    "Palantir (PLTR)":            "PLTR",
    "JPMorgan Chase (JPM)":       "JPM",
    "Goldman Sachs (GS)":         "GS",
    "Visa (V)":                   "V",
    "Mastercard (MA)":            "MA",
    "Johnson & Johnson (JNJ)":    "JNJ",
    "UnitedHealth (UNH)":         "UNH",
    "Pfizer (PFE)":               "PFE",
    "Eli Lilly (LLY)":            "LLY",
    "Walmart (WMT)":              "WMT",
    "Coca-Cola (KO)":             "KO",
    "S&P 500 ETF (SPY)":          "SPY",
    "NASDAQ ETF (QQQ)":           "QQQ",
    "Bitcoin (BTC-USD)":          "BTC-USD",
    "Infosys (INFY)":             "INFY",
    "Wipro (WIT)":                "WIT",
    "HDFC Bank (HDB)":            "HDB",
    "Tata Motors (TTM)":          "TTM",
}
SYMBOL_TO_NAME = {v: k for k, v in STOCK_CATALOGUE.items()}

# ── Data helpers ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def get_live_stock_data(symbol: str) -> dict | None:
    try:
        stock = yf.Ticker(symbol)
        intra = stock.history(period="1d", interval="1m", prepost=True)
        current_price = (
            float(intra["Close"].iloc[-1])
            if not intra.empty
            else getattr(stock.fast_info, "last_price", None)
               or stock.info.get("regularMarketPrice",
                                 stock.info.get("currentPrice", 0))
        )
        hist = stock.history(period="1mo", prepost=True)
        if hist.empty:
            return None
        open_ = float(hist["Open"].iloc[-1])
        return {
            "symbol": symbol,
            "price": current_price,
            "open": open_,
            "high": float(hist["High"].iloc[-1]),
            "low": float(hist["Low"].iloc[-1]),
            "volume": float(hist["Volume"].iloc[-1]),
            "change": current_price - open_,
            "change_percent": ((current_price - open_) / open_ * 100) if open_ else 0.0,
            "history": hist,
            "info": stock.info,
        }
    except Exception as exc:
        st.warning(f"Could not fetch {symbol}: {exc}")
        return None


@st.cache_data(ttl=300)
def get_multiple_stocks(symbols: tuple) -> dict:
    result = {}
    for sym in symbols:
        data = get_live_stock_data(sym)
        if data:
            result[sym] = data
        time.sleep(0.35)
    return result


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    delta = df["Close"].diff()
    gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"]      = (100 - (100 / (1 + rs))).fillna(50)
    df["BB_Middle"] = df["Close"].rolling(20).mean()
    bb_std          = df["Close"].rolling(20).std()
    df["BB_Upper"]  = df["BB_Middle"] + bb_std * 2
    df["BB_Lower"]  = df["BB_Middle"] - bb_std * 2
    exp1 = df["Close"].ewm(span=12, adjust=False).mean()
    exp2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df


# ── Plotly dark layout ────────────────────────────────────────────────────────
DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(19,22,30,0)",
    plot_bgcolor="rgba(28,32,48,0.5)",
    font=dict(family="DM Sans", color="#8892a4", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4", size=10)),
    margin=dict(l=8, r=8, t=36, b=8),
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:4rem 0.4rem 0.4rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
                border-radius:10px;display:flex;align-items:center;justify-content:center;
                font-weight:700;font-size:.85rem;color:white;font-family:'Syne',sans-serif">S</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;
                    color:#f0f2f8!important">StockFin</div>
                <span class="live-dot" style="font-size:.65rem">LIVE</span>
            </div>
        </div>
        <div class="nav-group">Platform</div>
        <div class="nav-item active">Dashboard</div>
        <div class="nav-group" style="margin-top:.5rem">Pages</div>
        <div class="nav-item">Analytics</div>
        <div class="nav-item">Portfolio</div>
        <div class="nav-item">ML Predictions</div>
        <div class="nav-item">Watchlist & Alerts</div>
        <div class="nav-item">Backtesting</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:0.8rem 0">
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:.7rem;font-weight:600;letter-spacing:.1em;'
        'text-transform:uppercase;color:#4e5669;padding:.3rem .4rem .1rem">Select Stocks</div>',
        unsafe_allow_html=True,
    )

    # Checkboxes using full company names
    selected_stocks: list[str] = []
    for name, sym in STOCK_CATALOGUE.items():
        # Only show first 12 in sidebar checkboxes to avoid overflow
        if list(STOCK_CATALOGUE.keys()).index(name) >= 12:
            break
        if st.checkbox(name, value=(sym in ["AAPL", "TSLA", "MSFT"])):
            selected_stocks.append(sym)

    st.markdown(
        '<hr style="border-color:rgba(255,255,255,.06);margin:.8rem 0">',
        unsafe_allow_html=True,
    )
    chart_period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=0)
    total_value  = st.number_input("Initial Investment ($)", value=10_000, step=1_000, min_value=0)

    st.markdown(
        '<hr style="border-color:rgba(255,255,255,.06);margin:.8rem 0">',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="font-size:.72rem;color:#4e5669;padding:.2rem .4rem">'
        "Data · Yahoo Finance · Refreshes ~60 s</div>",
        unsafe_allow_html=True,
    )

# ── Header ────────────────────────────────────────────────────────────────────
hc1, hc2, hc3 = st.columns([3, 1.4, 0.8])
with hc1:
    st.markdown("""
    <div style="padding:.8rem 0 .2rem 3.5rem">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:.5rem">
            <div style="width:40px;height:40px;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
                border-radius:12px;display:flex;align-items:center;justify-content:center;
                font-weight:800;font-size:1rem;color:white;font-family:'Syne',sans-serif;
                box-shadow:0 4px 16px rgba(79,143,255,.3);flex-shrink:0">S</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
                    color:#f0f2f8;line-height:1">StockFin</div>
                <div style="font-size:.82rem;color:#8892a4;margin-top:.2rem">
                    Live Market Dashboard &nbsp;·&nbsp; Real-time analytics</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with hc2:
    now = datetime.now().strftime("%b %d, %Y  %H:%M")
    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
        padding:.55rem 1rem;text-align:center;margin-top:.8rem">
        <div style="font-size:.65rem;color:#4e5669;text-transform:uppercase;
            letter-spacing:.07em">Last Update</div>
        <div style="font-size:.82rem;font-weight:600;color:#f0f2f8">{now}</div>
    </div>
    """, unsafe_allow_html=True)
with hc3:
    st.markdown("<div style='margin-top:.8rem'>", unsafe_allow_html=True)
    if st.button("Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

# ── Guard: no stocks selected ─────────────────────────────────────────────────
if not selected_stocks:
    st.markdown("""
    <div class="fin-card" style="text-align:center;padding:3rem">
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8">
            Select stocks from the sidebar to get started
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with st.spinner("Fetching live market data…"):
    stocks_data = get_multiple_stocks(tuple(selected_stocks))

if not stocks_data:
    st.error("No stock data could be fetched. Check your internet connection and try again.")
    st.stop()

# ── Ticker grid ───────────────────────────────────────────────────────────────
st.markdown(
    "<div style=\"font-family:'Syne',sans-serif;font-size:.82rem;font-weight:600;"
    "letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.6rem\">"
    "Market Overview</div>",
    unsafe_allow_html=True,
)

n_cols = min(4, len(stocks_data))
cols = st.columns(n_cols)
for idx, (sym, data) in enumerate(list(stocks_data.items())[:8]):
    col_idx = idx % n_cols
    display_name = SYMBOL_TO_NAME.get(sym, sym)
    with cols[col_idx]:
        up = data["change"] >= 0
        st.markdown(f"""
        <div class="ticker-card">
            <div class="ticker-sym">{sym}</div>
            <div style="font-size:.65rem;color:#4e5669;margin-bottom:.2rem">{display_name[:22]}</div>
            <div class="ticker-price">${data['price']:.2f}</div>
            <div class="ticker-chg {'up' if up else 'down'}">
                {'▲' if up else '▼'} {abs(data['change_percent']):.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Detailed analysis ─────────────────────────────────────────────────────────
st.markdown(
    "<div style=\"font-family:'Syne',sans-serif;font-size:.82rem;font-weight:600;"
    "letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.6rem\">"
    "Detailed Analysis</div>",
    unsafe_allow_html=True,
)

# Selectbox with full company names, returns symbol
sym_keys  = list(stocks_data.keys())
sym_names = [SYMBOL_TO_NAME.get(s, s) for s in sym_keys]
sel_idx   = st.selectbox(
    "Select stock to analyse",
    range(len(sym_keys)),
    format_func=lambda i: f"{sym_keys[i]}  —  {sym_names[i]}",
    label_visibility="collapsed",
)
selected_symbol = sym_keys[sel_idx]

if selected_symbol and selected_symbol in stocks_data:
    data = stocks_data[selected_symbol]
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Price Chart", "Indicators", "Company Info", "Alerts"]
    )

    # ── Price Chart ──────────────────────────────────────────────────────────
    with tab1:
        hist = calculate_indicators(data["history"])

        # Tighter vertical_spacing and row_heights for compact look
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.60, 0.18, 0.22],
            subplot_titles=("Price & Moving Averages", "Volume", "RSI (14)"),
        )
        fig.add_trace(
            go.Candlestick(
                x=hist.index, open=hist["Open"], high=hist["High"],
                low=hist["Low"], close=hist["Close"],
                increasing_line_color="#22d98a", decreasing_line_color="#f05252",
                name="Price",
            ), row=1, col=1,
        )
        for col_name, label, color in [
            ("MA20",     "MA20", "#f5a623"),
            ("MA50",     "MA50", "#7c6ff7"),
            ("BB_Upper", "BB+",  "rgba(255,255,255,.25)"),
            ("BB_Lower", "BB-",  "rgba(255,255,255,.25)"),
        ]:
            fig.add_trace(
                go.Scatter(
                    x=hist.index, y=hist[col_name], name=label,
                    line=dict(color=color, width=1,
                              dash="dot" if "BB" in col_name else "solid"),
                ), row=1, col=1,
            )
        bar_colors = [
            "#22d98a" if hist["Close"].iloc[i] >= hist["Open"].iloc[i] else "#f05252"
            for i in range(len(hist))
        ]
        fig.add_trace(
            go.Bar(x=hist.index, y=hist["Volume"], name="Volume",
                   marker_color=bar_colors, opacity=0.7), row=2, col=1,
        )
        fig.add_trace(
            go.Scatter(x=hist.index, y=hist["RSI"], name="RSI",
                       line=dict(color="#4f8fff", width=1.5)), row=3, col=1,
        )
        fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=0.5, row=3, col=1)
        fig.update_layout(
            height=680, showlegend=True, xaxis_rangeslider_visible=False,
            title=f"{selected_symbol} — {SYMBOL_TO_NAME.get(selected_symbol, '')}",
            title_font=dict(family="Syne", size=13, color="#f0f2f8"),
            **DARK_LAYOUT,
        )
        # Tighten subplot title font
        for ann in fig.layout.annotations:
            ann.font.size = 10
            ann.font.color = "#8892a4"
        st.plotly_chart(fig, use_container_width=True)

    # ── Indicators ───────────────────────────────────────────────────────────
    with tab2:
        hist = calculate_indicators(data["history"])
        latest_rsi = float(hist["RSI"].iloc[-1])
        rsi_status = "Overbought" if latest_rsi > 70 else "Oversold" if latest_rsi < 30 else "Neutral"
        rsi_color  = "#f05252" if latest_rsi > 70 else "#22d98a" if latest_rsi < 30 else "#f5a623"
        macd_bull  = float(hist["MACD"].iloc[-1]) > float(hist["Signal"].iloc[-1])

        ic1, ic2 = st.columns(2)
        with ic1:
            st.markdown(f"""
            <div class="glass-card">
                <h4>Key Statistics</h4>
                <table style="width:100%">
                    <tr><td>Current Price</td><td><strong>${data['price']:.2f}</strong></td></tr>
                    <tr><td>Day Open</td><td>${data['open']:.2f}</td></tr>
                    <tr><td>Day High</td><td>${data['high']:.2f}</td></tr>
                    <tr><td>Day Low</td><td>${data['low']:.2f}</td></tr>
                    <tr><td>Volume</td><td>{data['volume']:,.0f}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        with ic2:
            st.markdown(f"""
            <div class="glass-card">
                <h4>Technical Indicators</h4>
                <table style="width:100%">
                    <tr><td>RSI (14)</td>
                        <td><strong style="color:{rsi_color}">{latest_rsi:.1f} — {rsi_status}</strong></td></tr>
                    <tr><td>MACD</td>
                        <td><strong style="color:{'#22d98a' if macd_bull else '#f05252'}">
                            {'Bullish' if macd_bull else 'Bearish'}</strong></td></tr>
                    <tr><td>MA 20</td><td>${hist['MA20'].iloc[-1]:.2f}</td></tr>
                    <tr><td>MA 50</td><td>${hist['MA50'].iloc[-1]:.2f}</td></tr>
                    <tr><td>BB Upper</td><td>${hist['BB_Upper'].iloc[-1]:.2f}</td></tr>
                    <tr><td>BB Lower</td><td>${hist['BB_Lower'].iloc[-1]:.2f}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

        fig2 = go.Figure()
        for col_name, label, color in [
            ("Close",  "Close Price", "#4f8fff"),
            ("MA20",   "MA20",        "#f5a623"),
            ("MA50",   "MA50",        "#7c6ff7"),
        ]:
            fig2.add_trace(
                go.Scatter(x=hist.index, y=hist[col_name], name=label,
                           line=dict(color=color, width=1.8 if col_name == "Close" else 1.2))
            )
        fig2.update_layout(
            height=300, title="Price vs Moving Averages",
            title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Company Info ─────────────────────────────────────────────────────────
    with tab3:
        info = data["info"]
        ci1, ci2 = st.columns(2)
        with ci1:
            st.markdown(f"""
            <div class="glass-card">
                <h4>Company Profile</h4>
                <table style="width:100%">
                    <tr><td>Name</td><td>{info.get('longName','N/A')}</td></tr>
                    <tr><td>Sector</td><td>{info.get('sector','N/A')}</td></tr>
                    <tr><td>Industry</td><td>{info.get('industry','N/A')}</td></tr>
                    <tr><td>Country</td><td>{info.get('country','N/A')}</td></tr>
                    <tr><td>Website</td>
                        <td><a href="{info.get('website','#')}" target="_blank"
                            style="color:#4f8fff">{info.get('website','N/A')}</a></td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        with ci2:
            st.markdown(f"""
            <div class="glass-card">
                <h4>Financial Metrics</h4>
                <table style="width:100%">
                    <tr><td>Market Cap</td><td>${info.get('marketCap',0):,.0f}</td></tr>
                    <tr><td>P/E Ratio</td><td>{info.get('trailingPE','N/A')}</td></tr>
                    <tr><td>52W High</td><td>${info.get('fiftyTwoWeekHigh',0):.2f}</td></tr>
                    <tr><td>52W Low</td><td>${info.get('fiftyTwoWeekLow',0):.2f}</td></tr>
                    <tr><td>Dividend Yield</td>
                        <td>{(info.get('dividendYield') or 0) * 100:.2f}%</td></tr>
                    <tr><td>Beta</td><td>{info.get('beta','N/A')}</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    # ── Alerts ───────────────────────────────────────────────────────────────
    with tab4:
        hist = calculate_indicators(data["history"])
        latest_rsi = float(hist["RSI"].iloc[-1])
        avg_vol    = float(hist["Volume"].rolling(20).mean().iloc[-1])
        alerts: list[tuple[str, str]] = []

        if data["change_percent"] > 3:
            alerts.append((f"{selected_symbol} surged <strong>+{data['change_percent']:.2f}%</strong> today", "#f5a623"))
        elif data["change_percent"] < -3:
            alerts.append((f"{selected_symbol} dropped <strong>{data['change_percent']:.2f}%</strong> today", "#f05252"))
        if latest_rsi > 70:
            alerts.append((f"RSI overbought — <strong>{latest_rsi:.1f}</strong>", "#f05252"))
        elif latest_rsi < 30:
            alerts.append((f"RSI oversold — <strong>{latest_rsi:.1f}</strong>", "#22d98a"))
        if avg_vol and data["volume"] > avg_vol * 1.5:
            alerts.append((f"Unusual volume — <strong>{data['volume']:,.0f}</strong>", "#4f8fff"))

        if alerts:
            for msg, color in alerts:
                st.markdown(f"""
                <div style="background:rgba(19,22,30,1);border:1px solid {color}33;
                    border-left:3px solid {color};border-radius:0 8px 8px 0;
                    padding:.8rem 1rem;font-size:.83rem;color:#8892a4;margin-bottom:.5rem">
                    {msg}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(34,217,138,.07);border:1px solid rgba(34,217,138,.2);
                border-radius:14px;padding:1rem;font-size:.83rem;color:#22d98a">
                No significant alerts at this time
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
            "<div style='margin-top:1rem;font-size:.72rem;font-weight:600;letter-spacing:.08em;"
            "text-transform:uppercase;color:#4e5669;margin-bottom:.5rem'>Headlines</div>",
            unsafe_allow_html=True,
        )
        for headline in [
            f"{selected_symbol} shows momentum in latest session",
            f"Analysts revise {selected_symbol} price target upward",
            f"Institutional activity noted in {selected_symbol}",
            f"Technical indicators signal trend continuation for {selected_symbol}",
        ]:
            st.markdown(
                f"<div style='padding:.4rem 0;font-size:.82rem;color:#8892a4;"
                f"border-bottom:1px solid rgba(255,255,255,.05)'>→ {headline}</div>",
                unsafe_allow_html=True,
            )

# ── Portfolio summary strip ───────────────────────────────────────────────────
st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
st.markdown('<hr style="border-color:rgba(255,255,255,.06)">', unsafe_allow_html=True)
st.markdown(
    "<div style=\"font-family:'Syne',sans-serif;font-size:.82rem;font-weight:600;"
    "letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.7rem\">"
    "Portfolio Summary</div>",
    unsafe_allow_html=True,
)

portfolio_value = float(total_value)
for sym, d in stocks_data.items():
    if d and d["open"]:
        alloc = total_value / max(len(stocks_data), 1)
        portfolio_value = portfolio_value - alloc + alloc * d["price"] / d["open"]
pct_return = ((portfolio_value - total_value) / total_value * 100) if total_value else 0.0

ps1, ps2, ps3, ps4 = st.columns(4)
for col, title, value in [
    (ps1, "Total Value",  f"${portfolio_value:,.2f}"),
    (ps2, "Total Return", f"{pct_return:+.2f}%"),
    (ps3, "Holdings",     str(len(stocks_data))),
    (ps4, "Risk Score",   "Medium"),
]:
    with col:
        color = "#22d98a" if "+" in value else "#f05252" if value.startswith("-") else "#f0f2f8"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-label">{title}</div>
            <div class="stat-value" style="color:{color};font-size:1.6rem">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:1.5rem 0 .5rem;font-size:.75rem;color:#4e5669">
    Data provided by Yahoo Finance &nbsp;·&nbsp; For educational purposes only
    &nbsp;·&nbsp; Not financial advice
</div>
""", unsafe_allow_html=True)
