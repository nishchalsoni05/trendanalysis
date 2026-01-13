"""
Aadhaar Sanket - Policy & Decision Insights
"""
import streamlit as st
import polars as pl
import json
from pathlib import Path
import sys

# Configure page
st.set_page_config(
    page_title="Policy & Decision Insights | Aadhaar Sanket",
    page_icon="⚖️",
    layout="wide",
)

# Setup path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import frontend.styles as styles
import frontend.drill_down as drill_down

# Apply global styles
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

if "loader_shown_P6" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("SYNTHESIZING INTERVENTIONS", "Matching trends to policy framework..."),
        ("PRIORITIZING ZONES", "Ranking districts by urgency..."),
        ("READY", "Loading decision support system...")
    ])
    st.session_state["loader_shown_P6"] = True

# Enforce Data Availability
from frontend.guardrails import require_data
require_data()

# Drill-down handler
drill_down.init_navigation()
if st.session_state.get("drill_down_active", False):
    drill_down.render_evidence_page(
        st.session_state.drill_down_metric,
        st.session_state.drill_down_params
    )
    st.stop()

# Header
st.markdown(
    styles.render_header(
        "Policy & Decision Insights",
        "Plain-language interpretation for governance decisions"
    ),
    unsafe_allow_html=True
)
st.markdown("---")

# Data Loading with Caching
@st.cache_data
def load_decision_data():
    """Load pre-calculated decision intelligence data."""
    try:
        data_path = PROJECT_ROOT / "processed" / "parquet"
        
        # Load Parquet files
        policy_df = pl.read_parquet(data_path / "policy_recommendations.parquet")
        insights_df = pl.read_parquet(data_path / "insights.parquet")
        
        # Load JSON Summary
        with open(PROJECT_ROOT / "processed" / "reports" / "insights.json", "r") as f:
            insights_json = json.load(f)
            
        return policy_df, insights_df, insights_json, True
    except FileNotFoundError:
        return None, None, None, False
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None, None, False

policy_df, insights_df, insights_json, available = load_decision_data()

if not available:
    st.warning("⚠️ Decision Intelligence data not found. Please run the analytics pipeline first.")
    st.stop()

# --- DASHBOARD CONTENT ---

# Executive Summary Card
total_insights = insights_json.get("total_insights", 0)
generated_at = insights_json.get("generated_at", "Unknown")

st.markdown(f"### 📊 Intelligence Summary (Generated: {generated_at.split('T')[0]})")

col1, col2, col3 = st.columns(3)

# Calculate high-level metrics from policy_df
high_priority = policy_df.filter(pl.col("priority") == "High").height
action_types = policy_df.group_by("primary_action").count().sort("count", descending=True).head(1).item(0, "primary_action")

with col1:
    st.markdown(styles.render_metric_card(
        "Total Intelligence Reports",
        str(total_insights),
        "Geographic Units Analyzed",
        "neutral"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(styles.render_metric_card(
        "High Priority Actions",
        str(high_priority),
        "Requires Immediate Review",
        "high" if high_priority > 0 else "good"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(styles.render_metric_card(
        "Dominant Action Type",
        action_types.replace("_", " ").title(),
        "Most Common Recommendation",
        "info"
    ), unsafe_allow_html=True)

st.markdown("---")

# --- INTERACTIVE INSIGHTS EXPLORER ---

st.markdown("## 🧠 Explainable Insights Explorer")

# Filter controls
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 🔍 Filters")
    
    # Check if state column exists, otherwise skip state filter
    if "state" in policy_df.columns:
        filter_state = st.selectbox("Filter by State", ["All"] + sorted(policy_df["state"].unique().to_list()))
    else:
        filter_state = "All"
        st.info("State-level filtering not available (geo_key based data)")
    
    filter_action = st.selectbox("Filter by Action Type", ["All"] + sorted(policy_df["primary_action"].unique().to_list()))

with col2:
    search_query = st.text_input("Search Districts", placeholder="Enter district name...")

# Filter logic
filtered_insights = insights_df
if filter_state != "All":
    # Need to join state info back to insights_df or filter via geo_key if it implies state
    relevant_keys = policy_df.filter(pl.col("state") == filter_state)["geo_key"].to_list()
    filtered_insights = filtered_insights.filter(pl.col("geo_key").is_in(relevant_keys))

if search_query:
    filtered_insights = filtered_insights.filter(pl.col("geo_key").str.to_lowercase().str.contains(search_query.lower()))

# Display Insights
for row in filtered_insights.head(10).to_dicts():
    geo_key = row['geo_key']
    summary = row['insight_summary']
    findings = row['key_findings'].split("; ")
    action = row['recommended_action']
    confidence = row['confidence_statement']
    
    # Determine card color based on action/summary keywords
    card_type = "neutral"
    if "High" in confidence or "Strong" in summary:
        card_type = "high"
    
    with st.container():
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <h3 style="margin: 0; color: #1e293b; font-size: 1.1rem;">📍 {geo_key}</h3>
                <span style="background: #f1f5f9; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.75rem; color: #475569;">
                    {confidence.split('.')[0]}
                </span>
            </div>
            <p style="color: #334155; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">
                {summary}
            </p>
            <div style="background: #f8fafc; padding: 1rem; border-radius: 0.4rem; margin-bottom: 1rem;">
                <strong style="color: #475569; font-size: 0.85rem; display: block; margin-bottom: 0.5rem;">KEY FINDINGS</strong>
                <ul style="margin: 0; padding-left: 1.2rem; color: #334155; font-size: 0.9rem;">
                    {''.join([f'<li style="margin-bottom: 0.2rem;">{f}</li>' for f in findings])}
                </ul>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                <span style="font-size: 1.2rem;">🚀</span>
                <div>
                    <strong style="display: block; font-size: 0.8rem; color: #64748b;">RECOMMENDED ACTION</strong>
                    <span style="color: #0f172a; font-weight: 500;">{action}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if len(filtered_insights) == 0:
    st.info(f"No insights found matching your criteria.")
elif len(filtered_insights) > 10:
    st.caption(f"Showing top 10 of {len(filtered_insights)} matching records.")

st.markdown("---")
st.markdown("### 📋 Detailed Policy Recommendations Table")

# Policy Table
display_cols = ["state", "district", "priority", "action_type", "primary_action", "reasoning"]
st.dataframe(
    policy_df.select([c for c in display_cols if c in policy_df.columns]),
    use_container_width=True,
    hide_index=True
)
