"""
Advanced Analytics  ·  pages/1_Analytics.py
DO NOT call st.set_page_config() here — it lives only in app.py.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import warnings

warnings.filterwarnings("ignore")

# Shared CSS (sidebar toggle fix included)
from utils.styling import apply_css, DARK_LAYOUT
apply_css()


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str, period: str = "6mo") -> tuple:
    try:
        stock = yf.Ticker(symbol)
        hist  = stock.history(period=period)
        return (hist, stock.info) if not hist.empty else (None, {})
    except Exception as exc:
        st.error(f"Error fetching {symbol}: {exc}")
        return None, {}


def calc_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicator columns to price DataFrame."""
    df = df.copy()

    # Moving averages
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()

    # RSI
    delta  = df["Close"].diff()
    gain_  = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss_  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    rs     = gain_ / loss_.replace(0, np.nan)
    df["RSI"] = (100 - (100 / (1 + rs))).fillna(50)

    # MACD
    e1          = df["Close"].ewm(span=12, adjust=False).mean()
    e2          = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]  = e1 - e2
    df["Signal"]= df["MACD"].ewm(span=9, adjust=False).mean()

    # Stochastic
    low_min  = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()
    denom    = (high_max - low_min).replace(0, np.nan)
    df["Stoch_K"] = (100 * (df["Close"] - low_min) / denom).fillna(50)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ATR
    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"]  - df["Close"].shift()).abs()
    df["ATR"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

    # OBV
    df["OBV"] = (np.sign(df["Close"].diff()) * df["Volume"]).fillna(0).cumsum()

    # Momentum & ROC
    df["Momentum"] = df["Close"] - df["Close"].shift(10)
    df["ROC"]      = (df["Close"] / df["Close"].shift(10) - 1) * 100

    # Fibonacci levels
    price_max  = df["High"].max()
    price_min  = df["Low"].min()
    diff       = price_max - price_min
    df["Fib_236"] = price_max - diff * 0.236
    df["Fib_382"] = price_max - diff * 0.382
    df["Fib_500"] = price_max - diff * 0.500
    df["Fib_618"] = price_max - diff * 0.618

    return df


def calc_risk(df: pd.DataFrame) -> dict:
    """Compute annualised risk metrics from price data."""
    r   = df["Close"].pct_change().dropna()
    ar  = r.mean() * 252 * 100
    av  = r.std()  * np.sqrt(252) * 100
    sr  = ar / av if av else 0.0
    cum = (1 + r).cumprod()
    mdd = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100
    var_= float(np.percentile(r, 5)) * 100
    dr  = r[r < 0]
    dd  = dr.std() * np.sqrt(252) * 100 if len(dr) else 0.0
    sor = ar / dd if dd else 0.0
    return {
        "Annual Return":     ar,
        "Annual Volatility": av,
        "Sharpe Ratio":      sr,
        "Max Drawdown":      mdd,
        "VaR (95%)":         var_,
        "Sortino Ratio":     sor,
    }


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem .4rem .6rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#7c6ff7,#4f8fff);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">📊</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;
                color:#f0f2f8!important">Analytics</div>
        </div>
        <div class="nav-group">Analysis Tools</div>
        <div class="nav-item active">📈 Technical Indicators</div>
        <div class="nav-item">⚠️ Risk Metrics</div>
        <div class="nav-item">📊 Correlation</div>
        <div class="nav-item">🎯 Price Levels</div>
        <div class="nav-item">🤖 AI Signals</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.4rem 0 .8rem">
    """, unsafe_allow_html=True)

    stock_symbol   = st.text_input("Stock Symbol", value="AAPL").upper().strip()
    period         = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
    compare_stocks = st.multiselect(
        "Compare With (Correlation tab)",
        ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"],
        default=["MSFT"],
    )

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
        color:#f0f2f8;line-height:1">Advanced Stock Analytics</div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">
        Technical analysis, risk metrics and AI-driven signals</div>
</div>
""", unsafe_allow_html=True)

if not stock_symbol:
    st.info("Enter a stock symbol in the sidebar to begin analysis.")
    st.stop()

with st.spinner(f"Analysing {stock_symbol}…"):
    df, info = fetch_stock_data(stock_symbol, period)

if df is None or df.empty:
    st.error("Could not fetch data. Check the symbol and try again.")
    st.stop()

df    = calc_indicators(df)
risk  = calc_risk(df)
cur_p = float(df["Close"].iloc[-1])
chg   = cur_p - float(df["Close"].iloc[-2])
chg_p = (chg / float(df["Close"].iloc[-2])) * 100

