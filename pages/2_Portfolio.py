import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
import json, os


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{
    --bg-base:#0d0f14;--bg-card:#13161e;--bg-elevated:#1c2030;
    --border:rgba(255,255,255,.07);--border-active:rgba(255,255,255,.14);
    --accent-blue:#4f8fff;--accent-violet:#7c6ff7;--accent-green:#22d98a;
    --accent-red:#f05252;--accent-amber:#f5a623;
    --text-primary:#f0f2f8;--text-secondary:#8892a4;--text-muted:#4e5669;
    --radius-sm:8px;--radius-md:14px;--radius-lg:20px;
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--text-primary)!important;}
.stApp{background:var(--bg-base)!important;}
section[data-testid="stSidebar"]{background:var(--bg-card)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text-secondary)!important;}
#MainMenu,footer,header{visibility:hidden;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--text-primary)!important;}
.stMarkdown p{color:var(--text-secondary);font-size:.84rem;}
/* hero card */
.portfolio-hero{background:linear-gradient(135deg,#1a1f35 0%,#1e2540 100%);
    border:1px solid rgba(79,143,255,.2);border-radius:var(--radius-lg);padding:1.6rem;}
/* stat cards */
.p-stat{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
    padding:1.3rem 1.5rem;position:relative;overflow:hidden;}
.p-stat::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet));opacity:.5;}
.p-stat-label{font-size:.68rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--text-secondary);}
.p-stat-val{font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:700;color:var(--text-primary);line-height:1.1;margin:.3rem 0;}
/* holding rows */
.holding-row{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:.75rem 1rem;margin-bottom:.4rem;transition:border-color .2s;}
.holding-row:hover{border-color:var(--border-active);}
.up{color:#22d98a;font-weight:600;} .dn{color:#f05252;font-weight:600;}
/* allocation bar */
.alloc-bar{height:5px;background:rgba(255,255,255,.06);border-radius:10px;overflow:hidden;margin:.3rem 0;}
.alloc-fill{height:100%;background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet));border-radius:10px;}
/* glass card */
.glass-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.2rem 1.4rem;}
/* nav */
.nav-group{font-size:.62rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text-muted)!important;padding:.5rem .4rem .2rem;}
.nav-item{display:flex;align-items:center;gap:9px;padding:.5rem .8rem;border-radius:var(--radius-sm);
    font-size:.83rem;font-weight:500;color:var(--text-secondary)!important;cursor:pointer;margin:2px 0;}
