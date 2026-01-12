"""
Aadhaar Sanket - Spatial Stress & Hotspots Page

Zone classification and cluster detection visualization.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Spatial Stress | Aadhaar Sanket",
    page_icon="🔥",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.markdown("# 🔥 Spatial Stress & Hotspots")
st.markdown("Identify areas under demographic pressure and emerging clusters")

st.markdown("---")

try:
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base
    from src.engines.spatial import add_zone_classification, detect_hotspot_clusters, aggregate_by_state
    import polars as pl
    import plotly.express as px
    
    # Load and process data
    demographic_df = load_processed_dataset("demographic")
    enrolment_df = load_processed_dataset("enrolment")
    
    demographic_df = apply_signal_weights(demographic_df, "demographic")
    population_df = calculate_population_base(enrolment_df, "district")
    mvi_df = calculate_mvi(demographic_df, population_df, "district")
    mvi_df = add_zone_classification(mvi_df)
    mvi_df = detect_hotspot_clusters(mvi_df)
    
    # Zone summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Zone Distribution")
        
        zone_counts = mvi_df.group_by("zone_type").count().to_pandas()
        
        color_map = {
            "high_inflow": "#ef4444",
            "moderate_inflow": "#f97316",
            "stable": "#22c55e",
            "decline": "#6366f1",
        }
        
        fig = px.pie(
            zone_counts,
            values="count",
            names="zone_type",
            color="zone_type",
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Hotspot Clusters")
        
        clusters = mvi_df.filter(pl.col("is_cluster") == True)
        
        if len(clusters) > 0:
            cluster_states = clusters.group_by("state").agg(
                pl.col("high_mvi_count").first()
            ).sort("high_mvi_count", descending=True).to_pandas()
            
            st.dataframe(cluster_states, use_container_width=True, hide_index=True)
            
            st.warning(f"⚠️ {len(cluster_states)} states have clustered high-pressure regions")
        else:
            st.success("✓ No significant hotspot clusters detected")
    
    # Detailed breakdown
    st.markdown("---")
    st.markdown("### High Pressure Zones (MVI > 30)")
    
    high_pressure = mvi_df.filter(pl.col("mvi") >= 30).sort("mvi", descending=True)
    
    if len(high_pressure) > 0:
        st.dataframe(
            high_pressure.select(["state", "district", "mvi", "confidence"]).to_pandas(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No districts currently in high-pressure zone")
    
    st.markdown("### Elevated Zones (MVI 15-30)")
    
    elevated = mvi_df.filter(
        (pl.col("mvi") >= 15) & (pl.col("mvi") < 30)
    ).sort("mvi", descending=True)
    
    if len(elevated) > 0:
        st.dataframe(
            elevated.select(["state", "district", "mvi", "confidence"]).head(20).to_pandas(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No districts in elevated zone")

except FileNotFoundError:
    st.warning("⚠️ Data not yet processed. Run the pipeline first.")
except Exception as e:
    st.error(f"Error: {e}")
