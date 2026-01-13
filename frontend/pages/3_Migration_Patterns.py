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

if "loader_shown_P3" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("LOADING MAP TILES", "Vectorizing district boundaries..."),
        ("CALCULATING FLOW VECTORS", "Analyzing migration paths..."),
        ("READY", "Rendering geospatial layers...")
    ])
    st.session_state["loader_shown_P3"] = True

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
        "Migration & Stability Map",
        "Interactive visualization of migration patterns across India"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

# Cache data loading for performance
@st.cache_data(show_spinner="Loading migration data...")
def load_migration_data():
    """Load pre-calculated migration analytics."""
    try:
        from src.engines.ingestion import load_processed_dataset
        import polars as pl
        
        # Load verified backend outputs
        # Primary: Trend Typology (contains MVI, zone_type, confidence)
        typology_df = load_processed_dataset("trend_typology")
        
        # Secondary: Seasonality (for improved filtering)
        try:
            seasonality_df = load_processed_dataset("seasonality")
            # Join seasonality info if needed, or just return both
        except:
            seasonality_df = None
            
        if "mean_mvi" in typology_df.columns:
            typology_df = typology_df.rename({"mean_mvi": "mvi"})
            
        return typology_df, seasonality_df, True
    except Exception as e:
        return None, None, False

# Load data
mvi_df, seasonality_df, data_available = load_migration_data()

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
if "state" in mvi_df.columns:
    states = sorted(mvi_df.select("state").unique().to_series().to_list())
