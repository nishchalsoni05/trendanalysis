"""
Aadhaar Sanket - Migration & Stability Map Page

Interactive geographic visualization of migration patterns.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Migration Map | Aadhaar Sanket",
    page_icon="🗺️",
    layout="wide",
)

# Add project path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.markdown("# 🗺️ Migration & Stability Map")
st.markdown("Interactive visualization of migration patterns across India")

st.markdown("---")

# Try to load data
try:
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base
    from src.engines.spatial import add_zone_classification, aggregate_by_state
    
    demographic_df = load_processed_dataset("demographic")
    enrolment_df = load_processed_dataset("enrolment")
    
    demographic_df = apply_signal_weights(demographic_df, "demographic")
    population_df = calculate_population_base(enrolment_df, "district")
    mvi_df = calculate_mvi(demographic_df, population_df, "district")
    mvi_df = add_zone_classification(mvi_df)
    
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
            import polars as pl
            filtered_df = filtered_df.filter(pl.col("zone_type").is_in(zone_filter))
        
        st.markdown(f"**Showing {len(filtered_df)} districts**")
        
        # Display as table with color coding
        display_df = filtered_df.select([
            "state", "district", "mvi", "mvi_band", "zone_type", "confidence"
        ]).sort("mvi", descending=True).to_pandas()
        
        # Color code by band
        def highlight_mvi(val):
            if val == "High Pressure":
                return "background-color: #fef2f2; color: #ef4444"
            elif val == "Elevated":
                return "background-color: #fff7ed; color: #f97316"
            elif val == "Moderate":
                return "background-color: #fefce8; color: #eab308"
            else:
                return "background-color: #f0fdf4; color: #22c55e"
        
        styled_df = display_df.style.applymap(
            highlight_mvi, subset=["mvi_band"]
        )
        
        st.dataframe(styled_df, use_container_width=True, height=500)

except ImportError as e:
    st.warning(f"⚠️ Required modules not available: {e}")
    st.info("Run the pipeline first: `python run_pipeline.py`")

except FileNotFoundError:
    st.warning("⚠️ Data not yet processed.")
    st.info("Run the data pipeline first: `python run_pipeline.py`")
    
    st.markdown("### Map Preview (Demo)")
    st.info("Interactive map will appear after data processing")

except Exception as e:
    st.error(f"Error loading data: {e}")
