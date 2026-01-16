"""
Aadhaar Sanket - Consolidated Risk Report Page

Printable and PDF-downloadable summary of all high-risk alerts and critical data.
"""
import streamlit as st
from pathlib import Path
from datetime import datetime
import sys
import base64

st.set_page_config(
    page_title="Risk Report | Aadhaar Sanket",
    page_icon="📄",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles

# Apply global CSS (same as other pages)
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Report-specific CSS - ONLY for report content, not global UI
REPORT_CSS = """
<style>
/* Report content styling - specific to report sections */
.report-container {
    background: white !important;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    max-width: 210mm; /* A4 width */
    margin: 0 auto;
}

.report-container * {
    color: #000000 !important;
}

.report-header {
    text-align: center;
    border-bottom: 3px solid #F5A623;
    padding-bottom: 1.5rem;
    margin-bottom: 2rem;
    background: white !important;
}

.report-header h1 {
    color: #000000 !important;
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.report-header h2 {
    color: #1A1A1A !important;
}

.report-timestamp {
    color: #555555 !important;
    font-size: 0.9rem;
}

.report-section {
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: #FAF7F2 !important;
    border-left: 4px solid #F5A623;
    border-radius: 4px;
}

.report-section * {
    color: #000000 !important;
}

.report-section h2 {
    color: #000000 !important;
    font-size: 1.5rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #F5A623;
    padding-bottom: 0.5rem;
}

.report-section h3 {
    color: #000000 !important;
    font-size: 1.2rem;
    margin-top: 1rem;
    margin-bottom: 0.75rem;
}

.report-metric {
    background: white !important;
    padding: 1rem;
    margin: 0.5rem 0;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
}

.report-metric * {
    color: #000000 !important;
}

.alert-item {
    background: white !important;
    padding: 1rem;
    margin: 0.75rem 0;
    border-left: 4px solid #DC2626;
    border-radius: 4px;
}

.alert-item * {
    color: #000000 !important;
}

.alert-item.high {
    border-left-color: #EA580C;
}

.alert-item.medium {
    border-left-color: #F59E0B;
}

.zone-item {
    background: white !important;
    padding: 0.75rem;
    margin: 0.5rem 0;
    border: 1px solid #E2E8F0;
    border-radius: 4px;
}

.zone-item * {
    color: #000000 !important;
}

/* Print-specific styles - only active when printing */
@media print {
    /* Hide Streamlit UI elements */
    header[data-testid="stHeader"],
    section[data-testid="stSidebar"],
    .stButton,
    .print-hide,
    footer {
        display: none !important;
    }
    
    /* Reset backgrounds for print */
    body, .stApp, .block-container {
        background: white !important;
    }
    
    /* Ensure all report text is dark for print */
    .report-container,
    .report-container * {
        color: black !important;
    }
    
    /* Page breaks */
    .page-break {
        page-break-after: always;
    }
    
    /* Print margins */
    @page {
        margin: 1cm;
    }
    
    /* Remove shadows for print */
    .report-container,
    .report-section,
    .report-metric,
    .alert-item,
    .zone-item {
        box-shadow: none !important;
    }
}
</style>
"""

st.markdown(REPORT_CSS, unsafe_allow_html=True)

# Enforce Data Availability
from frontend.guardrails import require_data
require_data()

# Page header
st.markdown("""
<div class="report-header">
    <h1>📄 Project Aadhaar Sanket</h1>
    <h2>High-Risk Alert & Intelligence Report</h2>
    <div class="report-timestamp">Generated: {}</div>
</div>
""".format(datetime.now().strftime("%B %d, %Y at %I:%M %p")), unsafe_allow_html=True)

# Print button (hidden in print view)
import streamlit.components.v1 as components
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown('<div class="print-hide">', unsafe_allow_html=True)
    if st.button("🖨️ Print Report", use_container_width=True):
        components.html(
            "<script>window.parent.print()</script>",
            height=0,
            width=0
        )
    st.markdown('</div>', unsafe_allow_html=True)

# Load all necessary data
@st.cache_data(show_spinner="Loading report data...")
def load_report_data():
    """Load all data needed for the report."""
    from src.engines.ingestion import load_processed_dataset
    from src.engines.anomaly import generate_anomaly_report, generate_alerts
    import polars as pl
    
    data = {}
    
    # Load anomaly data
    try:
        # Try to load pre-processed anomalies
        try:
            anomaly_df = load_processed_dataset("anomalies")
        except FileNotFoundError:
            # Fallback: Calculate anomalies on the fly
            from src.engines.anomaly import detect_mvi_anomalies
            mvi_df = load_processed_dataset("trend_typology")
            
            if "mean_mvi" in mvi_df.columns:
                mvi_df = mvi_df.rename({"mean_mvi": "mvi"})
            
            # Extract state/district if needed
            if "state" not in mvi_df.columns and "geo_key" in mvi_df.columns:
                sample_key = mvi_df.select("geo_key").head(1).item()
                if "_" in str(sample_key):
                    try:
                        mvi_df = mvi_df.with_columns([
                            pl.col("geo_key").str.split("_").list.get(1).alias("state"),
                            pl.col("geo_key").str.split("_").list.get(0).alias("district")
                        ])
                    except:
                        pass
                else:
                    mvi_df = mvi_df.with_columns(pl.col("geo_key").alias("district"))
                    try:
                        demo_df = load_processed_dataset("demographic")
                        state_map = demo_df.select(["district", "state"]).unique()
                        mvi_df = mvi_df.join(state_map, on="district", how="left")
                    except:
                        mvi_df = mvi_df.with_columns(pl.lit("Unknown").alias("state"))
            
            anomaly_df = detect_mvi_anomalies(mvi_df)
        
        data['anomaly_df'] = anomaly_df
        data['anomaly_report'] = generate_anomaly_report(anomaly_df)
        data['alerts'] = generate_alerts(anomaly_df, min_severity="MEDIUM")
    except Exception as e:
        st.error(f"Could not load anomaly data: {e}")
        data['anomaly_df'] = None
        data['anomaly_report'] = None
        data['alerts'] = []
    
    # Load trend typology for high-pressure zones
    try:
        typology_df = load_processed_dataset("trend_typology")
        if "mean_mvi" in typology_df.columns:
            typology_df = typology_df.rename({"mean_mvi": "mvi"})
        data['typology_df'] = typology_df
    except Exception as e:
        st.warning(f"Could not load trend typology: {e}")
        data['typology_df'] = None
    
    # Load policy recommendations
    try:
        policy_df = load_processed_dataset("policy_recommendations")
        data['policy_df'] = policy_df
    except Exception as e:
        data['policy_df'] = None
    
    # Load insights
    try:
        insights_df = load_processed_dataset("insights")
        data['insights_df'] = insights_df
    except Exception as e:
        data['insights_df'] = None
    
    return data

data = load_report_data()

st.markdown('<div class="report-container">', unsafe_allow_html=True)

# ============================================================================
# EXECUTIVE SUMMARY
# ============================================================================

st.markdown('<div class="report-section">', unsafe_allow_html=True)
st.markdown("## 📊 Executive Summary", unsafe_allow_html=True)

if data['anomaly_report']:
    import polars as pl
    
    report = data['anomaly_report']
    critical_count = report['by_severity'].get('CRITICAL', 0)
    high_count = report['by_severity'].get('HIGH', 0)
    total_anomalies = report['summary']['anomaly_count']
    
    # Count high-pressure zones
    high_pressure_count = 0
    if data['typology_df'] is not None and 'mvi' in data['typology_df'].columns:
        high_pressure_count = len(data['typology_df'].filter(pl.col('mvi') >= 30))
    
    # Determine overall risk level
    if critical_count > 0:
        risk_level = "🔴 HIGH RISK"
        risk_color = "#DC2626"
    elif high_count > 5 or high_pressure_count > 10:
        risk_level = "🟠 ELEVATED RISK"
        risk_color = "#EA580C"
    else:
        risk_level = "🟡 MODERATE RISK"
        risk_color = "#F59E0B"
    
    st.markdown(f"""
    <div class="report-metric">
        <h3 style="color: {risk_color} !important; margin-top: 0;">Overall Risk Level: {risk_level}</h3>
        <ul>
            <li><strong>Critical Alerts:</strong> {critical_count}</li>
            <li><strong>High Severity Alerts:</strong> {high_count}</li>
            <li><strong>Total Anomalies Detected:</strong> {total_anomalies}</li>
            <li><strong>High-Pressure Migration Zones (MVI ≥ 30):</strong> {high_pressure_count}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Key recommendation
    if critical_count > 0 or high_count > 5:
        st.markdown("""
        <div class="report-metric" style="background: #FEF2F2; border-left: 4px solid #DC2626;">
            <strong style="color: #991B1B !important;">⚠️ IMMEDIATE ACTION REQUIRED</strong><br>
            <span style="color: #000000 !important;">
            Multiple critical or high-severity alerts detected. Prioritize investigation of affected regions and 
            cross-reference with local events or data quality issues. Deploy field verification teams to 
            high-pressure zones immediately.
            </span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Anomaly data not available. Run the pipeline to generate report.")

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# CRITICAL ALERTS
# ============================================================================

st.markdown('<div class="report-section page-break">', unsafe_allow_html=True)
st.markdown("## 🚨 Critical & High-Priority Alerts", unsafe_allow_html=True)

if data['alerts'] and len(data['alerts']) > 0:
    for alert in data['alerts']:
        severity_class = "alert-item"
        if alert.severity == "HIGH":
            severity_class += " high"
        elif alert.severity == "MEDIUM":
            severity_class += " medium"
        
        regions_text = ", ".join(alert.affected_regions[:5])
        if len(alert.affected_regions) > 5:
            regions_text += f" (+{len(alert.affected_regions) - 5} more)"
        
        st.markdown(f"""
        <div class="{severity_class}">
            <strong style="color: #000000 !important; font-size: 1.1rem;">{alert.severity}: {alert.title}</strong><br>
            <span style="color: #1A1A1A !important;">{alert.summary}</span><br><br>
            <strong style="color: #000000 !important;">Affected Regions:</strong><br>
            <span style="color: #333333 !important;">{regions_text}</span><br><br>
            <strong style="color: #000000 !important;">Metrics:</strong><br>
            <span style="color: #333333 !important;">
                Count: {alert.metrics.get('count', 'N/A')} | 
                Max Z-Score: {alert.metrics.get('max_z_score', 0):.2f}
            </span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="report-metric" style="background: #F0FDF4; border-left: 4px solid #16A34A;">
        <strong style="color: #166534 !important;">✓ No Critical Alerts</strong><br>
        <span style="color: #000000 !important;">
        No anomalous patterns requiring immediate attention detected. Continue routine monitoring.
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# HIGH-PRESSURE MIGRATION ZONES
# ============================================================================

st.markdown('<div class="report-section">', unsafe_allow_html=True)
st.markdown("## 📍 High-Pressure Migration Zones (MVI ≥ 30)", unsafe_allow_html=True)

if data['typology_df'] is not None and 'mvi' in data['typology_df'].columns:
    import polars as pl
    
    high_pressure = data['typology_df'].filter(pl.col('mvi') >= 30).sort('mvi', descending=True)
    
    if len(high_pressure) > 0:
        st.markdown(f"""
        <p style="color: #000000 !important;">
        <strong>{len(high_pressure)} districts</strong> identified with Migration Velocity Index (MVI) ≥ 30, 
        indicating high migration pressure requiring immediate resource allocation and service capacity planning.
        </p>
        """, unsafe_allow_html=True)
        
        # Display top 20
        for idx, row in enumerate(high_pressure.head(20).to_dicts()):
            geo_col = "district" if "district" in row else "geo_key"
            district_name = row.get(geo_col, "Unknown")
            state_name = row.get("state", "")
            mvi_value = row.get("mvi", 0)
            trend_type = row.get("trend_type", "N/A")
            
            location = f"{district_name}, {state_name}" if state_name else district_name
            
            st.markdown(f"""
            <div class="zone-item">
                <strong style="color: #000000 !important;">{idx + 1}. {location}</strong><br>
                <span style="color: #333333 !important;">
                    MVI: {mvi_value:.2f} | Trend Type: {trend_type}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        if len(high_pressure) > 20:
            st.markdown(f"""
            <p style="color: #555555 !important; font-style: italic;">
            ... and {len(high_pressure) - 20} more districts. See full data in Migration Patterns page.
            </p>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="report-metric" style="background: #F0FDF4;">
            <span style="color: #000000 !important;">No districts currently exceed the high-pressure threshold (MVI ≥ 30).</span>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Migration data not available.")

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# POLICY RECOMMENDATIONS
# ============================================================================

st.markdown('<div class="report-section page-break">', unsafe_allow_html=True)
st.markdown("## 📋 Priority Policy Recommendations", unsafe_allow_html=True)

if data['policy_df'] is not None and len(data['policy_df']) > 0:
    import polars as pl
    
    # Filter to high/critical priority if column exists
    if 'priority' in data['policy_df'].columns:
        priority_recs = data['policy_df'].filter(
            pl.col('priority').is_in(['HIGH', 'CRITICAL'])
        ).head(10)
    else:
        priority_recs = data['policy_df'].head(10)
    
    if len(priority_recs) > 0:
        for idx, row in enumerate(priority_recs.to_dicts()):
            recommendation = row.get('recommendation', row.get('action', 'N/A'))
            location = row.get('district', row.get('geo_key', 'National'))
            priority = row.get('priority', 'MEDIUM')
            
            st.markdown(f"""
            <div class="report-metric">
                <strong style="color: #000000 !important;">{idx + 1}. [{priority}] {location}</strong><br>
                <span style="color: #1A1A1A !important;">{recommendation}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No high-priority policy recommendations at this time.")
else:
    st.markdown("""
    <div class="report-metric">
        <span style="color: #000000 !important;">
        Policy recommendations data not available. Standard monitoring protocols apply.
        </span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# DATA QUALITY & TRUST
# ============================================================================

st.markdown('<div class="report-section">', unsafe_allow_html=True)
st.markdown("## 🔍 Data Quality & Trust Status", unsafe_allow_html=True)

st.markdown("""
<div class="report-metric">
    <strong style="color: #000000 !important;">Data Sources:</strong><br>
    <span style="color: #333333 !important;">
    • UIDAI Official Datasets (Enrolment, Demographic, Biometric Updates)<br>
    • Processed through deterministic, auditable pipeline<br>
    • All calculations use transparent statistical methods (no black-box ML)
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="report-metric">
    <strong style="color: #000000 !important;">Quality Assurance:</strong><br>
    <span style="color: #333333 !important;">
    • Great Expectations validation applied to all datasets<br>
    • Signal vs. noise separation using configurable weights<br>
    • Anomaly detection via Z-score analysis (threshold: 2.0)<br>
    • Multi-stage data cleaning and deduplication
    </span>
</div>
""", unsafe_allow_html=True)

if data['anomaly_report']:
    anomaly_rate = data['anomaly_report']['summary']['anomaly_rate']
    if anomaly_rate > 10:
        st.markdown(f"""
        <div class="report-metric" style="background: #FFF7ED; border-left: 4px solid #EA580C;">
            <strong style="color: #9A3412 !important;">⚠️ Data Quality Alert</strong><br>
            <span style="color: #000000 !important;">
            Anomaly rate of {anomaly_rate:.1f}% is elevated. Recommend additional data validation 
            and cross-referencing with ground truth sources.
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="report-metric" style="background: #F0FDF4; border-left: 4px solid #16A34A;">
            <strong style="color: #166534 !important;">✓ Data Quality: Good</strong><br>
            <span style="color: #000000 !important;">
            Anomaly rate of {anomaly_rate:.1f}% is within acceptable range. Data quality is satisfactory.
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("""
<div style="margin-top: 3rem; padding-top: 1.5rem; border-top: 2px solid #E2E8F0; text-align: center;">
    <p style="color: #555555 !important; font-size: 0.85rem;">
        <strong style="color: #000000 !important;">Project Aadhaar Sanket</strong> | 
        Trustworthy Demographic Intelligence System<br>
        For official use only. Handle in accordance with data protection protocols.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Download as PDF note
st.markdown('<div class="print-hide">', unsafe_allow_html=True)
st.markdown("---")
st.info("💡 **To download as PDF:** Click the Print Report button above, then select 'Save as PDF' in your browser's print dialog.")
st.markdown('</div>', unsafe_allow_html=True)
