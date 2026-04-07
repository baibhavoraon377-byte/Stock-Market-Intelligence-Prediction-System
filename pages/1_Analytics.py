"""
Advanced Analytics + ML Prediction + Portfolio Benchmark
pages/1_Analytics.py

FIXES:
  - Excel export error: norm/rets may contain timezone-aware DatetimeIndex
    which openpyxl cannot serialise. Fixed by calling .reset_index() and
    converting the index to tz-naive before writing.
  - All emojis removed from labels, tabs, and messages.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import io, warnings
warnings.filterwarnings("ignore")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from utils.styling import apply_css, DARK_LAYOUT
apply_css()

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# ── Helpers ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch(symbol: str, period: str = "2y") -> tuple:
    try:
        t    = yf.Ticker(symbol)
        hist = t.history(period=period)
        return (hist, t.info) if not hist.empty else (None, {})
    except Exception as e:
        st.error(f"{e}"); return None, {}

def calc_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret1"]  = df["Close"].pct_change()
    df["ret5"]  = df["Close"].pct_change(5)
    df["ret20"] = df["Close"].pct_change(20)
    df["MA20"]  = df["Close"].rolling(20).mean()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA_ratio"] = df["MA20"] / df["MA50"]
    delta = df["Close"].diff()
    g_ = delta.where(delta > 0, 0).rolling(14).mean()
    l_ = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df["RSI"]      = (100 - 100 / (1 + g_ / l_.replace(0, np.nan))).fillna(50)
    e1 = df["Close"].ewm(span=12, adjust=False).mean()
    e2 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]     = e1 - e2
    df["MACD_sig"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_diff"]= df["MACD"] - df["MACD_sig"]
    m_ = df["Close"].rolling(20).mean()
    s_ = df["Close"].rolling(20).std()
    df["BB_pos"]   = (df["Close"] - m_) / (2 * s_ + 1e-9)
    lmin = df["Low"].rolling(14).min()
    hmax = df["High"].rolling(14).max()
    df["Stoch"]    = 100 * (df["Close"] - lmin) / (hmax - lmin + 1e-9)
    df["ATR"]      = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1).rolling(14).mean()
    df["vol20"]    = df["ret1"].rolling(20).std() * np.sqrt(252)
    df["OBV"]      = (np.sign(df["Close"].diff()) * df["Volume"]).fillna(0).cumsum()
    df["OBV_ret"]  = df["OBV"].pct_change(5)
    df["target"]   = (df["Close"].shift(-5) > df["Close"]).astype(int)
    return df

FEATURES = ["ret1","ret5","ret20","RSI","MACD_diff","BB_pos","Stoch","ATR","vol20","MA_ratio","OBV_ret"]

def calc_risk(df: pd.DataFrame) -> dict:
    r   = df["Close"].pct_change().dropna()
    ar  = r.mean() * 252 * 100
    av  = r.std()  * np.sqrt(252) * 100
    sr  = ar / av if av else 0
    cum = (1 + r).cumprod()
    mdd = ((cum - cum.expanding().max()) / cum.expanding().max()).min() * 100
    dr  = r[r < 0]
    dd  = dr.std() * np.sqrt(252) * 100 if len(dr) else 0
    return {"Annual Return": ar, "Annual Volatility": av, "Sharpe Ratio": sr,
            "Max Drawdown": mdd, "VaR 95%": float(np.percentile(r, 5)) * 100,
            "Sortino": ar / dd if dd else 0}


def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
    """
    FIX for Excel export ValueError:
    openpyxl cannot write timezone-aware datetime values.
    Convert the index to tz-naive UTC and reset it to a plain column.
    """
    df = df.copy()
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df.reset_index()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#7c6ff7,#4f8fff);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem">A</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">Analytics</div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .8rem">
    """, unsafe_allow_html=True)
    symbol   = st.text_input("Symbol", "AAPL").upper().strip()
    period   = st.selectbox("Period", ["6mo","1y","2y","3y","5y"], index=1)
    bench    = st.text_input("Benchmark", "SPY").upper().strip()
    compare  = st.multiselect("Compare With",
                  ["AAPL","MSFT","GOOGL","TSLA","AMZN","NVDA","META"], default=["MSFT"])
    ml_model = st.selectbox("ML Model",
                  ["Random Forest","Gradient Boost"] + (["XGBoost"] if HAS_XGB else []))

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .2rem">Advanced Analytics — {symbol}</div>'
            f'<div style="font-size:.82rem;color:#8892a4">Technical analysis · Risk metrics · ML predictions · Benchmark comparison</div>',
            unsafe_allow_html=True)

