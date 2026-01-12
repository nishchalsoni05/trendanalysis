"""
Aadhaar Sanket - Policy Insights Page

Plain-language interpretation for governance decisions.
No equations or ML jargon - just actionable insights.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Policy & Decision Insights | Aadhaar Sanket",
    page_icon="⚖️",
    layout="wide",
)

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
        "Policy & Decision Insights",
        "Plain-language interpretation for governance decisions"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

@st.cache_data(show_spinner="Generating policy insights...")
def load_policy_data():
    """Load and process policy-relevant data with caching."""
    try:
        from src.engines.ingestion import load_processed_dataset
        from src.engines.signal_separation import apply_signal_weights
        from src.engines.mvi import calculate_mvi, calculate_population_base, generate_mvi_summary
        from src.engines.spatial import add_zone_classification, aggregate_by_state, detect_hotspot_clusters
        from src.engines.anomaly import detect_mvi_anomalies, generate_anomaly_report
        import polars as pl
        
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
        
        return mvi_df, mvi_summary, anomaly_report, True
    except Exception as e:
        return None, None, None, False

# Load data
mvi_df, mvi_summary, anomaly_report, data_available = load_policy_data()

if not data_available:
    st.markdown(styles.clean_html("""
    <div class="alert-card-warning">
        <strong>⚠️ Data Not Processed</strong><br>
        Please run the data pipeline to generate policy insights.
    </div>
    """), unsafe_allow_html=True)
    st.info("Run: `python run_pipeline.py`")
    st.stop()

import polars as pl

# Executive Summary
st.markdown("## 📊 Executive Summary")

high_pressure = mvi_summary['interpretation']['high_pressure_count']
elevated = mvi_summary['interpretation']['attention_needed'] - high_pressure
total = mvi_summary['total_units']
avg_mvi = mvi_summary['mvi_statistics']['mean']

# Create executive summary card using Saffron/Navy/Ivory theme
# Using "alert-info" style generic container or custom glass card
st.markdown(styles.clean_html(f"""
<div class="glass-card">
    <p style="color: #334155; font-size: 1rem; line-height: 1.8;">
    Based on analysis of <strong style="color: #0F172A;">{total}</strong> districts across India:
    </p>
    <ul style="color: #475569; font-size: 0.95rem; line-height: 1.8;">
        <li><span style="color: #DC2626; font-weight: 700;">{high_pressure} districts</span> show <strong>high demographic pressure</strong> requiring immediate attention</li>
        <li><span style="color: #EA580C; font-weight: 700;">{elevated} districts</span> show <strong>elevated activity</strong> requiring monitoring</li>
        <li>Overall migration velocity is <strong>{'above normal' if avg_mvi > 15 else 'within normal range'}</strong> (Average MVI: {avg_mvi:.1f})</li>
    </ul>
