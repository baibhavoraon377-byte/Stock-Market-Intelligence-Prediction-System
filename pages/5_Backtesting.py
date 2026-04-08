"""
Backtesting Engine  ·  pages/6_Backtesting.py
Strategy backtester with performance analytics and equity curve.
DO NOT call st.set_page_config() here — it lives only in app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

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
.bt-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
    padding:1.2rem 1.4rem;margin-bottom:.8rem;position:relative;overflow:hidden;}
.bt-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#7c6ff7,#4f8fff);opacity:.7;}
.bt-card h4{font-family:'Syne',sans-serif;font-size:.72rem;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;color:var(--text-secondary);margin-bottom:.5rem;}
.bt-stat{background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:1rem;text-align:center;}
.bt-stat h4{font-size:.65rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
    color:var(--text-secondary);margin:0 0 .35rem;}
.bt-stat h2{font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:700;color:var(--text-primary);margin:0;}
.bt-stat .sub{font-size:.68rem;color:#4e5669;margin-top:.25rem;}
.trade-row{background:var(--bg-elevated);border-left:3px solid;border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    padding:.6rem .9rem;margin-bottom:.3rem;font-size:.82rem;}
.win{border-left-color:#22d98a;} .loss{border-left-color:#f05252;}
.badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;font-size:.68rem;font-weight:600;}
.badge-green{background:rgba(34,217,138,.12);color:#22d98a;}
.badge-red{background:rgba(240,82,82,.12);color:#f05252;}
.badge-blue{background:rgba(79,143,255,.12);color:#4f8fff;}
.badge-amber{background:rgba(245,166,35,.12);color:#f5a623;}
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
.stSelectbox>div>div{background:var(--bg-elevated)!important;border:1px solid var(--border)!important;border-radius:var(--radius-sm)!important;}
.stSlider{color:#4f8fff!important;}
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
    font=dict(family="DM Sans", color="#8892a4", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4", size=10)),
    margin=dict(l=8, r=8, t=40, b=8),
)

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
        <div class="nav-item">🔔 Watchlist & Alerts</div>
        <div class="nav-item active">⚙️ Backtesting</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:0.8rem 0">
    """, unsafe_allow_html=True)

    symbol   = st.text_input("Symbol", value="AAPL").upper().strip()
    period   = st.selectbox("Period", ["1y", "2y", "5y", "10y"], index=1)
    strategy = st.selectbox("Strategy", [
        "SMA Crossover (20/50)",
        "RSI Mean Reversion",
        "Bollinger Band Breakout",
        "MACD Signal",
        "Momentum (ROC)",
    ])
    capital  = st.number_input("Initial Capital ($)", value=10_000, step=1_000, min_value=1_000)
    commission = st.slider("Commission per trade ($)", min_value=0.0, max_value=20.0, value=1.0, step=0.5)
    run_btn  = st.button("▶ Run Backtest", use_container_width=True, type="primary")

# ── Strategy logic ────────────────────────────────────────────────────────────
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA20"]      = df["Close"].rolling(20).mean()
    df["MA50"]      = df["Close"].rolling(50).mean()
    df["MA20v50_x"] = (df["MA20"] > df["MA50"]).astype(int)
    delta   = df["Close"].diff()
    gain    = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss    = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df["RSI"] = (100 - (100 / (1 + gain / loss.replace(0, np.nan)))).fillna(50)
    df["BB_Mid"]   = df["Close"].rolling(20).mean()
    df["BB_Std"]   = df["Close"].rolling(20).std()
    df["BB_Upper"] = df["BB_Mid"] + df["BB_Std"] * 2
    df["BB_Lower"] = df["BB_Mid"] - df["BB_Std"] * 2
    exp1 = df["Close"].ewm(span=12).mean()
    exp2 = df["Close"].ewm(span=26).mean()
    df["MACD"]   = exp1 - exp2
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["ROC20"]  = df["Close"].pct_change(20) * 100
    df.dropna(inplace=True)
    return df


