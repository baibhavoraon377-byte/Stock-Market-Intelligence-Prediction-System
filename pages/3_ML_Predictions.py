"""
ML Price Predictions  ·  pages/4_ML_Predictions.py
Real machine-learning price forecasting with sklearn & XGBoost.
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
.ml-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
    padding:1.3rem 1.5rem;margin-bottom:.8rem;position:relative;overflow:hidden;}
.ml-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,#4f8fff,#7c6ff7);opacity:.6;}
.ml-card h4{font-family:'Syne',sans-serif;font-size:.72rem;font-weight:600;letter-spacing:.08em;
    text-transform:uppercase;color:var(--text-secondary);margin-bottom:.6rem;}
.ml-card table td{padding:.28rem .4rem;font-size:.82rem;color:var(--text-secondary);}
.ml-card table td:last-child{color:var(--text-primary);}
.pred-badge{display:inline-flex;align-items:center;gap:5px;padding:4px 12px;border-radius:20px;
    font-size:.75rem;font-weight:600;}
.pred-up{background:rgba(34,217,138,.12);color:#22d98a;}
.pred-down{background:rgba(240,82,82,.12);color:#f05252;}
.pred-neutral{background:rgba(79,143,255,.12);color:#4f8fff;}
.model-chip{background:var(--bg-elevated);border:1px solid var(--border-active);
    border-radius:20px;padding:3px 10px;font-size:.7rem;font-weight:600;color:#8892a4;display:inline-block;margin:2px;}
.metric-box{background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:1rem;text-align:center;}
.metric-box h4{font-size:.65rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
    color:var(--text-secondary);margin:0 0 .4rem;}
.metric-box h2{font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text-primary);margin:0;}
.nav-group{font-size:.62rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text-muted)!important;padding:.5rem .4rem .2rem;}
.nav-item{display:flex;align-items:center;gap:9px;padding:.5rem .8rem;border-radius:var(--radius-sm);
    font-size:.83rem;font-weight:500;color:var(--text-secondary)!important;cursor:pointer;margin:2px 0;}
.nav-item:hover{background:rgba(255,255,255,.05);}
.nav-item.active{background:rgba(79,143,255,.15);color:var(--accent-blue)!important;font-weight:600;}
.live-dot{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;font-weight:600;color:var(--accent-green);}
.live-dot::before{content:'';width:7px;height:7px;background:var(--accent-green);border-radius:50%;animation:pdot 2s infinite;}
@keyframes pdot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(1.3);}}
.stButton>button{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;border-radius:var(--radius-sm)!important;font-size:.8rem!important;transition:all .15s!important;}
.stButton>button:hover{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stButton>button[kind="primary"]{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stSelectbox>div>div,.stSlider{background:var(--bg-elevated)!important;}
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
        <div class="nav-item active">🤖 ML Predictions</div>
        <div class="nav-item">🔔 Watchlist & Alerts</div>
        <div class="nav-item">⚙️ Backtesting</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:0.8rem 0">
    """, unsafe_allow_html=True)

    symbol = st.text_input("Stock Symbol", value="AAPL", placeholder="e.g. TSLA, NVDA").upper().strip()
    period = st.selectbox("Training Data Period", ["6mo", "1y", "2y", "5y"], index=2)
    forecast_days = st.slider("Forecast Horizon (days)", min_value=5, max_value=30, value=10, step=5)
    model_choice = st.selectbox("Model", ["XGBoost", "Random Forest", "Linear Regression", "All (Ensemble)"])
    run_btn = st.button("🚀 Run Prediction", use_container_width=True, type="primary")