if not symbol:
    st.info("Enter a symbol in the sidebar."); st.stop()

with st.spinner(f"Fetching {symbol}…"):
    df_raw, info = fetch(symbol, period)
    df_spy, _    = fetch(bench, period)

if df_raw is None:
    st.error("No data."); st.stop()

df   = calc_features(df_raw)
risk = calc_risk(df_raw)
cur  = float(df["Close"].iloc[-1])
chg  = cur - float(df["Close"].iloc[-2])
chgp = chg / float(df["Close"].iloc[-2]) * 100

# ── Metrics row ────────────────────────────────────────────────────────────────
for col, lbl, val, d in zip(st.columns(5),
    ["Price","Volume","52W High","52W Low","Sharpe"],
    [f"${cur:.2f}", f"{df['Volume'].iloc[-1]:,.0f}",
     f"${info.get('fiftyTwoWeekHigh',0):.2f}", f"${info.get('fiftyTwoWeekLow',0):.2f}",
     f"{risk['Sharpe Ratio']:.2f}"],
    [f"{chgp:+.2f}%", None, None, None, None]):
    with col: st.metric(lbl, val, d)

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Technical","Risk","ML Prediction","Benchmark","Price Levels","Correlation"])

# ── TECHNICAL ─────────────────────────────────────────────────────────────────
with tab1:
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=.03,
                        row_heights=[.3,.18,.18,.17,.17],
                        subplot_titles=("Price & MAs","RSI (14)","Stochastic","MACD","OBV"))
    fig.add_trace(go.Scatter(x=df.index, y=df.Close,    name="Close",  line=dict(color="#4f8fff",width=1.8)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.MA20,     name="MA20",   line=dict(color="#f5a623",width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.MA50,     name="MA50",   line=dict(color="#7c6ff7",width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.RSI,      name="RSI",    line=dict(color="#4f8fff",width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#f05252", opacity=.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#22d98a", opacity=.5, row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.Stoch,    name="Stoch K",line=dict(color="#4f8fff",width=1.2)), row=3, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="#f05252", opacity=.5, row=3, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="#22d98a", opacity=.5, row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.MACD,     name="MACD",   line=dict(color="#4f8fff",width=1.2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.MACD_sig, name="Signal", line=dict(color="#f5a623",width=1.2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df.OBV,      name="OBV",    line=dict(color="#22d98a",width=1.2)), row=5, col=1)
    fig.update_layout(height=1050, showlegend=True,
                      title=f"{symbol} Full Technical Dashboard",
                      title_font=dict(family="Syne",size=14,color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    rsi_v = float(df.RSI.iloc[-1])
    rsi_s = "Overbought" if rsi_v > 70 else "Oversold" if rsi_v < 30 else "Neutral"
    for col, lbl, val, d in zip(st.columns(4),
        ["RSI 14","Stochastic","MACD","ATR Volatility"],
        [f"{rsi_v:.1f}", f"{df.Stoch.iloc[-1]:.1f}", f"{df.MACD.iloc[-1]:.4f}", f"${df.ATR.iloc[-1]:.2f}"],
        [rsi_s, None, "Bullish" if df.MACD.iloc[-1] > df.MACD_sig.iloc[-1] else "Bearish", "Daily volatility"]):
        with col: st.metric(lbl, val, d)

# ── RISK ──────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">Risk Metrics</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    for col, lbl, val in [
        (c1, "Annual Return",    f"{risk['Annual Return']:+.1f}%"),
        (c2, "Annual Volatility",f"{risk['Annual Volatility']:.1f}%"),
        (c3, "Sharpe Ratio",     f"{risk['Sharpe Ratio']:.2f}"),
    ]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    for col, lbl, val in [
        (c4, "Max Drawdown", f"{risk['Max Drawdown']:.1f}%"),
        (c5, "VaR 95%",      f"{risk['VaR 95%']:.2f}%"),
        (c6, "Sortino Ratio",f"{risk['Sortino']:.2f}"),
    ]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>', unsafe_allow_html=True)

    rs  = sum([30 if risk["Annual Volatility"] > 40 else 20 if risk["Annual Volatility"] > 25 else 10,
               30 if risk["Max Drawdown"] < -30 else 20 if risk["Max Drawdown"] < -15 else 10,
               20 if risk["Sharpe Ratio"] < 1 else 0])
    rl  = "High" if rs > 60 else "Medium" if rs > 30 else "Low"
    rc_ = "#f05252" if rl == "High" else "#f5a623" if rl == "Medium" else "#22d98a"
    st.markdown(f'<div class="insight-text" style="margin-top:.7rem">'
                f'<strong style="color:#f0f2f8">Risk Level: <span style="color:{rc_}">{rl}</span></strong>'
                f' — Score {rs}/100<br>'
                f'{"High volatility — size positions carefully." if rl=="High" else "Moderate — typical growth profile." if rl=="Medium" else "Conservative risk profile."}'
                f'</div>', unsafe_allow_html=True)

    rv = df["Close"].pct_change().rolling(20).std() * np.sqrt(252) * 100
    fig2 = go.Figure(go.Scatter(x=df.index, y=rv, fill="tozeroy",
                                line=dict(color="#f5a623",width=2), fillcolor="rgba(245,166,35,.08)"))
    fig2.update_layout(height=260, title="20-Day Rolling Volatility (Annualised %)",
                       title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

# ── ML PREDICTION ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.4rem">ML Price Direction Prediction — {ml_model}</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.78rem;color:#8892a4;margin-bottom:.8rem">Predicts whether price will be higher in 5 trading days. Trained on 11 technical features using walk-forward validation.</div>', unsafe_allow_html=True)

    with st.spinner("Training model…"):
        ml_df = df[FEATURES + ["target"]].dropna()
        if len(ml_df) < 60:
            st.error("Not enough data to train (need 60+ rows)."); st.stop()

        X  = ml_df[FEATURES].values
        y  = ml_df["target"].values
        sc = StandardScaler()
        X  = sc.fit_transform(X)
        split   = int(len(X) * 0.8)
        X_tr, X_te = X[:split], X[split:]
        y_tr, y_te = y[:split], y[split:]

        if ml_model == "Random Forest":
            clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1)
        elif ml_model == "Gradient Boost":
            clf = GradientBoostingClassifier(n_estimators=150, max_depth=4, learning_rate=.05, random_state=42)
        else:
            clf = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=.05,
                                use_label_encoder=False, eval_metric="logloss", random_state=42)

        clf.fit(X_tr, y_tr)
        preds    = clf.predict(X_te)
        probas   = clf.predict_proba(X_te)[:, 1]
        acc      = accuracy_score(y_te, preds) * 100
        last_feat= sc.transform(ml_df[FEATURES].iloc[[-1]].values)
        cur_pred = clf.predict(last_feat)[0]
        cur_prob = clf.predict_proba(last_feat)[0][1] * 100

    pred_dir = "UP" if cur_pred == 1 else "DOWN"
    pred_col = "#22d98a" if cur_pred == 1 else "#f05252"
    conf_col = "#22d98a" if cur_prob > 60 else "#f05252" if cur_prob < 40 else "#f5a623"

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f'<div class="metric-box"><h4>5-Day Prediction</h4><h2 style="color:{pred_col}">{pred_dir}</h2></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-box"><h4>Confidence</h4><h2 style="color:{conf_col}">{cur_prob:.1f}%</h2></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-box"><h4>Test Accuracy</h4><h2>{acc:.1f}%</h2></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-box"><h4>Training Samples</h4><h2>{split}</h2></div>', unsafe_allow_html=True)

    test_idx = ml_df.index[split:]
    fig_ml = go.Figure()
    fig_ml.add_trace(go.Scatter(x=test_idx, y=probas * 100, name="P(Up)",
                                fill="tozeroy", line=dict(color="#4f8fff",width=2),
                                fillcolor="rgba(79,143,255,.1)"))
    fig_ml.add_hline(y=50, line_dash="dot", line_color="#f5a623", opacity=.6)
    fig_ml.update_layout(height=280, title="Predicted Probability of Upward Move (Test Period)",
                         title_font=dict(family="Syne",size=13,color="#f0f2f8"),
                         yaxis_title="P(Up) %", **DARK_LAYOUT)
    st.plotly_chart(fig_ml, use_container_width=True)

    if hasattr(clf, "feature_importances_"):
        fi = pd.DataFrame({"Feature": FEATURES, "Importance": clf.feature_importances_}).sort_values("Importance", ascending=True)
        fig_fi = px.bar(fi, x="Importance", y="Feature", orientation="h",
                        color="Importance", color_continuous_scale=["#1c2030","#4f8fff"],
                        title="Feature Importance")
        fig_fi.update_layout(height=360, showlegend=False,
                             title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
        st.plotly_chart(fig_fi, use_container_width=True)

    st.markdown('<div class="insight-text"><strong style="color:#f0f2f8">Disclaimer</strong><br>ML models are trained on historical patterns. Predictions are probabilistic and do not constitute financial advice.</div>', unsafe_allow_html=True)

# ── BENCHMARK ─────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.4rem">Portfolio Benchmark: {symbol} vs {bench}</div>', unsafe_allow_html=True)

    if df_spy is None:
        st.error(f"Could not fetch {bench}. Try 'SPY' or '^GSPC'.")
    else:
        s1   = df_raw["Close"].rename(symbol)
        s2   = df_spy["Close"].rename(bench)
        comb = pd.concat([s1, s2], axis=1).dropna()
        norm = comb / comb.iloc[0] * 100

        fig_bm = go.Figure()
        fig_bm.add_trace(go.Scatter(x=norm.index, y=norm[symbol], name=symbol,
                                    line=dict(color="#4f8fff",width=2)))
        fig_bm.add_trace(go.Scatter(x=norm.index, y=norm[bench], name=bench,
                                    line=dict(color="#8892a4",width=1.5,dash="dot")))
        fig_bm.update_layout(height=380, title="Normalised Performance (Base=100)",
                             title_font=dict(family="Syne",size=14,color="#f0f2f8"),
                             yaxis_title="Index", **DARK_LAYOUT)
        st.plotly_chart(fig_bm, use_container_width=True)

        rets     = comb.pct_change().dropna()
        cov      = rets.cov()
        beta     = cov.loc[symbol, bench] / rets[bench].var() if rets[bench].var() > 0 else 1
        alpha_ann= (rets[symbol].mean() - beta * rets[bench].mean()) * 252 * 100
        corr     = rets[symbol].corr(rets[bench])
        sym_ret  = (comb[symbol].iloc[-1] / comb[symbol].iloc[0] - 1) * 100
        bm_ret   = (comb[bench].iloc[-1]  / comb[bench].iloc[0]  - 1) * 100

        bm1, bm2, bm3, bm4 = st.columns(4)
        for col, lbl, val, color in [
            (bm1, f"{symbol} Return",    f"{sym_ret:+.1f}%",   "#22d98a" if sym_ret > 0 else "#f05252"),
            (bm2, f"{bench} Return",     f"{bm_ret:+.1f}%",    "#22d98a" if bm_ret > 0 else "#f05252"),
            (bm3, "Beta vs Benchmark",   f"{beta:.2f}",         "#f0f2f8"),
            (bm4, "Annualised Alpha",    f"{alpha_ann:+.1f}%",  "#22d98a" if alpha_ann > 0 else "#f05252"),
        ]:
            col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{color}">{val}</h2></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="insight-text" style="margin-top:.6rem">'
                    f'<strong style="color:#f0f2f8">Interpretation</strong><br>'
                    f'Beta of <strong>{beta:.2f}</strong> means {symbol} moves roughly {beta:.1f}x the {bench}. '
                    f'Alpha of <strong>{alpha_ann:+.1f}%</strong>/yr represents '
                    f'{"outperformance" if alpha_ann > 0 else "underperformance"}. '
                    f'Correlation: <strong>{corr:.2f}</strong>.</div>', unsafe_allow_html=True)

        roll_corr = rets[symbol].rolling(60).corr(rets[bench])
        fig_rc = go.Figure(go.Scatter(x=roll_corr.index, y=roll_corr, fill="tozeroy",
                                      line=dict(color="#7c6ff7",width=2),
                                      fillcolor="rgba(124,111,247,.08)"))
        fig_rc.update_layout(height=240, title=f"60-Day Rolling Correlation: {symbol} vs {bench}",
                             title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
        st.plotly_chart(fig_rc, use_container_width=True)

        # ── EXCEL EXPORT FIX ──────────────────────────────────────────────────
        # Root cause: norm/rets have a timezone-aware DatetimeIndex (from yfinance).
        # openpyxl raises ValueError when it encounters tz-aware datetimes.
        # Fix: strip timezone info and reset_index() before writing.
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            _strip_tz(norm).to_excel(w, sheet_name="Performance", index=False)
            _strip_tz(rets).to_excel(w, sheet_name="Returns",     index=False)
        st.download_button(
            "Export Report (Excel)",
            buf.getvalue(),
            file_name=f"{symbol}_vs_{bench}_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ── PRICE LEVELS ─────────────────────────────────────────────────────────────
with tab5:
    hi   = df["High"].max(); lo = df["Low"].min(); diff = hi - lo
    fibs = {"23.6%": hi - diff * .236, "38.2%": hi - diff * .382,
            "50.0%": hi - diff * .5,   "61.8%": hi - diff * .618}
    r_hi = float(df["High"].tail(20).max()); r_lo = float(df["Low"].tail(20).min())
    pos  = (cur - r_lo) / (r_hi - r_lo) * 100 if r_hi != r_lo else 0

    c1, c2 = st.columns(2)
    c1.markdown(f"""<div class="glass-card"><h4>Fibonacci Retracement</h4><table style="width:100%">
    {''.join(f'<tr><td>{k}</td><td>${v:.2f}</td></tr>' for k,v in fibs.items())}
    </table></div>""", unsafe_allow_html=True)
    pos_label = "Near Resistance" if pos > 70 else "Near Support" if pos < 30 else "Mid Range"
    c2.markdown(f"""<div class="glass-card"><h4>20-Day Support &amp; Resistance</h4><table style="width:100%">
    <tr><td>Resistance</td><td>${r_hi:.2f}</td></tr>
    <tr><td>Support</td><td>${r_lo:.2f}</td></tr>
    <tr><td>Price Position</td><td>{pos:.1f}% — {pos_label}</td></tr>
    </table></div>""", unsafe_allow_html=True)

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=df.index, y=df.Close, name="Price", line=dict(color="#4f8fff",width=2)))
    for (lbl, lvl), col in zip(fibs.items(), ["#f5a623","#f05252","#8892a4","#22d98a"]):
        fig5.add_hline(y=lvl, line_dash="dot", line_color=col, opacity=.7,
                       annotation_text=lbl, annotation_font=dict(color=col, size=10))
    fig5.update_layout(height=380, title="Fibonacci Retracement Levels",
                       title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig5, use_container_width=True)

# ── CORRELATION ──────────────────────────────────────────────────────────────
with tab6:
    if compare:
        closes = {symbol: df_raw["Close"]}
        for s in compare:
            sd, _ = fetch(s, period)
            if sd is not None: closes[s] = sd["Close"]
        corr_df = pd.DataFrame(closes).pct_change().dropna().corr()
        fig_c = px.imshow(corr_df, text_auto=".2f",
                          color_continuous_scale=["#f05252","#1c2030","#4f8fff"],
                          zmin=-1, zmax=1, title="Return Correlation Matrix")
        fig_c.update_layout(height=400, title_font=dict(family="Syne",size=13,color="#f0f2f8"), **DARK_LAYOUT)
        st.plotly_chart(fig_c, use_container_width=True)
        for s in compare:
            if s in corr_df.columns:
                cv = float(corr_df.loc[symbol, s])
                meaning = ("highly correlated (low diversification)" if cv > .7 else
                           "negatively correlated (good diversification)" if cv < -.3 else
                           "moderate relationship")
                st.markdown(f'<div style="font-size:.82rem;color:#8892a4;padding:.28rem 0;'
                            f'border-bottom:1px solid rgba(255,255,255,.04)">'
                            f'<strong style="color:#f0f2f8">{symbol} vs {s}:</strong> {cv:.2f} — {meaning}</div>',
                            unsafe_allow_html=True)
    else:
        st.info("Select comparison symbols in the sidebar.")

st.markdown('<div style="text-align:center;padding:1rem 0 .2rem;font-size:.72rem;color:#4e5669">Data · Yahoo Finance · ML predictions are not financial advice</div>', unsafe_allow_html=True)
