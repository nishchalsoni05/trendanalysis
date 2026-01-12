"""
Aadhaar Sanket - Policy Insights Page

Plain-language interpretation for governance decisions.
No equations or ML jargon - just actionable insights.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Policy Insights | Aadhaar Sanket",
    page_icon="📋",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.markdown("# 📋 Policy Insights")
st.markdown("Plain-language interpretation for governance decisions")

st.markdown("---")

try:
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base, generate_mvi_summary
    from src.engines.spatial import add_zone_classification, aggregate_by_state, detect_hotspot_clusters
    from src.engines.anomaly import detect_mvi_anomalies, generate_anomaly_report
    import polars as pl
    
    # Load data
    demographic_df = load_processed_dataset("demographic")
    enrolment_df = load_processed_dataset("enrolment")
    
    demographic_df = apply_signal_weights(demographic_df, "demographic")
    population_df = calculate_population_base(enrolment_df, "district")
    mvi_df = calculate_mvi(demographic_df, population_df, "district")
    mvi_df = add_zone_classification(mvi_df)
    mvi_df = detect_hotspot_clusters(mvi_df)
    
    mvi_summary = generate_mvi_summary(mvi_df)
    anomaly_df = detect_mvi_anomalies(mvi_df)
    anomaly_report = generate_anomaly_report(anomaly_df)
    
    # Executive Summary
    st.markdown("## Executive Summary")
    
    high_pressure = mvi_summary['interpretation']['high_pressure_count']
    elevated = mvi_summary['interpretation']['attention_needed'] - high_pressure
    total = mvi_summary['total_units']
    
    st.markdown(f"""
    Based on analysis of **{total}** districts across India:
    
    - **{high_pressure}** districts show **high demographic pressure** requiring immediate attention
    - **{elevated}** districts show **elevated activity** requiring monitoring
    - Overall migration velocity is {'above normal' if mvi_summary['mvi_statistics']['mean'] > 15 else 'within normal range'}
    """)
    
    # Key Insights by Policy Domain
    st.markdown("---")
    st.markdown("## Key Insights by Policy Domain")
    
    tab1, tab2, tab3 = st.tabs(["🗳️ Electoral Preparedness", "🏙️ Urban Planning", "📊 Census Validation"])
    
    with tab1:
        st.markdown("### Electoral Preparedness Insights")
        
        st.markdown("""
        **Key Findings:**
        
        1. **Voter Roll Updates**: Districts with high MVI may have significant population changes since the last electoral roll update.
        
        2. **Booth Planning**: High-inflow areas may need additional polling booths to accommodate new residents.
        
        3. **Verification Priority**: Focus verification efforts on districts showing anomalous demographic patterns.
        """)
        
        # Show high MVI districts
        high_mvi = mvi_df.filter(pl.col("mvi") >= 30).sort("mvi", descending=True)
        
        if len(high_mvi) > 0:
            st.warning(f"⚠️ {len(high_mvi)} districts require electoral roll review")
            
            with st.expander("View Priority Districts"):
                st.dataframe(
                    high_mvi.select(["state", "district", "mvi"]).head(10).to_pandas(),
                    hide_index=True
                )
    
    with tab2:
        st.markdown("### Urban Planning Insights")
        
        st.markdown("""
        **Key Findings:**
        
        1. **Infrastructure Stress**: High-inflow areas may experience strain on water, electricity, and transport.
        
        2. **Housing Demand**: Elevated migration signals suggest increased housing demand in these areas.
        
        3. **Service Delivery**: Municipal services may need capacity expansion in high-pressure zones.
        """)
        
        # State-level summary
        state_df = aggregate_by_state(mvi_df)
        top_states = state_df.sort("mvi", descending=True).head(5)
        
        st.markdown("**Top 5 States by Migration Pressure:**")
        for i, row in enumerate(top_states.to_dicts(), 1):
            st.write(f"{i}. {row['state']} - Urban planning attention recommended")
    
    with tab3:
        st.markdown("### Census Validation Insights")
        
        st.markdown("""
        **Key Findings:**
        
        1. **Population Estimates**: Current Aadhaar data suggests significant population redistribution since Census 2011.
        
        2. **Validation Points**: Districts with high demographic churn may show larger discrepancies in census verification.
        
        3. **Enumeration Planning**: Allocate additional census resources to high-turnover areas.
        """)
        
        # Summary statistics
        mean_mvi = mvi_summary['mvi_statistics']['mean']
        
        if mean_mvi > 20:
            st.warning("⚠️ High overall migration activity suggests significant population redistribution since Census 2011")
        elif mean_mvi > 10:
            st.info("ℹ️ Moderate migration activity - standard census validation procedures recommended")
        else:
            st.success("✓ Low migration activity - population distribution relatively stable")
    
    # Recommendations
    st.markdown("---")
    st.markdown("## Recommended Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Immediate Actions")
        st.markdown("""
        1. Review electoral rolls in high-pressure districts
        2. Assess infrastructure capacity in high-inflow areas
        3. Investigate anomalous patterns for data quality issues
        """)
    
    with col2:
        st.markdown("### Medium-Term Actions")
        st.markdown("""
        1. Update population projections for high-MVI regions
        2. Coordinate with state governments on urban expansion
        3. Plan census enumeration resources accordingly
        """)
    
    # Data Quality Note
    st.markdown("---")
    st.info("""
    **Data Quality Note**: This analysis is based on aggregated, anonymized Aadhaar update data. 
    All insights are directional indicators and should be validated with ground-truth verification 
    before policy implementation.
    """)

except FileNotFoundError:
    st.warning("⚠️ Data not yet processed. Run the pipeline first.")
except Exception as e:
    st.error(f"Error: {e}")
