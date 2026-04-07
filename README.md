# 📈 StockFin — Stock Market Intelligence & Prediction System

A multi-page Streamlit dashboard for live stock data, technical analysis,
portfolio tracking, and AI compliance monitoring.

---

## 🗂 Project Structure

```
stockfin/
├── app.py                        ← Main entry point (run this)
├── requirements.txt
├── .env                          ← API keys (never commit)
├── .gitignore
│
├── .streamlit/
│   └── config.toml               ← Dark theme + server settings
│
├── pages/                        ← Streamlit multi-page routing
│   ├── 1_Analytics.py            ← Advanced technical analysis
│   ├── 2_Portfolio.py            ← Portfolio tracker
│   └── 3_Compliance.py           ← AI compliance dashboard
│
├── utils/                        ← Shared utilities
│   ├── __init__.py
│   ├── stock_data.py             ← yfinance data fetcher + PortfolioManager
│   ├── indicators.py             ← TechnicalIndicators class
│   └── styling.py                ← DashboardStyling + ColorPalette
│
└── data/
    └── portfolio_data.json       ← Persisted portfolio holdings
```

---

## 🚀 Quick Start

### 1. Clone & create virtual environment
```bash
git clone https://github.com/your-username/stockfin.git
cd stockfin
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env — yfinance needs no key; fill others as desired
```

### 4. Run the app
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 📄 Pages

| Page | File | Description |
|------|------|-------------|
| 🏠 Live Dashboard | `app.py` | Real-time ticker grid, candlestick chart, alerts |
| 📊 Analytics | `pages/1_Analytics.py` | RSI, MACD, Stochastic, Fibonacci, AI signals |
| 💼 Portfolio | `pages/2_Portfolio.py` | Holdings tracker, P&L, allocation charts |
| 🛡️ Compliance | `pages/3_Compliance.py` | AI workflow risk monitoring |

---

## ⚠️ Common Issues & Fixes

| Problem | Fix applied |
|---------|-------------|
| `st.set_page_config()` called in page files | Removed from all `pages/*.py` — only lives in `app.py` |
| `yfinance==0.2.33` breaks with pandas ≥ 2 | Upgraded to `yfinance>=0.2.40` |
| `stat-badge` CSS class missing in Compliance | Added `.stat-badge`, `.badge-up/down/info` to CSS |
| Variable `l` shadowed Python built-in | Renamed to `loss_` in Analytics |
| RSI/Stochastic division-by-zero | Added `.replace(0, np.nan)` guards |
| `get_multiple_stocks` unhashable list arg | Converted to `tuple` before cache call |

---

## 🔑 Environment Variables (`.env`)

```env
# yfinance — no key needed
ALPHA_VANTAGE_API_KEY=your_key_here   # optional
POLYGON_API_KEY=your_key_here         # optional
DATABASE_URL=sqlite:///stock_dashboard.db
PORTFOLIO_FILE=data/portfolio_data.json
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit ≥1.32` | Web UI framework |
| `yfinance ≥0.2.40` | Market data |
| `pandas ≥2.1` | Data manipulation |
| `plotly ≥5.18` | Interactive charts |
| `scikit-learn` | ML signals |

---

> **Disclaimer:** For educational purposes only. Not financial advice.
