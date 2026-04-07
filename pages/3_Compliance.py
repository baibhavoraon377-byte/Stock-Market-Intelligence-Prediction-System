import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random


# ── Dark premium CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{
    --bg-base:#0d0f14;--bg-card:#13161e;--bg-elevated:#1c2030;
    --border:rgba(255,255,255,.07);--border-active:rgba(255,255,255,.14);
    --accent-blue:#4f8fff;--accent-violet:#7c6ff7;--accent-green:#22d98a;
    --accent-red:#f05252;--accent-amber:#f5a623;
    --text-primary:#f0f2f8;--text-secondary:#8892a4;--text-muted:#4e5669;
    --radius-sm:8px;--radius-md:14px;--radius-lg:20px;
}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;color:var(--text-primary)!important;}
.stApp{background:var(--bg-base)!important;}
section[data-testid="stSidebar"]{background:var(--bg-card)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] *{color:var(--text-secondary)!important;}
#MainMenu,footer,header{visibility:hidden;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--text-primary)!important;}
.stMarkdown p{color:var(--text-secondary);font-size:.84rem;}
/* compliance stat cards */
.compliance-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
    padding:1.3rem 1.5rem;margin-bottom:.8rem;position:relative;overflow:hidden;transition:border-color .2s;}
.compliance-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet));opacity:.6;}
.compliance-card:hover{border-color:var(--border-active);}
.stat-number{font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:700;color:var(--text-primary);
    line-height:1;margin:.35rem 0;}