# ── Feature engineering ───────────────────────────────────────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Returns"]     = df["Close"].pct_change()
    df["Log_Returns"] = np.log(df["Close"] / df["Close"].shift(1))
    for w in [5, 10, 20, 50]:
        df[f"MA{w}"]       = df["Close"].rolling(w).mean()
        df[f"STD{w}"]      = df["Close"].rolling(w).std()
        df[f"MOM{w}"]      = df["Close"] - df["Close"].shift(w)
        df[f"ROC{w}"]      = df["Close"].pct_change(w)
    delta = df["Close"].diff()
    gain  = delta.where(delta > 0, 0.0).rolling(14).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
    df["RSI"]  = 100 - (100 / (1 + gain / loss.replace(0, np.nan))).fillna(50)
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["OBV"]  = (np.sign(df["Close"].diff()) * df["Volume"]).fillna(0).cumsum()
    df["VolumeMA10"] = df["Volume"].rolling(10).mean()
    df["VolRatio"]   = df["Volume"] / df["VolumeMA10"].replace(0, np.nan)
    df["Target"]     = df["Close"].shift(-1)           # predict next-day close
    df.dropna(inplace=True)
    return df


@st.cache_data(ttl=600, show_spinner=False)
def fetch_and_train(symbol: str, period: str, forecast_days: int, model_choice: str):
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    try:
        import xgboost as xgb
        HAS_XGB = True
    except ImportError:
        HAS_XGB = False

    ticker = yf.Ticker(symbol)
    raw = ticker.history(period=period)
    if raw.empty or len(raw) < 80:
        return None

    df = build_features(raw)

    feature_cols = [c for c in df.columns if c not in
                    ["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits", "Target"]]
    X = df[feature_cols].values
    y = df["Target"].values

    split = int(len(X) * 0.80)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    models = {}
    if model_choice in ("Random Forest", "All (Ensemble)"):
        rf = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)
        rf.fit(X_train_s, y_train)
        models["Random Forest"] = rf
    if model_choice in ("XGBoost", "All (Ensemble)") and HAS_XGB:
        xgbm = xgb.XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05,
                                 subsample=0.8, colsample_bytree=0.8,
                                 random_state=42, verbosity=0)
        xgbm.fit(X_train_s, y_train)
        models["XGBoost"] = xgbm
    if model_choice in ("Linear Regression", "All (Ensemble)"):
        lr = Ridge(alpha=1.0)
        lr.fit(X_train_s, y_train)
        models["Linear Regression"] = lr

    if not models:  # fallback
        rf = RandomForestRegressor(n_estimators=200, random_state=42)
        rf.fit(X_train_s, y_train)
        models["Random Forest"] = rf

    # ── Backtest metrics ──────────────────────────────────────────────────────
    metrics = {}
    preds_test = {}
    for name, m in models.items():
        p = m.predict(X_test_s)
        preds_test[name] = p
        mae  = mean_absolute_error(y_test, p)
        r2   = r2_score(y_test, p)
        mape = float(np.mean(np.abs((y_test - p) / np.where(y_test == 0, 1, y_test))) * 100)
        direction_acc = float(np.mean(np.sign(np.diff(p)) == np.sign(np.diff(y_test))) * 100)
        metrics[name] = dict(mae=mae, r2=r2, mape=mape, direction_acc=direction_acc)

    # ── Future forecast ────────────────────────────────────────────────────────
    last_row = df[feature_cols].iloc[-1].values.reshape(1, -1)
    future_preds = {}
    for name, m in models.items():
        preds = []
        row = last_row.copy()
        for _ in range(forecast_days):
            row_s   = scaler.transform(row)
            next_p  = float(m.predict(row_s)[0])
            preds.append(next_p)
            # crude feature shift — shift momentum/lag features
            row[0, 0] = (next_p - row[0, -1]) / max(row[0, -1], 1e-9)  # returns
        future_preds[name] = preds

    ensemble_future = np.mean(list(future_preds.values()), axis=0).tolist() if len(future_preds) > 1 else list(future_preds.values())[0]

    # ── Feature importance (first tree model found) ───────────────────────────
    feat_imp = None
    for name in ("XGBoost", "Random Forest"):
        if name in models:
            fi = models[name].feature_importances_
            feat_imp = pd.Series(fi, index=feature_cols).nlargest(12)
            break

    return dict(
        history    = df,
        feature_cols = feature_cols,
        y_test     = y_test,
        preds_test = preds_test,
        metrics    = metrics,
        future_preds = future_preds,
        ensemble_future = ensemble_future,
        last_close = float(df["Close"].iloc[-1]),
        models     = list(models.keys()),
        feat_imp   = feat_imp,
        test_dates = df.index[split:],
    )

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:.8rem 0 .4rem">
    <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">
        🤖 ML Price Predictions
    </div>
    <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">
        Real machine-learning forecasts using sklearn &amp; XGBoost
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