else:
    states = []

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("### 🔍 Filters")
    
    # Custom CSS to fix dropdown visibility
    st.markdown("""
    <style>
    /* Fix selectbox and multiselect styling */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #1e293b !important;
        color: white !important;
    }
    /* Make labels dark/black for visibility on light sidebar */
    .stSelectbox label, .stMultiSelect label, .stSlider label {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border-color: #475569 !important;
    }
    div[data-baseweb="select"] span {
        color: white !important;
    }
    /* Dropdown menu items */
    ul[role="listbox"] {
        background-color: #1e293b !important;
    }
    ul[role="listbox"] li {
        color: white !important;
    }
    ul[role="listbox"] li:hover {
        background-color: #334155 !important;
    }
    /* Section headers in sidebar */
    .stMarkdown h4 {
        color: #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    state_list = states if states else ["All"]
    selected_state = st.selectbox(
        "🗺️ Select State", 
        ["All States"] + (state_list if "All" not in state_list else []),
        help="Filter districts by state"
    )
    
    mvi_range = st.slider(
        "📊 MVI Range",
        min_value=0.0,
        max_value=float(mvi_df.select("mvi").max().item()),
        value=(0.0, float(mvi_df.select("mvi").max().item())),
        help="Migration Velocity Index filter"
    )
    
    # Get actual trend types from data
    if "trend_type" in mvi_df.columns:
        available_trend_types = sorted(mvi_df.select("trend_type").unique().to_series().to_list())
    else:
        available_trend_types = []
    
    # Enhanced trend type filter
    zone_filter = st.multiselect(
        "📈 Trend Classification",
        available_trend_types if available_trend_types else ["structural", "seasonal", "cyclical", "volatile", "stable"],
        default=available_trend_types if available_trend_types else [],
        help="Filter by migration trend type"
    )
    
    # Additional MVI Band filter
    st.markdown("#### 🎯 MVI Classification")
    band_options = {
        "🟢 Stable (< 5)": (0, 5),
        "🟡 Moderate (5-15)": (5, 15),
        "🟠 Elevated (15-30)": (15, 30),
        "🔴 High Pressure (30+)": (30, 9999)
    }
    
    selected_bands = st.multiselect(
        "Quick Filter by MVI Band",
        list(band_options.keys()),
        default=[],
        help="Select predefined MVI ranges"
    )
    
    # Confidence filter if available
    if "confidence" in mvi_df.columns:
        available_confidence = sorted(mvi_df.select("confidence").unique().to_series().to_list())
        confidence_filter = st.multiselect(
            "🎖️ Data Confidence",
            available_confidence,
            default=[],
            help="Filter by statistical confidence level"
        )

with col2:
    # Apply filters
    filtered_df = mvi_df
    
    # Ensure state/district exist (if only geo_key is present)
    if "state" not in filtered_df.columns and "geo_key" in filtered_df.columns:
        # Assuming geo_key is "District_State" or similar? 
        # Actually pipeline usually works with specific grains. 
        # If needed, we can extract or just rely on what's there.
        # Let's try to extract if possible, or skip state filter if missing.
        pass

    if "state" in filtered_df.columns:
        if selected_state != "All States":
            filtered_df = filtered_df.filter(pl.col("state") == selected_state)
    
    # Apply MVI range filter from slider
    if "mvi" in filtered_df.columns:
        filtered_df = filtered_df.filter(
            (pl.col("mvi") >= mvi_range[0]) & 
            (pl.col("mvi") <= mvi_range[1])
        )
    
    # Apply MVI band quick filter (overrides slider if selected)
    if selected_bands and "mvi" in filtered_df.columns:
        band_conditions = []
        for band_name in selected_bands:
            min_val, max_val = band_options[band_name]
            band_conditions.append(
                (pl.col("mvi") >= min_val) & (pl.col("mvi") < max_val)
            )
        # Combine with OR (any selected band matches)
        if band_conditions:
            combined_filter = band_conditions[0]
            for cond in band_conditions[1:]:
                combined_filter = combined_filter | cond
            filtered_df = filtered_df.filter(combined_filter)
    
    # Map 'trend_type' to zone filter if 'zone_type' is missing
    type_col = "zone_type" if "zone_type" in filtered_df.columns else "trend_type"
    
    if zone_filter and type_col in filtered_df.columns:
        filtered_df = filtered_df.filter(pl.col(type_col).is_in(zone_filter))
    
    # Apply confidence filter if selected
    if "confidence" in mvi_df.columns and "confidence_filter" in dir() and confidence_filter:
        filtered_df = filtered_df.filter(pl.col("confidence").is_in(confidence_filter))
    
    st.markdown(f"**Showing {len(filtered_df)} districts**")
    
    # Use tabs for better organization
    tab1, tab2 = st.tabs(["📊 Data Table", "📈 Summary Stats"])
    
    with tab1:
        # Display as table with color coding - PAGINATED to 30 rows
        if len(filtered_df) > 0:
            # Select available columns dynamically
            cols_to_show = ["state", "district", "mvi", "trend_type", "confidence"]
            available_cols = [c for c in cols_to_show if c in filtered_df.columns]
            
            # If state/district missing, show geo_key
            if "district" not in available_cols:
                available_cols = ["geo_key"] + [c for c in available_cols if c not in ["state", "district"]]
            
            display_df = filtered_df.select(available_cols).sort("mvi", descending=True).head(30).to_pandas()
            
            # Format visual dataframe
            display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
            if "Mvi" in display_df.columns:
                display_df["Mvi"] = display_df["Mvi"].round(2)
            
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
                # Use geo_key if district not available
                geo_col = "district" if "district" in filtered_df.columns else "geo_key"
                max_location = filtered_df.filter(pl.col("mvi") == max_mvi).select(geo_col).item()
                drill_down.render_metric_button(
                    value=f"{max_mvi:.2f}",
                    label=f"Max MVI ({max_location})",
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
            # Zone type distribution
            st.markdown("### Zone Distribution by Type")
            
            # Use trend_type column (zone_type doesn't exist)
            type_col = "trend_type" if "trend_type" in filtered_df.columns else "zone_type"
            zone_counts = filtered_df.group_by(type_col).len().to_pandas()
            
            cols = st.columns(len(zone_counts)) if len(zone_counts) > 0 else [st.container()]
            
            for idx, row in zone_counts.iterrows():
                zone = row[type_col]
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
                    <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; color: #000000;">
                        {badge}<br>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #0f172a; margin-top: 0.5rem;">{count}</div>
                        <div style="color: #64748b; font-size: 0.8rem;">{pct:.1f}%</div>
                    </div>
                    """), unsafe_allow_html=True)

        else:
            st.warning("No data to display summary statistics.")

st.markdown("---")
st.caption("💡 Tip: Use filters to focus on specific states or MVI ranges. High-pressure zones (red) require immediate attention.")
