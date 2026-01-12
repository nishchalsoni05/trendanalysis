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

        * {
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

        /* FORCE BLACK TEXT EVERYWHERE */
        p, span, div, label, li, td, th, input, textarea {
            color: var(--text-black) !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-black) !important;
            font-weight: 700 !important;
        }

        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 2rem !important; }
        h3 { font-size: 1.5rem !important; }

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
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-black) !important;
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

        /* BUTTONS */
        .stButton > button {
            background: linear-gradient(135deg, var(--accent-saffron), var(--accent-orange));
            color: #FFFFFF !important;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 1.5rem;
            font-weight: 600;
            box-shadow: var(--shadow-soft);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .stButton > button * {
            color: #FFFFFF !important;
        }

        /* FORM INPUTS */
        div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 8px;
        }

        div[data-baseweb="select"] * {
            color: var(--text-black) !important;
        }

        input, textarea {
            background: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 8px;
            color: var(--text-black) !important;
        }

        /* FILE UPLOADER */
        [data-testid="stFileUploader"] {
            background: var(--bg-card);
            border: 2px dashed var(--border-light);
            border-radius: 16px;
            padding: 2rem;
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
            background: var(--bg-card) !important;
            border: 1px solid var(--border-light);
            border-radius: 12px;
            color: var(--text-black) !important;
            padding: 0.75rem 1rem !important;
        }

        .streamlit-expanderHeader:hover {
            border-color: var(--accent-saffron);
        }

        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.5) !important;
            border: 1px solid var(--border-light);
            border-top: none;
            border-radius: 0 0 12px 12px;
            padding: 1rem !important;
        }

        /* Fix expander icon overlap - hide the text, show only icon */
        .streamlit-expanderHeader svg {
            min-width: 1rem;
        }
        
        /* Hide the material icon text that appears */
        details summary::-webkit-details-marker {
            display: none;
        }
        
        details summary {
            list-style: none;
        }
        
        details summary::marker {
            display: none;
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
