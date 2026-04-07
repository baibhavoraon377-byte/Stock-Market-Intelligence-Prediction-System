"""
utils/styling.py — Single source of truth for dark-premium CSS.
Import and call apply_css() at the top of every page (after set_page_config in app.py).
"""
import streamlit as st


# ── Shared dark-theme CSS ──────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-base:       #0d0f14;
    --bg-card:       #13161e;
    --bg-elevated:   #1c2030;
    --border:        rgba(255,255,255,.07);
    --border-active: rgba(255,255,255,.14);
    --accent-blue:   #4f8fff;
    --accent-violet: #7c6ff7;
    --accent-green:  #22d98a;
    --accent-red:    #f05252;
    --accent-amber:  #f5a623;
    --text-primary:  #f0f2f8;
    --text-secondary:#8892a4;
    --text-muted:    #4e5669;
    --radius-sm:8px; --radius-md:14px; --radius-lg:20px;
}

/* ── Base ── */
html,body,[class*="css"]{ font-family:'DM Sans',sans-serif!important; color:var(--text-primary)!important; }
.stApp{ background:var(--bg-base)!important; }

/* ── Sidebar ── */
section[data-testid="stSidebar"]{ background:var(--bg-card)!important; border-right:1px solid var(--border)!important; }
section[data-testid="stSidebar"] *{ color:var(--text-secondary)!important; }
section[data-testid="stSidebar"] label{ color:var(--text-secondary)!important; font-size:.85rem!important; }

/* ── SIDEBAR TOGGLE FIX ──
   Hide only the Streamlit footer/deploy bar.
   Do NOT hide #MainMenu or header — that removes the sidebar toggle button.
   Instead we surgically hide just the deploy button and the "Made with Streamlit" footer.
*/
footer{ visibility:hidden!important; }
[data-testid="stToolbar"]{ display:none!important; }
[data-testid="stDecoration"]{ display:none!important; }
[data-testid="stStatusWidget"]{ display:none!important; }

/* Keep sidebar collapse arrow button always visible and on top */
[data-testid="collapsedControl"],
button[kind="headerNoPadding"],
.st-emotion-cache-zq5wmm,
[data-testid="baseButton-headerNoPadding"]{
    visibility:visible!important;
    display:flex!important;
    z-index:999!important;
    opacity:1!important;
}

/* ── Typography ── */
h1,h2,h3{ font-family:'Syne',sans-serif!important; color:var(--text-primary)!important; }
.stMarkdown p{ color:var(--text-secondary); font-size:.84rem; }

/* ── Cards ── */
.fin-card,.glass-card{
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1.2rem 1.4rem;
    transition:border-color .2s,transform .2s;
}
.fin-card:hover,.glass-card:hover{ border-color:var(--border-active); transform:translateY(-2px); }
.glass-card h4{
    font-family:'Syne',sans-serif; font-size:.72rem; font-weight:600;
    letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin-bottom:.6rem;
}
.glass-card table td{ padding:.28rem .4rem; font-size:.82rem; color:var(--text-secondary); }
.glass-card table td:last-child{ color:var(--text-primary); }

/* Stat card with top gradient line */
.stat-card{
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1.2rem 1.4rem;
    position:relative; overflow:hidden; transition:border-color .2s,transform .2s;
}
.stat-card::before{
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet)); opacity:.7;
}
.stat-card:hover{ border-color:var(--border-active); transform:translateY(-2px); }
.stat-label{ font-size:.7rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin-bottom:.4rem; }
.stat-value{ font-family:'Syne',sans-serif!important; font-size:1.8rem; font-weight:700; color:var(--text-primary); line-height:1.1; }

/* Badges */
.stat-badge{ display:inline-flex; align-items:center; gap:4px; font-size:.7rem; font-weight:600; padding:3px 8px; border-radius:20px; margin-top:.4rem; }
.badge-up{ background:rgba(34,217,138,.12); color:var(--accent-green); }
.badge-down{ background:rgba(240,82,82,.12); color:var(--accent-red); }
.badge-info{ background:rgba(79,143,255,.12); color:var(--accent-blue); }

/* Ticker mini card */
.ticker-card{ background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); text-align:center; padding:.9rem; transition:all .2s; }
.ticker-card:hover{ border-color:var(--accent-blue); transform:translateY(-3px); box-shadow:0 8px 24px rgba(79,143,255,.12); }
.ticker-sym{ font-size:.68rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:var(--text-secondary); }
.ticker-price{ font-family:'Syne',sans-serif; font-size:1.2rem; font-weight:700; color:var(--text-primary); margin:.25rem 0; }
.ticker-chg{ font-size:.75rem; font-weight:600; }
.up{ color:var(--accent-green); } .down{ color:var(--accent-red); }

