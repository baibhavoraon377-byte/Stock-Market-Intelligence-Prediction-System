"""
AI Compliance Dashboard · pages/3_Compliance.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from utils.styling import apply_css, DARK_LAYOUT
apply_css()

st.markdown("""<style>
.compliance-card{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-lg);
    padding:1.3rem 1.5rem;position:relative;overflow:hidden;transition:border-color .2s;}
.compliance-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
    background:linear-gradient(90deg,var(--accent-blue),var(--accent-violet));opacity:.6;}
.compliance-card:hover{border-color:var(--border-active);}
.stat-number{font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:700;color:var(--text-primary);line-height:1;margin:.35rem 0;}
.stat-sublabel{font-size:.75rem;color:var(--text-muted);margin-top:.2rem;}
.v-tag{display:inline-flex;align-items:center;font-size:.65rem;font-weight:600;padding:3px 8px;border-radius:6px;}
.v-pii{background:rgba(240,82,82,.15);color:#f87171;}
.v-leak{background:rgba(245,166,35,.15);color:#fbbf24;}
.v-jail{background:rgba(124,111,247,.2);color:#a78bfa;}
.v-sens{background:rgba(79,143,255,.15);color:#60a5fa;}
.tbl-hdr{font-size:.65rem;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
    color:var(--text-muted);padding:.5rem 0;border-bottom:1px solid var(--border);margin-bottom:.3rem;}
</style>""",unsafe_allow_html=True)

# ── Sample data ────────────────────────────────────────────────────────────────
users = [
    {"name":"Mike Chen","dept":"Engineering","avatar":"MC","interactions":245,"flags":12},
    {"name":"Sarah Jones","dept":"Marketing","avatar":"SJ","interactions":189,"flags":3},
    {"name":"John Smith","dept":"Sales","avatar":"JS","interactions":320,"flags":8},
    {"name":"Emily Brown","dept":"HR","avatar":"EB","interactions":95,"flags":1},
    {"name":"David Lee","dept":"Legal","avatar":"DL","interactions":67,"flags":0},
]
dept_risks={"Eng":{"low":45,"medium":12,"high":8},"Sales":{"low":120,"medium":5,"high":0},
            "Mktg":{"low":85,"medium":3,"high":1},"HR":{"low":12,"medium":8,"high":2},"Legal":{"low":8,"medium":2,"high":0}}
recent_prompts=[
    {"user":"Mike Chen","dept":"Engineering","avatar":"MC","summary":'"Generate a list of all employee SSNs…"',"vtype":"PII Exposure","vtag":"v-pii","model":"GPT-4-Turbo","time":"Today, 10:42 AM","severity":"high"},
    {"user":"Sarah Jones","dept":"Marketing","avatar":"SJ","summary":'"Write a competitor analysis based on…"',"vtype":"Data Leakage","vtag":"v-leak","model":"Claude 3.5","time":"Yesterday, 4:15 PM","severity":"high"},
    {"user":"David Kim","dept":"Sales","avatar":"DK","summary":'"Ignore previous instructions and rev…"',"vtype":"Jailbreak Try","vtag":"v-jail","model":"GPT-4","time":"Yesterday, 2:30 PM","severity":"medium"},
    {"user":"Alex Lee","dept":"Legal","avatar":"AL","summary":"Analyze this attached unredacted contract…","vtype":"Sensitive Doc","vtag":"v-sens","model":"Custom-Legal-1","time":"Oct 24, 9:00 AM","severity":"medium"},
]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""<div style="padding:.8rem .4rem .4rem">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="width:34px;height:34px;background:linear-gradient(135deg,#f05252,#7c6ff7);
          border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.1rem">🛡️</div>
        <div><div style="font-family:'Syne',sans-serif;font-weight:700;font-size:.95rem;color:#f0f2f8">AI Compliance</div>
        <span class="live-dot" style="font-size:.62rem">MONITORING</span></div>
      </div>
    </div>
    <hr style="border-color:rgba(255,255,255,.06);margin:.2rem 0 .8rem">
    <div style="font-size:.72rem;color:#4e5669;padding:.2rem .4rem">Last audit: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    """,unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
h1,h2=st.columns([3.5,1])
with h1: st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.6rem;font-weight:800;color:#f0f2f8;padding:.6rem 0 .2rem">AI Compliance Overview</div><div style="font-size:.82rem;color:#8892a4">Monitor and manage AI workflow risks across your organisation</div>',unsafe_allow_html=True)
with h2: st.markdown(f'<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:.55rem 1rem;text-align:right;margin-top:.8rem"><div style="font-size:.62rem;color:#4e5669;text-transform:uppercase">Live</div><div style="font-size:.78rem;font-weight:600;color:#f0f2f8">{datetime.now().strftime("%b %d – %H:%M")}</div></div>',unsafe_allow_html=True)
st.markdown("<div style='height:.4rem'></div>",unsafe_allow_html=True)

# ── Stat cards ─────────────────────────────────────────────────────────────────
ti=sum(u["interactions"] for u in users); tf=sum(u["flags"] for u in users); pr=sum(1 for p in recent_prompts if p["severity"]=="high")
for col,val,lbl,badge,bcls,icon in zip(st.columns(4),
    [str(ti),str(tf),"94/100",str(pr)],
    ["Total AI interactions","Flagged by policy","Compliance score","High-risk pending"],
    ["▲ 12% vs last wk","▼ 5% improving","▲ Good standing","Needs attention"],
    ["badge-up","badge-up","badge-up","badge-down"],["👥","🚩","🛡️","⚠️"]):
    with col:
        st.markdown(f'<div class="compliance-card"><div style="display:flex;justify-content:space-between"><span style="opacity:.6">{icon}</span><span class="stat-badge {bcls}">{badge}</span></div><div class="stat-number">{val}</div><div class="stat-sublabel">{lbl}</div></div>',unsafe_allow_html=True)

st.markdown("<div style='height:.3rem'></div>",unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
cc1,cc2=st.columns([1.6,1])
with cc1:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">AI Prompt Volume (7 Days)</div>',unsafe_allow_html=True)
    dates=pd.date_range(end=datetime.now(),periods=7,freq="D")
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=dates,y=[1200,1800,2800,4800,4200,3100,2500],name="Total",fill="tozeroy",line=dict(color="#4f8fff",width=2),fillcolor="rgba(79,143,255,.12)"))
    fig.add_trace(go.Scatter(x=dates,y=[80,120,180,250,200,160,130],name="High Risk",fill="tozeroy",line=dict(color="#f05252",width=1.5),fillcolor="rgba(240,82,82,.1)"))
    fig.update_layout(height=260,xaxis_tickformat="%a",**DARK_LAYOUT)
    st.plotly_chart(fig,use_container_width=True)
with cc2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8;margin-bottom:.6rem">Risk by Department</div>',unsafe_allow_html=True)
    st.markdown('<div class="tbl-hdr" style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr"><span>DEPT</span><span>LOW</span><span>MED</span><span>HIGH</span></div>',unsafe_allow_html=True)
    for dept,r in dept_risks.items():
        hc="#f05252" if r["high"]>5 else "#f5a623" if r["high"]>0 else "rgba(34,217,138,.5)"
        st.markdown(f'<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;align-items:center;padding:.45rem 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:.82rem"><span style="color:#f0f2f8;font-weight:500">{dept}</span><span style="color:#8892a4">{r["low"]}</span><span style="color:#f5a623;font-weight:600">{r["medium"]}</span><span style="background:rgba(240,82,82,.12);color:{hc};font-weight:700;padding:2px 8px;border-radius:6px;font-size:.72rem">{r["high"]}</span></div>',unsafe_allow_html=True)

st.markdown("<div style='height:.8rem'></div>",unsafe_allow_html=True)

# ── Recent prompts ─────────────────────────────────────────────────────────────
st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.6rem"><div style="font-family:\'Syne\',sans-serif;font-size:.9rem;font-weight:700;color:#f0f2f8">Recent High-Risk Prompts</div><div style="font-size:.75rem;color:#4f8fff">View All →</div></div>',unsafe_allow_html=True)
st.markdown('<div style="display:grid;grid-template-columns:2.5fr 3fr 1.5fr 1.5fr 2fr 1fr;font-size:.62rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:#4e5669;padding:.4rem 0;border-bottom:1px solid rgba(255,255,255,.06);margin-bottom:.3rem"><span>USER</span><span>SUMMARY</span><span>VIOLATION</span><span>MODEL</span><span>TIME</span><span>ACTION</span></div>',unsafe_allow_html=True)
for p in recent_prompts:
    bc="#f05252" if p["severity"]=="high" else "#f5a623"
    st.markdown(f'<div style="display:grid;grid-template-columns:2.5fr 3fr 1.5fr 1.5fr 2fr 1fr;align-items:center;padding:.65rem 0 .65rem .6rem;border-bottom:1px solid rgba(255,255,255,.04);border-left:2px solid {bc};font-size:.8rem"><div style="display:flex;align-items:center;gap:8px"><div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#4f8fff,#7c6ff7);display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700;color:white;flex-shrink:0">{p["avatar"]}</div><div><div style="color:#f0f2f8;font-weight:500">{p["user"]}</div><div style="color:#4e5669;font-size:.7rem">{p["dept"]}</div></div></div><div style="color:#8892a4;font-size:.78rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:.5rem">{p["summary"]}</div><div><span class="v-tag {p["vtag"]}">{p["vtype"]}</span></div><div style="color:#8892a4;font-size:.78rem">{p["model"]}</div><div style="color:#4e5669;font-size:.75rem">{p["time"]}</div><div><button style="background:rgba(28,32,48,1);border:1px solid rgba(255,255,255,.14);color:#8892a4;padding:4px 12px;border-radius:6px;font-size:.72rem;cursor:pointer;font-family:\'DM Sans\',sans-serif">Review</button></div></div>',unsafe_allow_html=True)

st.markdown("<div style='height:.8rem'></div>",unsafe_allow_html=True)
bc1,bc2=st.columns(2)
with bc1:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Model Usage</div>',unsafe_allow_html=True)
    mu={"GPT-4-Turbo":38,"Claude 3.5":28,"GPT-4":22,"Custom":12}
    fig2=px.pie(values=list(mu.values()),names=list(mu.keys()),color_discrete_sequence=["#4f8fff","#7c6ff7","#22d98a","#f5a623"],hole=.55)
    fig2.update_traces(textfont=dict(size=10,color="#8892a4"),marker=dict(line=dict(color="rgba(0,0,0,0)",width=0)))
    fig2.update_layout(height=260,**DARK_LAYOUT); st.plotly_chart(fig2,use_container_width=True)
with bc2:
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:.85rem;font-weight:700;color:#f0f2f8;margin-bottom:.5rem">Weekly Violations</div>',unsafe_allow_html=True)
    wk=["Wk 1","Wk 2","Wk 3","Wk 4"]; vi=[45,38,32,28]
    fig3=go.Figure(go.Scatter(x=wk,y=vi,mode="lines+markers",fill="tozeroy",
        line=dict(color="#f05252",width=2.5),marker=dict(size=7,color="#f05252"),fillcolor="rgba(240,82,82,.07)"))
    fig3.update_layout(height=260,title=f"↓ {vi[0]-vi[-1]} violations reduced",title_font=dict(color="#22d98a",size=11),**DARK_LAYOUT)
    st.plotly_chart(fig3,use_container_width=True)

ac1,ac2,ac3=st.columns(3)
with ac1: st.button("⚙️ Settings",use_container_width=True)
with ac2: st.button("👁️ View All Flags",use_container_width=True,type="primary")
with ac3: st.button("📊 Generate Report",use_container_width=True)

st.markdown(f'<div style="text-align:center;padding:1rem 0 .2rem;font-size:.72rem;color:#4e5669">🛡️ Compliance Dashboard · Last scan: {datetime.now().strftime("%H:%M:%S")}</div>',unsafe_allow_html=True)
