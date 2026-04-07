"""
Portfolio Tracker — pages/2_Portfolio.py

Fixes & improvements:
  - "Add Holdings" uses a stock picker (selectbox) from a preset universe
    PLUS a free-text field, so users can choose stocks and add them easily
  - Pie chart % labels in BLACK (color="#000000") as requested
  - Benchmark comparison vs SPY (or custom)
  - CSV + Excel export of holdings
  - Remove individual holding button
  - Sidebar toggle always visible via styling.py
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

# ── Persistence ───────────────────────────────────────────────────────────────
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

# ── Data helpers ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_price(sym: str) -> float | None:
    try:
        return float(yf.Ticker(sym).history(period="1d")["Close"].iloc[-1])
    except:
        return None

@st.cache_data(ttl=300)
def get_hist_close(sym: str, period: str = "1y") -> pd.Series | None:
    try:
        return yf.Ticker(sym).history(period=period)["Close"]
    except:
        return None

def calc(holdings: list) -> tuple:
    cash = st.session_state.portfolio["cash_balance"]
    tv, ti, rows = cash, 0.0, []
    for h in holdings:
        p = get_price(h["symbol"])
        if not p: continue
        cur = h["shares"] * p; inv = h["shares"] * h["buy_price"]
        pnl = cur - inv; pnl_pct = (pnl / inv * 100) if inv else 0.0
        tv += cur; ti += inv
        rows.append({**h, "current_price": p, "current_value": cur,
                     "invested": inv, "pnl": pnl, "pnl_percent": pnl_pct, "allocation": 0.0})
    for r in rows:
        r["allocation"] = (r["current_value"] / tv * 100) if tv else 0.0
    base = ti + cash
    pnl_total = tv - base
    pnl_pct   = (pnl_total / base * 100) if base else 0.0
    return rows, tv, pnl_total, pnl_pct

# ── Preset stock universe for picker ─────────────────────────────────────────
PRESET_STOCKS = {
    "── Tech ──": "",
    "Apple (AAPL)": "AAPL", "Microsoft (MSFT)": "MSFT", "NVIDIA (NVDA)": "NVDA",
    "Google (GOOGL)": "GOOGL", "Meta (META)": "META", "Amazon (AMZN)": "AMZN",
    "Tesla (TSLA)": "TSLA", "Netflix (NFLX)": "NFLX", "AMD": "AMD", "Intel (INTC)": "INTC",
    "── Finance ──": "",
    "JPMorgan (JPM)": "JPM", "Goldman Sachs (GS)": "GS", "Visa (V)": "V", "Mastercard (MA)": "MA",
    "── Healthcare ──": "",
    "J&J (JNJ)": "JNJ", "Pfizer (PFE)": "PFE", "UnitedHealth (UNH)": "UNH",
    "── Consumer ──": "",
    "Walmart (WMT)": "WMT", "Costco (COST)": "COST", "Nike (NKE)": "NKE",
    "── Custom ──": "__custom__",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#4f8fff,#22d98a);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">💼</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">Portfolio</div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .8rem">
    """, unsafe_allow_html=True)

    # ── ADD HOLDING (stock picker + form) ─────────────────────────────────────
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.2rem .4rem .4rem">Add Holding</div>', unsafe_allow_html=True)

    # Stock picker dropdown
    picker_choice = st.selectbox(
        "Choose from list",
        options=list(PRESET_STOCKS.keys()),
        index=1,
        label_visibility="collapsed",
        key="stock_picker",
    )
    picked_sym = PRESET_STOCKS.get(picker_choice, "")

    with st.form("add_holding", clear_on_submit=True):
        # If "Custom" was picked or it's a divider, show text input
        if picked_sym in ("__custom__", ""):
            sym = st.text_input("Symbol", placeholder="e.g. BABA, BTC-USD, INFY.NS")
        else:
            sym = st.text_input("Symbol", value=picked_sym)

        c1, c2 = st.columns(2)
        with c1: shrs  = st.number_input("Shares", min_value=0.01, step=1.0, value=1.0)
        with c2: bp    = st.number_input("Buy Price ($)", min_value=0.01, step=0.01, value=100.0)
        bdate = st.date_input("Buy Date", datetime.now())

        # Auto-fill current price button inside form
        fill_price = st.form_submit_button("Fetch Current Price", use_container_width=False)

        submitted = st.form_submit_button("Add to Portfolio", use_container_width=True, type="primary")

        if fill_price and sym:
            p = get_price(sym.upper().strip())
            if p:
                st.info(f"Current price of {sym.upper()}: ${p:.2f}")

        if submitted and sym and shrs > 0 and bp > 0:
            st.session_state.portfolio["holdings"].append({
                "symbol":   sym.upper().strip(),
                "shares":   shrs,
                "buy_price": bp,
                "buy_date":  bdate.strftime("%Y-%m-%d"),
            })
            save()
            st.success(f"Added {shrs} × {sym.upper()}")
            st.rerun()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.5rem 0">', unsafe_allow_html=True)

    # Cash balance
    st.markdown('<div style="font-size:.68rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:#4e5669;padding:.1rem .4rem .2rem">Cash Balance</div>', unsafe_allow_html=True)
    cash_in = st.number_input("", value=float(st.session_state.portfolio["cash_balance"]),
                               step=100.0, min_value=0.0, label_visibility="collapsed", key="cash_input")
    if cash_in != st.session_state.portfolio["cash_balance"]:
        st.session_state.portfolio["cash_balance"] = cash_in; save(); st.rerun()

    # Benchmark
    bench_sym = st.text_input("Benchmark", "SPY").upper().strip()

    st.markdown('<hr style="border-color:rgba(255,255,255,.06);margin:.5rem 0">', unsafe_allow_html=True)
    if st.button("Reset Portfolio", use_container_width=True):
        st.session_state.portfolio = {"holdings": [], "cash_balance": 10_000.0}; save(); st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.6rem 0 .3rem">
  <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">Portfolio Tracker</div>
  <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">Real-time P&amp;L · Allocation · Benchmark · Export</div>
