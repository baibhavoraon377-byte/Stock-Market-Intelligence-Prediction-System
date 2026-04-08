import streamlit as st


class DashboardStyling:
    """Centralized dark premium styling for the dashboard — Finrise/AI Compliance aesthetic"""

    @staticmethod
    def apply_custom_css():
        st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

            :root {
                --bg-base:       #0d0f14;
                --bg-card:       #13161e;
                --bg-card-hover: #181c27;
                --bg-elevated:   #1c2030;
                --border:        rgba(255,255,255,0.07);
                --border-active: rgba(255,255,255,0.14);

                --accent-blue:   #4f8fff;
                --accent-violet: #7c6ff7;
                --accent-green:  #22d98a;
                --accent-red:    #f05252;
                --accent-amber:  #f5a623;

                --text-primary:   #f0f2f8;
                --text-secondary: #8892a4;
                --text-muted:     #4e5669;

                --radius-sm: 8px;
                --radius-md: 14px;
                --radius-lg: 20px;
            }

            /* ── Base ── */
            html, body, [class*="css"] {
                font-family: 'DM Sans', sans-serif !important;
                color: var(--text-primary) !important;
            }
            .stApp {
                background: var(--bg-base) !important;
            }
            section[data-testid="stSidebar"] {
                background: var(--bg-card) !important;
                border-right: 1px solid var(--border) !important;
            }
            section[data-testid="stSidebar"] * {
                color: var(--text-secondary) !important;
            }
            section[data-testid="stSidebar"] .stCheckbox label,
            section[data-testid="stSidebar"] label {
                color: var(--text-secondary) !important;
                font-size: 0.85rem !important;
            }

            /* ── Hide Streamlit chrome ── */
            #MainMenu, footer, header { visibility: hidden; }

            /* ── Cards ── */
            .fin-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.4rem 1.6rem;
                transition: border-color 0.2s, transform 0.2s;
            }
            .fin-card:hover {
                border-color: var(--border-active);
                transform: translateY(-2px);
            }

            /* ── Stat cards ── */
            .stat-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.4rem 1.6rem;
                position: relative;
                overflow: hidden;
            }
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 2px;
                background: linear-gradient(90deg, var(--accent-blue), var(--accent-violet));
                opacity: 0.7;
            }
            .stat-label {
                font-size: 0.72rem;
                font-weight: 500;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--text-secondary);
                margin-bottom: 0.5rem;
            }
            .stat-value {
                font-family: 'Syne', sans-serif !important;
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary);
                line-height: 1.1;
            }
            .stat-badge {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                font-size: 0.72rem;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 20px;
                margin-top: 0.5rem;
            }
            .badge-up   { background: rgba(34,217,138,0.12); color: var(--accent-green); }
            .badge-down { background: rgba(240,82,82,0.12);  color: var(--accent-red);   }
            .badge-info { background: rgba(79,143,255,0.12); color: var(--accent-blue);  }

            /* ── Stock ticker cards ── */
            .ticker-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 1rem 1.1rem;
                cursor: pointer;
                transition: all 0.2s;
                text-align: center;
            }
            .ticker-card:hover {
                border-color: var(--accent-blue);
                background: var(--bg-card-hover);
                transform: translateY(-3px);
                box-shadow: 0 8px 24px rgba(79,143,255,0.12);
            }
            .ticker-sym {
                font-size: 0.7rem;
                font-weight: 600;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: var(--text-secondary);
            }
            .ticker-price {
                font-family: 'Syne', sans-serif;
                font-size: 1.3rem;
                font-weight: 700;
                color: var(--text-primary);
                margin: 0.35rem 0;
            }
            .ticker-chg {
                font-size: 0.78rem;
                font-weight: 600;
            }
            .up   { color: var(--accent-green); }
            .down { color: var(--accent-red);   }

            /* ── Section headings ── */
            .section-title {
                font-family: 'Syne', sans-serif;
                font-size: 1.05rem;
                font-weight: 700;
                color: var(--text-primary);
                letter-spacing: -0.01em;
                margin-bottom: 0.1rem;
            }
            .section-sub {
                font-size: 0.78rem;
                color: var(--text-muted);
            }

            /* ── Sidebar nav items ── */
            .nav-group-label {
                font-size: 0.65rem;
                font-weight: 600;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--text-muted) !important;
                padding: 0.6rem 0.5rem 0.3rem;
            }
            .nav-item {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 0.55rem 0.85rem;
                border-radius: var(--radius-sm);
                font-size: 0.85rem;
                font-weight: 500;
                color: var(--text-secondary) !important;
                cursor: pointer;
                transition: background 0.15s;
                margin: 2px 0;
            }
            .nav-item:hover  { background: rgba(255,255,255,0.05); }
            .nav-item.active {
                background: rgba(79,143,255,0.15);
                color: var(--accent-blue) !important;
                font-weight: 600;
            }
            .nav-badge {
                margin-left: auto;
                background: var(--accent-red);
                color: white;
                font-size: 0.65rem;
                font-weight: 700;
                padding: 2px 7px;
                border-radius: 20px;
            }

            /* ── Compliance risk badges ── */
            .risk-low    { background: rgba(34,217,138,0.12); color: var(--accent-green); }
            .risk-medium { background: rgba(245,166,35,0.15); color: var(--accent-amber); }
            .risk-high   { background: rgba(240,82,82,0.12);  color: var(--accent-red);   }
            .risk-pill {
                display: inline-block;
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 0.7rem;
                font-weight: 600;
            }

            /* ── Table rows ── */
            .table-row {
                display: grid;
                align-items: center;
                padding: 0.7rem 0;
                border-bottom: 1px solid var(--border);
                font-size: 0.83rem;
            }
            .table-row:last-child { border-bottom: none; }
            .table-header {
                font-size: 0.68rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--text-muted);
                padding-bottom: 0.5rem;
                border-bottom: 1px solid var(--border);
            }

            /* ── Alert / prompt items ── */
            .prompt-row {
                background: var(--bg-elevated);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 0.9rem 1rem;
                margin-bottom: 0.5rem;
                transition: border-color 0.15s;
            }
            .prompt-row:hover { border-color: var(--border-active); }

            .violation-tag {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                font-size: 0.68rem;
                font-weight: 600;
                padding: 3px 9px;
                border-radius: 6px;
            }
            .tag-pii      { background: rgba(240,82,82,0.15);  color: #f87171; }
            .tag-leak     { background: rgba(245,166,35,0.15); color: #fbbf24; }
            .tag-jailbreak{ background: rgba(124,111,247,0.2); color: #a78bfa; }
            .tag-sensitive{ background: rgba(79,143,255,0.15); color: #60a5fa; }

            /* ── Review button ── */
            .review-btn {
                background: var(--bg-elevated);
                border: 1px solid var(--border-active);
                color: var(--text-secondary);
                padding: 4px 14px;
                border-radius: var(--radius-sm);
                font-size: 0.75rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s;
            }
            .review-btn:hover {
                background: var(--accent-blue);
                color: white;
                border-color: var(--accent-blue);
            }

            /* ── Live dot ── */
            .live-dot {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                font-size: 0.72rem;
                font-weight: 600;
                color: var(--accent-green);
            }
            .live-dot::before {
                content: '';
                width: 7px; height: 7px;
                background: var(--accent-green);
                border-radius: 50%;
                animation: pulse-dot 2s infinite;
            }
            @keyframes pulse-dot {
                0%, 100% { opacity: 1; transform: scale(1); }
                50%      { opacity: 0.4; transform: scale(1.3); }
            }

            /* ── Glass card variant ── */
            .glass-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.25rem 1.5rem;
            }

            /* ── Portfolio gradient card ── */
            .portfolio-hero {
                background: linear-gradient(135deg, #1a1f35 0%, #1e2540 100%);
                border: 1px solid rgba(79,143,255,0.2);
                border-radius: var(--radius-lg);
                padding: 1.6rem;
            }

            /* ── Metric box (analytics page) ── */
            .metric-box {
                background: var(--bg-elevated);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 1.1rem;
                text-align: center;
            }
            .metric-box h4 {
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--text-secondary);
                margin: 0 0 0.4rem;
            }
            .metric-box h2 {
                font-family: 'Syne', sans-serif;
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--text-primary);
                margin: 0;
            }

            /* ── Insight text ── */
            .insight-text {
                background: rgba(245,166,35,0.08);
                border-left: 3px solid var(--accent-amber);
                border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
                padding: 0.9rem 1rem;
                font-size: 0.85rem;
                color: var(--text-secondary);
            }

            /* ── Allocation bar ── */
            .allocation-bar {
                height: 6px;
                background: var(--bg-elevated);
                border-radius: 10px;
                overflow: hidden;
                margin: 0.4rem 0;
            }
            .allocation-fill {
                height: 100%;
                background: linear-gradient(90deg, var(--accent-blue), var(--accent-violet));
                border-radius: 10px;
                transition: width 0.5s ease;
            }

            /* ── Streamlit overrides ── */
            .stTabs [data-baseweb="tab-list"] {
                background: var(--bg-card) !important;
                border-radius: var(--radius-md) !important;
                gap: 4px;
                padding: 4px;
                border: 1px solid var(--border) !important;
            }
            .stTabs [data-baseweb="tab"] {
                background: transparent !important;
                color: var(--text-secondary) !important;
                border-radius: var(--radius-sm) !important;
                font-size: 0.82rem !important;
                font-weight: 500 !important;
                padding: 6px 16px !important;
            }
            .stTabs [aria-selected="true"] {
                background: var(--bg-elevated) !important;
                color: var(--text-primary) !important;
                font-weight: 600 !important;
            }
            .stSelectbox > div > div,
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input {
                background: var(--bg-elevated) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                color: var(--text-primary) !important;
                font-size: 0.85rem !important;
            }
            .stButton > button {
                background: var(--bg-elevated) !important;
                border: 1px solid var(--border-active) !important;
                color: var(--text-secondary) !important;
                border-radius: var(--radius-sm) !important;
                font-size: 0.82rem !important;
                font-weight: 500 !important;
                transition: all 0.15s !important;
            }
            .stButton > button:hover {
                background: var(--accent-blue) !important;
                border-color: var(--accent-blue) !important;
                color: white !important;
            }
            .stButton > button[kind="primary"] {
                background: var(--accent-blue) !important;
                border-color: var(--accent-blue) !important;
                color: white !important;
            }
            div[data-testid="stMetric"] {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 0.9rem 1.1rem;
            }
            div[data-testid="stMetric"] label {
                color: var(--text-secondary) !important;
                font-size: 0.72rem !important;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {
                font-family: 'Syne', sans-serif !important;
                color: var(--text-primary) !important;
                font-size: 1.6rem !important;
            }
            div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
                font-size: 0.78rem !important;
            }
            .stDataFrame, .stTable {
                background: var(--bg-card) !important;
                border-radius: var(--radius-md) !important;
            }
            [data-testid="stDataFrameContainer"] {
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-md) !important;
            }
            ::-webkit-scrollbar { width: 5px; height: 5px; }
            ::-webkit-scrollbar-track { background: var(--bg-base); }
            ::-webkit-scrollbar-thumb {
                background: var(--border-active);
                border-radius: 10px;
            }

            /* ── h1/h2/h3 override ── */
            h1, h2, h3 {
                font-family: 'Syne', sans-serif !important;
                color: var(--text-primary) !important;
            }
            p, span, div { color: var(--text-primary); }
            .stMarkdown p { color: var(--text-secondary); font-size: 0.85rem; }

            /* analytics card */
            .analytics-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
            }
            .analytics-card h4 {
                font-family: 'Syne', sans-serif;
                font-size: 0.85rem;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.08em;
                margin-bottom: 0.75rem;
            }
            .analytics-card table td {
                padding: 0.3rem 0.5rem;
                font-size: 0.83rem;
                color: var(--text-secondary);
            }
            .analytics-card table td:last-child {
                color: var(--text-primary);
            }

            /* compliance card */
            .compliance-card {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-lg);
                padding: 1.4rem 1.6rem;
                margin-bottom: 1rem;
                transition: border-color 0.2s;
            }
            .compliance-card:hover { border-color: var(--border-active); }
            .stat-number {
                font-family: 'Syne', sans-serif;
                font-size: 2.4rem;
                font-weight: 700;
                color: var(--text-primary);
                margin: 0.4rem 0;
                line-height: 1;
            }
            .risk-badge {
                padding: 3px 10px;
                border-radius: 20px;
                font-size: 0.7rem;
                font-weight: 600;
                display: inline-block;
            }
            .risk-low    { background: rgba(34,217,138,0.12); color: #22d98a; }
            .risk-medium { background: rgba(245,166,35,0.15); color: #f5a623; }
            .risk-high   { background: rgba(240,82,82,0.12);  color: #f05252; }
            .prompt-item {
                background: var(--bg-elevated);
                border: 1px solid var(--border);
                border-left: 3px solid;
                padding: 0.9rem 1rem;
                margin-bottom: 0.5rem;
                border-radius: var(--radius-md);
                transition: border-color 0.15s;
            }
            .prompt-item:hover { border-color: var(--border-active); }

            /* portfolio card */
            .portfolio-card {
                background: linear-gradient(135deg, #1a1f35 0%, #1e2540 100%);
                border: 1px solid rgba(79,143,255,0.18);
                border-radius: var(--radius-lg);
                padding: 1.4rem;
                color: white;
                margin-bottom: 1rem;
            }
            .holding-item {
                background: var(--bg-card);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 0.85rem 1rem;
                margin-bottom: 0.5rem;
                transition: border-color 0.2s;
            }
            .holding-item:hover { border-color: var(--border-active); }
            .profit-positive { color: var(--accent-green); font-weight: 600; }
            .profit-negative { color: var(--accent-red);   font-weight: 600; }
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def display_metric_card(title: str, value: str, delta: str = None, icon: str = None, badge_type: str = "info"):
        badge_class = f"badge-{'up' if badge_type == 'success' else 'down' if badge_type == 'danger' else 'info'}"
        delta_html = f'<div class="stat-badge {badge_class}">{delta}</div>' if delta else ''
        icon_html = f'<span style="font-size:1.4rem;opacity:0.7">{icon}</span>' if icon else ''
        st.markdown(f"""
        <div class="stat-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div class="stat-label">{title}</div>
                {icon_html}
            </div>
            <div class="stat-value">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def display_alert(message: str, alert_type: str = "info"):
        color_map = {
            "info":    ("rgba(79,143,255,0.1)",  "#4f8fff"),
            "success": ("rgba(34,217,138,0.1)",  "#22d98a"),
            "warning": ("rgba(245,166,35,0.12)", "#f5a623"),
            "error":   ("rgba(240,82,82,0.1)",   "#f05252"),
        }
        bg, border = color_map.get(alert_type, color_map["info"])
        st.markdown(f"""
        <div style="background:{bg};border-left:3px solid {border};border-radius:0 8px 8px 0;
                    padding:0.75rem 1rem;font-size:0.83rem;color:var(--text-secondary);margin-bottom:0.5rem">
            {message}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def display_badge(text: str, badge_type: str = "info"):
        cls_map = {"success": "badge-up", "danger": "badge-down", "info": "badge-info", "warning": "badge-down"}
        st.markdown(f'<span class="stat-badge {cls_map.get(badge_type, "badge-info")}">{text}</span>', unsafe_allow_html=True)

    @staticmethod
    def display_live_indicator():
        st.markdown('<span class="live-dot">LIVE</span>', unsafe_allow_html=True)

    @staticmethod
    def create_progress_bar(percentage: float):
        st.markdown(f"""
        <div class="allocation-bar">
            <div class="allocation-fill" style="width:{percentage}%"></div>
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def display_tooltip(content: str, tooltip_text: str):
        st.markdown(f'<span title="{tooltip_text}" style="cursor:help;border-bottom:1px dashed var(--text-muted)">{content}</span>', unsafe_allow_html=True)


class ColorPalette:
    PRIMARY        = "#4f8fff"
    PRIMARY_DARK   = "#7c6ff7"
    SECONDARY      = "#22d98a"
    SUCCESS        = "#22d98a"
    DANGER         = "#f05252"
    WARNING        = "#f5a623"
    INFO           = "#4f8fff"
    TEXT_PRIMARY   = "#f0f2f8"
    TEXT_SECONDARY = "#8892a4"
    TEXT_LIGHT     = "#4e5669"
    BG_PRIMARY     = "#0d0f14"
    BG_SECONDARY   = "#13161e"
    BG_DARK        = "#0d0f14"
    CHART_COLORS   = ["#4f8fff", "#7c6ff7", "#22d98a", "#f5a623", "#f05252", "#ec4899", "#06b6d4", "#84cc16"]

    @staticmethod
    def get_gradient(start_color: str, end_color: str):
        return f"linear-gradient(135deg, {start_color} 0%, {end_color} 100%)"

    @staticmethod
    def get_price_color(change: float) -> str:
        if change > 0:   return ColorPalette.SUCCESS
        elif change < 0: return ColorPalette.DANGER
        else:            return ColorPalette.WARNING


def init_styling():
    DashboardStyling.apply_custom_css()


init_styling()
