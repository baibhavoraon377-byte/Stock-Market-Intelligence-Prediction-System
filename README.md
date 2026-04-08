# StockFin — Live Market Dashboard

> A premium, dark-themed stock analytics platform built with **Streamlit**, **yfinance**, and **scikit-learn / XGBoost**. Real-time quotes, technical analysis, ML price forecasting, portfolio tracking, backtesting, and price alerts — all in one place.

---

## Table of Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Page-by-Page Guide](#page-by-page-guide)
- [Tech Stack](#tech-stack)
- [Configuration](#configuration)
- [Known Issues & Fixes Applied](#known-issues--fixes-applied)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

---

## Screenshots

| Dashboard | Analytics | ML Predictions |
|-----------|-----------|----------------|
| Live ticker grid, candlestick chart, Volume + RSI subplots | Technical indicators, risk metrics, correlation matrix | XGBoost / Random Forest forecast with confidence band |

---

## Features

| Feature | Details |
|---------|---------|
| **Live Quotes** | Real-time price, change %, volume via yfinance (1-min intraday + 1-month history) |
| **Candlestick Charts** | Compact 3-panel layout: Price + MAs, Volume, RSI — reduced vertical gaps |
| **Company Name Dropdowns** | Every page shows full company names (e.g. *Apple (AAPL)*) instead of raw tickers |
| **Technical Analysis** | SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic, ATR, OBV, Ichimoku |
| **AI Trading Signals** | Composite BUY / SELL / NEUTRAL signal from 4 indicators with confidence scores |
| **Risk Metrics** | Annual return, volatility, Sharpe, Sortino, max drawdown, VaR (95%) |
| **Correlation Matrix** | Heatmap of returns correlation between selected stocks |
| **Fibonacci Levels** | Auto-computed retracement levels plotted on price chart |
| **ML Forecasting** | XGBoost, Random Forest, Ridge Regression — 5–30 day forward forecast |
| **Portfolio Tracker** | Add holdings, track real-time P&L, allocation pie chart, risk analysis |
| **Backtesting Engine** | 5 strategies: SMA Crossover, RSI Mean Reversion, BB Breakout, MACD, Momentum |
| **Watchlist & Alerts** | Live watchlist with sparklines; session-based price / RSI / change% alerts |
| **34+ Stocks Pre-loaded** | US large-cap, ETFs, crypto, Indian ADRs |

---

## Project Structure

```
stockfin/
├── app.py                      # Entry point — Dashboard page
├── pages/
│   ├── 1_Analytics.py          # Advanced technical & risk analytics
│   ├── 2_Portfolio.py          # Portfolio tracker & P&L
│   ├── 3_ML_Predictions.py     # Machine-learning price forecasting
│   ├── 4_Watchlist.py          # Live watchlist + price alerts
│   └── 5_Backtesting.py        # Strategy backtesting engine
├── utils/
│   ├── __init__.py
│   ├── stock_data.py           # StockDataFetcher, PortfolioManager
│   ├── indicators.py           # TechnicalIndicators class
│   ├── styling.py              # DashboardStyling, ColorPalette
│   └── stock_constants.py      # Shared STOCK_CATALOGUE + helper widgets
├── data/
│   └── portfolio_data.json     # Persisted portfolio holdings
└── requirements.txt
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/stockfin.git
cd stockfin
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** XGBoost is optional but recommended for ML Predictions. If it is not available, the app falls back to Random Forest automatically.

### 4. Run the app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Page-by-Page Guide

### Dashboard (`app.py`)

The home page. Select up to 12 stocks via checkboxes **or** type any custom symbol (supports international tickers like `INFY.NS`, `BTC-USD`).

- **Market Overview** — ticker card grid showing price and daily change
- **Detailed Analysis** — pick a stock from the company-name dropdown:
  - *Price Chart* — compact candlestick + Volume + RSI (reduced subplot spacing)
  - *Indicators* — key stats table + price vs MA chart
  - *Company Info* — sector, P/E, 52W range, dividend yield, beta
  - *Alerts* — RSI overbought/oversold, volume spikes, large daily moves
- **Portfolio Summary** — estimated return on a configurable initial investment

### Analytics (`pages/1_Analytics.py`)

Deep-dive into a single stock over a chosen period.

- Choose any stock from the **company-name selectbox** or type a custom symbol
- **Technical tab** — 5-panel chart: Price/MAs, RSI, Stochastic, MACD, OBV
- **Risk tab** — 6 risk metrics + 20-day rolling volatility chart
- **Correlation tab** — heatmap vs comparison stocks (also via company names)
- **Price Levels tab** — Fibonacci retracement + support/resistance (20-day range)
- **AI Signals tab** — composite signal with per-indicator breakdown

### Portfolio (`pages/2_Portfolio.py`)

Track your personal holdings.

- Add holdings via the **company-name dropdown** or manual text input
- View real-time P&L, allocation percentages, and 30-day simulated performance curve
- Risk summary: diversification score, concentration risk, portfolio beta

### ML Predictions (`pages/3_ML_Predictions.py`)

Real machine-learning forecasts.

- Select stock from the **company-name selectbox**
- Choose model: XGBoost, Random Forest, Linear Regression, or All (Ensemble)
- Configure training period (6 months – 5 years) and forecast horizon (5–30 days)
- Output: forecast chart with ±5% confidence band, model comparison table, feature importances

### Watchlist & Alerts (`pages/4_Watchlist.py`)

Monitor multiple stocks simultaneously.

- Add symbols from the **company-name dropdown** or free-text input
- **Watchlist tab** — live price, change, sparkline, volume, market cap, RSI badge for each symbol
- **Alerts tab** — set threshold conditions: `Price >=`, `Price <=`, `Change% >=`, `RSI >=`, etc.
- Alerts are checked live; triggered alerts are highlighted in red

> **Bug fixed in this version:** `fetch_quote()` was previously defined *after* the sidebar code that called it, causing a `NameError` at runtime. The function is now defined before all call sites.

### Backtesting (`pages/5_Backtesting.py`)

Simulate trading strategies on historical data.

- Select stock from the **company-name selectbox**
- Available strategies:
  - **SMA Crossover (20/50)** — golden / death cross signals
  - **RSI Mean Reversion** — buy oversold (<30), sell overbought (>70)
  - **Bollinger Band Breakout** — trade price-band touches
  - **MACD Signal** — trade MACD/signal-line crossovers
  - **Momentum (ROC)** — trade based on 20-day rate of change
- Output: equity curve vs buy-and-hold, drawdown bar chart, trade log, P&L distribution

---

## Tech Stack

| Library | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥ 1.32 | UI framework |
| `yfinance` | ≥ 0.2.40 | Market data |
| `pandas` | ≥ 2.1 | Data manipulation |
| `numpy` | ≥ 1.26 | Numerical computing |
| `plotly` | ≥ 5.18 | Interactive charts |
| `scikit-learn` | ≥ 1.3.2 | ML models |
| `xgboost` | ≥ 2.0.3 | Gradient boosting |
| `sqlalchemy` | ≥ 2.0 | Database (future) |

---

## Configuration

| Setting | Where | Default |
|---------|-------|---------|
| Cache TTL (live price) | `app.py` → `@st.cache_data(ttl=60)` | 60 s |
| Cache TTL (history) | `@st.cache_data(ttl=300)` | 300 s |
| Rate-limit delay | `get_multiple_stocks()` | 0.35 s |
| Portfolio file path | `pages/2_Portfolio.py` | `data/portfolio_data.json` |
| Default watchlist | `pages/4_Watchlist.py` session state | AAPL, TSLA, NVDA, MSFT, AMZN |

---

## Known Issues & Fixes Applied

| Issue | Status |
|-------|--------|
| `fetch_quote` NameError in Watchlist — function defined after its call site | **Fixed** — moved above sidebar |
| `ZeroDivisionError` in RSI when all prices flat | **Fixed** — `loss.replace(0, np.nan)` |
| Fibonacci variables overwritten before use in Analytics | **Fixed** — computed once at the end |
| Stochastic `/ 0` when high == low | **Fixed** — `denom.replace(0, np.nan)` |
| Sparkline `fillcolor` crash for non-rgb color strings | **Fixed** — simple hex + `20` alpha suffix |
| Large vertical gaps between Price / Volume / RSI subplots | **Fixed** — `vertical_spacing=0.06`, `height=680` |
| All pages used emoji icons instead of text labels | **Fixed** — replaced throughout |
| Stock selection was raw ticker text inputs only | **Fixed** — company-name selectboxes on every page |

---

## Roadmap

- [ ] Persistent alert notifications (email / Telegram)
- [ ] Multi-currency support (INR, EUR, GBP)
- [ ] Options chain visualiser
- [ ] News sentiment analysis via NewsAPI
- [ ] Database-backed portfolio (replace JSON)
- [ ] User authentication (Streamlit-Authenticator)
- [ ] Docker deployment guide

---

## Disclaimer

> This application is built **for educational and research purposes only**. It does not constitute financial advice. Always do your own research before making investment decisions. Past performance does not guarantee future results.

---

*Data provided by Yahoo Finance · Built with Streamlit*
