"""
Aadhaar Sanket - Spatial Stress & Hotspots Page

Zone classification and cluster detection visualization.
"""
import streamlit as st
from pathlib import Path
import sys
import polars as pl
import plotly.express as px

st.set_page_config(
    page_title="Spatial Stress Analysis | Aadhaar Sanket",
    page_icon="🔥",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles
import frontend.drill_down as drill_down
import frontend.chart_config as chart_config

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

if "loader_shown_P4_Stress" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("SCANNING ZONES", "Identifying stress clusters..."),
        ("COMPUTING DENSITY INDEX", "Normalizing population metrics..."),
        ("READY", "Visualizing spatial stress...")
    ])
    st.session_state["loader_shown_P4_Stress"] = True

# Enforce Data Availability
from frontend.guardrails import require_data
require_data()

# Initialize drill-down
drill_down.init_navigation()

# Check drill-down state
if st.session_state.get("drill_down_active", False):
    drill_down.render_evidence_page(
        st.session_state.drill_down_metric,
        st.session_state.drill_down_params
    )
    st.stop()

# Render header
st.markdown(
    styles.render_header(
        "Spatial Stress Analysis",
        "Identify areas under demographic pressure and emerging clusters"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

@st.cache_data(show_spinner="Loading spatial data...")
def load_spatial_data():
    """Load and process spatial stress data with caching."""
    try:
        from src.engines.ingestion import load_processed_dataset
        from src.engines.signal_separation import apply_signal_weights
        from src.engines.mvi import calculate_mvi, calculate_population_base
        from src.engines.spatial import add_zone_classification, detect_hotspot_clusters
        
        demographic_df = load_processed_dataset("demographic")
        enrolment_df = load_processed_dataset("enrolment")
        
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        population_df = calculate_population_base(enrolment_df, "district")
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        mvi_df = add_zone_classification(mvi_df)
        mvi_df = detect_hotspot_clusters(mvi_df)
        
        return mvi_df, True
    except Exception as e:
        return None, False

# Load data
mvi_df, data_available = load_spatial_data()

if not data_available:
    st.markdown(styles.clean_html("""
    <div class="alert-card-warning">
        <strong>⚠️ Data Not Processed</strong><br>
        Please run the data pipeline to generate spatial insights.
    </div>
    """), unsafe_allow_html=True)
    st.info("Run: `python run_pipeline.py`")
    st.stop()

# 4-PART VISUAL STORYTELLING
high_count = len(mvi_df.filter(pl.col("mvi") >= 30))
elevated_count = len(mvi_df.filter((pl.col("mvi") >= 15) & (pl.col("mvi") < 30)))
clusters = mvi_df.filter(pl.col("is_cluster") == True)
cluster_count = len(clusters)

st.markdown(styles.render_insight_card(
    "Are there clusters of high-pressure areas?",
    f"Found {high_count} high-pressure districts and {elevated_count} elevated districts. {cluster_count} districts show spatial clustering of high migration.",
    "Clustered regions may need coordinated regional planning interventions. Single high-pressure districts can be addressed locally, but clusters require state or multi-district strategies.",
    "🔥"
), unsafe_allow_html=True)

st.markdown("---")

# Clickable Metrics Row
col1, col2, col3 = st.columns(3)

with col1:
    drill_down.render_metric_button(
        value=f"{high_count}",
        label="High Pressure Districts",
        metric_id="high_pressure_districts_spatial",
        params={"mvi_min": 30},
        trend_direction="down" if high_count > 0 else "neutral"
    )

with col2:
    drill_down.render_metric_button(
        value=f"{elevated_count}",
        label="Elevated Stress",
        metric_id="elevated_pressure_spatial",
        params={"mvi_min": 15, "mvi_max": 30},
        trend_direction="neutral"
    )

with col3:
    # Count of STATES with clusters might be more interesting
    states_with_clusters = clusters.select("state").n_unique()
    drill_down.render_metric_button(
        value=f"{states_with_clusters}",
        label="States with Clusters",
        metric_id="cluster_states",
        params={"cluster_only": True},
        trend="Active",
        trend_direction="down" if states_with_clusters > 0 else "neutral"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Zone summary
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Zone Distribution")
    
    zone_counts = mvi_df.group_by("zone_type").len().to_pandas()
    
    color_map = {
        "high_inflow": "#DC2626",      # Red
        "moderate_inflow": "#EA580C",  # Orange
        "stable": "#16A34A",           # Green
        "decline": "#64748B",          # Slate
    }
    
    fig = px.pie(
        zone_counts,
        values="len",
        names="zone_type",
        color="zone_type",
        color_discrete_map=color_map,
        hole=0.4,
    )
    fig.update_layout(
        height=350,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.0,
            font=dict(color="#000000")
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(255,255,255,0.9)",
        plot_bgcolor="rgba(255,255,255,0.9)",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Inter",
            font_color="#000000",
            bordercolor="#E5E7EB"
        )
    )
    # Remove dark theme - use light theme
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🗺️ Hotspot Clusters")
    
    if len(clusters) > 0:
        cluster_states = clusters.group_by("state").agg(
            pl.col("high_mvi_count").first()
        ).sort("high_mvi_count", descending=True).to_pandas()
        
        st.dataframe(
            cluster_states.rename(columns={"state": "State", "high_mvi_count": "High-Pressure Districts"}),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown(styles.clean_html(f"""
        <div class="alert-card-warning">
            <strong>Cluster Alert:</strong><br/>
            {len(cluster_states)} states have clustered high-pressure regions requiring coordinated response.
        </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(styles.clean_html("""
        <div class="alert-card-success">
            <strong>No Clusters Detected:</strong><br/>
            High-pressure districts are geographically dispersed, allowing for localized interventions.
        </div>
        """), unsafe_allow_html=True)

# Use tabs for detailed breakdown
st.markdown("---")
st.markdown("### 📋 Detailed Zone Analysis")

tab1, tab2, tab3 = st.tabs([
    "🔴 High Pressure (MVI ≥ 30)",
    "🟠 Elevated (MVI 15-30)",
    "🟢 Stable (MVI < 5)"
])

def render_district_table(df, title_color, message):
    if len(df) > 0:
        display_df = df.select([
            "state", "district", "mvi", "confidence"
        ]).head(20).to_pandas()
        
        display_df.columns = ["State", "District", "MVI", "Confidence"]
        display_df["MVI"] = display_df["MVI"].round(2)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        if len(df) > 20:
            st.info(f"Showing top 20 of {len(df)} districts")
            
        st.markdown(styles.clean_html(f"""
        <div class="glass-card">
            <strong style="color: {title_color};">{message['title']}</strong><br/>
            <span style="color: #475569;">{message['body']}</span>
        </div>
        """), unsafe_allow_html=True)
    else:
        st.info("No districts found in this category.")

with tab1:
    high_pressure = mvi_df.filter(pl.col("mvi") >= 30).sort("mvi", descending=True)
    render_district_table(
        high_pressure, 
        "#DC2626", 
        {
            "title": "⚠️ Immediate Action Required",
            "body": f"These {len(high_pressure)} districts show rapid demographic change. Prioritize for electoral roll verification."
        }
    )

with tab2:
    elevated = mvi_df.filter((pl.col("mvi") >= 15) & (pl.col("mvi") < 30)).sort("mvi", descending=True)
    render_district_table(
        elevated, 
        "#EA580C", 
        {
            "title": "📊 Monitor Closely",
            "body": f"These {len(elevated)} districts show elevated activity. Prepare contingency plans."
        }
    )

with tab3:
    stable = mvi_df.filter(pl.col("mvi") < 5).sort("mvi", descending=False)
    render_district_table(
        stable, 
        "#16A34A", 
        {
            "title": "✓ Low Migration Activity",
            "body": f"These {len(stable)} districts show stable populations."
        }
    )

# NEW SECTION: State-Level Comparison Tool
st.markdown("---")
st.markdown("### 🔍 State Comparison Tool")
st.markdown("Compare migration stress metrics between two states side-by-side.")

compare_col1, compare_col2 = st.columns(2)

# Get unique states - filter out numeric-only values
if "state" in mvi_df.columns:
    all_states_raw = mvi_df.select("state").unique().to_series().to_list()
    # Filter out None, empty strings, and numeric-only values like "100000" or 100000
    all_states = []
    for s in all_states_raw:
        if s is None or s == "":
            continue
        # Convert to string and check
        s_str = str(s).strip()
        # Skip if empty after strip or if it's purely numeric
        if not s_str or s_str.isdigit():
            continue
        all_states.append(s_str)
    all_states = sorted(all_states)
    
    with compare_col1:
        state_a = st.selectbox("Select State A", all_states, key="state_a")
    
    with compare_col2:
        state_b = st.selectbox("Select State B", all_states, index=min(1, len(all_states)-1), key="state_b")
    
    if state_a and state_b:
        metric_col1, metric_col2 = st.columns(2)
        
        # State A metrics
        state_a_data = mvi_df.filter(pl.col("state") == state_a)
        state_a_avg_mvi = state_a_data.select("mvi").mean().item() if len(state_a_data) > 0 else 0
        state_a_districts = len(state_a_data)
        state_a_high = len(state_a_data.filter(pl.col("mvi") >= 30))
        
        with metric_col1:
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #3b82f6;">
                <h4 style="color: #1f2937; margin-top: 0;">{state_a}</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">Districts</div>
                        <div style="color: #000000; font-size: 1.5rem; font-weight: 700;">{state_a_districts}</div>
                    </div>
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">Avg MVI</div>
                        <div style="color: #000000; font-size: 1.5rem; font-weight: 700;">{state_a_avg_mvi:.2f}</div>
                    </div>
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">High Pressure</div>
                        <div style="color: #dc2626; font-size: 1.5rem; font-weight: 700;">{state_a_high}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # State B metrics
        state_b_data = mvi_df.filter(pl.col("state") == state_b)
        state_b_avg_mvi = state_b_data.select("mvi").mean().item() if len(state_b_data) > 0 else 0
        state_b_districts = len(state_b_data)
        state_b_high = len(state_b_data.filter(pl.col("mvi") >= 30))
        
        with metric_col2:
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; border-left: 4px solid #10b981;">
                <h4 style="color: #1f2937; margin-top: 0;">{state_b}</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">Districts</div>
                        <div style="color: #000000; font-size: 1.5rem; font-weight: 700;">{state_b_districts}</div>
                    </div>
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">Avg MVI</div>
                        <div style="color: #000000; font-size: 1.5rem; font-weight: 700;">{state_b_avg_mvi:.2f}</div>
                    </div>
                    <div>
                        <div style="color: #6b7280; font-size: 0.875rem;">High Pressure</div>
                        <div style="color: #dc2626; font-size: 1.5rem; font-weight: 700;">{state_b_high}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Winner indication
        if state_a_avg_mvi > state_b_avg_mvi:
            st.warning(f"⚠️ **{state_a}** has higher average migration pressure than {state_b}")
        elif state_b_avg_mvi > state_a_avg_mvi:
            st.warning(f"⚠️ **{state_b}** has higher average migration pressure than {state_a}")
        else:
            st.info("Both states have similar migration pressure levels")

# NEW SECTION: State-Level Heatmap
st.markdown("---")
st.markdown("### 🗺️ State-Level MVI Heatmap")
st.markdown("Overview of migration pressure across all states.")

if "state" in mvi_df.columns:
    import plotly.graph_objects as go
    
    # Aggregate by state
    state_summary = mvi_df.group_by("state").agg([
        pl.col("mvi").mean().alias("avg_mvi"),
        pl.count().alias("district_count"),
        (pl.col("mvi") >= 30).sum().alias("high_pressure_count")
    ]).sort("avg_mvi", descending=True)
    
    # Create heatmap-style bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=state_summary.select("state").to_series().to_list(),
        x=state_summary.select("avg_mvi").to_series().to_list(),
        orientation='h',
        marker=dict(
            color=state_summary.select("avg_mvi").to_series().to_list(),
            colorscale=[
                [0, "#10b981"],      # Green (low)
                [0.3, "#f59e0b"],    # Yellow (moderate)
                [0.6, "#ea580c"],    # Orange (elevated)
                [1, "#dc2626"]       # Red (high)
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text="Avg MVI", font=dict(color="#000000")),
                tickfont=dict(color="#000000")
            )
        ),
        text=state_summary.select("avg_mvi").to_series().to_list(),
        texttemplate="%{text:.1f}",
        textposition="outside",
        textfont=dict(color="#000000")
    ))
    
    fig.update_layout(
        title=dict(text="Average MVI by State", font=dict(color="#000000")),
        xaxis=dict(title=dict(text="Average MVI", font=dict(color="#000000")), tickfont=dict(color="#000000")),
        yaxis=dict(tickfont=dict(color="#000000"), autorange="reversed"),
        height=max(400, len(state_summary) * 25),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=150, r=50, t=50, b=50),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Inter",
            font_color="#000000",
            bordercolor="#E5E7EB"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("💡 Tip: Focus on high-pressure zones for immediate intervention. Monitor elevated zones for emerging patterns.")

