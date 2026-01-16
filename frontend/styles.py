"""
Aadhaar Sanket - Professional Light Glassmorphic Design System
Theme: Clean, Professional, Government-Grade
"""

def get_global_css():
    """Returns comprehensive CSS for light glassmorphic theme."""
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --bg-cream: #FAF7F2;
            --bg-card: rgba(255, 255, 255, 0.75);
            --accent-saffron: #F5A623;
            --accent-orange: #FF9800;
            --text-black: #000000;
            --text-dark: #1A1A1A;
            --text-secondary: #333333;
            --text-muted: #555555;
            --border-light: rgba(0, 0, 0, 0.08);
            --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        html, body, .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6, p, label, li, td, th, input, textarea, button {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        .stApp {
            background: var(--bg-cream);
            color: var(--text-black);
        }

        .block-container {
            padding: 3rem 2rem !important;
            max-width: 1400px !important;
        }



        /* GLASSMORPHIC CARDS */
        .glass-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--border-light);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: var(--shadow-soft);
        }

        .glass-card * {
            color: var(--text-black) !important;
        }

        /* KPI CARDS */
        .kpi-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0.7));
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-light);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            box-shadow: var(--shadow-soft);
            position: relative;
            overflow: hidden;
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-saffron), var(--accent-orange));
        }

        .kpi-value {
            font-size: 3rem;
            font-weight: 800;
            color: var(--text-black) !important;
            margin: 0.5rem 0;
        }

        .kpi-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* METRIC CARDS */
        .metric-card {
            background: var(--bg-card);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border-light);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow-soft);
            transition: transform 0.2s;
        }

        .metric-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-saffron);
        }

        .metric-value {
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--text-black) !important;
            white-space: nowrap !important;
            letter-spacing: -0.9px;
            line-height: 1;
        }

        .metric-label {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-muted) !important;
            text-transform: uppercase;
        }

        /* ALERT CARDS */
        .alert-card-critical {
            background: rgba(254, 242, 242, 0.9);
            border-left: 4px solid #DC2626;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .alert-card-critical * {
            color: #991B1B !important;
        }

        .alert-card-warning {
            background: rgba(255, 247, 237, 0.9);
            border-left: 4px solid #EA580C;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .alert-card-warning * {
            color: #9A3412 !important;
        }

        .alert-card-info {
            background: rgba(240, 249, 255, 0.9);
            border-left: 4px solid #0284C7;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .alert-card-info * {
            color: #075985 !important;
        }

        .alert-card-success {
            background: rgba(240, 253, 244, 0.9);
            border-left: 4px solid #16A34A;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        .alert-card-success * {
            color: #166534 !important;
        }

        /* HEADER & SIDEBAR */
        header[data-testid="stHeader"] {
            background: linear-gradient(90deg, var(--accent-saffron), var(--accent-orange));
            border-bottom: 2px solid var(--accent-saffron);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1E293B, #0F172A);
        }

        section[data-testid="stSidebar"] * {
            color: #E2E8F0 !important;
        }

        [data-testid="stSidebarNav"] a {
            padding: 0.75rem 1rem !important;
            margin-bottom: 0.5rem;
            border-radius: 8px;
        }

        [data-testid="stSidebarNav"] a:hover {
            background: rgba(245, 166, 35, 0.1);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(245, 166, 35, 0.2);
            border-left: 4px solid var(--accent-saffron);
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: var(--accent-saffron) !important;
        }

        /* FORCE ALL BUTTONS TO MATCH EXACTLY (Reset & Browse) */
        .stButton > button,
        .stButton > button:first-child,
        div.stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        [data-testid="stFileUploader"] button,
        [data-testid="stFileUploader"] button:first-child {
            background: linear-gradient(135deg, #EA580C, #C2410C) !important;
            background-color: #EA580C !important; /* Fallback */
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.4rem 1rem !important;
            font-weight: 600 !important;
            box-shadow: var(--shadow-soft) !important;
            white-space: nowrap !important;
            min-height: auto !important;
            opacity: 1 !important;
        }

        .stButton > button:hover,
        .stButton > button:first-child:hover,
        button[kind="primary"]:hover,
        button[kind="secondary"]:hover,
        [data-testid="stFileUploader"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
            background: linear-gradient(135deg, #C2410C, #9A3412) !important;
            color: #FFFFFF !important;
        }

        .stButton > button:active, 
        .stButton > button:focus,
        .stButton > button:first-child:focus,
        button[kind="primary"]:focus,
        [data-testid="stFileUploader"] button:active,
        [data-testid="stFileUploader"] button:focus {
             color: #FFFFFF !important;
             border-color: transparent !important;
             box-shadow: none !important;
             outline: none !important;
        }
        
        /* Secondary Buttons - Solid Orange */
        button[kind="secondary"] {
             background: linear-gradient(135deg, #EA580C, #C2410C) !important;
             border: none !important;
             color: #FFFFFF !important;
        }

        /* FORM INPUTS & DROPDOWNS (Aggressive White Theme) */
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px;
            color: #000000 !important;
        }

        div[data-baseweb="select"] span {
            color: #000000 !important;
        }
        
        /* Dropdown menu container */
        div[data-baseweb="popover"] > div,
        div[role="listbox"] {
            background-color: #FFFFFF !important;
        }
        
        /* Dropdown items */
        div[role="listbox"] li {
            background-color: #FFFFFF !important; 
            color: #000000 !important;
        }
        
        div[role="listbox"] li:hover {
            background-color: #FFF7ED !important; /* light orange hover */
        }
        
        /* Multiselect Tags */
        div[data-baseweb="tag"] {
            background-color: #FFF7ED !important;
            border: 1px solid #FED7AA !important;
        }
        
        div[data-baseweb="tag"] span {
            color: #C2410C !important; /* dark orange text */
        }
        
        div[data-baseweb="tag"] svg {
            color: #C2410C !important;
        }
        
        /* Dropdown arrow icons - make them BLACK for visibility */
        div[data-baseweb="select"] svg,
        .stSelectbox svg,
        [data-baseweb="select"] button svg {
            color: #000000 !important;
            fill: #000000 !important;
        }
        
        /* Selectbox chevron/arrow icon */
        [data-testid="stSelectbox"] svg {
            color: #000000 !important;
            fill: #000000 !important;
        }
        
        /* RADIO BUTTON LABELS - FORCE BLACK */
        .stRadio label {
            color: #000000 !important;
        }
        .stRadio [data-baseweb="radio"] span {
            color: #000000 !important;
        }
        [data-testid="stWidgetLabel"] p {
            color: #000000 !important;
        }
        /* Radio option text */
        .stRadio > div > label > div:last-child {
            color: #000000 !important;
        }
        [role="radiogroup"] label {
            color: #000000 !important;
        }
        [role="radiogroup"] label > div {
            color: #000000 !important;
        }

        input, textarea {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            caret-color: #000000 !important;
        }

        /* FILE UPLOADER */
        [data-testid="stFileUploader"] {
            background-color: #FFFFFF !important; /* Force White Background */
            border: 2px dashed #E2E8F0 !important;
            border-radius: 16px;
            padding: 2rem;
        }
        
        [data-testid="stFileUploader"] section {
            background-color: #FFFFFF !important;
        }
        
        [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] div {
            color: var(--text-black) !important;
        }

        /* DATA TABLES */
        [data-testid="stDataFrame"] {
            background: rgba(255, 255, 255, 0.95) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 12px !important;
            overflow: hidden;
        }

        [data-testid="stDataFrame"] * {
            background: transparent !important;
            color: var(--text-black) !important;
        }

        [data-testid="stDataFrame"] th {
            background: rgba(250, 247, 242, 0.8) !important;
            font-weight: 700 !important;
            border-bottom: 2px solid var(--accent-saffron) !important;
        }

        [data-testid="stDataFrame"] tr:hover {
            background: rgba(245, 166, 35, 0.05) !important;
        }

        /* TABS */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem;
            border-bottom: 2px solid var(--border-light);
        }

        .stTabs [data-baseweb="tab"] {
            color: var(--text-secondary) !important;
            font-weight: 600;
        }

        .stTabs [aria-selected="true"] {
            color: var(--accent-saffron) !important;
            border-bottom: 3px solid var(--accent-saffron);
        }

        /* EXPANDERS */
        .streamlit-expanderHeader {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 12px;
            color: #000000 !important;
            padding: 0.75rem 1rem !important;
        }

        .streamlit-expanderHeader:hover,
        .streamlit-expanderHeader:active,
        .streamlit-expanderHeader:focus,
        .streamlit-expanderHeader:focus-visible,
        div[data-testid="stExpander"] > details > summary:hover,
        div[data-testid="stExpander"] > details > summary:focus {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border-color: var(--accent-saffron) !important;
            outline: none !important;
        }

        .streamlit-expanderHeader p, 
        .streamlit-expanderHeader span,
        .streamlit-expanderHeader svg {
            color: #000000 !important;
            fill: #000000 !important;
        }

        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.5) !important;
            border: 1px solid var(--border-light);
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 1rem !important;
        }



        /* CHARTS */
        .js-plotly-plot {
            background: transparent !important;
        }

        .plotly text {
            fill: var(--text-black) !important;
        }

        /* CODE BLOCKS */
        code {
            background: rgba(0, 0, 0, 0.05) !important;
            color: var(--text-black) !important;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
        }

        /* BADGES */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }

        .badge-critical {
            background: rgba(220, 38, 38, 0.15);
            color: #991B1B !important;
            border: 1px solid #DC2626;
        }

        .badge-warning {
            background: rgba(234, 88, 12, 0.15);
            color: #9A3412 !important;
            border: 1px solid #EA580C;
        }

        .badge-success {
            background: rgba(22, 163, 74, 0.15);
            color: #166534 !important;
            border: 1px solid #16A34A;
        }

        .badge-info {
            background: rgba(2, 132, 199, 0.15);
            color: #075985 !important;
            border: 1px solid #0284C7;
        }

        /* HIDE STREAMLIT BRANDING */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* SCROLLBAR */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-cream);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--accent-saffron);
            border-radius: 5px;
        }

        /* ========================================
           GLOBAL METRIC TEXT VISIBILITY FIXES
           Ensures all st.metric components have BLACK text
           ======================================== */
        [data-testid="stMetricValue"] {
            color: #000000 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #000000 !important;
        }
        [data-testid="stMetricDelta"] {
            color: #16a34a !important;
        }
        [data-testid="stMetricDeltaIcon-Up"] {
            color: #16a34a !important;
        }
        [data-testid="stMetricDeltaIcon-Down"] {
            color: #dc2626 !important;
        }
        
        /* Metric container background */
        [data-testid="metric-container"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
            padding: 1rem !important;
            border-radius: 12px !important;
            border: 1px solid #e5e7eb !important;
        }

        /* ========================================
           PLOTLY CHART HOVER TOOLTIP FIXES
           Ensures all chart tooltips are readable
           ======================================== */
        .hoverlayer .hovertext {
            background-color: #FFFFFF !important;
        }
        .hoverlayer .hovertext text {
            fill: #000000 !important;
        }
        
        /* ========================================
           CHECKBOX AND RADIO BUTTON TEXT FIXES
           ======================================== */
        .stCheckbox label span,
        .stRadio label span,
        .stCheckbox > label > div[data-testid="stMarkdownContainer"] p,
        .stRadio > label > div[data-testid="stMarkdownContainer"] p {
            color: #000000 !important;
        }
        
        /* ========================================
           GENERAL TEXT VISIBILITY ENFORCEMENT
           ======================================== */
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        .main .block-container h5,
        .main .block-container p,
        .main .block-container li,
        .main .block-container span:not([class*="badge"]) {
            color: var(--text-black) !important;
        }
        
        /* Caption text visibility */
        .stCaption, [data-testid="stCaptionContainer"] {
            color: #555555 !important;
        }
        
        /* Info/Warning/Error box text */
        .stAlert > div {
            color: #000000 !important;
        }
    </style>
    """

def clean_html(html_str):
    """Clean HTML string."""
    return html_str.replace("\n", "").replace("    ", "")

def render_header(title, subtitle=None):
    """Render professional page header."""
    subtitle_html = f'<p style="color: {subtitle}; font-size: 1.125rem; margin-top: 0.5rem;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin-bottom: 2rem;">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """

