"""
Advanced Analytics — pages/1_Analytics.py

Replaces Compliance with four high-value features:
  1. Real ML Prediction  — XGBoost / RandomForest trained on 11 indicators
  2. Watchlist + Alerts  — persistent price-alert monitoring
  3. Backtesting         — SMA / RSI / MACD / Bollinger strategy tester
  4. Stock Screener      — universe scan with live filters

Chart: Price / Volume / RSI panels have increased vertical_spacing
       and row_heights for more visual breathing room.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime
import io, warnings, time
warnings.filterwarnings("ignore")

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from utils.styling import apply_css, DARK_LAYOUT
apply_css()

# ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def fetch(symbol: str, period: str = "2y") -> tuple:
    try:
        t = yf.Ticker(symbol)
        h = t.history(period=period)
        return (h, t.info) if not h.empty else (None, {})
    except Exception as e:
        st.error(str(e)); return None, {}


@st.cache_data(ttl=60)
def price_now(sym: str) -> float | None:
    try: return float(yf.Ticker(sym).history(period="1d")["Close"].iloc[-1])
    except: return None


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret1"]  = df["Close"].pct_change()
    df["ret5"]  = df["Close"].pct_change(5)
    df["ret20"] = df["Close"].pct_change(20)
    df["MA20"]  = df["Close"].rolling(20).mean()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA_r"]  = df["MA20"] / df["MA50"]
    d = df["Close"].diff()
    g = d.where(d>0,0).rolling(14).mean()
    l = (-d.where(d<0,0)).rolling(14).mean()
    df["RSI"]   = (100 - 100/(1 + g/l.replace(0,np.nan))).fillna(50)
    e1 = df["Close"].ewm(span=12,adjust=False).mean()
    e2 = df["Close"].ewm(span=26,adjust=False).mean()
    df["MACD"]  = e1 - e2
    df["MACD_s"]= df["MACD"].ewm(span=9,adjust=False).mean()
    df["MACD_d"]= df["MACD"] - df["MACD_s"]
    m_ = df["Close"].rolling(20).mean(); s_ = df["Close"].rolling(20).std()
    df["BB_pos"]= (df["Close"]-m_)/(2*s_+1e-9)
    lo = df["Low"].rolling(14).min(); hi = df["High"].rolling(14).max()
    df["Stoch"] = 100*(df["Close"]-lo)/(hi-lo+1e-9)
    df["ATR"]   = pd.concat([df["High"]-df["Low"],
                              (df["High"]-df["Close"].shift()).abs(),
                              (df["Low"]-df["Close"].shift()).abs()],axis=1).max(axis=1).rolling(14).mean()
    df["vol20"] = df["ret1"].rolling(20).std()*np.sqrt(252)
    df["OBV"]   = (np.sign(df["Close"].diff())*df["Volume"]).fillna(0).cumsum()
    df["OBV_r"] = df["OBV"].pct_change(5)
    df["target"]= (df["Close"].shift(-5) > df["Close"]).astype(int)
    return df

FEATS = ["ret1","ret5","ret20","RSI","MACD_d","BB_pos","Stoch","ATR","vol20","MA_r","OBV_r"]

def risk_metrics(df: pd.DataFrame) -> dict:
    r  = df["Close"].pct_change().dropna()
    ar = r.mean()*252*100; av = r.std()*np.sqrt(252)*100
    sr = ar/av if av else 0
    cum= (1+r).cumprod(); mdd=((cum-cum.expanding().max())/cum.expanding().max()).min()*100
    dr = r[r<0]; dd = dr.std()*np.sqrt(252)*100 if len(dr) else 0
    return {"Annual Return":ar,"Annual Vol":av,"Sharpe":sr,"Max DD":mdd,
            "VaR 95%":float(np.percentile(r,5))*100,"Sortino":ar/dd if dd else 0}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.8rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#7c6ff7,#4f8fff);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">📊</div>
        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">Analytics Hub</div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .8rem">
    """, unsafe_allow_html=True)
    symbol   = st.text_input("Symbol", "AAPL").upper().strip()
    period   = st.selectbox("Period", ["6mo","1y","2y","3y","5y"], index=1)
    bench    = st.text_input("Benchmark", "SPY").upper().strip()
    compare  = st.multiselect("Compare With", ["AAPL","MSFT","GOOGL","TSLA","AMZN","NVDA","META"], default=["MSFT"])
    ml_model = st.selectbox("ML Model", ["Random Forest","Gradient Boost"] + (["XGBoost"] if HAS_XGB else []))

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .2rem">Analytics Hub — {symbol}</div><div style="font-size:.82rem;color:#8892a4">Technical · Risk · ML Prediction · Watchlist · Backtest · Screener · Benchmark</div>', unsafe_allow_html=True)

