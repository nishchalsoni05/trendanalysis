"""
Project Aadhaar Sanket - National Overview Dashboard
Professional Light Glassmorphic Design
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="National Overview | Aadhaar Sanket",
    page_icon="🇮🇳",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import frontend.styles as styles
import frontend.drill_down as drill_down

st.markdown(styles.get_global_css(), unsafe_allow_html=True)
drill_down.init_navigation()

def render_sidebar():
    """Render sidebar with trust panel."""
    with st.sidebar:
        try:
            from src.engines.metadata_tracker import MetadataTracker
            metadata = MetadataTracker.load()
            summary = metadata.get("summary", {})
            trust_metrics = {
                "last_updated": summary.get("run_timestamp", "Pending Data"),
                "source": "UIDAI Official Data"
            }
        except:
            trust_metrics = {"last_updated": "Pending Data", "source": "UIDAI Official Data"}
        
        st.markdown(styles.render_trust_panel(**trust_metrics), unsafe_allow_html=True)

def main():
    """Main dashboard entry point."""
    
    if "auto_ingest_run" not in st.session_state:
        try:
            from src.engines.data_ingestion_manager import HardenedDataIngestionManager
            dm = HardenedDataIngestionManager()
            dm.scan_and_ingest_all()
            st.session_state["auto_ingest_run"] = True
            st.rerun()
        except:
            st.session_state["auto_ingest_run"] = True

    from src.engines.data_ingestion_manager import check_data_availability
    data_available, data_status = check_data_availability()
    
    if st.session_state.get("drill_down_active", False):
        drill_down.render_evidence_page(
            st.session_state.drill_down_metric,
            st.session_state.drill_down_params
        )
        return
    
    render_sidebar()
    
    if not data_available:
        st.markdown(styles.render_header("Aadhaar Sanket", "National Demographic Overview"), unsafe_allow_html=True)
        
        st.markdown(styles.clean_html("""
        <div class="alert-card-critical">
            <h3 style="margin-top: 0;">🚫 Action Required: Upload Data</h3>
            <p>The system requires official UIDAI datasets to perform analysis.</p>
            <p style="margin-top: 1rem;">Navigate to <strong>Data Ingestion</strong> in the sidebar to proceed.</p>
        </div>
        """), unsafe_allow_html=True)
        st.stop()
    
    st.markdown(styles.render_header("Aadhaar Sanket", "National Demographic Overview"), unsafe_allow_html=True)
    
    @st.cache_data(show_spinner="Loading analytics...")
    def load_data():
        try:
            from src.engines.ingestion import load_processed_dataset
            from src.engines.signal_separation import apply_signal_weights
            from src.engines.mvi import calculate_mvi, calculate_population_base, generate_mvi_summary
            from src.engines.spatial import add_zone_classification
            
            demographic_df = load_processed_dataset("demographic")
            enrolment_df = load_processed_dataset("enrolment")
            
            demographic_df = apply_signal_weights(demographic_df, "demographic")
            population_df = calculate_population_base(enrolment_df, "district")
            mvi_df = calculate_mvi(demographic_df, population_df, "district")
            mvi_df = add_zone_classification(mvi_df)
            
            mvi_summary = generate_mvi_summary(mvi_df)
            
            return {'mvi_df': mvi_df, 'mvi_summary': mvi_summary}
        except:
            return None

    data_result = load_data()
    
    if not data_result:
        st.error("Error loading processed data. Please check Data Quality page.")
        st.stop()
        
    mvi_summary = data_result['mvi_summary']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        drill_down.render_metric_button(
            value=f"{mvi_summary['total_units']:,}",
            label="Districts Analyzed",
            metric_id="total_districts"
        )
    
    with col2:
        drill_down.render_metric_button(
            value=f"{mvi_summary['mvi_statistics']['mean']:.1f}",
            label="Average MVI",
            metric_id="average_mvi"
        )
    
    with col3:
        high_pressure = mvi_summary['interpretation']['high_pressure_count']
        drill_down.render_metric_button(
            value=f"{high_pressure}",
            label="High-Pressure Zones",
            metric_id="high_mvi",
            trend="⚠️ Critical" if high_pressure > 0 else "✓ Clear",
            trend_direction="up" if high_pressure > 0 else "down"
        )
    
    with col4:
        attention = mvi_summary['interpretation']['attention_needed']
        drill_down.render_metric_button(
            value=f"{attention}",
            label="Zones Needing Attention",
            metric_id="elevated_mvi",
            trend="Monitor" if attention > 0 else "Stable",
            trend_direction="neutral"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0;">🗺️ Migration Pressure by State</h3>', unsafe_allow_html=True)
        
        from src.engines.spatial import aggregate_by_state
        import plotly.express as px
        
        mvi_df = data_result['mvi_df']
        state_df = aggregate_by_state(mvi_df)
        state_data = state_df.sort("mvi", descending=True).head(10).to_pandas()
        
        fig = px.bar(
            state_data,
            x="state",
            y="mvi",
            color="mvi",
            color_continuous_scale=["#FBBF24", "#F5A623", "#EF4444", "#991B1B"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", color="#000000", size=12),
            height=400,
            showlegend=False,
            margin=dict(l=0, r=20, t=20, b=0),
            xaxis_title=None,
            yaxis_title="Migration Velocity Index",
            yaxis=dict(gridcolor="rgba(0, 0, 0, 0.1)"),
            coloraxis_colorbar=dict(
                title=dict(text="MVI", font=dict(color="#000000")),
                tickfont=dict(color="#000000")
            )
        )
        fig.update_xaxes(tickfont=dict(color="#000000"))
        fig.update_yaxes(tickfont=dict(color="#000000"))
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0;">📋 Zone Classification</h3>', unsafe_allow_html=True)
        
        zone_counts = mvi_df.group_by("zone_type").len().to_pandas()
        
        for _, row in zone_counts.iterrows():
            zone = row["zone_type"]
            count = row["len"]
            
            color_map = {
                "high_inflow": "#EF4444",
                "moderate_inflow": "#F5A623",
                "stable": "#10B981",
                "decline": "#6B7280",
            }
            
            color = color_map.get(zone, "#6B7280")
            label = zone.replace("_", " ").title()
            
            st.markdown(styles.clean_html(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin: 1rem 0; padding: 0.75rem; background: rgba(255, 255, 255, 0.5); border-radius: 8px; border-left: 4px solid {color};">
                <span style="color: #000000; font-weight: 600;">{label}</span>
                <span style="color: #000000; font-weight: 700; font-size: 1.25rem;">{count}</span>
            </div>
            """), unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(styles.clean_html("""
    <div style="text-align: center; color: #555555; font-size: 0.875rem; margin-top: 2rem;">
        Aadhaar Sanket | Demographic Intelligence System | <span style="color: var(--accent-saffron); font-weight: 600;">Official Use Only</span>
    </div>
    """), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