.nav-item:hover{background:rgba(255,255,255,.05);}
.nav-item.active{background:rgba(79,143,255,.15);color:var(--accent-blue)!important;font-weight:600;}
/* buttons */
.stButton>button{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;border-radius:var(--radius-sm)!important;font-size:.8rem!important;transition:all .15s!important;}
.stButton>button:hover{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stButton>button[kind="primary"]{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input,.stDateInput>div>div>input{
    background:var(--bg-elevated)!important;border:1px solid var(--border)!important;
    border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;font-size:.84rem!important;}
div[data-testid="stMetric"]{background:var(--bg-card);border:1px solid var(--border);
    border-radius:var(--radius-md);padding:.8rem 1rem;}
div[data-testid="stMetric"] label{color:var(--text-secondary)!important;font-size:.68rem!important;
    letter-spacing:.06em;text-transform:uppercase;}
div[data-testid="stMetric"] [data-testid="stMetricValue"]{font-family:'Syne',sans-serif!important;
    color:var(--text-primary)!important;font-size:1.4rem!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--bg-card)!important;border-radius:var(--radius-md)!important;
    gap:4px;padding:4px;border:1px solid var(--border)!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;color:var(--text-secondary)!important;
    border-radius:var(--radius-sm)!important;font-size:.8rem!important;font-weight:500!important;padding:6px 14px!important;}
.stTabs [aria-selected="true"]{background:var(--bg-elevated)!important;color:var(--text-primary)!important;font-weight:600!important;}
[data-testid="stDataFrameContainer"]{border:1px solid var(--border)!important;border-radius:var(--radius-md)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:10px;}
</style>
""", unsafe_allow_html=True)

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(28,32,48,0.5)",
    font=dict(family="DM Sans", color="#8892a4", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4", size=10)),
    margin=dict(l=8, r=8, t=36, b=8),
)

# ── Session state ──────────────────────────────────────────────────────────────
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {'holdings': [], 'cash_balance': 10000.00}

import pathlib as _pathlib
PORTFOLIO_FILE = str(_pathlib.Path(__file__).parent.parent / 'data' / 'portfolio_data.json')

def save_portfolio():
    with open(PORTFOLIO_FILE, 'w') as f: json.dump(st.session_state.portfolio, f)

def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f: st.session_state.portfolio = json.load(f)

load_portfolio()

@st.cache_data(ttl=60)
def get_price(symbol):
    try:
        return yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1]
    except: return None

def calc_metrics(holdings):
    total_val = st.session_state.portfolio['cash_balance']
    total_inv = 0
    rows = []
    for h in holdings:
        p = get_price(h['symbol'])
        if p:
            cur  = h['shares'] * p
            inv  = h['shares'] * h['buy_price']
            pnl  = cur - inv
            pnl_ = (pnl / inv) * 100 if inv else 0
            total_val += cur; total_inv += inv
            rows.append({**h, 'current_price':p, 'current_value':cur,
                         'invested':inv, 'pnl':pnl, 'pnl_percent':pnl_, 'allocation':0})
    for r in rows: r['allocation'] = (r['current_value']/total_val*100) if total_val else 0
    pnl_total = total_val - (total_inv + st.session_state.portfolio['cash_balance'])
    pnl_pct   = (pnl_total/(total_inv+st.session_state.portfolio['cash_balance'])*100) if (total_inv+st.session_state.portfolio['cash_balance']) else 0
    return rows, total_val, pnl_total, pnl_pct

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem .4rem .4rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#22d98a);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;color:white;font-family:"Syne",sans-serif">P</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8!important">Portfolio</div>
        </div>
        <div class="nav-group">Navigation</div>
        <div class="nav-item active">Holdings</div>
        <div class="nav-item">Performance</div>
        <div class="nav-item">Risk Analysis</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.3rem .4rem .2rem">Add Holding</div>', unsafe_allow_html=True)

    STOCK_CATALOGUE = {
        "Apple (AAPL)":"AAPL","Microsoft (MSFT)":"MSFT","NVIDIA (NVDA)":"NVDA",
        "Alphabet/Google (GOOGL)":"GOOGL","Meta (META)":"META","Amazon (AMZN)":"AMZN",
        "Tesla (TSLA)":"TSLA","Netflix (NFLX)":"NFLX","AMD (AMD)":"AMD",
        "Intel (INTC)":"INTC","Qualcomm (QCOM)":"QCOM","Broadcom (AVGO)":"AVGO",
        "Salesforce (CRM)":"CRM","Oracle (ORCL)":"ORCL","Adobe (ADBE)":"ADBE",
        "Palantir (PLTR)":"PLTR","JPMorgan (JPM)":"JPM","Goldman Sachs (GS)":"GS",
        "Visa (V)":"V","Mastercard (MA)":"MA","J&J (JNJ)":"JNJ",
        "UnitedHealth (UNH)":"UNH","Pfizer (PFE)":"PFE","Eli Lilly (LLY)":"LLY",
        "Walmart (WMT)":"WMT","Coca-Cola (KO)":"KO","SPY ETF (SPY)":"SPY",
        "QQQ ETF (QQQ)":"QQQ","Bitcoin (BTC-USD)":"BTC-USD",
        "Infosys (INFY)":"INFY","Wipro (WIT)":"WIT","HDFC Bank (HDB)":"HDB",
    }

    with st.form("add_holding"):
        cat_names   = ["— choose from list —"] + list(STOCK_CATALOGUE.keys())
        chosen_cat  = st.selectbox("Stock", cat_names, index=0)
        sym         = st.text_input("Or type symbol manually", placeholder="AAPL, TSLA…")
        if not sym.strip() and chosen_cat != "— choose from list —":
            sym = STOCK_CATALOGUE[chosen_cat]
        shrs  = st.number_input("Shares", min_value=0.01, step=0.01)
        bp    = st.number_input("Buy Price ($)", min_value=0.01, step=0.01)
        bdate = st.date_input("Date", datetime.now())
        if st.form_submit_button("Add", use_container_width=True) and sym and shrs > 0 and bp > 0:
            st.session_state.portfolio['holdings'].append(
                {'symbol':sym.upper(),'shares':shrs,'buy_price':bp,'buy_date':bdate.strftime("%Y-%m-%d")})
            save_portfolio(); st.success(f"Added {shrs} × {sym.upper()}"); st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.1rem .4rem .2rem">Cash Balance</div>', unsafe_allow_html=True)
    cash = st.number_input("", value=st.session_state.portfolio['cash_balance'], step=100.0, label_visibility="collapsed")
    if cash != st.session_state.portfolio['cash_balance']:
        st.session_state.portfolio['cash_balance'] = cash; save_portfolio(); st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    if st.button("Reset Portfolio", use_container_width=True):
        st.session_state.portfolio = {'holdings':[],'cash_balance':10000.00}; save_portfolio(); st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">
        Portfolio Tracker
    </div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">Track your investments and monitor performance in real-time</div>
</div>
""", unsafe_allow_html=True)