/* Metric card (analytics) */
.metric-box{
    background:var(--bg-elevated); border:1px solid var(--border);
    border-radius:var(--radius-md); padding:1rem; text-align:center;
}
.metric-box h4{ font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin:0 0 .4rem; }
.metric-box h2{ font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:700; color:var(--text-primary); margin:0; }

/* Insight callout */
.insight-text{
    background:rgba(245,166,35,.07); border-left:3px solid var(--accent-amber);
    border-radius:0 var(--radius-sm) var(--radius-sm) 0;
    padding:.8rem 1rem; font-size:.82rem; color:var(--text-secondary);
}

/* Holding rows (portfolio) */
.holding-row{
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-md); padding:.75rem 1rem;
    margin-bottom:.4rem; transition:border-color .2s;
}
.holding-row:hover{ border-color:var(--border-active); }

/* Allocation bar */
.alloc-bar{ height:5px; background:rgba(255,255,255,.06); border-radius:10px; overflow:hidden; margin:.3rem 0; }
.alloc-fill{ height:100%; background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet)); border-radius:10px; }

/* Sidebar live dot */
.live-dot{ display:inline-flex; align-items:center; gap:6px; font-size:.7rem; font-weight:600; color:var(--accent-green); }
.live-dot::before{ content:''; width:7px; height:7px; background:var(--accent-green); border-radius:50%; animation:pdot 2s infinite; }
@keyframes pdot{ 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(1.3);} }

/* Nav items */
.nav-group{ font-size:.62rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--text-muted)!important; padding:.5rem .4rem .2rem; }
.nav-item{ display:flex; align-items:center; gap:9px; padding:.5rem .8rem; border-radius:var(--radius-sm); font-size:.83rem; font-weight:500; color:var(--text-secondary)!important; cursor:pointer; transition:background .15s; margin:2px 0; }
.nav-item:hover{ background:rgba(255,255,255,.05); }
.nav-item.active{ background:rgba(79,143,255,.15); color:var(--accent-blue)!important; font-weight:600; }

/* Form inputs */
.stSelectbox>div>div,
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input{
    background:var(--bg-elevated)!important; border:1px solid var(--border)!important;
    border-radius:var(--radius-sm)!important; color:var(--text-primary)!important; font-size:.84rem!important;
}

/* Buttons */
.stButton>button{
    background:var(--bg-elevated)!important; border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important; border-radius:var(--radius-sm)!important;
    font-size:.8rem!important; font-weight:500!important; transition:all .15s!important;
}
.stButton>button:hover{ background:var(--accent-blue)!important; border-color:var(--accent-blue)!important; color:white!important; }
.stButton>button[kind="primary"]{ background:var(--accent-blue)!important; border-color:var(--accent-blue)!important; color:white!important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"]{ background:var(--bg-card)!important; border-radius:var(--radius-md)!important; gap:4px; padding:4px; border:1px solid var(--border)!important; }
.stTabs [data-baseweb="tab"]{ background:transparent!important; color:var(--text-secondary)!important; border-radius:var(--radius-sm)!important; font-size:.8rem!important; font-weight:500!important; padding:6px 14px!important; }
.stTabs [aria-selected="true"]{ background:var(--bg-elevated)!important; color:var(--text-primary)!important; font-weight:600!important; }

/* Metric widget */
div[data-testid="stMetric"]{ background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); padding:.8rem 1rem; }
div[data-testid="stMetric"] label{ color:var(--text-secondary)!important; font-size:.7rem!important; letter-spacing:.06em; text-transform:uppercase; }
div[data-testid="stMetric"] [data-testid="stMetricValue"]{ font-family:'Syne',sans-serif!important; color:var(--text-primary)!important; font-size:1.4rem!important; }

/* Dataframe */
[data-testid="stDataFrameContainer"]{ border:1px solid var(--border)!important; border-radius:var(--radius-md)!important; }

/* Scrollbar */
::-webkit-scrollbar{ width:5px; height:5px; }
::-webkit-scrollbar-track{ background:var(--bg-base); }
::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.1); border-radius:10px; }
</style>
"""


def apply_css() -> None:
    """Inject shared dark-premium CSS into the current page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ── Shared Plotly dark layout ──────────────────────────────────────────────────
DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(28,32,48,0.5)",
    font=dict(family="DM Sans", color="#8892a4", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4", size=10)),
    margin=dict(l=8, r=8, t=36, b=8),
)
