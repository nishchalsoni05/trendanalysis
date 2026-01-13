
"""
AI CHAT ASSISTANT
Dedicated conversational analytics interface.
"""
import streamlit as st
from pathlib import Path
import sys

# Page Config
st.set_page_config(
    page_title="AI Chat Assistant | Aadhaar Sanket",
    page_icon="💬",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import frontend.styles as styles
from frontend.guardrails import require_data

# --- SETUP ---
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

if "loader_shown_P10" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("INITIALIZING CONVERSATIONAL AGENT", "Loading semantic models..."),
        ("CONNECTING TO KNOWLEDGE GRAPH", "Indexing demographic entities..."),
        ("READY", "Chat interface active...")
    ])
    st.session_state["loader_shown_P10"] = True

require_data()

# --- API KEY CHECK ---
def check_api_key():
    """Check if GEMINI_API_KEY is configured."""
    import os
    from pathlib import Path
    
    env_path = Path(__file__).parent.parent.parent / ".env"
    api_key = None
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    return bool(api_key)

if not check_api_key():
    st.warning("""
⚠️ **API Key Not Found**

To enable AI features:

1. Create a `.env` file in the root folder (if not already present)
2. Copy-paste the following content:

```
GEMINI_API_KEY={Insert API KEY HERE, CHECK README.MD}
```
""")
    st.stop()

# Initialize AI Engine
# Temporarily disabled caching to force reload after fixes
# @st.cache_resource
def get_ai_engine():
    try:
        # Force-add site-packages to ensure visibility in Streamlit
        import sys
        from pathlib import Path
        
        site_pkg = Path(r"C:\Users\Nishchal Soni\Downloads\uidai\code\.venv\Lib\site-packages")
        if str(site_pkg) not in sys.path:
            sys.path.append(str(site_pkg))
            
        # Manual .env approach matching the dashboard
        from src.ai.insight_engine import InsightEngine
        return InsightEngine()
    except Exception as e:
        import sys
        debug_info = f"Python Executable: {sys.executable}\\nPaths: {sys.path[:3]}"
        return f"Error: {e}\\n\\nDebug Info:\\n{debug_info}"

engine = get_ai_engine()

if isinstance(engine, str) or not engine:
    st.error(f"❌ AI Engine Failed to Initialize: {engine}")
    st.stop()

# --- CSS FOR TRANSPARENT SEARCH ---
st.markdown("""
<style>
    /* Hide label */
    .stTextInput label {
        display: none;
    }
    
    /* Input Styling - Google Style Transparent */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 24px !important;
        padding: 1rem 1.5rem !important;
        color: white !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    }
    
    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    /* Container adjustments */
    .block-container {
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- HERO SECTION ---
st.markdown("""
<div style="background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); padding: 3rem 2rem 5rem 2rem; border-radius: 0 0 24px 24px; text-align: center; margin-bottom: -3rem; margin-top: -4rem; margin-left: -4rem; margin-right: -4rem;">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">💬 Aadhaar Sanket AI Chat</h1>
    <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-top: 1rem; max-width: 800px; margin-left: auto; margin-right: auto;">
        Your dedicated conversational analyst. Ask complex questions about demographic trends, migration anomalies, 
        and high-risk zones using natural language.
    </p>
</div>
""", unsafe_allow_html=True)

# --- SEARCH INPUT (TOP) ---
# We use a container to pull it up into the hero area visually using negative margin in CSS if needed, 
# but here standard flow works best with the transparent style.

if "search_input_val" not in st.session_state:
    st.session_state.search_input_val = ""

def submit():
    st.session_state.query_to_run = st.session_state.search_widget
    st.session_state.search_widget = ""  # Clear input

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.text_input(
        "Search", 
        placeholder="🔍 Ask anything... (e.g., 'Show high risk districts')", 
        key="search_widget", 
        on_change=submit
    )

# --- STATE HANDLING ---
if "chat_history_full" not in st.session_state:
    st.session_state.chat_history_full = []

query_to_process = None

# Check manual search submission
if "query_to_run" in st.session_state and st.session_state.query_to_run:
    query_to_process = st.session_state.query_to_run
    del st.session_state.query_to_run

# --- SUGGESTED QUERIES ---
if not st.session_state.chat_history_full and not query_to_process:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("### 💡 Or try one of these:")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔥 Identify Hotspots", use_container_width=True):
            query_to_process = "Which districts are currently classified as high-pressure hotspots?"
    with col2:
        if st.button("📉 Explain Volatility", use_container_width=True):
            query_to_process = "Why are we seeing volatility in the central region?"
    with col3:
        if st.button("📊 National Summary", use_container_width=True):
            query_to_process = "Give me a high-level summary of national migration trends."
    with col4:
        if st.button("🔮 Forecast Risks", use_container_width=True):
            query_to_process = "Based on current signals, which areas are at risk for next month?"

# --- PROCESSING ---
if query_to_process:
    # Add to history immediately
    with st.spinner("Analyzing..."):
        resp = engine.ask(query_to_process)
    st.session_state.chat_history_full.append((query_to_process, resp))

# --- CHAT HISTORY DISPLAY ---
# Display in reverse chronological or standard? Standard usually enables reading flow.
# But for "Search Engine" feel, results appear below.

if st.session_state.chat_history_full:
    st.markdown("---")
    for q, a in reversed(st.session_state.chat_history_full): # Show newest first like a feed? Or standard? Let's do newest first for "Search" feel
        with st.container():
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 1); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border: 1px solid #334155;">
                <div style="font-weight: 600; color: #94a3b8; margin-bottom: 0.5rem;">Q: {q}</div>
                <div style="color: #f1f5f9; line-height: 1.6;">{a}</div>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: #94a3b8; font-size: 0.8rem;">
    Aadhaar Sanket AI Intelligence Layer • Strictly Read-Only Access
</div>
""", unsafe_allow_html=True)