def generate_signals(df: pd.DataFrame, strategy: str) -> pd.Series:
    sig = pd.Series(0, index=df.index)
    if strategy == "SMA Crossover (20/50)":
        prev = df["MA20v50_x"].shift(1)
        sig[(df["MA20v50_x"] == 1) & (prev == 0)] =  1  # golden cross → buy
        sig[(df["MA20v50_x"] == 0) & (prev == 1)] = -1  # death cross  → sell
    elif strategy == "RSI Mean Reversion":
        sig[df["RSI"] < 30] =  1   # oversold → buy
        sig[df["RSI"] > 70] = -1   # overbought → sell
    elif strategy == "Bollinger Band Breakout":
        sig[df["Close"] < df["BB_Lower"]] =  1
        sig[df["Close"] > df["BB_Upper"]] = -1
    elif strategy == "MACD Signal":
        prev_macd = df["MACD"].shift(1)
        prev_sig  = df["Signal"].shift(1)
        sig[(df["MACD"] > df["Signal"]) & (prev_macd <= prev_sig)] =  1
        sig[(df["MACD"] < df["Signal"]) & (prev_macd >= prev_sig)] = -1
    elif strategy == "Momentum (ROC)":
        sig[df["ROC20"] > 5]  =  1
        sig[df["ROC20"] < -5] = -1
    return sig


def run_backtest(df: pd.DataFrame, signals: pd.Series, capital: float, commission: float):
    pos   = 0        # 0 = flat, 1 = long
    cash  = capital
    shares = 0.0
    equity = []
    trades = []

    for i, (dt, row) in enumerate(df.iterrows()):
        price = float(row["Close"])
        sig   = signals.iloc[i]

        if sig == 1 and pos == 0:          # enter long
            shares = (cash - commission) / price
            cash   = 0.0
            pos    = 1
            trades.append({"date": dt, "type": "BUY", "price": price, "shares": shares,
                           "value": shares * price, "pnl": None})
        elif sig == -1 and pos == 1:       # exit long
            proceeds = shares * price - commission
            pnl      = proceeds - trades[-1]["value"] - commission
            cash     = proceeds
            pos      = 0
            trades.append({"date": dt, "type": "SELL", "price": price, "shares": shares,
                           "value": proceeds, "pnl": pnl})
            shares   = 0.0

        equity.append(cash + shares * price)

    # Close any open position at last price
    if pos == 1:
        last_price = float(df["Close"].iloc[-1])
        proceeds   = shares * last_price - commission
        pnl        = proceeds - trades[-1]["value"] - commission
        cash       = proceeds
        trades.append({"date": df.index[-1], "type": "SELL (close)", "price": last_price,
                       "shares": shares, "value": proceeds, "pnl": pnl})
        equity[-1] = cash

    equity_s = pd.Series(equity, index=df.index)
    return equity_s, trades