</div>
""", unsafe_allow_html=True)

holdings = st.session_state.portfolio["holdings"]

if not holdings:
    st.markdown("""
    <div style="background:#13161e;border:1px dashed rgba(255,255,255,.12);border-radius:20px;
      padding:3.5rem 2rem;text-align:center;margin-top:1rem">
      <div style="font-size:2rem;margin-bottom:1rem">💼</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">
        Your portfolio is empty</div>
      <div style="font-size:.84rem;color:#8892a4">Use the sidebar — pick a stock from the dropdown, enter shares and buy price, then click <strong>Add to Portfolio</strong>.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

metrics, total_val, total_pnl, total_pnl_pct = calc(holdings)
total_inv = sum(m["invested"] for m in metrics)
pnl_color = "#22d98a" if total_pnl >= 0 else "#f05252"
pnl_icon  = "▲" if total_pnl >= 0 else "▼"

# ── Stat cards ─────────────────────────────────────────────────────────────────
for col, lbl, val, color in zip(st.columns(4),
    ["Total Portfolio Value","Total P&L","Total Invested","Cash Balance"],
    [f"${total_val:,.2f}",
     f"{pnl_icon} ${abs(total_pnl):,.2f}  ({total_pnl_pct:+.2f}%)",
     f"${total_inv:,.2f}",
     f"${st.session_state.portfolio['cash_balance']:,.2f}"],
    ["#4f8fff", pnl_color, "#f5a623", "#22d98a"]):
    with col:
        st.markdown(f'<div class="p-stat"><div class="p-stat-label">{lbl}</div><div class="p-stat-val" style="color:{color};font-size:1.5rem">{val}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["Holdings", "Performance & Benchmark", "Risk Analysis", "Export"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — HOLDINGS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    cc1, cc2 = st.columns(2)

    with cc1:
        alloc_df = pd.DataFrame([{"Symbol": m["symbol"], "Allocation": m["allocation"]}
                                  for m in metrics if m["allocation"] > 0])
        if not alloc_df.empty:
            fig_pie = px.pie(alloc_df, values="Allocation", names="Symbol", hole=0.55,
                             color_discrete_sequence=["#4f8fff","#7c6ff7","#22d98a","#f5a623","#f05252","#ec4899","#06b6d4"])
            fig_pie.update_traces(
                # All % labels in BLACK as requested
                textfont=dict(family="DM Sans", size=11, color="#000000"),
                textinfo="percent+label",
                marker=dict(line=dict(color="rgba(0,0,0,0)", width=0)),
            )
            fig_pie.update_layout(height=300, title="Portfolio Allocation", **DARK_LAYOUT)
            st.plotly_chart(fig_pie, use_container_width=True)

    with cc2:
        perf_df = pd.DataFrame([{"Symbol": m["symbol"], "P&L %": m["pnl_percent"]} for m in metrics])
        colors  = ["#22d98a" if x >= 0 else "#f05252" for x in perf_df["P&L %"]]
        fig_bar = go.Figure(go.Bar(x=perf_df["Symbol"], y=perf_df["P&L %"],
                                   marker_color=colors, marker_line_width=0))
        fig_bar.update_layout(height=300, yaxis_title="Return (%)", title="Return by Stock", **DARK_LAYOUT)
        st.plotly_chart(fig_bar, use_container_width=True)

    # Holdings table
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Current Holdings</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 0.7fr 0.8fr 0.8fr 1fr 1fr 0.8fr 0.8fr 0.6fr 0.5fr;
        font-size:.6rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
        color:#4e5669;padding:.35rem .5rem;border-bottom:1px solid rgba(255,255,255,.06)">
        <span>Symbol</span><span>Shares</span><span>Buy $</span><span>Now $</span>
        <span>Invested</span><span>Value</span><span>P&L $</span><span>P&L %</span>
        <span>Alloc</span><span>Del</span>
    </div>""", unsafe_allow_html=True)

    to_del = None
    for idx, m in enumerate(metrics):
        cls = "up" if m["pnl"] >= 0 else "dn"
        st.markdown(f"""
        <div class="holding-row" style="display:grid;grid-template-columns:1fr 0.7fr 0.8fr 0.8fr 1fr 1fr 0.8fr 0.8fr 0.6fr 0.5fr;
            font-size:.79rem;align-items:center">
            <span style="font-weight:600;color:#f0f2f8">{m['symbol']}</span>
            <span style="color:#8892a4">{m['shares']:.2f}</span>
            <span style="color:#8892a4">${m['buy_price']:.2f}</span>
            <span style="color:#f0f2f8">${m['current_price']:.2f}</span>
            <span style="color:#8892a4">${m['invested']:,.0f}</span>
            <span style="color:#f0f2f8">${m['current_value']:,.0f}</span>
            <span class="{cls}">${m['pnl']:,.0f}</span>
            <span class="{cls}">{m['pnl_percent']:+.1f}%</span>
            <span style="color:#8892a4">{m['allocation']:.1f}%</span>
            <span></span>
        </div>""", unsafe_allow_html=True)
        if st.button("✕", key=f"del_{idx}_{m['symbol']}", help=f"Remove {m['symbol']}"):
            to_del = m["symbol"]

    if to_del:
        st.session_state.portfolio["holdings"] = [
            h for h in st.session_state.portfolio["holdings"] if h["symbol"] != to_del]
        save(); st.rerun()

    # Allocation bars
    st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Allocation Breakdown</div>', unsafe_allow_html=True)
    for m in sorted(metrics, key=lambda x: x["allocation"], reverse=True)[:8]:
        st.markdown(f"""
        <div style="margin-bottom:.5rem">
          <div style="display:flex;justify-content:space-between;margin-bottom:.2rem">
            <span style="font-size:.8rem;font-weight:600;color:#f0f2f8">{m['symbol']}</span>
            <span style="font-size:.78rem;color:#8892a4">{m['allocation']:.1f}%</span>
          </div>
          <div class="alloc-bar"><div class="alloc-fill" style="width:{min(m['allocation'],100):.1f}%"></div></div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PERFORMANCE & BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    perf_period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y"], index=2, key="perf_p")

    with st.spinner("Building performance chart…"):
        port_vals = {}
        for m in metrics:
            h = get_hist_close(m["symbol"], perf_period)
            if h is not None:
                port_vals[m["symbol"]] = h * m["shares"]
        bm_h = get_hist_close(bench_sym, perf_period)

        if port_vals:
            port_series = pd.DataFrame(port_vals).sum(axis=1) + st.session_state.portfolio["cash_balance"]
            port_norm   = port_series / port_series.iloc[0] * 100

            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(x=port_norm.index, y=port_norm.values, name="My Portfolio",
                                          line=dict(color="#4f8fff",width=2.5), fill="tozeroy",
                                          fillcolor="rgba(79,143,255,.06)"))
            if bm_h is not None:
                bm_norm = bm_h / bm_h.iloc[0] * 100
                bm_al   = bm_norm.reindex(port_norm.index, method="ffill").dropna()
                fig_perf.add_trace(go.Scatter(x=bm_al.index, y=bm_al.values, name=bench_sym,
                                              line=dict(color="#8892a4",width=1.5,dash="dot")))
            fig_perf.update_layout(height=380, title=f"Portfolio vs {bench_sym} (Base=100)",
                                   title_font=dict(family="Syne",size=14,color="#f0f2f8"),
                                   yaxis_title="Index", **DARK_LAYOUT)
            st.plotly_chart(fig_perf, use_container_width=True)

            port_ret = (port_series.iloc[-1]/port_series.iloc[0]-1)*100
            bm_ret   = (bm_h.iloc[-1]/bm_h.iloc[0]-1)*100 if bm_h is not None else 0
            alpha    = port_ret - bm_ret

            for col, lbl, val, clr in zip(st.columns(4),
                ["Portfolio Return","Benchmark Return","Alpha","Portfolio P&L $"],
                [f"{port_ret:+.1f}%",f"{bm_ret:+.1f}%",f"{alpha:+.1f}%",
                 f"${port_series.iloc[-1]-port_series.iloc[0]:+,.0f}"],
                ["#22d98a" if port_ret>0 else "#f05252",
                 "#22d98a" if bm_ret>0 else "#f05252",
                 "#22d98a" if alpha>0 else "#f05252","#4f8fff"]):
                col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{clr}">{val}</h2></div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RISK ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    n       = len(metrics)
    largest = max([m["allocation"] for m in metrics], default=0)
    cash_w  = st.session_state.portfolio["cash_balance"] / total_val * 100 if total_val else 0
    div_lbl = "Good" if n >= 7 else "Moderate" if n >= 3 else "Concentrated"
    conc    = "High" if largest > 40 else "Moderate" if largest > 20 else "Diversified"

    rc1,rc2,rc3,rc4 = st.columns(4)
    for col,lbl,val,sub in [
        (rc1,"Holdings",str(n),div_lbl),
        (rc2,"Largest Position",f"{largest:.1f}%",conc),
        (rc3,"Cash Weight",f"{cash_w:.1f}%","Uninvested"),
        (rc4,"Positions",str(n),"Total"),
    ]:
        with col: st.metric(lbl, val, sub)

    # Portfolio volatility from historical returns
    rets_list = []
    for m in metrics:
        h = get_hist_close(m["symbol"], "1y")
        if h is not None:
            rets_list.append(h.pct_change().rename(m["symbol"]) * m["allocation"] / 100)
    if rets_list:
        port_r   = pd.concat(rets_list, axis=1).sum(axis=1).dropna()
        port_vol = port_r.std() * np.sqrt(252) * 100
        port_sh  = (port_r.mean() * 252 / port_r.std() * np.sqrt(252)) if port_r.std() > 0 else 0
        cum_r    = (1 + port_r).cumprod()
        port_mdd = ((cum_r - cum_r.expanding().max()) / cum_r.expanding().max()).min() * 100

        pm1,pm2,pm3 = st.columns(3)
        for col,lbl,val in [(pm1,"Portfolio Vol",f"{port_vol:.1f}%/yr"),
                            (pm2,"Portfolio Sharpe",f"{port_sh:.2f}"),
                            (pm3,"Portfolio Max DD",f"{port_mdd:.1f}%")]:
            col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>',unsafe_allow_html=True)

        # Volatility chart
        rv = port_r.rolling(20).std() * np.sqrt(252) * 100
        fig_rv = go.Figure(go.Scatter(x=rv.index,y=rv,fill="tozeroy",
                                       line=dict(color="#f5a623",width=2),fillcolor="rgba(245,166,35,.08)"))
        fig_rv.update_layout(height=240,title="Portfolio Rolling Volatility (20d annualised %)",
                             title_font=dict(family="Syne",size=13,color="#f0f2f8"),**DARK_LAYOUT)
        st.plotly_chart(fig_rv,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div style="font-size:.82rem;font-weight:600;color:#f0f2f8;margin-bottom:.6rem">Export Portfolio Data</div>', unsafe_allow_html=True)

    df_export = pd.DataFrame([{
        "Symbol":        m["symbol"],
        "Shares":        m["shares"],
        "Buy Price":     m["buy_price"],
        "Current Price": m["current_price"],
        "Invested":      round(m["invested"], 2),
        "Current Value": round(m["current_value"], 2),
        "PnL $":         round(m["pnl"], 2),
        "PnL %":         round(m["pnl_percent"], 2),
        "Allocation %":  round(m["allocation"], 2),
        "Buy Date":      m.get("buy_date", "—"),
    } for m in metrics])

    ec1, ec2 = st.columns(2)
    with ec1:
        st.download_button("Export CSV", df_export.to_csv(index=False).encode(),
                           file_name="portfolio.csv", mime="text/csv",
                           use_container_width=True)
    with ec2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df_export.to_excel(w, sheet_name="Holdings", index=False)
            pd.DataFrame([{
                "Total Value": round(total_val, 2),
                "Total Invested": round(total_inv, 2),
                "Total PnL": round(total_pnl, 2),
                "PnL %": round(total_pnl_pct, 2),
                "Cash": st.session_state.portfolio["cash_balance"],
            }]).to_excel(w, sheet_name="Summary", index=False)
        st.download_button("Export Excel", buf.getvalue(),
                           file_name="portfolio.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.dataframe(df_export, use_container_width=True, hide_index=True)

st.markdown('<div style="text-align:center;padding:1rem 0 .2rem;font-size:.72rem;color:#4e5669">Portfolio values refresh ~60 s · Data by Yahoo Finance · Not financial advice</div>', unsafe_allow_html=True)