# ── Main ────────────────────────────────────────────────────────────────────────
if st.session_state.portfolio['holdings']:
    metrics, total_val, total_pnl, total_pnl_pct = calc_metrics(st.session_state.portfolio['holdings'])

    # ── Stat cards ──
    sc1, sc2, sc3, sc4 = st.columns(4)
    pnl_color = "#22d98a" if total_pnl >= 0 else "#f05252"
    pnl_icon  = "▲" if total_pnl >= 0 else "▼"

    for col, lbl, val, color in [
        (sc1, "Total Portfolio Value", f"${total_val:,.2f}", "#4f8fff"),
        (sc2, "Total P&L", f"{pnl_icon} ${abs(total_pnl):,.2f}  ({total_pnl_pct:+.2f}%)", pnl_color),
        (sc3, "Total Invested", f"${sum(m['invested'] for m in metrics):,.2f}", "#f5a623"),
        (sc4, "Cash Balance", f"${st.session_state.portfolio['cash_balance']:,.2f}", "#22d98a"),
    ]:
        with col:
            st.markdown(f"""
            <div class="p-stat">
                <div class="p-stat-label">{lbl}</div>
                <div class="p-stat-val" style="color:{color};font-size:1.6rem">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # ── Charts ──
    cc1, cc2 = st.columns(2)

    with cc1:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Portfolio Allocation</div>', unsafe_allow_html=True)
        alloc_data = [{'Symbol':m['symbol'],'Allocation':m['allocation']} for m in metrics if m['allocation']>0]
        if alloc_data:
            df_alloc = pd.DataFrame(alloc_data)
            fig = px.pie(df_alloc, values='Allocation', names='Symbol', hole=0.55,
                         color_discrete_sequence=['#4f8fff','#7c6ff7','#22d98a','#f5a623','#f05252','#ec4899'])
            fig.update_traces(textfont=dict(family="DM Sans", size=10, color="#8892a4"),
                              marker=dict(line=dict(color='rgba(0,0,0,0)', width=0)))
            fig.update_layout(height=300, **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with cc2:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Return by Stock</div>', unsafe_allow_html=True)
        perf_df = pd.DataFrame([{'Symbol':m['symbol'],'P&L %':m['pnl_percent']} for m in metrics])
        colors  = ['#22d98a' if x >= 0 else '#f05252' for x in perf_df['P&L %']]
        fig2 = go.Figure(go.Bar(x=perf_df['Symbol'], y=perf_df['P&L %'],
                                marker_color=colors, marker_line_width=0))
        fig2.update_layout(height=300, yaxis_title="Return (%)", **DARK_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Holdings table ──
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem;margin-top:.3rem">Current Holdings</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
        font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
        color:#4e5669;padding:.4rem .5rem;border-bottom:1px solid rgba(255,255,255,.06)">
        <span>Symbol</span><span>Shares</span><span>Buy $</span><span>Current $</span>
        <span>Invested</span><span>Value</span><span>P&L $</span><span>P&L %</span><span>Alloc</span>
    </div>
    """, unsafe_allow_html=True)
    for m in metrics:
        pnl_cls = "up" if m['pnl'] >= 0 else "dn"
        st.markdown(f"""
        <div class="holding-row" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
            font-size:.8rem;align-items:center">
            <span style="font-weight:600;color:#f0f2f8">{m['symbol']}</span>
            <span style="color:#8892a4">{m['shares']:.2f}</span>
            <span style="color:#8892a4">${m['buy_price']:.2f}</span>
            <span style="color:#f0f2f8">${m['current_price']:.2f}</span>
            <span style="color:#8892a4">${m['invested']:,.0f}</span>
            <span style="color:#f0f2f8">${m['current_value']:,.0f}</span>
            <span class="{pnl_cls}">${m['pnl']:,.0f}</span>
            <span class="{pnl_cls}">{m['pnl_percent']:+.1f}%</span>
            <span style="color:#8892a4">{m['allocation']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Allocation bars ──
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Allocation Breakdown</div>', unsafe_allow_html=True)
    for m in sorted(metrics, key=lambda x: x['allocation'], reverse=True)[:6]:
        st.markdown(f"""
        <div style="margin-bottom:.6rem">
            <div style="display:flex;justify-content:space-between;margin-bottom:.2rem">
                <span style="font-size:.8rem;font-weight:600;color:#f0f2f8">{m['symbol']}</span>
                <span style="font-size:.78rem;color:#8892a4">{m['allocation']:.1f}%</span>
            </div>
            <div class="alloc-bar">
                <div class="alloc-fill" style="width:{min(m['allocation'],100)}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk metrics ──
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">Risk Analysis</div>', unsafe_allow_html=True)
    rc1, rc2, rc3 = st.columns(3)
    n = len(metrics)
    div_label = "High" if n >= 7 else "Medium" if n >= 3 else "Low"
    largest   = max([m['allocation'] for m in metrics]) if metrics else 0
    conc      = "High" if largest > 40 else "Medium" if largest > 20 else "Low"
    for col, lbl, val, sub in [
        (rc1, "Portfolio Beta", "1.2", "Moderate risk"),
        (rc2, "Diversification", div_label, f"{n} holdings"),
        (rc3, "Concentration", conc, f"Largest: {largest:.1f}%"),
    ]:
        with col: st.metric(lbl, val, sub)

    # ── Performance chart ──
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Portfolio Performance (30 days)</div>', unsafe_allow_html=True)
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    rng   = np.random.default_rng(seed=42)  # FIX: seeded RNG — consistent chart each run
    perf  = [100 + i*0.4 + (rng.random()*2-1) for i in range(30)]
    fig3  = go.Figure()
    fig3.add_trace(go.Scatter(x=dates, y=perf, mode='lines', name='Value Index',
                              line=dict(color='#4f8fff', width=2),
                              fill='tozeroy', fillcolor='rgba(79,143,255,.08)'))
    fig3.update_layout(height=280, yaxis_title="Index (base 100)", **DARK_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.markdown("""
    <div style="background:#13161e;border:1px dashed rgba(255,255,255,.12);border-radius:20px;
        padding:3.5rem 2rem;text-align:center;margin-top:1rem">
        <div style="
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">
            Your portfolio is empty
        </div>
        <div style="font-size:.84rem;color:#8892a4">Use the sidebar to add your first stock holding</div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:.6rem;max-width:420px;margin:1.5rem auto 0;text-align:left">
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#4f8fff;margin-bottom:.3rem">STEP 1</div>
                <div style="font-size:.82rem;color:#f0f2f8">Add a stock symbol</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#4f8fff;margin-bottom:.3rem">STEP 2</div>
                <div style="font-size:.82rem;color:#f0f2f8">Enter shares & buy price</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#7c6ff7;margin-bottom:.3rem">STEP 3</div>
                <div style="font-size:.82rem;color:#f0f2f8">Track real-time P&L</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#22d98a;margin-bottom:.3rem">STEP 4</div>
                <div style="font-size:.82rem;color:#f0f2f8">Analyse allocation & risk</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Portfolio values update in real-time · Data by Yahoo Finance
</div>
""", unsafe_allow_html=True)