</div>
"""), unsafe_allow_html=True)

# Key Insights by Policy Domain
st.markdown("---")
st.markdown("## 🎯 Key Insights by Policy Domain")

tab1, tab2, tab3 = st.tabs(["🗳️ Electoral", "🏙️ Urban Planning", "📊 Census"])

with tab1:
    st.markdown("### Electoral Preparedness Insights")
    
    st.markdown(styles.render_insight_card(
        "How does migration affect electoral preparedness?",
        f"{high_pressure} districts show high population churn and may have significant changes since the last electoral roll update. High-inflow areas may also need additional polling booths to accommodate new residents.",
        "Prioritize electoral roll verification in high-MVI districts. Allocate additional booth planning resources for high-inflow areas. Cross-reference with local voter registration data.",
        "🗳️"
    ), unsafe_allow_html=True)
    
    # Show high MVI districts table
    high_mvi = mvi_df.filter(pl.col("mvi") >= 30).sort("mvi", descending=True)
    
    if len(high_mvi) > 0:
        st.markdown(f"**{len(high_mvi)} districts require electoral roll review:**")
        
        with st.expander("View Priority Districts"):
            # Limit to 10 for performance
            display_df = high_mvi.select([
                "state", "district", "mvi"
            ]).head(10).to_pandas()
            
            display_df.columns = ["State", "District", "MVI"]
            display_df["MVI"] = display_df["MVI"].round(2)
            
            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True
            )
            
            if len(high_mvi) > 10:
                st.info(f"+ {len(high_mvi) - 10} more districts")

with tab2:
    st.markdown("### Urban Planning Insights")
    
    st.markdown(styles.render_insight_card(
        "Which areas need infrastructure attention?",
        f"{elevated} districts show elevated migration signals, indicating potential strain on water, electricity, transport, and housing. High-inflow areas may experience increased demand for municipal services.",
        "Assess infrastructure capacity in high-pressure zones. Plan housing expansion in districts with sustained high MVI. Coordinate with municipal bodies for service capacity planning.",
        "🏙️"
    ), unsafe_allow_html=True)
    
    # State-level summary
    from src.engines.spatial import aggregate_by_state
    state_df = aggregate_by_state(mvi_df)
    top_states = state_df.sort("mvi", descending=True).head(5)
    
    st.markdown("**Top 5 States by Migration Pressure:**")
    for i, row in enumerate(top_states.to_dicts(), 1):
        state_name = row['state']
        state_mvi = row['mvi']
        if state_mvi >= 30:
            badge = styles.render_badge(f"MVI {state_mvi:.1f}", "high")
        elif state_mvi >= 15:
            badge = styles.render_badge(f"MVI {state_mvi:.1f}", "elevated")
        else:
            badge = styles.render_badge(f"MVI {state_mvi:.1f}", "moderate")
        
        st.markdown(f"{i}. **{state_name}** {badge} - Urban planning attention recommended", unsafe_allow_html=True)

with tab3:
    st.markdown("### Census Validation Insights")
    
    st.markdown(styles.render_insight_card(
        "How does this help with census planning?",
        f"Average MVI of {avg_mvi:.1f} suggests {'significant' if avg_mvi > 20 else 'moderate' if avg_mvi > 10 else 'minimal'} population redistribution since Census 2011. High-MVI districts may show larger discrepancies in census verification.",
        "Allocate additional enumeration resources to high-turnover areas. Use MVI trends to validate population projection models. Plan for intensive verification in high-MVI districts.",
        "📊"
    ), unsafe_allow_html=True)
    
    # Summary assessment
    if avg_mvi > 20:
        st.markdown(styles.clean_html("""
        <div class="alert-card-warning">
            <strong>⚠️ High Overall Migration Activity</strong><br/>
            Significant population redistribution since Census 2011. Recommend intensive census verification procedures.
        </div>
        """), unsafe_allow_html=True)
    elif avg_mvi > 10:
        st.markdown(styles.clean_html("""
        <div class="alert-card-info">
            <strong>ℹ️ Moderate Migration Activity</strong><br/>
            Standard census validation procedures recommended with additional attention to high-MVI districts.
        </div>
        """), unsafe_allow_html=True)
    else:
        st.markdown(styles.clean_html("""
        <div class="alert-card-success">
            <strong>✓ Low Migration Activity</strong><br/>
            Population distribution relatively stable. Standard census procedures should be sufficient.
        </div>
        """), unsafe_allow_html=True)

# Recommendations
st.markdown("---")
st.markdown("## ✅ Recommended Actions")

col1, col2 = st.columns(2)

with col1:
    st.markdown(styles.clean_html("""
    <div class="glass-card">
        <h4 style="color: #991B1B; margin-top: 0;">⚡ Immediate Actions</h4>
        <ul style="color: #334155; line-height: 1.8;">
            <li>Review electoral rolls in high-pressure districts</li>
            <li>Assess infrastructure capacity in high-inflow areas</li>
            <li>Investigate anomalous patterns for data quality issues</li>
            <li>Cross-reference findings with local administrators</li>
        </ul>
    </div>
    """), unsafe_allow_html=True)

with col2:
    st.markdown(styles.clean_html("""
    <div class="glass-card">
        <h4 style="color: #9A3412; margin-top: 0;">📅 Medium-Term Actions</h4>
        <ul style="color: #334155; line-height: 1.8;">
            <li>Update population projections for high-MVI regions</li>
            <li>Coordinate with state governments on urban expansion</li>
            <li>Plan census enumeration resources accordingly</li>
            <li>Monitor elevated zones for emerging trends</li>
        </ul>
    </div>
    """), unsafe_allow_html=True)

# Data Quality Note
st.markdown("---")
st.markdown(styles.clean_html("""
<div class="alert-card-info">
    <strong>📌 Data Quality Note</strong><br/>
    This analysis is based on aggregated, anonymized Aadhaar update data. 
    All insights are directional indicators and should be validated with ground-truth verification 
    before policy implementation. Use confidence levels to prioritize investigations.
</div>
"""), unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 Tip: Share these insights with relevant departments. Each policy domain requires coordination across multiple government levels.")
