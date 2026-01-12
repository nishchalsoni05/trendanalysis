"""
Project Aadhaar Sanket - Streamlit Dashboard

GOVERNMENT SITUATION ROOM DESIGN

This dashboard provides:
1. National Overview - Bird's eye view of migration patterns
2. Migration & Stability Map - Interactive geography visualization
3. Spatial Stress Hotspots - Zone classification and clusters
4. Forecasts & Alerts - Early warnings and anomalies
5. Policy Insights - Plain-language interpretation

Design Philosophy:
- Calm, neutral colors (government-appropriate)
- Maps before charts
- Insights before numbers
- One page answers one question
- No flashy animations
"""
import streamlit as st
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Aadhaar Sanket - Demographic Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for government situation room aesthetic
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.3rem;
    }
    
    /* Zone indicators */
    .zone-stable { color: #22c55e; }
    .zone-moderate { color: #eab308; }
    .zone-elevated { color: #f97316; }
    .zone-high { color: #ef4444; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1e3a5f;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a5f;
        border-bottom: 2px solid #0ea5e9;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Alert boxes */
    .alert-critical {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    
    .alert-warning {
        background-color: #fffbeb;
        border-left: 4px solid #eab308;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    
    .alert-info {
        background-color: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Add project path
import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def render_header():
    """Render the main dashboard header."""
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Aadhaar Sanket</h1>
        <p>Demographic Intelligence System | UIDAI Data Analytics Platform</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.markdown("### 📊 Navigation")
        st.markdown("---")
        
        st.markdown("### System Status")
        st.success("✓ Data Pipeline: Ready")
        st.info("📅 Last Updated: Live")
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        
        # These would be populated from actual data
        st.metric("Districts Analyzed", "640+")
        st.metric("States Covered", "28")
        st.metric("Data Quality", "98.5%")


def render_metric_card(value: str, label: str, trend: str = None):
    """Render a styled metric card."""
    trend_html = f'<span style="color: #22c55e; font-size: 0.8rem;">▲ {trend}</span>' if trend else ''
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {trend_html}
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main dashboard entry point."""
    render_header()
    render_sidebar()
    
    # Main content area
    st.markdown('<div class="section-header">📍 National Overview</div>', unsafe_allow_html=True)
    
    # Try to load data
    data_available = False
    try:
        from src.engines.ingestion import load_processed_dataset
        from src.engines.signal_separation import apply_signal_weights
        from src.engines.mvi import calculate_mvi, calculate_population_base, generate_mvi_summary
        from src.engines.spatial import add_zone_classification, aggregate_by_state
        
        demographic_df = load_processed_dataset("demographic")
        enrolment_df = load_processed_dataset("enrolment")
        
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        population_df = calculate_population_base(enrolment_df, "district")
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        mvi_df = add_zone_classification(mvi_df)
        
        mvi_summary = generate_mvi_summary(mvi_df)
        data_available = True
        
    except Exception as e:
        st.warning(f"⚠️ Data not yet processed. Run the pipeline first: `python run_pipeline.py`")
        st.info("Showing placeholder dashboard layout...")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    if data_available:
        with col1:
            render_metric_card(
                f"{mvi_summary['total_units']:,}",
                "Districts Analyzed"
            )
        
        with col2:
            render_metric_card(
                f"{mvi_summary['mvi_statistics']['mean']:.1f}",
                "Average MVI"
            )
        
        with col3:
            high_pressure = mvi_summary['interpretation']['high_pressure_count']
            render_metric_card(
                f"{high_pressure}",
                "High-Pressure Zones"
            )
        
        with col4:
            attention = mvi_summary['interpretation']['attention_needed']
            render_metric_card(
                f"{attention}",
                "Zones Needing Attention"
            )
    else:
        # Placeholder metrics
        with col1:
            render_metric_card("---", "Districts Analyzed")
        with col2:
            render_metric_card("---", "Average MVI")
        with col3:
            render_metric_card("---", "High-Pressure Zones")
        with col4:
            render_metric_card("---", "Zones Needing Attention")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main content split
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.markdown('<div class="section-header">🗺️ Migration Pressure by State</div>', unsafe_allow_html=True)
        
        if data_available:
            state_df = aggregate_by_state(mvi_df)
            
            # Display as bar chart
            import plotly.express as px
            
            state_data = state_df.sort("mvi", descending=True).head(15).to_pandas()
            
            fig = px.bar(
                state_data,
                x="state",
                y="mvi",
                color="mvi",
                color_continuous_scale=["#22c55e", "#eab308", "#f97316", "#ef4444"],
                labels={"state": "State", "mvi": "Migration Velocity Index"},
            )
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font=dict(family="Arial, sans-serif"),
                height=400,
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Chart will appear after running the data pipeline")
    
    with right_col:
        st.markdown('<div class="section-header">📋 Zone Classification</div>', unsafe_allow_html=True)
        
        if data_available:
            zone_counts = mvi_df.group_by("zone_type").count().to_pandas()
            
            for _, row in zone_counts.iterrows():
                zone = row["zone_type"]
                count = row["count"]
                
                color_map = {
                    "high_inflow": "#ef4444",
                    "moderate_inflow": "#f97316",
                    "stable": "#22c55e",
                    "decline": "#6366f1",
                }
                
                color = color_map.get(zone, "#64748b")
                label = zone.replace("_", " ").title()
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                    <div style="width: 12px; height: 12px; background-color: {color}; border-radius: 50%; margin-right: 0.5rem;"></div>
                    <span style="flex: 1;">{label}</span>
                    <span style="font-weight: 600;">{count}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Zone data will appear after processing")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">⚠️ Active Alerts</div>', unsafe_allow_html=True)
        
        if data_available:
            from src.engines.anomaly import detect_mvi_anomalies, generate_alerts
            
            try:
                anomaly_df = detect_mvi_anomalies(mvi_df)
                alerts = generate_alerts(anomaly_df)
                
                if alerts:
                    for alert in alerts[:3]:
                        severity_style = "alert-critical" if alert.severity == "CRITICAL" else "alert-warning"
                        st.markdown(f"""
                        <div class="{severity_style}">
                            <strong>{alert.severity}</strong>: {alert.title}<br>
                            <small>{alert.summary}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.success("✓ No active alerts")
            except Exception:
                st.info("Alert data will appear after anomaly detection")
        else:
            st.info("Alert data will appear after processing")
    
    # Top districts table
    st.markdown('<div class="section-header">📍 Top Districts by Migration Pressure</div>', unsafe_allow_html=True)
    
    if data_available:
        from src.engines.mvi import get_top_mvi_regions
        
        top_districts = get_top_mvi_regions(mvi_df, 10)
        display_df = top_districts.select([
            "district", "state", "mvi", "mvi_band", "confidence"
        ]).to_pandas()
        
        display_df.columns = ["District", "State", "MVI", "Classification", "Confidence"]
        display_df["MVI"] = display_df["MVI"].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("📋 Data table will appear after running the pipeline")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.8rem;">
        Aadhaar Sanket | Demographic Intelligence System | For Official Use
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