if not run_btn and "ml_result" not in st.session_state:
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:20px;
        padding:2.5rem;text-align:center;margin-top:1rem">
        <div style="font-size:2.5rem;margin-bottom:.8rem">🤖</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#f0f2f8;margin-bottom:.4rem">
            Configure &amp; Run a Prediction
        </div>
        <div style="font-size:.83rem;color:#8892a4">
            Select a symbol, training period, and model in the sidebar, then click <strong style="color:#4f8fff">Run Prediction</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if run_btn:
    with st.spinner(f"Training {model_choice} on {symbol} ({period} data)…"):
        result = fetch_and_train(symbol, period, forecast_days, model_choice)
    if result is None:
        st.error(f"Could not fetch enough data for **{symbol}**. Try a different symbol or longer period.")
        st.stop()
    st.session_state["ml_result"] = result
    st.session_state["ml_symbol"] = symbol
    st.session_state["ml_forecast_days"] = forecast_days

result = st.session_state.get("ml_result")
if result is None:
    st.stop()

sym_label = st.session_state.get("ml_symbol", symbol)
fdays     = st.session_state.get("ml_forecast_days", forecast_days)

# ── Summary metrics row ───────────────────────────────────────────────────────
best_model = max(result["metrics"], key=lambda k: result["metrics"][k]["r2"])
bm = result["metrics"][best_model]
last_close = result["last_close"]
ens_target = result["ensemble_future"][-1]
pred_change = ((ens_target - last_close) / last_close) * 100
signal = "BULLISH" if pred_change > 1 else "BEARISH" if pred_change < -1 else "NEUTRAL"
sig_color = "#22d98a" if signal == "BULLISH" else "#f05252" if signal == "BEARISH" else "#f5a623"
badge_cls  = "pred-up" if signal == "BULLISH" else "pred-down" if signal == "BEARISH" else "pred-neutral"

