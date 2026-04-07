"""
utils/styling.py — Single CSS source of truth.
Call apply_css() at the top of every page file.

SIDEBAR FIX
-----------
The toggle button ([data-testid="collapsedControl"]) is fixed-positioned so
it stays visible at all times — including fullscreen / presentation mode.
It is intentionally NOT attached to any scroll container so it floats above
the content and is always reachable.

EMOJI REMOVED from all nav / UI elements as requested.
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* TOKENS */
:root {
    --bg-base:#0d0f14; --bg-card:#13161e; --bg-elevated:#1c2030;
    --border:rgba(255,255,255,.07); --border-active:rgba(255,255,255,.18);
    --accent-blue:#4f8fff; --accent-violet:#7c6ff7;
    --accent-green:#22d98a; --accent-red:#f05252; --accent-amber:#f5a623;
    --text-primary:#f0f2f8; --text-secondary:#8892a4; --text-muted:#4e5669;
    --radius-sm:8px; --radius-md:14px; --radius-lg:20px;
}

/* HIDE ONLY CLUTTER — keep the header bar so the toggle works */
footer                          { visibility:hidden!important; height:0!important; }
[data-testid="stDeployButton"]  { display:none!important; }
[data-testid="stDecoration"]    { display:none!important; }
[data-testid="stStatusWidget"]  { display:none!important; }

/* SIDEBAR TOGGLE — fixed so it stays on screen in fullscreen / presentation mode */
[data-testid="collapsedControl"] {
    display:flex         !important;
    visibility:visible   !important;
    opacity:1            !important;
    pointer-events:auto  !important;
    position:fixed       !important;   /* float above all content */
    top:3.5rem           !important;
    left:0.4rem          !important;
    z-index:999999       !important;   /* above Streamlit's own overlays */
    background:var(--bg-card)         !important;
    border:1px solid var(--border-active) !important;
    border-radius:var(--radius-sm)    !important;
    padding:6px 9px      !important;
    box-shadow:0 4px 16px rgba(0,0,0,.5) !important;
    transition:background .15s, border-color .15s !important;
}
[data-testid="collapsedControl"]:hover {
    background:var(--accent-blue)   !important;
    border-color:var(--accent-blue) !important;
}
[data-testid="collapsedControl"] svg       { color:var(--text-secondary)!important; fill:var(--text-secondary)!important; }
[data-testid="collapsedControl"]:hover svg { color:white!important; fill:white!important; }

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background:var(--bg-card)!important;
    border-right:1px solid var(--border)!important;
    min-width:260px!important;
}
section[data-testid="stSidebar"] > div:first-child { padding-top:1rem!important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] small { color:var(--text-secondary)!important; }

/* BASE */
html,body,[class*="css"] { font-family:'DM Sans',sans-serif!important; color:var(--text-primary)!important; }
.stApp { background:var(--bg-base)!important; }
h1,h2,h3 { font-family:'Syne',sans-serif!important; color:var(--text-primary)!important; }
.stMarkdown p { color:var(--text-secondary); font-size:.84rem; }

/* CARDS */
.fin-card,.glass-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1.2rem 1.4rem;
    transition:border-color .2s,transform .2s;
}
.fin-card:hover,.glass-card:hover { border-color:var(--border-active); transform:translateY(-2px); }
.glass-card h4 {
    font-family:'Syne',sans-serif; font-size:.72rem; font-weight:600;
    letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin-bottom:.6rem;
}
.glass-card table td { padding:.28rem .4rem; font-size:.82rem; color:var(--text-secondary); }
.glass-card table td:last-child { color:var(--text-primary); }

.stat-card {
    background:var(--bg-card); border:1px solid var(--border);
    border-radius:var(--radius-lg); padding:1.2rem 1.4rem;
    position:relative; overflow:hidden; transition:border-color .2s,transform .2s;
}
.stat-card::before {
    content:''; position:absolute; top:0; left:0; right:0; height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet)); opacity:.7;
}
.stat-card:hover { border-color:var(--border-active); transform:translateY(-2px); }
.stat-label { font-size:.7rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin-bottom:.4rem; }
.stat-value { font-family:'Syne',sans-serif!important; font-size:1.8rem; font-weight:700; color:var(--text-primary); line-height:1.1; }

.metric-box { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius-md); padding:1rem; text-align:center; }
.metric-box h4 { font-size:.68rem; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text-secondary); margin:0 0 .4rem; }
.metric-box h2 { font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:700; color:var(--text-primary); margin:0; }

/* BADGES */
.stat-badge { display:inline-flex; align-items:center; gap:4px; font-size:.7rem; font-weight:600; padding:3px 8px; border-radius:20px; margin-top:.4rem; }
.badge-up   { background:rgba(34,217,138,.12); color:var(--accent-green); }
.badge-down { background:rgba(240,82,82,.12);  color:var(--accent-red);   }
.badge-info { background:rgba(79,143,255,.12); color:var(--accent-blue);  }

/* TICKER */
.ticker-card { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); text-align:center; padding:.9rem; transition:all .2s; }
.ticker-card:hover { border-color:var(--accent-blue); transform:translateY(-3px); box-shadow:0 8px 24px rgba(79,143,255,.12); }
.ticker-sym   { font-size:.68rem; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:var(--text-secondary); }
.ticker-price { font-family:'Syne',sans-serif; font-size:1.2rem; font-weight:700; color:var(--text-primary); margin:.25rem 0; }
.ticker-chg   { font-size:.75rem; font-weight:600; }
.up { color:var(--accent-green); } .down { color:var(--accent-red); }

/* NAV */
.nav-group { font-size:.62rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--text-muted)!important; padding:.5rem .4rem .2rem; }
.nav-item  { display:flex; align-items:center; gap:9px; padding:.5rem .8rem; border-radius:var(--radius-sm); font-size:.83rem; font-weight:500; color:var(--text-secondary)!important; cursor:pointer; transition:background .15s; margin:2px 0; }
.nav-item:hover  { background:rgba(255,255,255,.05); }
.nav-item.active { background:rgba(79,143,255,.15); color:var(--accent-blue)!important; font-weight:600; }

/* LIVE DOT */
.live-dot { display:inline-flex; align-items:center; gap:6px; font-size:.7rem; font-weight:600; color:var(--accent-green); }
.live-dot::before { content:''; width:7px; height:7px; background:var(--accent-green); border-radius:50%; animation:pdot 2s infinite; }
@keyframes pdot { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(1.3);} }

/* INPUTS */
.stSelectbox>div>div,
.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stDateInput>div>div>input,
.stMultiSelect>div>div {
    background:var(--bg-elevated)!important; border:1px solid var(--border)!important;
    border-radius:var(--radius-sm)!important; color:var(--text-primary)!important; font-size:.84rem!important;
}

/* BUTTONS */
.stButton>button {
    background:var(--bg-elevated)!important; border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important; border-radius:var(--radius-sm)!important;
    font-size:.8rem!important; font-weight:500!important; transition:all .15s!important;
}
.stButton>button:hover { background:var(--accent-blue)!important; border-color:var(--accent-blue)!important; color:white!important; }
.stButton>button[kind="primary"] { background:var(--accent-blue)!important; border-color:var(--accent-blue)!important; color:white!important; }
.stDownloadButton>button {
    background:var(--accent-green)!important; border-color:var(--accent-green)!important;
    color:#0d0f14!important; font-weight:600!important; border-radius:var(--radius-sm)!important;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] { background:var(--bg-card)!important; border-radius:var(--radius-md)!important; gap:4px; padding:4px; border:1px solid var(--border)!important; }
.stTabs [data-baseweb="tab"] { background:transparent!important; color:var(--text-secondary)!important; border-radius:var(--radius-sm)!important; font-size:.8rem!important; font-weight:500!important; padding:6px 14px!important; }
.stTabs [aria-selected="true"] { background:var(--bg-elevated)!important; color:var(--text-primary)!important; font-weight:600!important; }

/* METRIC WIDGET */
div[data-testid="stMetric"] { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); padding:.8rem 1rem; }
div[data-testid="stMetric"] label { color:var(--text-secondary)!important; font-size:.7rem!important; letter-spacing:.06em; text-transform:uppercase; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:var(--text-primary)!important; font-size:1.4rem!important; }

/* MISC */
[data-testid="stDataFrameContainer"] { border:1px solid var(--border)!important; border-radius:var(--radius-md)!important; }
.insight-text { background:rgba(245,166,35,.07); border-left:3px solid var(--accent-amber); border-radius:0 var(--radius-sm) var(--radius-sm) 0; padding:.8rem 1rem; font-size:.82rem; color:var(--text-secondary); }
.holding-row { background:var(--bg-card); border:1px solid var(--border); border-radius:var(--radius-md); padding:.75rem 1rem; margin-bottom:.4rem; transition:border-color .2s; }
.holding-row:hover { border-color:var(--border-active); }
.alloc-bar  { height:5px; background:rgba(255,255,255,.06); border-radius:10px; overflow:hidden; margin:.3rem 0; }
.alloc-fill { height:100%; background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet)); border-radius:10px; }
.heat-cell  { border-radius:var(--radius-sm); padding:.5rem .3rem; text-align:center; font-size:.72rem; font-weight:600; transition:transform .15s; }
.heat-cell:hover { transform:scale(1.06); }

::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:var(--bg-base); }
::-webkit-scrollbar-thumb { background:rgba(255,255,255,.1); border-radius:10px; }
</style>
"""

def apply_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

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