def render_kpi_card(value, label, trend=None, trend_direction="neutral"):
    """Render KPI card."""
    trend_html = ""
    if trend:
        trend_colors = {
            "up": "background: rgba(220, 38, 38, 0.15); color: #991B1B;",
            "down": "background: rgba(22, 163, 74, 0.15); color: #166534;",
            "neutral": "background: rgba(85, 85, 85, 0.15); color: #555555;"
        }
        trend_style = trend_colors.get(trend_direction, trend_colors["neutral"])
        trend_html = f'<div style="{trend_style} padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-top: 0.75rem; display: inline-block;">{trend}</div>'
    
    return clean_html(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {trend_html}
    </div>
    """)

def render_metric_card(value, label, trend=None, trend_direction="neutral"):
    """Render metric card."""
    return render_kpi_card(value, label, trend, trend_direction)

def render_insight_card(question, answer, recommendation, icon="💡"):
    """Render insight card."""
    return clean_html(f"""
    <div class="glass-card" style="border-left: 4px solid var(--accent-saffron);">
        <div style="display: flex; gap: 1.5rem;">
            <div style="background: rgba(245, 166, 35, 0.15); width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; border-radius: 12px; font-size: 1.5rem; flex-shrink: 0;">{icon}</div>
            <div style="flex: 1;">
                <h3 style="margin-top: 0;">{question}</h3>
                <p style="line-height: 1.6; margin-bottom: 1rem;">{answer}</p>
                <div style="background: rgba(0, 0, 0, 0.03); padding: 1rem; border-radius: 8px; border-left: 3px solid var(--accent-saffron);">
                    <strong>Recommendation:</strong> {recommendation}
                </div>
            </div>
        </div>
    </div>
    """)

def render_badge(text, type="info"):
    """Render colored badge."""
    badge_classes = {
        "critical": "badge-critical",
        "high": "badge-warning",
        "warning": "badge-warning",
        "elevated": "badge-warning",
        "moderate": "badge-info",
        "stable": "badge-success",
        "success": "badge-success",
        "info": "badge-info"
    }
    
    badge_class = badge_classes.get(type, "badge-info")
    return f'<span class="badge {badge_class}">{text}</span>'

def render_trust_panel(last_updated, source="UIDAI Official Data"):
    """Render data trust indicator."""
    return clean_html(f"""
    <div style="margin-top: 2rem; padding: 1rem; border-top: 1px solid rgba(255, 255, 255, 0.1); color: #94A3B8; font-size: 0.875rem;">
        <div style="margin-bottom: 0.5rem;"><strong style="color: #E2E8F0;">Source:</strong> {source}</div>
        <div><strong style="color: #E2E8F0;">Updated:</strong> {last_updated}</div>
    </div>
    """)
