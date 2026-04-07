"""
Portfolio Tracker  ·  pages/2_Portfolio.py
DO NOT call st.set_page_config() here — it lives only in app.py.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime
import json
import os
import pathlib

from utils.styling import apply_css, DARK_LAYOUT
apply_css()

# ── Portfolio persistence ──────────────────────────────────────────────────────
PORTFOLIO_FILE = str(pathlib.Path(__file__).parent.parent / "data" / "portfolio_data.json")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}


def save_portfolio() -> None:
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(st.session_state.portfolio, f, indent=2)


def load_portfolio() -> None:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            st.session_state.portfolio = json.load(f)


load_portfolio()


@st.cache_data(ttl=60)
def get_price(symbol: str) -> float | None:
    try:
        return float(yf.Ticker(symbol).history(period="1d")["Close"].iloc[-1])
    except Exception:
        return None


def calc_metrics(holdings: list) -> tuple:
    """Return (rows, total_value, total_pnl, total_pnl_pct)."""
    cash       = st.session_state.portfolio["cash_balance"]
    total_val  = cash
    total_inv  = 0.0
    rows: list = []

    for h in holdings:
        price = get_price(h["symbol"])
        if price is None:
            continue
        cur  = h["shares"] * price
        inv  = h["shares"] * h["buy_price"]
        pnl  = cur - inv
        rows.append({
            **h,
            "current_price": price,
            "current_value": cur,
            "invested":      inv,
            "pnl":           pnl,
            "pnl_percent":   (pnl / inv * 100) if inv else 0.0,
            "allocation":    0.0,  # filled below
        })
        total_val += cur
        total_inv += inv

    for r in rows:
        r["allocation"] = (r["current_value"] / total_val * 100) if total_val else 0.0

    base        = total_inv + cash
    total_pnl   = total_val - base
    total_pnl_p = (total_pnl / base * 100) if base else 0.0
    return rows, total_val, total_pnl, total_pnl_p


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem .4rem .6rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#22d98a);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">💼</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;
                color:#f0f2f8!important">Portfolio</div>
        </div>
        <div class="nav-group">Actions</div>
        <div class="nav-item active">💼 Holdings</div>
        <div class="nav-item">📈 Performance</div>
        <div class="nav-item">⚠️ Risk</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.4rem 0 .8rem">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;'
                'text-transform:uppercase;color:#4e5669;padding:.3rem .4rem .4rem">Add Holding</div>',
                unsafe_allow_html=True)
    with st.form("add_holding"):
        sym   = st.text_input("Symbol", placeholder="AAPL, TSLA…")
        shrs  = st.number_input("Shares", min_value=0.01, step=0.01, value=1.0)
        bp    = st.number_input("Buy Price ($)", min_value=0.01, step=0.01, value=100.0)
        bdate = st.date_input("Purchase Date", datetime.now())
        if st.form_submit_button("➕ Add Holding", use_container_width=True):
            if sym and shrs > 0 and bp > 0:
                st.session_state.portfolio["holdings"].append({
                    "symbol":   sym.upper().strip(),
                    "shares":   shrs,
                    "buy_price": bp,
                    "buy_date":  bdate.strftime("%Y-%m-%d"),
                })
                save_portfolio()
                st.success(f"Added {shrs} × {sym.upper()}")
                st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;'
                'text-transform:uppercase;color:#4e5669;padding:.1rem .4rem .3rem">Cash Balance ($)</div>',
                unsafe_allow_html=True)
    cash_input = st.number_input("", value=float(st.session_state.portfolio["cash_balance"]),
                                 step=100.0, label_visibility="collapsed")
    if cash_input != st.session_state.portfolio["cash_balance"]:
        st.session_state.portfolio["cash_balance"] = cash_input
        save_portfolio()
        st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.6rem 0">', unsafe_allow_html=True)
    if st.button("🗑️ Reset Portfolio", use_container_width=True):
        st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}
        save_portfolio()
        st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
        color:#f0f2f8;line-height:1">Portfolio Tracker</div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">
        Real-time P&amp;L, allocation &amp; risk overview</div>
</div>
""", unsafe_allow_html=True)

# ── Main ───────────────────────────────────────────────────────────────────────
holdings = st.session_state.portfolio["holdings"]

