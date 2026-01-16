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
        str(total_insights),
        "Total Intelligence Reports",
        "Geographic Units Analyzed",
        "neutral"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(styles.render_metric_card(
        str(high_priority),
        "High Priority Actions",
        "Requires Immediate Review",
        "high" if high_priority > 0 else "good"
    ), unsafe_allow_html=True)

with col3:
    # Abbreviate long action types for display
    action_display = action_types.replace("_", " ").title()
    if len(action_display) > 12:
        # Use abbreviated version
        words = action_display.split()
        if len(words) >= 2:
            action_display = words[0][:3].upper() + ". " + words[-1][:6].title()
        else:
            action_display = action_display[:12] + "..."
    
    st.markdown(styles.render_metric_card(
        action_display,
        "Dominant Action",
        "Top Recommendation",
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
    # Get all unique geo keys available for search
    all_districts = sorted(insights_df["geo_key"].unique().to_list())
    search_query = st.selectbox(
        "Search Districts",
        options=["All"] + all_districts,
        index=0,
        placeholder="Select or type district name..."
    )

# Filter logic
filtered_insights = insights_df
if filter_state != "All":
    # Need to join state info back to insights_df or filter via geo_key if it implies state
    relevant_keys = policy_df.filter(pl.col("state") == filter_state)["geo_key"].to_list()
    filtered_insights = filtered_insights.filter(pl.col("geo_key").is_in(relevant_keys))

if search_query != "All":
    filtered_insights = filtered_insights.filter(pl.col("geo_key") == search_query)

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

# Add filter controls for the table
table_col1, table_col2, table_col3, table_col4 = st.columns(4)

with table_col1:
    priority_filter = st.selectbox(
        "🎯 Priority Level",
        ["All"] + sorted(policy_df["priority"].unique().to_list()) if "priority" in policy_df.columns else ["All"],
        key="priority_filter"
    )

with table_col2:
    if "action_type" in policy_df.columns:
        action_filter = st.selectbox(
            "📌 Action Type",
            ["All"] + sorted(policy_df["action_type"].unique().to_list()),
            key="action_type_filter"
        )
    else:
        action_filter = "All"

with table_col3:
    if "primary_action" in policy_df.columns:
        primary_filter = st.selectbox(
            "🚀 Primary Action",
            ["All"] + sorted(policy_df["primary_action"].unique().to_list()),
            key="primary_action_filter"
        )
    else:
        primary_filter = "All"

with table_col4:
    sort_by = st.selectbox(
        "📊 Sort By",
        ["Priority (High First)", "Priority (Low First)", "State", "District"],
        key="sort_by"
    )

# Apply filters
filtered_policy = policy_df

if priority_filter != "All" and "priority" in filtered_policy.columns:
    filtered_policy = filtered_policy.filter(pl.col("priority") == priority_filter)
    
if action_filter != "All" and "action_type" in filtered_policy.columns:
    filtered_policy = filtered_policy.filter(pl.col("action_type") == action_filter)
    
if primary_filter != "All" and "primary_action" in filtered_policy.columns:
    filtered_policy = filtered_policy.filter(pl.col("primary_action") == primary_filter)

# Apply sorting
if "Priority (High First)" in sort_by and "priority" in filtered_policy.columns:
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    filtered_policy = filtered_policy.with_columns(
        pl.col("priority").replace(priority_order).alias("sort_key")
    ).sort("sort_key").drop("sort_key")
elif "Priority (Low First)" in sort_by and "priority" in filtered_policy.columns:
    priority_order = {"Low": 0, "Medium": 1, "High": 2}
    filtered_policy = filtered_policy.with_columns(
        pl.col("priority").replace(priority_order).alias("sort_key")
    ).sort("sort_key").drop("sort_key")
elif "State" in sort_by and "state" in filtered_policy.columns:
    filtered_policy = filtered_policy.sort("state")
elif "District" in sort_by and "district" in filtered_policy.columns:
    filtered_policy = filtered_policy.sort("district")

# Summary stats for filtered data
st.markdown("---")
stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    total_recs = len(filtered_policy)
    st.metric("Total Recommendations", total_recs)

with stat_col2:
    high_count = len(filtered_policy.filter(pl.col("priority") == "High")) if "priority" in filtered_policy.columns else 0
    st.metric("High Priority", high_count, delta="Urgent" if high_count > 0 else None, delta_color="inverse")

with stat_col3:
    medium_count = len(filtered_policy.filter(pl.col("priority") == "Medium")) if "priority" in filtered_policy.columns else 0
    st.metric("Medium Priority", medium_count)

with stat_col4:
    low_count = len(filtered_policy.filter(pl.col("priority") == "Low")) if "priority" in filtered_policy.columns else 0
    st.metric("Low Priority", low_count, delta="Normal" if low_count > 0 else None, delta_color="off")

# Display the filtered table
st.markdown("---")
display_cols = ["state", "district", "priority", "action_type", "primary_action", "reasoning"]
available_cols = [c for c in display_cols if c in filtered_policy.columns]

if len(filtered_policy) > 0:
    display_df = filtered_policy.select(available_cols).to_pandas()
    
    # Rename columns for better display
    column_renames = {
        "state": "🗺️ State",
        "district": "📍 District",
        "priority": "🎯 Priority",
        "action_type": "📌 Type",
        "primary_action": "🚀 Action",
        "reasoning": "📝 Reasoning"
    }
    display_df.rename(columns={k: v for k, v in column_renames.items() if k in display_df.columns}, inplace=True)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Export button
    export_col1, export_col2, _ = st.columns([1, 1, 2])
    with export_col1:
        csv_data = filtered_policy.select(available_cols).to_pandas().to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name="policy_recommendations.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with export_col2:
        if len(filtered_policy) > 0:
            st.caption(f"📊 Showing {len(filtered_policy)} recommendations")
else:
    st.info("No recommendations match your filter criteria. Try adjusting the filters.")

# Priority Overview Chart
st.markdown("---")
st.markdown("#### 📊 Priority Distribution")

if "priority" in policy_df.columns:
    priority_counts = policy_df.group_by("priority").len().to_pandas()
    
    import plotly.express as px
    
    fig = px.pie(
        priority_counts, 
        values='len', 
        names='priority',
        color='priority',
        color_discrete_map={
            'High': '#dc2626',
            'Medium': '#f59e0b', 
            'Low': '#16a34a'
        },
        hole=0.4
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#1f2937'),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2, xanchor='center', x=0.5)
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        textfont=dict(color='white'),
        hoverlabel=dict(bgcolor='white', font=dict(color='black'))
    )
    
    st.plotly_chart(fig, use_container_width=True)