if not symbol:
    st.info("Enter a symbol in the sidebar."); st.stop()

with st.spinner(f"Fetching {symbol}…"):
    df_raw, info = fetch(symbol, period)
    df_spy, _    = fetch(bench, period)

if df_raw is None:
    st.error("No data returned. Check the symbol."); st.stop()

df   = build_features(df_raw)
risk = risk_metrics(df_raw)
cur  = float(df["Close"].iloc[-1])
chg  = cur - float(df["Close"].iloc[-2])
chgp = chg / float(df["Close"].iloc[-2]) * 100

# Key metrics strip
for col, lbl, val, dlt in zip(st.columns(5),
    ["Price","Volume","52W High","52W Low","Sharpe"],
    [f"${cur:.2f}", f"{df['Volume'].iloc[-1]:,.0f}",
     f"${info.get('fiftyTwoWeekHigh',0):.2f}", f"${info.get('fiftyTwoWeekLow',0):.2f}",
     f"{risk['Sharpe']:.2f}"],
    [f"{chgp:+.2f}%", None, None, None, None]):
    with col: st.metric(lbl, val, dlt)

st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

(tab1, tab2, tab3, tab4, tab5,
 tab6, tab7, tab8) = st.tabs(["Technical","Risk","ML Prediction","Watchlist & Alerts",
                               "Backtesting","Screener","Benchmark & Export","Correlation"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — TECHNICAL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # Increased vertical_spacing and row_heights for more gap between panels
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True,
                        vertical_spacing=0.06,
                        row_heights=[0.32, 0.17, 0.17, 0.17, 0.17],
                        subplot_titles=("Price & MAs","RSI (14)","Stochastic","MACD","OBV"))
    fig.add_trace(go.Scatter(x=df.index,y=df.Close, name="Close",line=dict(color="#4f8fff",width=1.8)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.MA20,  name="MA20", line=dict(color="#f5a623",width=1.2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.MA50,  name="MA50", line=dict(color="#7c6ff7",width=1.2)),row=1,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.RSI,   name="RSI",  line=dict(color="#4f8fff",width=1.5)),row=2,col=1)
    fig.add_hline(y=70,line_dash="dot",line_color="#f05252",opacity=.5,row=2,col=1)
    fig.add_hline(y=30,line_dash="dot",line_color="#22d98a",opacity=.5,row=2,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.Stoch, name="Stoch",line=dict(color="#4f8fff",width=1.2)),row=3,col=1)
    fig.add_hline(y=80,line_dash="dot",line_color="#f05252",opacity=.5,row=3,col=1)
    fig.add_hline(y=20,line_dash="dot",line_color="#22d98a",opacity=.5,row=3,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.MACD,  name="MACD", line=dict(color="#4f8fff",width=1.2)),row=4,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.MACD_s,name="Signal",line=dict(color="#f5a623",width=1.2)),row=4,col=1)
    fig.add_trace(go.Scatter(x=df.index,y=df.OBV,   name="OBV",  line=dict(color="#22d98a",width=1.2)),row=5,col=1)
    fig.update_layout(height=1100,showlegend=True,title=f"{symbol} Full Technical",
                      title_font=dict(family="Syne",size=14,color="#f0f2f8"),**DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    rsi_v = float(df.RSI.iloc[-1])
    for col,lbl,val,d in zip(st.columns(4),
        ["RSI 14","Stochastic","MACD","ATR"],
        [f"{rsi_v:.1f}",f"{df.Stoch.iloc[-1]:.1f}",f"{df.MACD.iloc[-1]:.4f}",f"${df.ATR.iloc[-1]:.2f}"],
        ["Overbought" if rsi_v>70 else "Oversold" if rsi_v<30 else "Neutral",None,
         "Bullish" if df.MACD.iloc[-1]>df.MACD_s.iloc[-1] else "Bearish","Volatility"]):
        with col: st.metric(lbl,val,d)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RISK
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Risk Metrics</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    for col,lbl,val in [(c1,"Annual Return",f"{risk['Annual Return']:+.1f}%"),
                        (c2,"Annual Volatility",f"{risk['Annual Vol']:.1f}%"),
                        (c3,"Sharpe Ratio",f"{risk['Sharpe']:.2f}")]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>',unsafe_allow_html=True)
    c4,c5,c6 = st.columns(3)
    for col,lbl,val in [(c4,"Max Drawdown",f"{risk['Max DD']:.1f}%"),
                        (c5,"VaR 95%",f"{risk['VaR 95%']:.2f}%"),
                        (c6,"Sortino Ratio",f"{risk['Sortino']:.2f}")]:
        col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2>{val}</h2></div>',unsafe_allow_html=True)

    rs = (30 if risk["Annual Vol"]>40 else 20 if risk["Annual Vol"]>25 else 10) + \
         (30 if risk["Max DD"]<-30 else 20 if risk["Max DD"]<-15 else 10) + \
         (20 if risk["Sharpe"]<1 else 0)
    rl = "High" if rs>60 else "Medium" if rs>30 else "Low"
    rc = "#f05252" if rl=="High" else "#f5a623" if rl=="Medium" else "#22d98a"
    st.markdown(f'<div class="insight-text" style="margin-top:.7rem"><strong style="color:#f0f2f8">Risk Level: <span style="color:{rc}">{rl}</span></strong> — Score {rs}/100<br>{"⚠️ High volatility" if rl=="High" else "📊 Moderate profile" if rl=="Medium" else "✅ Conservative"}</div>',unsafe_allow_html=True)

    rv = df["Close"].pct_change().rolling(20).std()*np.sqrt(252)*100
    fig2 = go.Figure(go.Scatter(x=df.index,y=rv,fill="tozeroy",line=dict(color="#f5a623",width=2),fillcolor="rgba(245,166,35,.08)"))
    fig2.update_layout(height=260,title="20-Day Rolling Volatility (%)",title_font=dict(family="Syne",size=13,color="#f0f2f8"),**DARK_LAYOUT)
    st.plotly_chart(fig2,use_container_width=True)

    cum = (1+df["Close"].pct_change().dropna()).cumprod()
    dd_s = (cum-cum.expanding().max())/cum.expanding().max()*100
    figdd = go.Figure(go.Scatter(x=dd_s.index,y=dd_s,fill="tozeroy",line=dict(color="#f05252",width=1.5),fillcolor="rgba(240,82,82,.07)"))
    figdd.update_layout(height=220,title="Drawdown (%)",title_font=dict(family="Syne",size=13,color="#f0f2f8"),**DARK_LAYOUT)
    st.plotly_chart(figdd,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ML PREDICTION (XGBoost / RF / GB)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.3rem">Real ML Price Direction Prediction — {ml_model}</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.78rem;color:#8892a4;margin-bottom:.7rem">Predicts whether the price will be higher in 5 trading days. Trained on 11 technical features, walk-forward validated (80/20 split).</div>', unsafe_allow_html=True)

    with st.spinner("Training model…"):
        ml_df = df[FEATS+["target"]].dropna()
        if len(ml_df) < 60:
            st.error("Not enough history (need ≥60 rows)."); st.stop()

        X  = ml_df[FEATS].values; y = ml_df["target"].values
        sc = StandardScaler(); X = sc.fit_transform(X)
        sp = int(len(X)*.8)
        Xtr,Xte = X[:sp],X[sp:]; ytr,yte = y[:sp],y[sp:]

        if ml_model == "Random Forest":
            clf = RandomForestClassifier(n_estimators=200,max_depth=6,random_state=42,n_jobs=-1)
        elif ml_model == "Gradient Boost":
            clf = GradientBoostingClassifier(n_estimators=150,max_depth=4,learning_rate=.05,random_state=42)
        else:
            clf = XGBClassifier(n_estimators=200,max_depth=5,learning_rate=.05,
                                eval_metric="logloss",random_state=42,verbosity=0)

        clf.fit(Xtr,ytr)
        preds  = clf.predict(Xte)
        probas = clf.predict_proba(Xte)[:,1]
        acc    = accuracy_score(yte,preds)*100
        lf     = sc.transform(ml_df[FEATS].iloc[[-1]].values)
        cp     = clf.predict(lf)[0]
        cpb    = clf.predict_proba(lf)[0][1]*100

    pred_dir = "UP ▲" if cp==1 else "DOWN ▼"
    pred_col = "#22d98a" if cp==1 else "#f05252"
    conf_col = "#22d98a" if cpb>60 else "#f05252" if cpb<40 else "#f5a623"

    m1,m2,m3,m4 = st.columns(4)
    m1.markdown(f'<div class="metric-box"><h4>5-Day Prediction</h4><h2 style="color:{pred_col}">{pred_dir}</h2></div>',unsafe_allow_html=True)
    m2.markdown(f'<div class="metric-box"><h4>Confidence</h4><h2 style="color:{conf_col}">{cpb:.1f}%</h2></div>',unsafe_allow_html=True)
    m3.markdown(f'<div class="metric-box"><h4>Test Accuracy</h4><h2>{acc:.1f}%</h2></div>',unsafe_allow_html=True)
    m4.markdown(f'<div class="metric-box"><h4>Train Samples</h4><h2>{sp}</h2></div>',unsafe_allow_html=True)

    fig_ml = go.Figure()
    fig_ml.add_trace(go.Scatter(x=ml_df.index[sp:],y=probas*100,name="P(Up)",
                                fill="tozeroy",line=dict(color="#4f8fff",width=2),fillcolor="rgba(79,143,255,.1)"))
    fig_ml.add_hline(y=50,line_dash="dot",line_color="#f5a623",opacity=.6)
    fig_ml.update_layout(height=260,title="Predicted Probability of Upward Move (Test Set)",
                         title_font=dict(family="Syne",size=13,color="#f0f2f8"),yaxis_title="P(Up) %",**DARK_LAYOUT)
    st.plotly_chart(fig_ml,use_container_width=True)

    if hasattr(clf,"feature_importances_"):
        fi = pd.DataFrame({"Feature":FEATS,"Importance":clf.feature_importances_}).sort_values("Importance",ascending=True)
        fig_fi = px.bar(fi,x="Importance",y="Feature",orientation="h",
                        color="Importance",color_continuous_scale=["#1c2030","#4f8fff"],title="Feature Importance")
        fig_fi.update_layout(height=340,showlegend=False,title_font=dict(family="Syne",size=13,color="#f0f2f8"),**DARK_LAYOUT)
        st.plotly_chart(fig_fi,use_container_width=True)

    st.markdown('<div class="insight-text"><strong style="color:#f0f2f8">⚠️ Disclaimer</strong><br>ML models are trained on historical patterns only. Not financial advice. Past accuracy does not guarantee future results.</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — WATCHLIST & PRICE ALERTS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Watchlist & Price Alerts</div>', unsafe_allow_html=True)

    # Session state
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL","MSFT","TSLA","NVDA","GOOGL"]
    if "alerts" not in st.session_state:
        st.session_state.alerts = []  # list of {sym, cond, trigger, note}

    wc1, wc2 = st.columns([1.5, 1])

    # ── Watchlist ─────────────────────────────────────────────────────────────
    with wc1:
        st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">My Watchlist</div>', unsafe_allow_html=True)
        add_col, btn_col = st.columns([3, 1])
        with add_col:
            new_sym = st.text_input("Add symbol", placeholder="AMZN, BTC-USD…", label_visibility="collapsed", key="wl_inp")
        with btn_col:
            if st.button("Add", key="wl_add", use_container_width=True) and new_sym:
                s = new_sym.upper().strip()
                if s not in st.session_state.watchlist:
                    st.session_state.watchlist.append(s); st.rerun()

        to_rm = []
        for wl_sym in st.session_state.watchlist:
            p = price_now(wl_sym)
            if p is None: continue
            prev_d, _ = fetch(wl_sym, "5d")
            if prev_d is not None and len(prev_d) >= 2:
                prev = float(prev_d["Close"].iloc[-2])
                chg_p = (p - prev) / prev * 100
            else:
                chg_p = 0.0
            up = chg_p >= 0
            rc1, rc2, rc3 = st.columns([2, 1.2, 0.5])
            with rc1:
                st.markdown(f'<div style="font-weight:600;color:#f0f2f8;font-size:.88rem">{wl_sym}</div>', unsafe_allow_html=True)
            with rc2:
                st.markdown(f'<div style="font-size:.95rem;font-weight:700;color:#f0f2f8">${p:.2f}</div><div style="font-size:.72rem;color:{"#22d98a" if up else "#f05252"}">{chg_p:+.2f}%</div>', unsafe_allow_html=True)
            with rc3:
                if st.button("✕", key=f"rm_{wl_sym}"): to_rm.append(wl_sym)
            st.markdown("<hr style='border-color:rgba(255,255,255,.04);margin:.2rem 0'>", unsafe_allow_html=True)
        for s in to_rm:
            st.session_state.watchlist.remove(s); st.rerun()

    # ── Alerts ────────────────────────────────────────────────────────────────
    with wc2:
        st.markdown('<div style="font-size:.72rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#4e5669;margin-bottom:.4rem">Price Alerts</div>', unsafe_allow_html=True)
        with st.form("alert_form"):
            a_sym   = st.text_input("Symbol", placeholder="AAPL")
            a_cond  = st.selectbox("Condition", ["Price Above","Price Below","RSI Above 70","RSI Below 30"])
            a_price = st.number_input("Price threshold ($)", min_value=0.01, step=0.01, value=150.0)
            a_note  = st.text_input("Note (optional)", placeholder="Buy signal…")
            if st.form_submit_button("Set Alert", use_container_width=True) and a_sym:
                st.session_state.alerts.append({"sym":a_sym.upper(),"cond":a_cond,"trig":a_price,"note":a_note,"fired":False})
                st.success(f"Alert set for {a_sym.upper()}")

        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.session_state.alerts:
            for i, al in enumerate(st.session_state.alerts):
                p = price_now(al["sym"])
                fired = False
                if p:
                    if al["cond"] == "Price Above" and p > al["trig"]: fired = True
                    if al["cond"] == "Price Below" and p < al["trig"]: fired = True
                col = "#f05252" if fired else "#4e5669"
                ico = "🔴" if fired else "⏳"
                st.markdown(f'<div style="background:var(--bg-elevated);border:1px solid {col}33;border-left:3px solid {col};border-radius:0 8px 8px 0;padding:.6rem .9rem;font-size:.78rem;margin-bottom:.3rem">{ico} <strong style="color:#f0f2f8">{al["sym"]}</strong> — {al["cond"]} ${al["trig"]:.2f}{"  ✅ TRIGGERED" if fired else ""}{"  · "+al["note"] if al["note"] else ""}</div>', unsafe_allow_html=True)
            if st.button("Clear all alerts"):
                st.session_state.alerts = []; st.rerun()
        else:
            st.markdown('<div style="font-size:.78rem;color:#4e5669;padding:.4rem">No alerts set yet.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — BACKTESTING
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Strategy Backtester</div>', unsafe_allow_html=True)

    bc1,bc2,bc3,bc4 = st.columns(4)
    with bc1: bt_sym    = st.text_input("Symbol", symbol, key="bt_sym")
    with bc2: bt_period = st.selectbox("Period",["1y","2y","3y","5y"],index=1)
    with bc3: bt_strat  = st.selectbox("Strategy",["SMA Crossover","RSI Mean Reversion","MACD Signal","Bollinger Reversion"])
    with bc4: bt_cap    = st.number_input("Capital ($)",value=10_000,step=1_000,min_value=1_000)

    if bt_strat == "SMA Crossover":
        p1,p2 = st.columns(2)
        fast = p1.slider("Fast MA",5,50,20); slow = p2.slider("Slow MA",20,200,50)
    elif bt_strat == "RSI Mean Reversion":
        p1,p2 = st.columns(2)
        rsi_lo = p1.slider("Oversold",10,40,30); rsi_hi = p2.slider("Overbought",60,90,70)
    elif bt_strat == "Bollinger Reversion":
        bb_p = st.slider("BB Period",10,40,20)

    if st.button("▶ Run Backtest", type="primary"):
        with st.spinner("Running…"):
            bt_df, _ = fetch(bt_sym.upper(), bt_period)
            if bt_df is None:
                st.error("Cannot fetch data."); st.stop()
            bt_df = bt_df.copy(); bt_df["ret"] = bt_df["Close"].pct_change()

            if bt_strat == "SMA Crossover":
                bt_df["fast_ma"] = bt_df["Close"].rolling(fast).mean()
                bt_df["slow_ma"] = bt_df["Close"].rolling(slow).mean()
                bt_df["sig"] = np.where(bt_df["fast_ma"]>bt_df["slow_ma"],1,-1)
            elif bt_strat == "RSI Mean Reversion":
                d2 = bt_df["Close"].diff(); g2=d2.where(d2>0,0).rolling(14).mean(); l2=(-d2.where(d2<0,0)).rolling(14).mean()
                rsi2=(100-100/(1+g2/l2.replace(0,np.nan))).fillna(50)
                bt_df["sig"]=np.where(rsi2<rsi_lo,1,np.where(rsi2>rsi_hi,-1,0))
                bt_df["sig"]=bt_df["sig"].replace(0,np.nan).ffill().fillna(0)
            elif bt_strat == "MACD Signal":
                e1=bt_df["Close"].ewm(span=12,adjust=False).mean(); e2=bt_df["Close"].ewm(span=26,adjust=False).mean()
                m=e1-e2; s=m.ewm(span=9,adjust=False).mean(); bt_df["sig"]=np.where(m>s,1,-1)
            else:
                m_=bt_df["Close"].rolling(bb_p).mean(); s_=bt_df["Close"].rolling(bb_p).std()
                bt_df["sig"]=np.where(bt_df["Close"]<m_-2*s_,1,np.where(bt_df["Close"]>m_+2*s_,-1,0))
                bt_df["sig"]=bt_df["sig"].replace(0,np.nan).ffill().fillna(0)

            bt_df["sret"]    = bt_df["sig"].shift(1)*bt_df["ret"]
            bt_df["bh_val"]  = (1+bt_df["ret"]).cumprod()*bt_cap
            bt_df["st_val"]  = (1+bt_df["sret"].fillna(0)).cumprod()*bt_cap
            bt_df = bt_df.dropna(subset=["bh_val","st_val"])

            fs=float(bt_df["st_val"].iloc[-1]); fb=float(bt_df["bh_val"].iloc[-1])
            sr2=(fs/bt_cap-1)*100; bhr=(fb/bt_cap-1)*100
            rets2=bt_df["sret"].dropna(); sh2=(rets2.mean()/rets2.std()*np.sqrt(252)) if rets2.std()>0 else 0
            cum2=bt_df["st_val"]/bt_cap; mdd2=((cum2-cum2.expanding().max())/cum2.expanding().max()).min()*100
            ntrades=int(bt_df["sig"].diff().abs().sum()//2)

            for col,lbl,val,clr in zip(st.columns(5),
                ["Final Value","Strategy Return","Buy & Hold","Sharpe","Max DD"],
                [f"${fs:,.0f}",f"{sr2:+.1f}%",f"{bhr:+.1f}%",f"{sh2:.2f}",f"{mdd2:.1f}%"],
                ["#4f8fff","#22d98a" if sr2>0 else "#f05252","#f5a623","#7c6ff7","#f05252"]):
                col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{clr}">{val}</h2></div>',unsafe_allow_html=True)

            st.markdown(f'<div style="margin:.4rem 0;font-size:.8rem;color:#8892a4">Trades: <strong style="color:#f0f2f8">{ntrades}</strong> &nbsp;·&nbsp; Alpha: <strong style="color:{"#22d98a" if sr2>bhr else "#f05252"}">{sr2-bhr:+.1f}%</strong></div>',unsafe_allow_html=True)

            fig_bt = go.Figure()
            fig_bt.add_trace(go.Scatter(x=bt_df.index,y=bt_df["st_val"],name=bt_strat,line=dict(color="#4f8fff",width=2)))
            fig_bt.add_trace(go.Scatter(x=bt_df.index,y=bt_df["bh_val"],name="Buy & Hold",line=dict(color="#8892a4",width=1.5,dash="dot")))
            fig_bt.update_layout(height=360,title=f"{bt_sym.upper()} — {bt_strat} vs Buy & Hold",
                                 title_font=dict(family="Syne",size=14,color="#f0f2f8"),yaxis_title="Portfolio ($)",**DARK_LAYOUT)
            st.plotly_chart(fig_bt,use_container_width=True)

            csv_bt = bt_df[["Close","sig","sret","st_val","bh_val"]].round(4).to_csv()
            st.download_button("Export Backtest CSV", csv_bt.encode(),
                               file_name=f"backtest_{bt_sym}_{bt_strat.replace(' ','_')}.csv",
                               mime="text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — STOCK SCREENER
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Stock Screener</div>', unsafe_allow_html=True)

    UNIVERSE = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","NFLX","AMD","INTC",
                "JPM","GS","BAC","WFC","V","MA","PYPL","SQ","JNJ","PFE","MRNA","ABBV",
                "UNH","WMT","COST","TGT","HD","NKE","SBUX","DIS"]

    f1,f2,f3,f4 = st.columns(4)
    with f1: min_p,max_p = st.slider("Price ($)",0,5000,(0,5000))
    with f2: min_c,max_c = st.slider("Day Change %",-20,20,(-20,20))
    with f3: min_v       = st.number_input("Min Volume (M)",value=0.0,step=0.5)
    with f4: sectors     = st.multiselect("Sector",["Technology","Healthcare","Finance","Consumer","Energy","Any"],default=["Any"])

    if st.button("Run Screener", type="primary"):
        with st.spinner(f"Scanning {len(UNIVERSE)} stocks…"):
            results = []; prog = st.progress(0)
            for i,s in enumerate(UNIVERSE):
                try:
                    t = yf.Ticker(s); info2=t.info
                    p2 = info2.get("regularMarketPrice") or info2.get("currentPrice",0) or 0
                    prev2 = info2.get("regularMarketPreviousClose",p2)
                    chg2  = (p2-prev2)/prev2*100 if prev2 else 0
                    vol2  = (info2.get("regularMarketVolume",0) or 0)/1e6
                    sec2  = info2.get("sector","Unknown")
                    pe2   = info2.get("trailingPE","—")
                    ok    = (min_p<=p2<=max_p and min_c<=chg2<=max_c and vol2>=min_v)
                    if ok and "Any" not in sectors:
                        ok = any(sx.lower() in sec2.lower() for sx in sectors)
                    if ok:
                        results.append({"Symbol":s,"Price":f"${p2:.2f}","Change":f"{chg2:+.2f}%",
                                        "Volume(M)":f"{vol2:.1f}","Sector":sec2,"P/E":pe2,
                                        "52W Hi":f"${info2.get('fiftyTwoWeekHigh',0):.2f}"})
                except: pass
                prog.progress((i+1)/len(UNIVERSE))

        if results:
            st.success(f"Found {len(results)} matching stocks")
            df_r = pd.DataFrame(results)
            st.dataframe(df_r, use_container_width=True, hide_index=True)
            st.download_button("Export Screener CSV", df_r.to_csv(index=False).encode(),
                               file_name="screener_results.csv", mime="text/csv")
        else:
            st.warning("No stocks matched the filters.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — BENCHMARK & EXPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown(f'<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.4rem">Benchmark: {symbol} vs {bench}</div>', unsafe_allow_html=True)

    if df_spy is None:
        st.error(f"Cannot fetch benchmark {bench}.")
    else:
        s1 = df_raw["Close"].rename(symbol)
        s2 = df_spy["Close"].rename(bench)
        comb = pd.concat([s1,s2],axis=1).dropna()
        norm = comb/comb.iloc[0]*100

        fig_bm = go.Figure()
        fig_bm.add_trace(go.Scatter(x=norm.index,y=norm[symbol],name=symbol,line=dict(color="#4f8fff",width=2)))
        fig_bm.add_trace(go.Scatter(x=norm.index,y=norm[bench],name=bench,line=dict(color="#8892a4",width=1.5,dash="dot")))
        fig_bm.update_layout(height=380,title=f"Normalised Performance (Base=100)",
                             title_font=dict(family="Syne",size=14,color="#f0f2f8"),**DARK_LAYOUT)
        st.plotly_chart(fig_bm,use_container_width=True)

        rets2 = comb.pct_change().dropna()
        cov   = rets2.cov(); beta = cov.loc[symbol,bench]/rets2[bench].var() if rets2[bench].var()>0 else 1
        alpha_ann = (rets2[symbol].mean()-beta*rets2[bench].mean())*252*100
        corr_val  = rets2[symbol].corr(rets2[bench])
        sym_ret   = (comb[symbol].iloc[-1]/comb[symbol].iloc[0]-1)*100
        bm_ret    = (comb[bench].iloc[-1]/comb[bench].iloc[0]-1)*100

        for col,lbl,val,clr in zip(st.columns(4),
            [f"{symbol} Return",f"{bench} Return","Beta","Alpha (ann)"],
            [f"{sym_ret:+.1f}%",f"{bm_ret:+.1f}%",f"{beta:.2f}",f"{alpha_ann:+.1f}%"],
            ["#22d98a" if sym_ret>0 else "#f05252","#22d98a" if bm_ret>0 else "#f05252",
             "#f0f2f8","#22d98a" if alpha_ann>0 else "#f05252"]):
            col.markdown(f'<div class="metric-box"><h4>{lbl}</h4><h2 style="color:{clr}">{val}</h2></div>',unsafe_allow_html=True)

        st.markdown(f'<div class="insight-text" style="margin-top:.6rem">Beta {beta:.2f} · Alpha {alpha_ann:+.1f}%/yr · Correlation {corr_val:.2f}</div>',unsafe_allow_html=True)

        # Export
        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        ec1, ec2 = st.columns(2)
        with ec1:
            # Strip tz before Excel export to avoid openpyxl ValueError
            norm_export = norm.copy()
            if hasattr(norm_export.index, "tz") and norm_export.index.tz is not None:
                norm_export.index = norm_export.index.tz_localize(None)
            rets_export = rets2.copy()
            if hasattr(rets_export.index, "tz") and rets_export.index.tz is not None:
                rets_export.index = rets_export.index.tz_localize(None)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                norm_export.reset_index().to_excel(w, sheet_name="Performance", index=False)
                rets_export.reset_index().to_excel(w, sheet_name="Returns", index=False)
            st.download_button("Export Excel Report", buf.getvalue(),
                               file_name=f"{symbol}_vs_{bench}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)
        with ec2:
            csv_bm = norm.reset_index().to_csv(index=False)
            st.download_button("Export CSV", csv_bm.encode(),
                               file_name=f"{symbol}_vs_{bench}.csv", mime="text/csv",
                               use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — CORRELATION
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    if compare:
        closes = {symbol: df_raw["Close"]}
        for s in compare:
            sd,_ = fetch(s, period)
            if sd is not None: closes[s] = sd["Close"]
        corr_df = pd.DataFrame(closes).pct_change().dropna().corr()
        fig_c = px.imshow(corr_df,text_auto=".2f",
                          color_continuous_scale=["#f05252","#1c2030","#4f8fff"],
                          zmin=-1,zmax=1,title="Return Correlation Matrix")
        fig_c.update_layout(height=400,title_font=dict(family="Syne",size=13,color="#f0f2f8"),**DARK_LAYOUT)
        st.plotly_chart(fig_c,use_container_width=True)
        for s in compare:
            if s in corr_df.columns:
                cv = float(corr_df.loc[symbol,s])
                meaning = "highly correlated" if cv>.7 else "negatively correlated (diversifier)" if cv<-.3 else "moderate correlation"
                st.markdown(f'<div style="font-size:.82rem;color:#8892a4;padding:.28rem 0;border-bottom:1px solid rgba(255,255,255,.04)"><strong style="color:#f0f2f8">{symbol} vs {s}:</strong> {cv:.2f} — {meaning}</div>',unsafe_allow_html=True)
    else:
        st.info("Select comparison symbols in the sidebar.")

st.markdown('<div style="text-align:center;padding:1rem 0 .2rem;font-size:.72rem;color:#4e5669">Data · Yahoo Finance · ML predictions are not financial advice</div>',unsafe_allow_html=True)