if holdings:
    metrics, total_val, total_pnl, total_pnl_pct = calc_metrics(holdings)
    total_invested = sum(m["invested"] for m in metrics)

    # ── Summary stat cards ──────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns(4)
    pnl_color  = "#22d98a" if total_pnl >= 0 else "#f05252"
    pnl_arrow  = "▲" if total_pnl >= 0 else "▼"

    for col, lbl, val, color in [
        (sc1, "Total Value",    f"${total_val:,.2f}",                                 "#4f8fff"),
        (sc2, "Total P&L",     f"{pnl_arrow} ${abs(total_pnl):,.2f} ({total_pnl_pct:+.2f}%)", pnl_color),
        (sc3, "Total Invested", f"${total_invested:,.2f}",                            "#f5a623"),
        (sc4, "Cash Balance",   f"${st.session_state.portfolio['cash_balance']:,.2f}", "#22d98a"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">{lbl}</div>
                <div class="stat-value" style="color:{color};font-size:1.5rem">{val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────────────────────
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                    'color:#f0f2f8;margin-bottom:.5rem">Portfolio Allocation</div>', unsafe_allow_html=True)
        alloc_df = pd.DataFrame([{"Symbol": m["symbol"], "Allocation": m["allocation"]}
                                 for m in metrics if m["allocation"] > 0])
        if not alloc_df.empty:
            fig = px.pie(alloc_df, values="Allocation", names="Symbol", hole=0.55,
                         color_discrete_sequence=["#4f8fff","#7c6ff7","#22d98a","#f5a623","#f05252","#ec4899"])
            fig.update_traces(textfont=dict(family="DM Sans", size=10, color="#8892a4"),
                              marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)))
            fig.update_layout(height=300, **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with cc2:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                    'color:#f0f2f8;margin-bottom:.5rem">P&L by Stock (%)</div>', unsafe_allow_html=True)
        perf_df = pd.DataFrame([{"Symbol": m["symbol"], "Return %": m["pnl_percent"]} for m in metrics])
        colors  = ["#22d98a" if x >= 0 else "#f05252" for x in perf_df["Return %"]]
        fig2 = go.Figure(go.Bar(x=perf_df["Symbol"], y=perf_df["Return %"],
                                marker_color=colors, marker_line_width=0))
        fig2.update_layout(height=300, yaxis_title="Return (%)", **DARK_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Holdings table ──────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                'color:#f0f2f8;margin-bottom:.5rem">Holdings</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
        font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
        color:#4e5669;padding:.4rem .5rem;border-bottom:1px solid rgba(255,255,255,.06)">
        <span>Symbol</span><span>Shares</span><span>Buy $</span><span>Now $</span>
        <span>Invested</span><span>Value</span><span>P&L $</span><span>P&L %</span><span>Alloc</span>
    </div>
    """, unsafe_allow_html=True)
    for m in metrics:
        cls = "up" if m["pnl"] >= 0 else "down"
        st.markdown(f"""
        <div class="holding-row" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;
            font-size:.8rem;align-items:center">
            <span style="font-weight:600;color:#f0f2f8">{m['symbol']}</span>
            <span style="color:#8892a4">{m['shares']:.2f}</span>
            <span style="color:#8892a4">${m['buy_price']:.2f}</span>
            <span style="color:#f0f2f8">${m['current_price']:.2f}</span>
            <span style="color:#8892a4">${m['invested']:,.0f}</span>
            <span style="color:#f0f2f8">${m['current_value']:,.0f}</span>
            <span class="{cls}">${m['pnl']:,.0f}</span>
            <span class="{cls}">{m['pnl_percent']:+.1f}%</span>
            <span style="color:#8892a4">{m['allocation']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Allocation bars ────────────────────────────────────────────────────────
    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                'color:#f0f2f8;margin-bottom:.5rem">Allocation Breakdown</div>', unsafe_allow_html=True)
    for m in sorted(metrics, key=lambda x: x["allocation"], reverse=True)[:8]:
        st.markdown(f"""
        <div style="margin-bottom:.6rem">
            <div style="display:flex;justify-content:space-between;margin-bottom:.2rem">
                <span style="font-size:.8rem;font-weight:600;color:#f0f2f8">{m['symbol']}</span>
                <span style="font-size:.78rem;color:#8892a4">{m['allocation']:.1f}%</span>
            </div>
            <div class="alloc-bar">
                <div class="alloc-fill" style="width:{min(m['allocation'], 100):.1f}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Risk summary ───────────────────────────────────────────────────────────
    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                'color:#f0f2f8;margin-bottom:.6rem">Risk Overview</div>', unsafe_allow_html=True)
    n       = len(metrics)
    largest = max((m["allocation"] for m in metrics), default=0)
    div_lbl = "Good — 7+ stocks" if n >= 7 else "Moderate" if n >= 3 else "Low — add more stocks"
    conc_lbl= "Concentrated" if largest > 40 else "Balanced" if largest < 25 else "Moderate"

    rc1, rc2, rc3 = st.columns(3)
    for col, lbl, val, sub in [
        (rc1, "Holdings",       str(n),        div_lbl),
        (rc2, "Largest Alloc",  f"{largest:.1f}%", conc_lbl),
        (rc3, "Cash Weight",
              f"{st.session_state.portfolio['cash_balance']/total_val*100:.1f}%" if total_val else "—",
              "Uninvested cash"),
    ]:
        with col:
            st.metric(lbl, val, sub)

else:
    # ── Empty state ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:#13161e;border:1px dashed rgba(255,255,255,.12);border-radius:20px;
        padding:3.5rem 2rem;text-align:center;margin-top:1rem">
        <div style="font-size:2.5rem;margin-bottom:1rem">💼</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
            color:#f0f2f8;margin-bottom:.5rem">Your portfolio is empty</div>
        <div style="font-size:.84rem;color:#8892a4">
            Use the sidebar to add your first stock holding</div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:.6rem;
            max-width:420px;margin:1.5rem auto 0;text-align:left">
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#4f8fff;margin-bottom:.3rem">STEP 1</div>
                <div style="font-size:.82rem;color:#f0f2f8">Enter a stock symbol</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#4f8fff;margin-bottom:.3rem">STEP 2</div>
                <div style="font-size:.82rem;color:#f0f2f8">Enter shares &amp; buy price</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#7c6ff7;margin-bottom:.3rem">STEP 3</div>
                <div style="font-size:.82rem;color:#f0f2f8">Track real-time P&amp;L</div>
            </div>
            <div style="background:#1c2030;border:1px solid rgba(255,255,255,.07);border-radius:12px;padding:1rem">
                <div style="font-size:.72rem;font-weight:600;color:#22d98a;margin-bottom:.3rem">STEP 4</div>
                <div style="font-size:.82rem;color:#f0f2f8">Analyse risk &amp; allocation</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Portfolio values update every ~60s · Data by Yahoo Finance · Not financial advice
</div>
""", unsafe_allow_html=True)