def compute_metrics(equity: pd.Series, capital: float, trades: list, df: pd.DataFrame):
    total_return  = (equity.iloc[-1] - capital) / capital * 100
    bh_return     = (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100

    daily_ret = equity.pct_change().dropna()
    sharpe    = (daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if daily_ret.std() > 0 else 0.0

    rolling_max   = equity.cummax()
    drawdown      = (equity - rolling_max) / rolling_max * 100
    max_drawdown  = float(drawdown.min())

    sell_trades = [t for t in trades if t["type"].startswith("SELL") and t["pnl"] is not None]
    wins        = [t for t in sell_trades if t["pnl"] > 0]
    losses      = [t for t in sell_trades if t["pnl"] <= 0]
    win_rate    = len(wins) / max(len(sell_trades), 1) * 100
    avg_win     = np.mean([t["pnl"] for t in wins])  if wins   else 0.0
    avg_loss    = np.mean([t["pnl"] for t in losses]) if losses else 0.0
    profit_factor = abs(sum(t["pnl"] for t in wins) / sum(t["pnl"] for t in losses)) if losses else np.inf

    return dict(
        total_return=total_return, bh_return=bh_return, sharpe=sharpe,
        max_drawdown=max_drawdown, win_rate=win_rate, avg_win=avg_win,
        avg_loss=avg_loss, profit_factor=profit_factor,
        total_trades=len(sell_trades), wins=len(wins), losses=len(losses),
        final_equity=float(equity.iloc[-1]),
    )


@st.cache_data(ttl=600, show_spinner=False)
def run_full_backtest(symbol: str, period: str, strategy: str, capital: float, commission: float):
    ticker = yf.Ticker(symbol)
    raw    = ticker.history(period=period)
    if raw.empty or len(raw) < 60:
        return None
    df      = add_indicators(raw)
    signals = generate_signals(df, strategy)
    equity, trades = run_backtest(df, signals, capital, commission)
    metrics = compute_metrics(equity, capital, trades, df)
    return dict(df=df, signals=signals, equity=equity, trades=trades, metrics=metrics)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">
        ⚙️ Backtesting Engine
    </div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">
        Simulate trading strategies on historical data with full performance analytics
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

if not run_btn and "bt_result" not in st.session_state:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:20px;
        padding:2.5rem;text-align:center;margin-top:1rem">
        <div style="font-size:2.5rem;margin-bottom:.8rem">⚙️</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8;margin-bottom:.4rem">
            Configure Your Strategy
        </div>
        <div style="font-size:.83rem;color:#8892a4">
            Pick a symbol, strategy, and period in the sidebar, then click <strong style="color:#4f8fff">Run Backtest</strong>.
        </div>
        <div style="margin-top:1rem;font-size:.78rem;color:#4e5669">
            Available: SMA Crossover · RSI Mean Reversion · Bollinger Band · MACD Signal · Momentum
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if run_btn:
    with st.spinner(f"Running {strategy} on {symbol} ({period})…"):
        result = run_full_backtest(symbol, period, strategy, float(capital), float(commission))
    if result is None:
        st.error(f"Not enough data for **{symbol}** over **{period}**. Try a different symbol or shorter period.")
        st.stop()
    st.session_state["bt_result"] = result
    st.session_state["bt_label"]  = f"{symbol} — {strategy} — {period}"

result = st.session_state.get("bt_result")
if result is None:
    st.stop()

m    = result["metrics"]
eq   = result["equity"]
df   = result["df"]
lbl  = st.session_state.get("bt_label", "")

# ── KPI strip ─────────────────────────────────────────────────────────────────
kc = st.columns(4)
kpis = [
    ("Total Return",    f"{m['total_return']:+.2f}%",   m['total_return'] >= 0),
    ("vs Buy & Hold",   f"{m['bh_return']:+.2f}%",      m['bh_return'] >= 0),
    ("Sharpe Ratio",    f"{m['sharpe']:.2f}",            m['sharpe'] >= 1),
    ("Max Drawdown",    f"{m['max_drawdown']:.2f}%",     False),
]
for col, (title, val, positive) in zip(kc, kpis):
    color = "#22d98a" if positive else "#f05252"
    with col:
        st.markdown(f"""
        <div class="bt-stat">
            <h4>{title}</h4>
            <h2 style="color:{color}">{val}</h2>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

kc2 = st.columns(4)
kpis2 = [
    ("Win Rate",        f"{m['win_rate']:.1f}%",         m['win_rate'] >= 50),
    ("Profit Factor",   f"{m['profit_factor']:.2f}" if m['profit_factor'] != np.inf else "∞", m['profit_factor'] >= 1),
    ("Total Trades",    str(m['total_trades']),           True),
    ("Final Equity",    f"${m['final_equity']:,.0f}",     m['final_equity'] >= float(capital)),
]
for col, (title, val, positive) in zip(kc2, kpis2):
    color = "#22d98a" if positive else "#f05252" if not positive else "#f0f2f8"
    with col:
        st.markdown(f"""
        <div class="bt-stat">
            <h4>{title}</h4>
            <h2 style="color:{color}">{val}</h2>
            <div class="sub">W:{m['wins']} / L:{m['losses']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Equity Curve", "📊 Price & Signals", "📋 Trade Log"])

with tab1:
    # Equity vs Buy-and-Hold
    bh_equity = (df["Close"] / float(df["Close"].iloc[0])) * float(capital)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=eq.index, y=eq.values, name="Strategy",
        line=dict(color="#4f8fff", width=2),
        fill="tozeroy", fillcolor="rgba(79,143,255,0.06)",
    ))
    fig.add_trace(go.Scatter(
        x=bh_equity.index, y=bh_equity.values, name="Buy & Hold",
        line=dict(color="#7c6ff7", width=1.5, dash="dot"),
    ))
    # Drawdown
    rolling_max = eq.cummax()
    drawdown    = (eq - rolling_max) / rolling_max * 100
    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                         row_heights=[0.7, 0.3])
    fig2.add_trace(go.Scatter(x=eq.index, y=eq.values, name="Strategy",
                              line=dict(color="#4f8fff", width=2),
                              fill="tozeroy", fillcolor="rgba(79,143,255,0.05)"), row=1, col=1)
    fig2.add_trace(go.Scatter(x=bh_equity.index, y=bh_equity.values, name="Buy & Hold",
                              line=dict(color="#7c6ff7", width=1.4, dash="dot")), row=1, col=1)
    fig2.add_trace(go.Bar(x=drawdown.index, y=drawdown.values, name="Drawdown %",
                          marker_color="#f05252", opacity=0.6), row=2, col=1)
    fig2.update_layout(height=500, title=f"Equity Curve — {lbl}",
                       title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
    fig2.update_yaxes(title_text="Portfolio ($)", row=1, col=1)
    fig2.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    signals = result["signals"]
    buys    = df[signals ==  1]
    sells   = df[signals == -1]

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close",
                              line=dict(color="#4f8fff", width=1.6)))
    fig3.add_trace(go.Scatter(x=df.index, y=df["MA20"], name="MA20",
                              line=dict(color="#f5a623", width=1, dash="dot")))
    fig3.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50",
                              line=dict(color="#7c6ff7", width=1, dash="dot")))
    if not buys.empty:
        fig3.add_trace(go.Scatter(x=buys.index, y=buys["Close"],
                                  mode="markers", name="Buy Signal",
                                  marker=dict(color="#22d98a", symbol="triangle-up", size=10)))
    if not sells.empty:
        fig3.add_trace(go.Scatter(x=sells.index, y=sells["Close"],
                                  mode="markers", name="Sell Signal",
                                  marker=dict(color="#f05252", symbol="triangle-down", size=10)))
    fig3.update_layout(height=420, title="Price Chart with Entry / Exit Signals",
                       title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

with tab3:
    trades = result["trades"]
    sell_trades = [t for t in trades if t["type"].startswith("SELL") and t["pnl"] is not None]
    if not sell_trades:
        st.info("No completed trades in this backtest.")
    else:
        log_df = pd.DataFrame([{
            "Date":   t["date"].strftime("%Y-%m-%d") if hasattr(t["date"], "strftime") else str(t["date"]),
            "Type":   t["type"],
            "Price":  f"${t['price']:.2f}",
            "Shares": f"{t['shares']:.4f}",
            "Value":  f"${t['value']:.2f}",
            "P&L":    f"${t['pnl']:+.2f}" if t["pnl"] is not None else "—",
        } for t in sell_trades])
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        # P&L distribution
        pnls = [t["pnl"] for t in sell_trades if t["pnl"] is not None]
        if len(pnls) >= 3:
            fig4 = go.Figure(go.Histogram(x=pnls, nbinsx=20,
                                          marker_color="#4f8fff", opacity=0.8))
            fig4.add_vline(x=0, line_dash="dot", line_color="#f05252", opacity=0.6)
            fig4.update_layout(height=280, title="P&L Distribution per Trade",
                               title_font=dict(family="Syne", size=13, color="#f0f2f8"),
                               xaxis_title="P&L ($)", **DARK_LAYOUT)
            st.plotly_chart(fig4, use_container_width=True)

st.markdown("""
<div style="text-align:center;padding:1rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Past performance does not guarantee future results · For educational purposes only · Not financial advice
</div>
""", unsafe_allow_html=True)
