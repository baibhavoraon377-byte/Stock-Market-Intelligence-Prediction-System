"""
Portfolio Tracker with Benchmark vs S&P 500 + CSV/Excel Export
pages/2_Portfolio.py

FIXES:
  - Pie chart percentage labels changed to black (color="#000000") as requested.
  - All emojis removed from labels, tabs, buttons, and messages.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from datetime import datetime
import json, os, pathlib, io

import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from utils.styling import apply_css, DARK_LAYOUT
apply_css()

# ── Persistence ────────────────────────────────────────────────────────────────
PORTFOLIO_FILE = str(pathlib.Path(__file__).parent.parent / "data" / "portfolio_data.json")

if "portfolio" not in st.session_state:
    st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}

def save():
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(st.session_state.portfolio, f, indent=2)

def load():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            st.session_state.portfolio = json.load(f)
load()

@st.cache_data(ttl=60)
def price(sym):
    try: return float(yf.Ticker(sym).history(period="1d")["Close"].iloc[-1])
    except: return None

@st.cache_data(ttl=300)
def hist_price(sym, period="1y"):
    try: return yf.Ticker(sym).history(period=period)["Close"]
    except: return None

def calc(holdings):
    cash = st.session_state.portfolio["cash_balance"]
    tv, ti, rows = cash, 0.0, []
    for h in holdings:
        p = price(h["symbol"])
        if not p: continue
        cur = h["shares"] * p; inv = h["shares"] * h["buy_price"]; pnl = cur - inv
        rows.append({**h, "current_price": p, "current_value": cur, "invested": inv,
                     "pnl": pnl, "pnl_pct": (pnl / inv * 100) if inv else 0, "allocation": 0})
        tv += cur; ti += inv
    for r in rows:
        r["allocation"] = (r["current_value"] / tv * 100) if tv else 0
    base = ti + cash; total_pnl = tv - base
    return rows, tv, total_pnl, (total_pnl / base * 100) if base else 0

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#22d98a);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">P</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">Portfolio</div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .8rem">
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .4rem">Add Holding</div>', unsafe_allow_html=True)
    with st.form("add"):
        sym   = st.text_input("Symbol", placeholder="AAPL…")
        shrs  = st.number_input("Shares", min_value=0.01, step=0.01, value=1.0)
        bp    = st.number_input("Buy Price ($)", min_value=0.01, step=0.01, value=100.0)
        bdate = st.date_input("Date", datetime.now())
        if st.form_submit_button("Add", use_container_width=True) and sym and shrs > 0 and bp > 0:
            st.session_state.portfolio["holdings"].append(
                {"symbol": sym.upper().strip(), "shares": shrs, "buy_price": bp,
                 "buy_date": bdate.strftime("%Y-%m-%d")})
            save(); st.success(f"Added {shrs} x {sym.upper()}"); st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.5rem 0">', unsafe_allow_html=True)
    cash_in = st.number_input("Cash Balance ($)", value=float(st.session_state.portfolio["cash_balance"]), step=100.0)
    if cash_in != st.session_state.portfolio["cash_balance"]:
        st.session_state.portfolio["cash_balance"] = cash_in; save(); st.rerun()

    bench_sym = st.text_input("Benchmark", "SPY").upper()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.5rem 0">', unsafe_allow_html=True)
    if st.button("Reset Portfolio", use_container_width=True):
        st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}; save(); st.rerun()

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .3rem">Portfolio Tracker</div>'
            '<div style="font-size:.82rem;color:#8892a4">Real-time P&amp;L · Allocation · Benchmark comparison · Export</div>',
            unsafe_allow_html=True)

holdings = st.session_state.portfolio["holdings"]

if not holdings:
    st.markdown("""<div style="background:#13161e;border:1px dashed rgba(255,255,255,.12);border-radius:20px;
    padding:3rem 2rem;text-align:center;margin-top:1rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8">Portfolio is empty</div>
    <div style="font-size:.84rem;color:#8892a4;margin-top:.4rem">Use the sidebar to add your first holding</div>
    </div>""", unsafe_allow_html=True); st.stop()

metrics, tv, total_pnl, total_pnl_pct = calc(holdings)
total_inv = sum(m["invested"] for m in metrics)
pnl_color = "#22d98a" if total_pnl >= 0 else "#f05252"

# ── Stat cards ─────────────────────────────────────────────────────────────────
for col, lbl, val, color in zip(st.columns(4),
    ["Total Value","Total P&L","Total Invested","Cash Balance"],
    [f"${tv:,.2f}",
     f"{'Up' if total_pnl>=0 else 'Down'} ${abs(total_pnl):,.2f} ({total_pnl_pct:+.2f}%)",
     f"${total_inv:,.2f}",
     f"${st.session_state.portfolio['cash_balance']:,.2f}"],
    ["#4f8fff", pnl_color, "#f5a623", "#22d98a"]):
    with col:
        st.markdown(f'<div class="stat-card"><div class="stat-label">{lbl}</div>'
                    f'<div class="stat-value" style="color:{color};font-size:1.5rem">{val}</div></div>',
                    unsafe_allow_html=True)

st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Holdings","Performance","Risk","Reports & Export"])

# ── HOLDINGS ──────────────────────────────────────────────────────────────────
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        alloc_df = pd.DataFrame([{"Symbol": m["symbol"], "Allocation": m["allocation"]}
                                  for m in metrics if m["allocation"] > 0])
        if not alloc_df.empty:
            fig = px.pie(alloc_df, values="Allocation", names="Symbol", hole=.55,
                         color_discrete_sequence=["#4f8fff","#7c6ff7","#22d98a","#f5a623","#f05252","#ec4899"])
            fig.update_traces(
                # FIX: all percentage labels shown in black as requested
                textfont=dict(size=11, color="#000000"),
                textinfo="percent+label",
                marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            )
            fig.update_layout(height=280, title="Allocation",
                              title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        perf_df = pd.DataFrame([{"Symbol": m["symbol"], "Return %": m["pnl_pct"]} for m in metrics])
        colors  = ["#22d98a" if x >= 0 else "#f05252" for x in perf_df["Return %"]]
        fig2    = go.Figure(go.Bar(x=perf_df.Symbol, y=perf_df["Return %"],
                                   marker_color=colors, marker_line_width=0))
        fig2.update_layout(height=280, yaxis_title="Return %", title="P&L by Stock",
                           title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.3rem">Holdings Detail</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:#4e5669;padding:.4rem .5rem;border-bottom:1px solid rgba(255,255,255,.06)"><span>Symbol</span><span>Shares</span><span>Buy $</span><span>Now $</span><span>Invested</span><span>Value</span><span>P&L $</span><span>P&L %</span><span>Alloc</span></div>', unsafe_allow_html=True)
    for m in metrics:
        cls = "up" if m["pnl"] >= 0 else "down"
        st.markdown(f'<div class="holding-row" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1.2fr 1.2fr 1fr 1fr 1fr;font-size:.8rem;align-items:center"><span style="font-weight:600;color:#f0f2f8">{m["symbol"]}</span><span style="color:#8892a4">{m["shares"]:.2f}</span><span style="color:#8892a4">${m["buy_price"]:.2f}</span><span style="color:#f0f2f8">${m["current_price"]:.2f}</span><span style="color:#8892a4">${m["invested"]:,.0f}</span><span style="color:#f0f2f8">${m["current_value"]:,.0f}</span><span class="{cls}">${m["pnl"]:,.0f}</span><span class="{cls}">{m["pnl_pct"]:+.1f}%</span><span style="color:#8892a4">{m["allocation"]:.1f}%</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    for m in sorted(metrics, key=lambda x: x["allocation"], reverse=True)[:8]:
        st.markdown(f'<div style="margin-bottom:.5rem"><div style="display:flex;justify-content:space-between;margin-bottom:.2rem"><span style="font-size:.8rem;font-weight:600;color:#f0f2f8">{m["symbol"]}</span><span style="font-size:.78rem;color:#8892a4">{m["allocation"]:.1f}%</span></div><div class="alloc-bar"><div class="alloc-fill" style="width:{min(m["allocation"],100):.1f}%"></div></div></div>', unsafe_allow_html=True)

# ── PERFORMANCE ────────────────────────────────────────────────────────────────
with tab2:
    perf_period = st.selectbox("Performance Period", ["1mo","3mo","6mo","1y"], index=2, key="pperf")

    with st.spinner("Building performance chart…"):
        port_vals = {}
        for m in metrics:
            h = hist_price(m["symbol"], perf_period)
            if h is not None:
                port_vals[m["symbol"]] = h * m["shares"]
        spy_h = hist_price(bench_sym, perf_period)

        if port_vals:
            port_df   = pd.DataFrame(port_vals).sum(axis=1) + st.session_state.portfolio["cash_balance"]
            port_norm = port_df / port_df.iloc[0] * 100

            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=port_norm.index, y=port_norm.values, name="My Portfolio",
                                      line=dict(color="#4f8fff",width=2.5), fill="tozeroy",
                                      fillcolor="rgba(79,143,255,.06)"))
            if spy_h is not None:
                spy_norm = spy_h / spy_h.iloc[0] * 100
                aligned  = spy_norm.reindex(port_norm.index, method="ffill").dropna()
                fig3.add_trace(go.Scatter(x=aligned.index, y=aligned.values, name=bench_sym,
                                          line=dict(color="#8892a4",width=1.5,dash="dot")))
            fig3.update_layout(height=380, title=f"Portfolio vs {bench_sym} ({perf_period})",
                               title_font=dict(family="Syne",size=14,color="#f0f2f8"),
                               yaxis_title="Index (Base=100)", **DARK_LAYOUT)
            st.plotly_chart(fig3, use_container_width=True)

            port_ret = (port_df.iloc[-1] / port_df.iloc[0] - 1) * 100
            bm_ret   = (spy_h.iloc[-1] / spy_h.iloc[0] - 1) * 100 if spy_h is not None else 0
            alpha    = port_ret - bm_ret
            for col, lbl, val, color in zip(st.columns(4),
                ["Portfolio Return","Benchmark Return","Alpha","Portfolio P&L $"],
                [f"{port_ret:+.1f}%", f"{bm_ret:+.1f}%", f"{alpha:+.1f}%",
                 f"${port_df.iloc[-1]-port_df.iloc[0]:+,.0f}"],
                ["#22d98a" if port_ret > 0 else "#f05252",
                 "#22d98a" if bm_ret > 0 else "#f05252",
                 "#22d98a" if alpha > 0 else "#f05252", "#4f8fff"]):
                col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{color}">{val}</h2></div>', unsafe_allow_html=True)

# ── RISK ──────────────────────────────────────────────────────────────────────
with tab3:
    n       = len(metrics)
    largest = max((m["allocation"] for m in metrics), default=0)
    cash_w  = st.session_state.portfolio["cash_balance"] / tv * 100 if tv else 0
    div_lbl = "Well diversified" if n >= 7 else "Moderate" if n >= 3 else "Concentrated"
    conc_lbl= "High concentration" if largest > 40 else "Balanced" if largest < 25 else "Moderate"

    c1, c2, c3, c4 = st.columns(4)
    for col, lbl, val, sub in [
        (c1, "Holdings",         str(n),         div_lbl),
        (c2, "Largest Position", f"{largest:.1f}%", conc_lbl),
        (c3, "Cash Weight",      f"{cash_w:.1f}%",  "Uninvested"),
        (c4, "Positions",        f"{n}",             "Unique"),
    ]:
        with col: st.metric(lbl, val, sub)

    rets_list = []
    for m in metrics:
        h = hist_price(m["symbol"], "1y")
        if h is not None:
            rets_list.append(h.pct_change().rename(m["symbol"]) * m["allocation"] / 100)
    if rets_list:
        port_r   = pd.concat(rets_list, axis=1).sum(axis=1).dropna()
        port_vol = port_r.std() * np.sqrt(252) * 100
        port_sr  = (port_r.mean() * 252 / port_r.std() * np.sqrt(252)) if port_r.std() > 0 else 0
        cum      = (1 + port_r).cumprod()
        port_mdd = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100

        pm1, pm2, pm3 = st.columns(3)
        for col, lbl, val in [
            (pm1, "Est. Portfolio Vol",  f"{port_vol:.1f}%/yr"),
            (pm2, "Portfolio Sharpe",    f"{port_sr:.2f}"),
            (pm3, "Portfolio Max DD",    f"{port_mdd:.1f}%"),
        ]:
            col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>', unsafe_allow_html=True)

# ── REPORTS & EXPORT ──────────────────────────────────────────────────────────
with tab4:
    st.markdown('<div style="font-size:.82rem;font-weight:600;color:#f0f2f8;margin-bottom:.6rem">Export Portfolio Data</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    df_export = pd.DataFrame([{
        "Symbol": m["symbol"], "Shares": m["shares"], "Buy Price": m["buy_price"],
        "Current Price": m["current_price"], "Invested": round(m["invested"], 2),
        "Current Value": round(m["current_value"], 2), "PnL $": round(m["pnl"], 2),
        "PnL %": round(m["pnl_pct"], 2), "Allocation %": round(m["allocation"], 2),
        "Buy Date": m.get("buy_date", "—"),
    } for m in metrics])

    with c1:
        st.markdown('<div style="font-size:.78rem;color:#8892a4;margin-bottom:.3rem">CSV Export</div>', unsafe_allow_html=True)
        st.download_button("Download Holdings CSV", df_export.to_csv(index=False).encode(),
                           file_name="portfolio_holdings.csv", mime="text/csv",
                           use_container_width=True)

    with c2:
        st.markdown('<div style="font-size:.78rem;color:#8892a4;margin-bottom:.3rem">Excel Report</div>', unsafe_allow_html=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_export.to_excel(w, sheet_name="Holdings", index=False)
            pd.DataFrame([{
                "Total Value": round(tv, 2), "Total Invested": round(total_inv, 2),
                "Total PnL": round(total_pnl, 2), "PnL %": round(total_pnl_pct, 2),
                "Cash Balance": st.session_state.portfolio["cash_balance"],
            }]).to_excel(w, sheet_name="Summary", index=False)
        st.download_button("Download Excel Report", buf.getvalue(),
                           file_name="portfolio_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    st.dataframe(df_export, use_container_width=True, hide_index=True)

st.markdown('<div style="text-align:center;padding:1rem 0 .2rem;font-size:.72rem;color:#4e5669">Portfolio values update ~60s · Data by Yahoo Finance · Not financial advice</div>', unsafe_allow_html=True)