# ── Key metrics row ────────────────────────────────────────────────────────────
mc1, mc2, mc3, mc4 = st.columns(4)
for col, lbl, val, delta in [
    (mc1, "Current Price", f"${cur_p:.2f}",                           f"{chg_p:+.2f}%"),
    (mc2, "Volume",        f"{df['Volume'].iloc[-1]:,.0f}",            None),
    (mc3, "52W High",      f"${info.get('fiftyTwoWeekHigh', 0):.2f}", None),
    (mc4, "52W Low",       f"${info.get('fiftyTwoWeekLow',  0):.2f}", None),
]:
    with col:
        st.metric(lbl, val, delta)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Technical", "⚠️ Risk", "📊 Correlation", "🎯 Price Levels", "🤖 AI Signals"]
)

# ── Tab 1 — Technical ─────────────────────────────────────────────────────────
with tab1:
    fig = make_subplots(
        rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.04,
        row_heights=[0.3, 0.2, 0.2, 0.15, 0.15],
        subplot_titles=("Price & MAs", "RSI (14)", "Stochastic", "MACD", "OBV"),
    )
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Close",
                             line=dict(color="#4f8fff", width=1.8)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA20"],  name="MA20",
                             line=dict(color="#f5a623", width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"],  name="MA50",
                             line=dict(color="#7c6ff7", width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],    name="RSI",
                             line=dict(color="#4f8fff", width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=.5, row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_K"], name="K",
                             line=dict(color="#4f8fff", width=1.2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_D"], name="D",
                             line=dict(color="#f5a623", width=1.2)), row=3, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="#f05252", opacity=.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="#22d98a", opacity=.5, row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],   name="MACD",
                             line=dict(color="#4f8fff", width=1.2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal"], name="Signal",
                             line=dict(color="#f5a623", width=1.2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["OBV"],    name="OBV",
                             line=dict(color="#22d98a", width=1.2)), row=5, col=1)
    fig.update_layout(
        height=1100, showlegend=True,
        title=f"{stock_symbol} — Full Technical Dashboard",
        title_font=dict(family="Syne", size=14, color="#f0f2f8"), **DARK_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics below the chart
    ic1, ic2, ic3, ic4 = st.columns(4)
    rsi_v = float(df["RSI"].iloc[-1])
    rsi_s = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
    for col, lbl, val, delta in [
        (ic1, "RSI (14)",  f"{rsi_v:.1f}",                   rsi_s),
        (ic2, "Stoch K",   f"{df['Stoch_K'].iloc[-1]:.1f}",  None),
        (ic3, "MACD",      f"{df['MACD'].iloc[-1]:.4f}",
             "Bullish" if df["MACD"].iloc[-1] > df["Signal"].iloc[-1] else "Bearish"),
        (ic4, "ATR",       f"${df['ATR'].iloc[-1]:.2f}",      "Volatility proxy"),
    ]:
        with col:
            st.metric(lbl, val, delta)

# ── Tab 2 — Risk ──────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;'
                'color:#f0f2f8;margin-bottom:.6rem">Risk Metrics</div>', unsafe_allow_html=True)

    rc1, rc2, rc3 = st.columns(3)
    for col, lbl, val in [
        (rc1, "Annual Return",     f"{risk['Annual Return']:+.2f}%"),
        (rc2, "Annual Volatility", f"{risk['Annual Volatility']:.2f}%"),
        (rc3, "Sharpe Ratio",      f"{risk['Sharpe Ratio']:.2f}"),
    ]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>',
                     unsafe_allow_html=True)

    rc4, rc5, rc6 = st.columns(3)
    for col, lbl, val in [
        (rc4, "Max Drawdown",  f"{risk['Max Drawdown']:.2f}%"),
        (rc5, "VaR (95%)",     f"{risk['VaR (95%)']:.2f}%"),
        (rc6, "Sortino Ratio", f"{risk['Sortino Ratio']:.2f}"),
    ]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>',
                     unsafe_allow_html=True)

    # Risk level callout
    rs = 0
    rs += 30 if risk["Annual Volatility"] > 40 else 20 if risk["Annual Volatility"] > 25 else 10
    rs += 30 if risk["Max Drawdown"] < -30 else 20 if risk["Max Drawdown"] < -15 else 10
    rs += 20 if risk["Sharpe Ratio"] < 1 else 0
    rl  = "High" if rs > 60 else "Medium" if rs > 30 else "Low"
    rc_ = "#f05252" if rl == "High" else "#f5a623" if rl == "Medium" else "#22d98a"
    tip = ("⚠️ High volatility — consider position sizing carefully."
           if rl == "High" else
           "📊 Moderate risk — suitable for most growth investors."
           if rl == "Medium" else
           "✅ Low risk profile — relatively stable price history.")
    st.markdown(f"""
    <div class="insight-text" style="margin-top:.8rem">
        <strong style="color:#f0f2f8">Risk Level: <span style="color:{rc_}">{rl}</span></strong>
        &nbsp;·&nbsp; Score {rs}/100<br>{tip}
    </div>
    """, unsafe_allow_html=True)

    # Rolling volatility chart
    rv  = df["Close"].pct_change().rolling(20).std() * np.sqrt(252) * 100
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df.index, y=rv, name="20d Volatility",
        fill="tozeroy", line=dict(color="#f5a623", width=2),
        fillcolor="rgba(245,166,35,.08)",
    ))
    fig2.update_layout(height=280, title="Rolling 20-Day Volatility (Annualised %)",
                       title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3 — Correlation ───────────────────────────────────────────────────────
with tab3:
    if compare_stocks:
        all_closes: dict[str, pd.Series] = {}
        for sym in list(set(compare_stocks + [stock_symbol])):
            sd, _ = fetch_stock_data(sym, period)
            if sd is not None:
                all_closes[sym] = sd["Close"]

        if len(all_closes) > 1:
            corr = pd.DataFrame(all_closes).corr()
            fig3 = px.imshow(
                corr, text_auto=True,
                color_continuous_scale=["#f05252", "#1c2030", "#4f8fff"],
                zmin=-1, zmax=1, title="Return Correlation Matrix",
            )
            fig3.update_layout(height=400,
                               title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
            st.plotly_chart(fig3, use_container_width=True)

            for sym in compare_stocks:
                if sym in corr.columns and stock_symbol in corr.index:
                    cv       = float(corr.loc[stock_symbol, sym])
                    strength = "Strong" if abs(cv) > 0.7 else "Moderate" if abs(cv) > 0.3 else "Weak"
                    direction= "positive" if cv > 0 else "negative"
                    meaning  = ("moves together — less diversification benefit."
                                if cv > 0.7 else
                                "inversely related — good diversification pair."
                                if cv < -0.3 else
                                "moderate relationship.")
                    st.markdown(
                        f"<div style='font-size:.82rem;color:#8892a4;padding:.3rem 0;"
                        f"border-bottom:1px solid rgba(255,255,255,.05)'>"
                        f"<strong style='color:#f0f2f8'>{stock_symbol} vs {sym}</strong>: "
                        f"{cv:.2f} — {strength} {direction} correlation. These stocks {meaning}</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Not enough data to build a correlation matrix.")
    else:
        st.info("Select comparison stocks in the sidebar to see how they correlate.")

# ── Tab 4 — Price Levels ──────────────────────────────────────────────────────
with tab4:
    fib  = df[["Fib_236", "Fib_382", "Fib_500", "Fib_618"]].iloc[-1]
    r_hi = float(df["High"].tail(20).max())
    r_lo = float(df["Low"].tail(20).min())
    pos  = ((cur_p - r_lo) / (r_hi - r_lo) * 100) if r_hi != r_lo else 0.0
    pos_label = "Near resistance" if pos > 70 else "Near support" if pos < 30 else "Mid-range"

    fc1, fc2 = st.columns(2)
    fc1.markdown(f"""
    <div class="glass-card">
        <h4>Fibonacci Retracement</h4>
        <table style="width:100%">
            <tr><td>23.6% level</td><td>${fib['Fib_236']:.2f}</td></tr>
            <tr><td>38.2% level</td><td>${fib['Fib_382']:.2f}</td></tr>
            <tr><td>50.0% level</td><td>${fib['Fib_500']:.2f}</td></tr>
            <tr><td>61.8% level</td><td>${fib['Fib_618']:.2f}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    fc2.markdown(f"""
    <div class="glass-card">
        <h4>20-Day Support &amp; Resistance</h4>
        <table style="width:100%">
            <tr><td>Resistance</td><td>${r_hi:.2f}</td></tr>
            <tr><td>Support</td><td>${r_lo:.2f}</td></tr>
            <tr><td>Current Price</td><td>${cur_p:.2f}</td></tr>
            <tr><td>Price Position</td><td>{pos:.1f}% of range — {pos_label}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Price",
                              line=dict(color="#4f8fff", width=2)))
    for level, color, label in [
        (fib["Fib_236"], "#f5a623", "Fib 23.6%"),
        (fib["Fib_382"], "#f05252", "Fib 38.2%"),
        (fib["Fib_500"], "#8892a4", "Fib 50.0%"),
        (fib["Fib_618"], "#22d98a", "Fib 61.8%"),
    ]:
        fig4.add_hline(y=float(level), line_dash="dot", line_color=color, opacity=0.7,
                       annotation_text=label, annotation_font=dict(color=color, size=10))
    fig4.update_layout(height=400, title="Price with Fibonacci Retracement Levels",
                       title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

# ── Tab 5 — AI Signals ────────────────────────────────────────────────────────
with tab5:
    signals: list[tuple[str, str, float]] = []
    rsi_v = float(df["RSI"].iloc[-1])
    if   rsi_v < 30: signals.append(("BUY",     "RSI oversold (<30)",           0.80))
    elif rsi_v > 70: signals.append(("SELL",    "RSI overbought (>70)",          0.80))
    else:            signals.append(("NEUTRAL", f"RSI neutral ({rsi_v:.1f})",    0.50))

    macd_v = float(df["MACD"].iloc[-1])
    sig_v  = float(df["Signal"].iloc[-1])
    if   macd_v > sig_v: signals.append(("BUY",     "MACD above signal line",     0.70))
    elif macd_v < sig_v: signals.append(("SELL",    "MACD below signal line",     0.70))
    else:                signals.append(("NEUTRAL", "MACD flat",                  0.50))

    ma20 = float(df["MA20"].iloc[-1])
    ma50 = float(df["MA50"].iloc[-1])
    if   ma20 > ma50: signals.append(("BUY",     "Golden cross: MA20 > MA50",   0.75))
    elif ma20 < ma50: signals.append(("SELL",    "Death cross: MA20 < MA50",    0.75))
    else:             signals.append(("NEUTRAL", "Moving averages aligned",      0.50))

    stk = float(df["Stoch_K"].iloc[-1])
    if   stk < 20: signals.append(("BUY",     "Stochastic oversold (<20)",    0.65))
    elif stk > 80: signals.append(("SELL",    "Stochastic overbought (>80)",  0.65))
    else:          signals.append(("NEUTRAL", f"Stochastic neutral ({stk:.1f})", 0.50))

    buys  = sum(1 for s in signals if s[0] == "BUY")
    sells = sum(1 for s in signals if s[0] == "SELL")
    if   buys > sells:  overall, oc = ("STRONG BUY"  if buys - sells >= 2 else "BUY"),  "#22d98a"
    elif sells > buys:  overall, oc = ("STRONG SELL" if sells - buys >= 2 else "SELL"), "#f05252"
    else:               overall, oc = "NEUTRAL", "#f5a623"

    st.markdown(f"""
    <div style="background:rgba(19,22,30,1);border:1px solid {oc}33;
        border-radius:var(--radius-lg);padding:2rem;text-align:center;margin-bottom:.8rem">
        <div style="font-size:.72rem;font-weight:600;letter-spacing:.1em;
            text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Overall Signal</div>
        <div style="font-family:'Syne',sans-serif;font-size:2.8rem;font-weight:800;
            color:{oc};line-height:1">{overall}</div>
        <div style="font-size:.8rem;color:#4e5669;margin-top:.4rem">
            {buys} buy · {sells} sell · {len(signals)-buys-sells} neutral signals</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.8rem;font-weight:700;'
                'color:#f0f2f8;margin-bottom:.5rem">Signal Breakdown</div>', unsafe_allow_html=True)

    for s_type, reason, conf in signals:
        color = "#22d98a" if s_type == "BUY" else "#f05252" if s_type == "SELL" else "#f5a623"
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
            padding:.6rem .8rem;background:#1c2030;border:1px solid rgba(255,255,255,.06);
            border-radius:var(--radius-sm);margin-bottom:.3rem;font-size:.8rem">
            <span style="color:{color};font-weight:600;min-width:90px">{s_type}</span>
            <span style="color:#8892a4;flex:1;padding:0 1rem">{reason}</span>
            <span style="color:#4e5669">{conf*100:.0f}% weight</span>
        </div>
        """, unsafe_allow_html=True)

    # Simple price prediction based on momentum
    mom   = float(df["Momentum"].tail(5).mean())
    pred  = cur_p * (1.02 if mom > 0 else 0.98)
    direction = "upward ▲" if mom > 0 else "downward ▼"
    lo, hi    = min(pred, cur_p) * 0.99, max(pred, cur_p) * 1.01
    st.markdown(f"""
    <div class="insight-text" style="margin-top:.8rem">
        <strong style="color:#f0f2f8">Momentum Forecast</strong><br>
        Short-term momentum is <strong style="color:{'#22d98a' if mom>0 else '#f05252'}">{direction}</strong>.<br>
        Estimated near-term range: <strong>${lo:.2f} – ${hi:.2f}</strong><br>
        <span style="font-size:.75rem;opacity:.7">⚠️ Simple momentum model — not financial advice.</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Data by Yahoo Finance &nbsp;·&nbsp; For educational purposes only
</div>
""", unsafe_allow_html=True)
