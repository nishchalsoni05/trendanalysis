"""
Aadhaar Sanket - Migration & Stability Map Page

Interactive geographic visualization of migration patterns.
"""
import streamlit as st
from pathlib import Path
import sys
import polars as pl

st.set_page_config(
    page_title="Migration Patterns | Aadhaar Sanket",
    page_icon="🗺️",
    layout="wide",
)

# Add project path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles
import frontend.drill_down as drill_down

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

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
        "Migration & Stability Map",
        "Interactive visualization of migration patterns across India"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

# Cache data loading for performance
@st.cache_data(show_spinner="Loading migration data...")
def load_migration_data():
    """Load and process migration data with caching."""
    try:
        from src.engines.ingestion import load_processed_dataset
        from src.engines.signal_separation import apply_signal_weights
        from src.engines.mvi import calculate_mvi, calculate_population_base
        from src.engines.spatial import add_zone_classification
        
        demographic_df = load_processed_dataset("demographic")
        enrolment_df = load_processed_dataset("enrolment")
        
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        population_df = calculate_population_base(enrolment_df, "district")
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        mvi_df = add_zone_classification(mvi_df)
        
        return mvi_df, True
    except Exception as e:
        return None, False

# Load data
mvi_df, data_available = load_migration_data()

if not data_available:
    st.markdown(styles.clean_html("""
    <div class="alert-card-warning">
        <strong>⚠️ Data Not Processed</strong><br>
        Please run the data pipeline to generate migration insights.
        <br><br>
        <code>python run_pipeline.py</code>
    </div>
    """), unsafe_allow_html=True)
    st.info("Or go to the **Data Upload** page to ingest new data.")
    st.stop()

# 4-PART VISUAL STORYTELLING
st.markdown(styles.render_insight_card(
    "Where is migration pressure highest?",
    f"Analyzing {len(mvi_df)} districts. Use filters to identify high-pressure zones (MVI ≥ 30) requiring immediate intervention.",
    "Prioritize electoral roll verification and service capacity planning in identified high-inflow districts.",
    "🗺️"
), unsafe_allow_html=True)

st.markdown("---")

# State selection
states = sorted(mvi_df.select("state").unique().to_series().to_list())

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 🔍 Filters")
    
    selected_state = st.selectbox("Select State", ["All States"] + states)
    
    mvi_range = st.slider(
        "MVI Range",
        min_value=0.0,
        max_value=float(mvi_df.select("mvi").max().item()),
        value=(0.0, float(mvi_df.select("mvi").max().item()))
    )
    
    zone_filter = st.multiselect(
        "Zone Type",
        ["high_inflow", "moderate_inflow", "stable", "decline"],
        default=["high_inflow", "moderate_inflow", "stable"]
    )

with col2:
    # Apply filters
    filtered_df = mvi_df
    
    if selected_state != "All States":
        filtered_df = filtered_df.filter(pl.col("state") == selected_state)
    
    filtered_df = filtered_df.filter(
        (pl.col("mvi") >= mvi_range[0]) & 
        (pl.col("mvi") <= mvi_range[1])
    )
    
    if zone_filter:
        filtered_df = filtered_df.filter(pl.col("zone_type").is_in(zone_filter))
    
    st.markdown(f"**Showing {len(filtered_df)} districts**")
    
    # Use tabs for better organization
    tab1, tab2 = st.tabs(["📊 Data Table", "📈 Summary Stats"])
    
    with tab1:
        # Display as table with color coding - PAGINATED to 30 rows
        if len(filtered_df) > 0:
            display_df = filtered_df.select([
                "state", "district", "mvi", "mvi_band", "zone_type", "confidence"
            ]).sort("mvi", descending=True).head(30).to_pandas()
            
            # Format visual dataframe
            display_df.columns = ["State", "District", "MVI", "Classification", "Zone Type", "Confidence"]
            display_df["MVI"] = display_df["MVI"].round(2)
            
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=500, 
                hide_index=True
            )
            
            if len(filtered_df) > 30:
                st.info(f"Showing top 30 of {len(filtered_df)} districts. Use filters to narrow down.")
        else:
            st.warning("No districts match the current filter criteria.")
    
    with tab2:
        if len(filtered_df) > 0:
            # Summary statistics - CLICKABLE
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                avg_mvi = filtered_df.select("mvi").mean().item()
                drill_down.render_metric_button(
                    value=f"{avg_mvi:.2f}",
                    label="Average MVI (Filtered)",
                    metric_id="avg_mvi_filtered",
                    params={"state": selected_state if selected_state != "All States" else None},
                    trend="↑" if avg_mvi > 15 else "→",
                    trend_direction="up" if avg_mvi > 15 else "neutral"
                )
            
            with col_b:
                max_mvi = filtered_df.select("mvi").max().item()
                max_district = filtered_df.filter(pl.col("mvi") == max_mvi).select("district").item()
                drill_down.render_metric_button(
                    value=f"{max_mvi:.2f}",
                    label=f"Max MVI ({max_district})",
                    metric_id="max_mvi_filtered",
                    trend="High Pressure",
                    trend_direction="down"
                )
            
            with col_c:
                high_count = len(filtered_df.filter(pl.col("mvi") >= 30))
                drill_down.render_metric_button(
                    value=f"{high_count}",
                    label="High Pressure Zones",
                    metric_id="high_pressure_filtered",
                    params={"mvi_min": 30},
                    trend_direction="down" if high_count > 0 else "neutral"
                )
            
            # Zone distribution
            st.markdown("---")
            st.markdown("### Zone Distribution")
            zone_counts = filtered_df.group_by("zone_type").len().to_pandas()
            
            cols = st.columns(len(zone_counts)) if len(zone_counts) > 0 else [st.container()]
            
            for idx, row in zone_counts.iterrows():
                zone = row["zone_type"]
                count = row["len"]
                pct = (count / len(filtered_df)) * 100
                
                if zone == "high_inflow":
                    badge = styles.render_badge("High Inflow", "high")
                elif zone == "moderate_inflow":
                    badge = styles.render_badge("Moderate", "moderate")
                elif zone == "stable":
                    badge = styles.render_badge("Stable", "stable")
                else:
                    badge = styles.render_badge("Decline", "info")
                
                with cols[idx % 4]:
                    st.markdown(styles.clean_html(f"""
                    <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0;">
                        {badge}<br>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 0.5rem;">{count}</div>
                        <div style="color: #64748b; font-size: 0.8rem;">{pct:.1f}%</div>
                    </div>
                    """), unsafe_allow_html=True)

        else:
            st.warning("No data to display summary statistics.")

st.markdown("---")
st.caption("💡 Tip: Use filters to focus on specific states or MVI ranges. High-pressure zones (red) require immediate attention.")