mc1, mc2, mc3, mc4 = st.columns(4)
for col, title, val, sub in [
    (mc1, "Current Price",        f"${last_close:.2f}",         sym_label),
    (mc2, f"{fdays}d Target",     f"${ens_target:.2f}",         f"{pred_change:+.2f}% forecast"),
    (mc3, f"Best Model R²",       f"{bm['r2']:.3f}",            best_model),
    (mc4, "Direction Accuracy",   f"{bm['direction_acc']:.1f}%", "test set"),
]:
    with col:
        color = sig_color if col == mc2 else "#f0f2f8"
        st.markdown(f"""
        <div class="metric-box">
            <h4>{title}</h4>
            <h2 style="color:{color}">{val}</h2>
            <div style="font-size:.7rem;color:#4e5669;margin-top:.3rem">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown(f"""
<div style="margin:.8rem 0;display:flex;align-items:center;gap:.6rem">
    <span class="pred-badge {badge_cls}">{signal} signal</span>
    <span style="font-size:.75rem;color:#4e5669">Ensemble of {len(result['models'])} model(s): {', '.join(result['models'])}</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Forecast Chart", "📊 Model Performance", "🔍 Feature Importance"])

with tab1:
    hist_df   = result["history"]
    last_date = hist_df.index[-1]
    future_dates = pd.bdate_range(start=last_date + timedelta(days=1), periods=fdays)

    fig = go.Figure()
    # Historical close (last 90 bars for clarity)
    display_hist = hist_df.tail(90)
    fig.add_trace(go.Scatter(
        x=display_hist.index, y=display_hist["Close"],
        name="Actual Close", line=dict(color="#4f8fff", width=1.8),
    ))
    colors_map = {"XGBoost":"#22d98a", "Random Forest":"#f5a623", "Linear Regression":"#7c6ff7"}
    for mname, preds in result["future_preds"].items():
        fig.add_trace(go.Scatter(
            x=[last_date] + list(future_dates), y=[last_close] + preds,
            name=f"{mname} forecast",
            line=dict(color=colors_map.get(mname, "#8892a4"), width=1.6, dash="dot"),
        ))
    if len(result["future_preds"]) > 1:
        ens = result["ensemble_future"]
        fig.add_trace(go.Scatter(
            x=[last_date] + list(future_dates), y=[last_close] + ens,
            name="Ensemble", line=dict(color="#ffffff", width=2.2, dash="solid"),
            fill=None,
        ))
        # confidence band (±5% of ensemble)
        ens_arr = np.array([last_close] + ens)
        fig.add_trace(go.Scatter(
            x=list([last_date] + list(future_dates)) + list(reversed([last_date] + list(future_dates))),
            y=list(ens_arr * 1.05) + list(reversed(list(ens_arr * 0.95))),
            fill="toself", fillcolor="rgba(255,255,255,0.04)",
            line=dict(color="rgba(0,0,0,0)"), name="±5% band", showlegend=True,
        ))
    fig.add_vline(x=str(last_date), line_dash="dot", line_color="rgba(255,255,255,.2)")
    fig.update_layout(
        height=420, title=f"{sym_label} — {fdays}-Day Price Forecast",
        title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Forecast table
    st.markdown(
        "<div style='font-size:.7rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;"
        "color:#4e5669;margin-bottom:.4rem'>Ensemble Forecast Schedule</div>",
        unsafe_allow_html=True,
    )
    fdf = pd.DataFrame({
        "Date":  [d.strftime("%b %d, %Y") for d in future_dates],
        "Predicted Close": [f"${p:.2f}" for p in result["ensemble_future"]],
        "Change vs Today": [f"{((p - last_close)/last_close)*100:+.2f}%" for p in result["ensemble_future"]],
    })
    st.dataframe(fdf, use_container_width=True, hide_index=True)

with tab2:
    # Actual vs predicted on test set
    test_dates = result["test_dates"]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=test_dates, y=result["y_test"], name="Actual",
        line=dict(color="#4f8fff", width=1.8),
    ))
    for mname, preds in result["preds_test"].items():
        fig2.add_trace(go.Scatter(
            x=test_dates, y=preds, name=f"{mname} pred",
            line=dict(color=colors_map.get(mname, "#8892a4"), width=1.4, dash="dot"),
        ))
    fig2.update_layout(
        height=360, title="Test Set: Actual vs Predicted",
        title_font=dict(family="Syne", size=13, color="#f0f2f8"), **DARK_LAYOUT,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Metrics table
    st.markdown(
        "<div style='font-size:.7rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;"
        "color:#4e5669;margin:.6rem 0 .3rem'>Model Comparison</div>",
        unsafe_allow_html=True,
    )
    rows = []
    for mname, m in result["metrics"].items():
        rows.append({
            "Model": mname,
            "MAE ($)": f"{m['mae']:.2f}",
            "MAPE (%)": f"{m['mape']:.2f}%",
            "R²": f"{m['r2']:.4f}",
            "Direction Acc.": f"{m['direction_acc']:.1f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with tab3:
    fi = result.get("feat_imp")
    if fi is not None:
        fig3 = go.Figure(go.Bar(
            x=fi.values[::-1], y=fi.index[::-1], orientation="h",
            marker_color="#4f8fff", opacity=0.85,
        ))
        fig3.update_layout(
            height=380, title="Top Feature Importances",
            title_font=dict(family="Syne", size=13, color="#f0f2f8"),
            xaxis_title="Importance Score", **DARK_LAYOUT,
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Feature importance is available for tree-based models (XGBoost, Random Forest).")

st.markdown("""
<div style="text-align:center;padding:1rem 0 .3rem;font-size:.72rem;color:#4e5669">
    Predictions are for educational purposes only · Not financial advice
</div>
""", unsafe_allow_html=True)