.stat-label-sm{font-size:.68rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:var(--text-secondary);}
.stat-sublabel{font-size:.75rem;color:var(--text-muted);margin-top:.2rem;}
/* risk badges */
.risk-badge{padding:3px 10px;border-radius:20px;font-size:.68rem;font-weight:600;display:inline-block;}
.risk-low{background:rgba(34,217,138,.12);color:#22d98a;}
.risk-medium{background:rgba(245,166,35,.15);color:#f5a623;}
.risk-high{background:rgba(240,82,82,.12);color:#f05252;}
/* nav */
.nav-group{font-size:.62rem;font-weight:600;letter-spacing:.12em;text-transform:uppercase;
    color:var(--text-muted)!important;padding:.5rem .4rem .2rem;}
.nav-item{display:flex;align-items:center;gap:9px;padding:.5rem .8rem;border-radius:var(--radius-sm);
    font-size:.83rem;font-weight:500;color:var(--text-secondary)!important;cursor:pointer;
    transition:background .15s;margin:2px 0;justify-content:space-between;}
.nav-item:hover{background:rgba(255,255,255,.05);}
.nav-item.active{background:rgba(79,143,255,.15);color:var(--accent-blue)!important;font-weight:600;}
.nav-badge{background:var(--accent-red);color:white;font-size:.62rem;font-weight:700;
    padding:2px 7px;border-radius:20px;}
.live-dot{display:inline-flex;align-items:center;gap:6px;font-size:.7rem;font-weight:600;color:var(--accent-green);}
.live-dot::before{content:'';width:7px;height:7px;background:var(--accent-green);border-radius:50%;
    animation:pdot 2s infinite;}
@keyframes pdot{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.4;transform:scale(1.3);}}
/* prompt rows */
.prompt-item{background:var(--bg-elevated);border:1px solid var(--border);border-left:3px solid;
    padding:.85rem 1rem;margin-bottom:.45rem;border-radius:0 var(--radius-md) var(--radius-md) 0;
    transition:border-color .15s;}
.prompt-item:hover{border-right-color:var(--border-active);border-top-color:var(--border-active);border-bottom-color:var(--border-active);}
/* violation tags */
.v-tag{display:inline-flex;align-items:center;gap:3px;font-size:.65rem;font-weight:600;
    padding:3px 8px;border-radius:6px;}
.v-pii{background:rgba(240,82,82,.15);color:#f87171;}
.v-leak{background:rgba(245,166,35,.15);color:#fbbf24;}
.v-jail{background:rgba(124,111,247,.2);color:#a78bfa;}
.v-sens{background:rgba(79,143,255,.15);color:#60a5fa;}
/* user row */
.user-row{background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);
    padding:.7rem .9rem;margin-bottom:.4rem;}
/* review button */
.review-btn{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;padding:3px 14px!important;border-radius:var(--radius-sm)!important;
    font-size:.75rem!important;}
/* table header */
.tbl-hdr{font-size:.65rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
    color:var(--text-muted);padding:.5rem 0;border-bottom:1px solid var(--border);margin-bottom:.3rem;}
/* buttons */
.stButton>button{background:var(--bg-elevated)!important;border:1px solid var(--border-active)!important;
    color:var(--text-secondary)!important;border-radius:var(--radius-sm)!important;
    font-size:.8rem!important;transition:all .15s!important;}
.stButton>button:hover{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stButton>button[kind="primary"]{background:var(--accent-blue)!important;border-color:var(--accent-blue)!important;color:white!important;}
.stSelectbox>div>div,.stTextInput>div>div>input{background:var(--bg-elevated)!important;
    border:1px solid var(--border)!important;border-radius:var(--radius-sm)!important;color:var(--text-primary)!important;}
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg-base);}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:10px;}
/* stat-badge classes — used in stat cards */
.stat-badge{display:inline-flex;align-items:center;gap:4px;font-size:.68rem;font-weight:600;
    padding:3px 8px;border-radius:20px;}
.badge-up{background:rgba(34,217,138,.12);color:#22d98a;}
.badge-down{background:rgba(240,82,82,.12);color:#f05252;}
.badge-info{background:rgba(79,143,255,.12);color:#4f8fff;}
</style>
""", unsafe_allow_html=True)

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(28,32,48,0.5)",
    font=dict(family="DM Sans", color="#8892a4", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8892a4", size=10)),
    margin=dict(l=8, r=8, t=36, b=8),
)

# ── Sample data ───────────────────────────────────────────────────────────────
users = [
    {"name":"Mike Chen",   "dept":"Engineering", "avatar":"MC", "interactions":245, "flags":12},
    {"name":"Sarah Jones", "dept":"Marketing",   "avatar":"SJ", "interactions":189, "flags":3},
    {"name":"John Smith",  "dept":"Sales",       "avatar":"JS", "interactions":320, "flags":8},
    {"name":"Emily Brown", "dept":"HR",          "avatar":"EB", "interactions":95,  "flags":1},
    {"name":"David Lee",   "dept":"Legal",       "avatar":"DL", "interactions":67,  "flags":0},
]
dept_risks = {
    "Eng":   {"low":45,"medium":12,"high":8},
    "Sales": {"low":120,"medium":5,"high":0},
    "Mktg":  {"low":85,"medium":3,"high":1},
    "HR":    {"low":12,"medium":8,"high":2},
    "Legal": {"low":8,"medium":2,"high":0},
}
recent_prompts = [
    {"user":"Mike Chen",   "dept":"Engineering","avatar":"MC",
     "summary":'"Generate a list of all employee SSNs…"',
     "vtype":"PII Exposure","vtag":"v-pii","model":"GPT-4-Turbo",
     "time":"Today, 10:42 AM","severity":"high"},
    {"user":"Sarah Jones", "dept":"Marketing",  "avatar":"SJ",
     "summary":'"Write a competitor analysis based on…"',
     "vtype":"Data Leakage","vtag":"v-leak","model":"Claude 3.5",
     "time":"Yesterday, 4:15 PM","severity":"high"},
    {"user":"David Kim",   "dept":"Sales",      "avatar":"DK",
     "summary":'"Ignore previous instructions and rev…"',
     "vtype":"Jailbreak Try","vtag":"v-jail","model":"GPT-4",
     "time":"Yesterday, 2:30 PM","severity":"medium"},
    {"user":"Alex Lee",    "dept":"Legal",      "avatar":"AL",
     "summary":"Analyze this attached unredacted co…",
     "vtype":"Sensitive Doc","vtag":"v-sens","model":"Custom-Legal-1",
     "time":"Oct 24, 9:00 AM","severity":"medium"},
]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.2rem .4rem .4rem">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:1.2rem">
            <div style="width:34px;height:34px;background:linear-gradient(135deg,#f05252,#7c6ff7);
                border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1rem">🛡️</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8!important">AI Compliance</div>
                <span class="live-dot" style="font-size:.62rem">MONITORING</span>
            </div>
        </div>
        <div class="nav-group">Platform</div>
        <div class="nav-item active"><span>⬛ Overview</span></div>
        <div class="nav-item"><span>🔴 Live Monitoring</span><span class="nav-badge" style="background:#22d98a">●</span></div>
        <div class="nav-item"><span>⚠️ Violations</span><span class="nav-badge">12</span></div>
        <div class="nav-group" style="margin-top:.5rem">Governance</div>
        <div class="nav-item">📋 Policies & Rules</div>
        <div class="nav-item">🎯 Risk Assessments</div>
        <div class="nav-item">📚 Model Inventory</div>
        <div class="nav-group" style="margin-top:.5rem">Administration</div>
        <div class="nav-item">📝 Audit Logs</div>
        <div class="nav-item">👥 User Access</div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.8rem 0">
    <div style="font-size:.72rem;color:#4e5669;padding:.2rem .4rem">
        Last audit: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """
    </div>
    """, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([3.5, 1])
with hc1:
    st.markdown("""
    <div style="padding:.8rem 0 .2rem">
        <div style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;color:#f0f2f8;line-height:1">
            AI Compliance Overview
        </div>
        <div style="font-size:.82rem;color:#8892a4;margin-top:.3rem">Monitor and manage AI workflow risks</div>
    </div>
    """, unsafe_allow_html=True)
with hc2:
    now = datetime.now().strftime("%b %d  –  %H:%M")
    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
        padding:.55rem 1rem;text-align:right;margin-top:.8rem">
        <div style="font-size:.62rem;color:#4e5669;text-transform:uppercase;letter-spacing:.07em">Dec 1 – Dec 31, 2024</div>
        <div style="font-size:.78rem;font-weight:600;color:#f0f2f8">{now}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

# ── Top stat cards ──────────────────────────────────────────────────────────────
total_interactions = sum(u['interactions'] for u in users)
total_flags        = sum(u['flags'] for u in users)
pending_reviews    = sum(1 for p in recent_prompts if p['severity'] == 'high')

sc1, sc2, sc3, sc4 = st.columns(4)
stat_cards = [
    (sc1, str(total_interactions), "Users interacting with AI", "▲ 12%",  "badge-up",   "👥", "2h ago"),
    (sc2, str(total_flags),        "Flagged by policy engine",  "▼ 5%",   "badge-down", "🚩", "30d Trend"),
    (sc3, "94/100",                "Org-wide compliance rating","▲ Good", "badge-up",   "🛡️", "30d Trend"),
    (sc4, str(pending_reviews),    "Issues requiring review",   "2h ago", "badge-info", "⚠️", "2h ago"),
]
for col, val, lbl, badge_text, badge_cls, icon, sub in stat_cards:
    with col:
        st.markdown(f"""
        <div class="compliance-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <span style="font-size:1.1rem;opacity:.6">{icon}</span>
                <span class="stat-badge {badge_cls}" style="display:inline-flex;align-items:center;gap:4px;
                    font-size:.68rem;font-weight:600;padding:3px 8px;border-radius:20px">{badge_text}</span>
            </div>
            <div class="stat-number">{val}</div>
            <div class="stat-sublabel">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)

# ── Chart row: Prompt Volume + Risk by Dept ──────────────────────────────────
cc1, cc2 = st.columns([1.6, 1])

with cc1:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.2rem">
        AI Prompt Volume
    </div>
    <div style="font-size:.75rem;color:#4e5669;margin-bottom:.8rem">Total prompts vs High-risk flags</div>
    """, unsafe_allow_html=True)
    dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
    total_p   = [1200,1800,2800,4800,4200,3100,2500]
    high_risk = [80, 120, 180, 250, 200, 160, 130]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=total_p, name="Total",
        fill='tozeroy', line=dict(color='#4f8fff', width=2),
        fillcolor='rgba(79,143,255,.12)'))
    fig.add_trace(go.Scatter(x=dates, y=high_risk, name="High Risk",
        fill='tozeroy', line=dict(color='#f05252', width=1.5),
        fillcolor='rgba(240,82,82,.1)'))
    fig.update_layout(height=280, xaxis_tickformat="%a", **DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

with cc2:
    st.markdown("""
    <div style="font-family:'Syne',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.2rem">
        Risk by Department
    </div>
    <div style="display:inline-block;font-size:.65rem;font-weight:600;padding:2px 8px;border-radius:6px;
        background:rgba(240,82,82,.15);color:#f05252;margin-bottom:.8rem">Top Risk: Engineering</div>
    """, unsafe_allow_html=True)
    # Table header
    st.markdown("""
    <div class="tbl-hdr" style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr">
        <span>DEPT</span><span>LOW</span><span>MED</span><span>HIGH</span>
    </div>
    """, unsafe_allow_html=True)
    for dept, r in dept_risks.items():
        high_color = "#f05252" if r['high'] > 5 else "#f5a623" if r['high'] > 0 else "rgba(34,217,138,.5)"
        med_color  = "#f5a623" if r['medium'] > 5 else "rgba(245,166,35,.5)"
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;align-items:center;
            padding:.5rem 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.82rem">
            <span style="color:#f0f2f8;font-weight:500">{dept}</span>
            <span style="color:#8892a4">{r['low']}</span>
            <span style="color:{med_color};font-weight:600">{r['medium']}</span>
            <span style="background:rgba(240,82,82,.12);color:{high_color};font-weight:700;
                padding:2px 8px;border-radius:6px;font-size:.72rem">{r['high']}</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# ── Recent High-Risk Prompts ───────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.7rem">
    <div style="font-family:'Syne',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8">
        Recent High-Risk Prompts
    </div>
    <div style="font-size:.75rem;color:#4f8fff;cursor:pointer">View All Flags →</div>
</div>
""", unsafe_allow_html=True)

# Column headers
st.markdown("""
<div style="display:grid;grid-template-columns:2.5fr 3fr 1.5fr 1.5fr 2fr 1fr;
    font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
    color:#4e5669;padding:.4rem 0;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:.3rem">
    <span>USER</span><span>PROMPT SUMMARY</span><span>VIOLATION TYPE</span>
    <span>MODEL</span><span>TIMESTAMP</span><span>ACTION</span>
</div>
""", unsafe_allow_html=True)

tag_map = {"v-pii":"PII Exposure","v-leak":"Data Leakage","v-jail":"Jailbreak Try","v-sens":"Sensitive Doc"}
for p in recent_prompts:
    border_color = "#f05252" if p['severity'] == 'high' else "#f5a623"
    tag_cls = p['vtag']
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:2.5fr 3fr 1.5fr 1.5fr 2fr 1fr;
        align-items:center;padding:.7rem 0 .7rem .6rem;border-bottom:1px solid rgba(255,255,255,.04);
        border-left:2px solid {border_color};font-size:.8rem;transition:background .15s"
        onmouseover="this.style.background='rgba(255,255,255,.02)'"
        onmouseout="this.style.background='transparent'">
        <div>
            <div style="display:flex;align-items:center;gap:8px">
                <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#4f8fff,#7c6ff7);
                    display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:white;flex-shrink:0">
                    {p['avatar']}
                </div>
                <div>
                    <div style="color:#f0f2f8;font-weight:500;font-size:.8rem">{p['user']}</div>
                    <div style="color:#4e5669;font-size:.7rem">{p['dept']}</div>
                </div>
            </div>
        </div>
        <div style="color:#8892a4;font-size:.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
            padding-right:.5rem" title="{p['summary']}">{p['summary']}</div>
        <div><span class="v-tag {tag_cls}" style="display:inline-flex;align-items:center;font-size:.65rem;
            font-weight:600;padding:3px 8px;border-radius:6px;white-space:nowrap">{p['vtype']}</span></div>
        <div style="color:#8892a4;font-size:.78rem">{p['model']}</div>
        <div style="color:#4e5669;font-size:.75rem">{p['time']}</div>
        <div><button onclick="" style="background:rgba(28,32,48,1);border:1px solid rgba(255,255,255,.14);
            color:#8892a4;padding:4px 12px;border-radius:6px;font-size:.72rem;cursor:pointer;
            font-family:'DM Sans',sans-serif">Review</button></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Bottom row: Model distribution + Weekly trend ─────────────────────────────
bc1, bc2 = st.columns(2)

with bc1:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">AI Model Usage Distribution</div>', unsafe_allow_html=True)
    model_usage = {'GPT-4-Turbo':38,'Claude 3.5':28,'GPT-4':22,'Custom Models':12}
    fig2 = px.pie(values=list(model_usage.values()), names=list(model_usage.keys()),
                  color_discrete_sequence=['#4f8fff','#7c6ff7','#22d98a','#f5a623'], hole=0.55)
    fig2.update_traces(textfont=dict(family="DM Sans", size=10, color="#8892a4"),
                       marker=dict(line=dict(color='rgba(0,0,0,0)', width=0)))
    fig2.update_layout(height=280, **DARK_LAYOUT)
    st.plotly_chart(fig2, use_container_width=True)

with bc2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Weekly Violation Trends</div>', unsafe_allow_html=True)
    weeks = ['Week 1','Week 2','Week 3','Week 4']
    violations = [45, 38, 32, 28]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=weeks, y=violations, mode='lines+markers',
        line=dict(color='#f05252', width=2.5),
        marker=dict(size=7, color='#f05252', line=dict(color='#0d0f14', width=2))))
    fig3.update_layout(height=280, yaxis_title="Violations",
                       title_font=dict(color="#f0f2f8"), **DARK_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

# ── Action strip ──────────────────────────────────────────────────────────────
st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
ac1, ac2, ac3 = st.columns(3)
with ac1: st.button("⚙️ Settings",         use_container_width=True)
with ac2: st.button("👁️ View All Flags",   use_container_width=True, type="primary")
with ac3: st.button("📊 Generate Report",  use_container_width=True)

st.markdown("""
<div style="text-align:center;padding:1.2rem 0 .3rem;font-size:.72rem;color:#4e5669">
    🛡️ AI Compliance Dashboard v2.0 · Real-time monitoring active ·
    Last scan: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
</div>
""", unsafe_allow_html=True)
