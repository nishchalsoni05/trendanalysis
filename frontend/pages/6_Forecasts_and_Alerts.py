"""
Aadhaar Sanket - Forecasts & Alerts Page

Early warnings and anomaly detection.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="Forecasts & Alerts | Aadhaar Sanket",
    page_icon="⚠️",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles
import frontend.drill_down as drill_down

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Fix expander styling for this page - white background, black text
st.markdown("""
<style>
    /* RADIO BUTTON LABELS - FORCE BLACK */
    .stRadio label,
    .stRadio span,
    [data-testid="stRadioButton"] label,
    [data-testid="stRadioButton"] span,
    div[role="radiogroup"] label,
    div[role="radiogroup"] span {
        color: #1f2937 !important;
    }
    
    /* Expander container - FORCE WHITE */
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stExpander"] > div {
        background-color: #FFFFFF !important;
    }
    
    /* Expander header bar - the click area - FORCE WHITE */
    [data-testid="stExpander"] > details {
        background-color: #FFFFFF !important;
    }
    
    [data-testid="stExpander"] > details > summary {
        background-color: #FFFFFF !important;
        color: #1f2937 !important;
    }
    
    [data-testid="stExpander"] summary {
        background-color: #FFFFFF !important;
        color: #1f2937 !important;
    }
    
    [data-testid="stExpander"] summary > span {
        color: #1f2937 !important;
    }
    
    /* Target the details element directly */
    details[data-testid="stExpander"] {
        background-color: #FFFFFF !important;
    }
    
    details summary {
        background-color: #FFFFFF !important;
        color: #1f2937 !important;
    }
    
    /* Expander content area */
    .streamlit-expanderContent {
        background-color: #FFFFFF !important;
        color: #1f2937 !important;
    }
    
    /* All text inside expander ONLY */
    .streamlit-expanderContent p,
    .streamlit-expanderContent span,
    .streamlit-expanderContent li,
    .streamlit-expanderContent strong {
        color: #1f2937 !important;
    }
    
    /* Expander chevron icon */
    [data-testid="stExpander"] svg {
        color: #1f2937 !important;
        fill: #1f2937 !important;
    }
</style>
""", unsafe_allow_html=True)

if "loader_shown_P5" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("RUNNING PROPHET MODELS", "Extrapolating 6-month horizons..."),
        ("CALIBRATING ALERTS", "Setting confidence intervals..."),
        ("READY", "Generating forecast report...")
    ])
    st.session_state["loader_shown_P5"] = True

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
        "Forecasts & Early Warnings",
        "Monitor anomalies and anticipate demographic pressure"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

@st.cache_data(show_spinner="Running anomaly detection...")
def load_forecast_data():
    """Load pre-calculated FORECAST and ANOMALY analytics."""
    try:
        from src.engines.ingestion import load_processed_dataset
        from src.engines.anomaly import generate_anomaly_report, generate_alerts
        import polars as pl
        
        try:
            anomaly_df = load_processed_dataset("anomalies")
        except FileNotFoundError:
            # Fallback: Calculate on the fly if file missing
            try:
                from src.engines.ingestion import load_processed_dataset
                from src.engines.anomaly import detect_mvi_anomalies
                # Load input data which has MVI (typology)
                mvi_df = load_processed_dataset("trend_typology")
                
                # Ensure column naming consistency
                if "mean_mvi" in mvi_df.columns:
                    mvi_df = mvi_df.rename({"mean_mvi": "mvi"})
                    
                # Fix: Extract state/district from geo_key if missing
                # Check 1: Is geo_key just District_State?
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
                        # Case 2: geo_key IS the district name (as seen in check results)
                        mvi_df = mvi_df.with_columns(pl.col("geo_key").alias("district"))
                        # Try to get state mapping from demographic data if available
                        try:
                            demo_df = load_processed_dataset("demographic")
                            # Create district->state mapping
                            state_map = demo_df.select(["district", "state"]).unique()
                            mvi_df = mvi_df.join(state_map, on="district", how="left")
                        except:
                            # If demo data missing, just fill state as Unknown
                            mvi_df = mvi_df.with_columns(pl.lit("Unknown").alias("state"))

                anomaly_df = detect_mvi_anomalies(mvi_df)
            except Exception as e2:
                # print(f"Fallback failed: {e2}")
                anomaly_df = None

        acceleration_df = load_processed_dataset("acceleration")
        
        # Generate reports from the loaded/calculated data
        if anomaly_df is not None:
            # Ensure anomaly_df has state/district for alerts if possible
            if "state" not in anomaly_df.columns and "geo_key" in anomaly_df.columns:
                 sample_key = anomaly_df.select("geo_key").head(1).item()
                 if "_" in str(sample_key):
                     try:
                        anomaly_df = anomaly_df.with_columns([
                            pl.col("geo_key").str.split("_").list.get(1).alias("state"),
                            pl.col("geo_key").str.split("_").list.get(0).alias("district")
                        ])
                     except:
                        pass
                 else:
                     # geo_key is district
                     anomaly_df = anomaly_df.with_columns(pl.col("geo_key").alias("district"))
                     try:
                        # Try to rejoin state from mvi_df if we calculated it there
                        if "mvi_df" in locals() and "state" in mvi_df.columns:
                             state_map = mvi_df.select(["district", "state"]).unique()
                             anomaly_df = anomaly_df.join(state_map, on="district", how="left")
                        else:
                             # Try loading demo data again if needed (less efficient but robust)
                             from src.engines.ingestion import load_processed_dataset
                             demo_df = load_processed_dataset("demographic")
                             state_map = demo_df.select(["district", "state"]).unique()
                             anomaly_df = anomaly_df.join(state_map, on="district", how="left")
                     except:
                        anomaly_df = anomaly_df.with_columns(pl.lit("Unknown").alias("state"))

            anomaly_report = generate_anomaly_report(anomaly_df)
            alerts = generate_alerts(anomaly_df)
        else:
            anomaly_report, alerts = None, None
        
        return anomaly_df, acceleration_df, anomaly_report, alerts, True
    except Exception as e:
        # Fallback for acceleration if not found
        return None, None, None, None, False

# Load data
anomaly_df, acceleration_df, anomaly_report, alerts, data_available = load_forecast_data()

if not data_available:
    st.markdown(styles.clean_html("""
    <div class="alert-card-warning">
        <strong>⚠️ Data Not Processed</strong><br>
        Please run the data pipeline to generate forecasts.
    </div>
    """), unsafe_allow_html=True)
    st.info("Run: `python run_pipeline.py`")
    st.stop()

import polars as pl

# 4-PART VISUAL STORYTELLING
critical = anomaly_report["by_severity"].get("CRITICAL", 0)
high = anomaly_report["by_severity"].get("HIGH", 0)
total_anomalies = anomaly_report["summary"]["anomaly_count"]

st.markdown(styles.render_insight_card(
    "What unusual patterns need attention?",
    f"Detected {total_anomalies} anomalous districts out of {anomaly_report['summary']['total_units']} analyzed. {critical} critical alerts and {high} high-severity alerts require immediate investigation.",
    "Investigate critical and high-severity alerts first. Cross-reference with local events or data quality issues. Not all anomalies are problems—some may be legitimate demographic shifts.",
    "⚠️"
), unsafe_allow_html=True)

st.markdown("---")

# Alert summary - CLICKABLE METRICS
col1, col2, col3 = st.columns(3)

with col1:
    drill_down.render_metric_button(
        value=str(critical),
        label="Critical Alerts",
        metric_id="critical_alerts_forecast",
        params={"severity": "CRITICAL", "is_anomaly": True},
        trend="⚠️" if critical > 0 else "✓",
        trend_direction="down" if critical > 0 else "neutral"
    )
    
with col2:
    drill_down.render_metric_button(
        value=str(high),
        label="High Severity",
        metric_id="high_severity_alerts_forecast",
        params={"severity": "HIGH", "is_anomaly": True},
        trend="⚠️" if high > 0 else "✓",
        trend_direction="down" if high > 0 else "neutral"
    )
    
with col3:
    rate = anomaly_report["summary"]["anomaly_rate"]
    drill_down.render_metric_button(
        value=f"{total_anomalies}",
        label=f"Total Anomalies ({rate:.1f}%)",
        metric_id="total_anomalies_forecast",
        params={"is_anomaly": True},
        trend="Monitor",
        trend_direction="neutral"
    )

st.markdown("---")

# Active Alerts
st.markdown("### 🚨 Active Alerts")

if alerts:
    # Limit to top 10 most severe alerts
    for alert in alerts[:10]:
        severity_class = "alert-card-critical" if alert.severity == "CRITICAL" else ("alert-card-warning" if alert.severity == "HIGH" else "alert-card-info")
        severity_badge = styles.render_badge(alert.severity, "critical" if alert.severity == "CRITICAL" else ("high" if alert.severity == "HIGH" else "info"))
        
        st.markdown(styles.clean_html(f"""
        <div class="{severity_class}">
            {severity_badge}
            <br/>
            <strong>{alert.title}</strong><br/>
            <span style="margin-top: 0.5rem; display: block;">{alert.summary}</span>
        </div>
        """), unsafe_allow_html=True)
        
        if alert.affected_regions:
            with st.expander(f"📍 Affected Regions ({len(alert.affected_regions)})"):
                # Limit to 10 for performance
                for region in alert.affected_regions[:10]:
                    st.write(f"• {region}")
                if len(alert.affected_regions) > 10:
                    st.info(f"+ {len(alert.affected_regions) - 10} more regions")
    
    if len(alerts) > 10:
        st.info(f"Showing top 10 of {len(alerts)} alerts. Focus on critical and high severity items first.")
else:
    st.markdown(styles.clean_html("""
    <div class="alert-card-success">
        <strong>✓ No Active Alerts</strong><br/>
        No anomalous patterns requiring immediate attention. Continue routine monitoring.
    </div>
    """), unsafe_allow_html=True)

st.markdown("---")

# Use tabs for detailed analysis
tab1, tab2 = st.tabs(["📊 Anomaly Breakdown", "📋 Anomaly Details"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By Type**")
        for atype, count in anomaly_report["by_type"].items():
            if atype != "NORMAL" and count > 0:
                badge = styles.render_badge(atype, "info")
                st.markdown(f"{badge} **{count}** districts", unsafe_allow_html=True)
    
    with col2:
        st.markdown("**By Severity**")
        for severity, count in anomaly_report["by_severity"].items():
            if severity != "NORMAL" and count > 0:
                if severity == "CRITICAL":
                    badge = styles.render_badge(severity, "critical")
                elif severity == "HIGH":
                    badge = styles.render_badge(severity, "high")
                elif severity == "MEDIUM":
                    badge = styles.render_badge(severity, "moderate")
                else:
                    badge = styles.render_badge(severity, "info")
                st.markdown(f"{badge} **{count}** districts", unsafe_allow_html=True)

with tab2:
    anomalies_only = anomaly_df.filter(pl.col("is_anomaly") == True).sort("z_score", descending=True)
    
    if len(anomalies_only) > 0:
        # Limit to top 15 for performance
        cols_to_show = ["state", "district", "mvi", "z_score", "anomaly_type", "severity"]
        available_cols = [c for c in cols_to_show if c in anomalies_only.columns]
        
        # Fallback to geo_key if district missing
        if "district" not in available_cols and "geo_key" in anomalies_only.columns:
            available_cols = ["geo_key"] + [c for c in available_cols if c not in ["state", "district"]]
            
        display_df = anomalies_only.select(available_cols).head(15).to_pandas()
        
        # Format columns nicely
        display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
        
        if "Z Score" in display_df.columns:
            display_df["Z Score"] = display_df["Z Score"].round(2)
        if "Mvi" in display_df.columns:
            display_df["Mvi"] = display_df["Mvi"].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        if len(anomalies_only) > 15:
            st.info(f"Showing top 15 of {len(anomalies_only)} anomalies")
    else:
        st.info("No anomalies detected in current data")

# Recommendations
st.markdown("---")
st.markdown("### 📝 Recommendations")

risk_level = anomaly_report["interpretation"]["risk_level"]
recommendation = anomaly_report["interpretation"]["recommendation"]

if risk_level == "HIGH":
    st.markdown(styles.clean_html(f"""
    <div class="alert-card-critical">
        <strong>Risk Level: {risk_level}</strong><br/>
        {recommendation}
    </div>
    """), unsafe_allow_html=True)
elif risk_level == "MEDIUM":
    st.markdown(styles.clean_html(f"""
    <div class="alert-card-warning">
        <strong>Risk Level: {risk_level}</strong><br/>
        {recommendation}
    </div>
    """), unsafe_allow_html=True)
else:
    st.markdown(styles.clean_html(f"""
    <div class="alert-card-success">
        <strong>Risk Level: {risk_level}</strong><br/>
        {recommendation}
    </div>
    """), unsafe_allow_html=True)

# NEW SECTION: Export Alerts
st.markdown("---")
st.markdown("### 📤 Export Alerts")

export_col1, export_col2 = st.columns(2)

with export_col1:
    # Export anomalies to CSV
    if anomaly_df is not None and len(anomaly_df) > 0:
        anomalies_for_export = anomaly_df.filter(pl.col("is_anomaly") == True)
        if len(anomalies_for_export) > 0:
            csv_data = anomalies_for_export.write_csv()
            st.download_button(
                label="📄 Download Anomalies as CSV",
                data=csv_data,
                file_name="anomaly_alerts.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No anomalies to export")
    else:
        st.info("No anomaly data available")

with export_col2:
    # Quick summary download
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_text = f"""
AADHAAR SANKET - ANOMALY REPORT
Generated: {current_time}

SUMMARY
-------
Total Units Analyzed: {anomaly_report['summary']['total_units']}
Total Anomalies: {anomaly_report['summary']['anomaly_count']}
Anomaly Rate: {anomaly_report['summary']['anomaly_rate']:.2f}%

BY SEVERITY
-----------
Critical: {anomaly_report['by_severity'].get('CRITICAL', 0)}
High: {anomaly_report['by_severity'].get('HIGH', 0)}
Medium: {anomaly_report['by_severity'].get('MEDIUM', 0)}
Low: {anomaly_report['by_severity'].get('LOW', 0)}

RISK ASSESSMENT
---------------
Risk Level: {risk_level}
Recommendation: {recommendation}
"""
    st.download_button(
        label="📋 Download Summary Report",
        data=summary_text,
        file_name="anomaly_summary.txt",
        mime="text/plain",
        use_container_width=True
    )

# NEW SECTION: Interactive Risk Score Calculator
st.markdown("---")
st.markdown("### 🧮 Interactive Risk Score Calculator")
st.markdown("Configure parameters and calculate risk scores for specific regions or custom scenarios.")

# Use radio buttons instead of tabs to maintain state during rerun
if "calc_mode" not in st.session_state:
    st.session_state.calc_mode = "📊 Current Data"

calc_mode = st.radio(
    "Select Analysis Mode",
    ["📊 Current Data", "🗺️ State-wise Analysis", "⚙️ Custom Calculator"],
    horizontal=True,
    key="calc_mode_radio",
    index=["📊 Current Data", "🗺️ State-wise Analysis", "⚙️ Custom Calculator"].index(st.session_state.calc_mode)
)

# Update session state
st.session_state.calc_mode = calc_mode

st.markdown("---")

if calc_mode == "📊 Current Data":
    # Current data risk score (existing functionality)
    calc_col1, calc_col2 = st.columns([1, 1])
    
    with calc_col1:
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb;">
            <h4 style="color: #1f2937; margin-top: 0;">📊 Risk Score Formula</h4>
            <div style="color: #475569; line-height: 1.8;">
                <p><strong>Critical Alerts</strong> × 10 = <span style="color: #dc2626;">{}</span></p>
                <p><strong>High Alerts</strong> × 5 = <span style="color: #ea580c;">{}</span></p>
                <p><strong>Anomaly Rate</strong> × 2 = <span style="color: #f59e0b;">{:.1f}</span></p>
                <hr style="border-color: #e5e7eb;"/>
                <p style="font-size: 1.25rem;"><strong>Total Risk Score</strong> = <span style="color: #000000; font-weight: 700;">{:.1f}</span></p>
            </div>
        </div>
        """.format(
            critical * 10,
            high * 5,
            anomaly_report['summary']['anomaly_rate'] * 2,
            (critical * 10) + (high * 5) + (anomaly_report['summary']['anomaly_rate'] * 2)
        ), unsafe_allow_html=True)
    
    with calc_col2:
        risk_score = (critical * 10) + (high * 5) + (anomaly_report['summary']['anomaly_rate'] * 2)
        
        if risk_score >= 50:
            risk_color = "#dc2626"
            risk_label = "HIGH RISK"
            risk_action = "Immediate investigation and intervention required"
        elif risk_score >= 20:
            risk_color = "#ea580c"
            risk_label = "ELEVATED RISK"
            risk_action = "Close monitoring and contingency planning needed"
        else:
            risk_color = "#16a34a"
            risk_label = "LOW RISK"
            risk_action = "Continue routine monitoring"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {risk_color}20, {risk_color}10); padding: 2rem; border-radius: 12px; border-left: 4px solid {risk_color}; text-align: center;">
            <div style="font-size: 3rem; font-weight: 800; color: {risk_color};">{risk_score:.0f}</div>
            <div style="font-size: 1rem; font-weight: 700; color: {risk_color}; margin-top: 0.5rem;">{risk_label}</div>
            <div style="font-size: 0.875rem; color: #475569; margin-top: 1rem;">{risk_action}</div>
        </div>
        """, unsafe_allow_html=True)

elif calc_mode == "🗺️ State-wise Analysis":
    # State-wise analysis
    st.markdown("**Select a state to analyze its risk profile and view detailed problems:**")
    
    # Get states from anomaly data
    if "state" in anomaly_df.columns:
        states_list = sorted([s for s in anomaly_df.select("state").unique().to_series().to_list() 
                              if s and str(s).strip() and not str(s).strip().isdigit()])
        
        if states_list:
            selected_state = st.selectbox("🗺️ Select State", ["All States"] + states_list, key="risk_calc_state")
            
            if selected_state != "All States":
                # Filter data for selected state
                state_anomalies = anomaly_df.filter(pl.col("state") == selected_state)
                state_critical = len(state_anomalies.filter((pl.col("is_anomaly") == True) & (pl.col("severity") == "CRITICAL")))
                state_high = len(state_anomalies.filter((pl.col("is_anomaly") == True) & (pl.col("severity") == "HIGH")))
                state_medium = len(state_anomalies.filter((pl.col("is_anomaly") == True) & (pl.col("severity") == "MEDIUM")))
                state_total = len(state_anomalies)
                state_anomaly_count = len(state_anomalies.filter(pl.col("is_anomaly") == True))
                state_anomaly_rate = (state_anomaly_count / state_total * 100) if state_total > 0 else 0
                state_risk_score = (state_critical * 10) + (state_high * 5) + (state_anomaly_rate * 2)
                
                # Get actual anomaly data for this state
                state_anomaly_details = state_anomalies.filter(pl.col("is_anomaly") == True)
            else:
                state_critical = critical
                state_high = high
                state_medium = anomaly_report['by_severity'].get('MEDIUM', 0)
                state_anomaly_rate = anomaly_report['summary']['anomaly_rate']
                state_risk_score = (state_critical * 10) + (state_high * 5) + (state_anomaly_rate * 2)
                state_anomaly_details = anomaly_df.filter(pl.col("is_anomaly") == True)
                state_total = len(anomaly_df)
                state_anomaly_count = len(state_anomaly_details)
            
            # Display state-specific metrics
            st.markdown(f"### 📊 Risk Overview: {selected_state}")
            state_col1, state_col2, state_col3, state_col4 = st.columns(4)
            
            with state_col1:
                st.metric("Critical Alerts", state_critical, delta=None)
            with state_col2:
                st.metric("High Alerts", state_high, delta=None)
            with state_col3:
                st.metric("Anomaly Rate", f"{state_anomaly_rate:.1f}%", delta=None)
            with state_col4:
                if state_risk_score >= 50:
                    st.metric("Risk Score", f"{state_risk_score:.0f}", delta="HIGH", delta_color="inverse")
                elif state_risk_score >= 20:
                    st.metric("Risk Score", f"{state_risk_score:.0f}", delta="ELEVATED", delta_color="inverse")
                else:
                    st.metric("Risk Score", f"{state_risk_score:.0f}", delta="LOW", delta_color="normal")
            
            st.markdown("---")
            
            # DETAILED PROBLEM BREAKDOWN
            st.markdown(f"### 🚨 Detailed Problems in {selected_state}")
            
            if len(state_anomaly_details) > 0:
                # Group by anomaly type
                if "anomaly_type" in state_anomaly_details.columns:
                    anomaly_types = state_anomaly_details.group_by("anomaly_type").len().sort("len", descending=True)
                    
                    st.markdown("#### Problem Types Identified:")
                    for row in anomaly_types.iter_rows():
                        atype, count = row[0], row[1]
                        if atype and atype != "NORMAL":
                            # Define problem descriptions and solutions
                            problem_info = {
                                "SPIKE": {
                                    "icon": "📈",
                                    "description": "Sudden dramatic increase in migration activity detected",
                                    "cause": "Could indicate mass migration event, seasonal worker movement, or data entry surge",
                                    "solution": "1. Verify data quality for entry errors\n2. Cross-reference with local events\n3. Deploy field verification teams\n4. Prepare service capacity expansion"
                                },
                                "SUSTAINED_HIGH": {
                                    "icon": "🔥",
                                    "description": "Consistently elevated migration levels over extended period",
                                    "cause": "Indicates ongoing population inflow pressure",
                                    "solution": "1. Increase electoral roll verification frequency\n2. Enhance service delivery capacity\n3. Plan infrastructure expansion\n4. Coordinate with source regions"
                                },
                                "ACCELERATION": {
                                    "icon": "🚀",
                                    "description": "Migration rate is increasing faster than normal",
                                    "cause": "Early indicator of emerging pressure zone",
                                    "solution": "1. Set up early warning monitoring\n2. Prepare contingency resources\n3. Alert district administration\n4. Begin capacity planning"
                                },
                                "VOLATILE": {
                                    "icon": "⚡",
                                    "description": "Unpredictable fluctuations in migration patterns",
                                    "cause": "May indicate seasonal effects, data issues, or unstable population dynamics",
                                    "solution": "1. Increase data monitoring frequency\n2. Investigate data quality\n3. Analyze seasonal patterns\n4. Deploy adaptive resource allocation"
                                }
                            }
                            
                            info = problem_info.get(atype, {
                                "icon": "⚠️",
                                "description": f"Anomalous pattern detected: {atype}",
                                "cause": "Requires investigation to determine root cause",
                                "solution": "1. Review data quality\n2. Perform field verification\n3. Consult local administration"
                            })
                            
                            with st.expander(f"{info['icon']} {atype} - {count} districts affected", expanded=True):
                                st.markdown(f"""
                                <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid #ea580c;">
                                    <strong style="color: #1f2937;">Problem:</strong> {info['description']}<br/><br/>
                                    <strong style="color: #1f2937;">Likely Cause:</strong> {info['cause']}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show affected districts
                                affected = state_anomaly_details.filter(pl.col("anomaly_type") == atype)
                                if "district" in affected.columns or "geo_key" in affected.columns:
                                    district_col = "district" if "district" in affected.columns else "geo_key"
                                    districts = affected.select(district_col).to_series().to_list()[:10]
                                    
                                    st.markdown("**Affected Districts:**")
                                    district_tags = " ".join([f'<span style="background: #fee2e2; color: #991b1b; padding: 0.25rem 0.75rem; border-radius: 12px; margin: 2px; display: inline-block; font-size: 0.85rem;">{d}</span>' for d in districts])
                                    st.markdown(district_tags, unsafe_allow_html=True)
                                    
                                    if len(affected) > 10:
                                        st.caption(f"+ {len(affected) - 10} more districts")
                                
                                st.markdown("**✅ Recommended Actions:**")
                                for i, action in enumerate(info['solution'].split('\n'), 1):
                                    st.markdown(f"{action}")
                
                # Show detailed table of all anomalies
                st.markdown("---")
                st.markdown("#### 📋 Complete Anomaly Details")
                
                cols_to_show = ["district", "geo_key", "mvi", "z_score", "anomaly_type", "severity"]
                available_cols = [c for c in cols_to_show if c in state_anomaly_details.columns]
                
                if available_cols:
                    display_df = state_anomaly_details.select(available_cols).sort("z_score", descending=True).head(20).to_pandas()
                    display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
                    
                    # Color-code severity
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    if len(state_anomaly_details) > 20:
                        st.info(f"Showing top 20 of {len(state_anomaly_details)} anomalies")
                
                # Summary recommendation box
                st.markdown("---")
                
                if state_risk_score >= 50:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fee2e220, #fecaca20); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #dc2626;">
                        <h4 style="color: #991b1b; margin-top: 0;">⚠️ HIGH RISK - Immediate Action Required</h4>
                        <ul style="color: #7f1d1d; margin-bottom: 0;">
                            <li><strong>Priority 1:</strong> Deploy field verification teams to {state_critical} critical districts within 48 hours</li>
                            <li><strong>Priority 2:</strong> Escalate to state election commission for enhanced monitoring</li>
                            <li><strong>Priority 3:</strong> Prepare emergency service capacity plans</li>
                            <li><strong>Priority 4:</strong> Initiate data quality audit for outlier detection</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                elif state_risk_score >= 20:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #fef3c720, #fde68a20); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #ea580c;">
                        <h4 style="color: #92400e; margin-top: 0;">📊 ELEVATED RISK - Close Monitoring Required</h4>
                        <ul style="color: #78350f; margin-bottom: 0;">
                            <li><strong>Action 1:</strong> Increase monitoring frequency to weekly</li>
                            <li><strong>Action 2:</strong> Prepare contingency plans for high-alert districts</li>
                            <li><strong>Action 3:</strong> Brief district collectors on emerging patterns</li>
                            <li><strong>Action 4:</strong> Review and validate data sources</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #dcfce720, #bbf7d020); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #16a34a;">
                        <h4 style="color: #166534; margin-top: 0;">✅ LOW RISK - Routine Monitoring</h4>
                        <ul style="color: #14532d; margin-bottom: 0;">
                            <li>Continue standard monitoring protocols</li>
                            <li>No immediate intervention required</li>
                            <li>Review in next scheduled assessment cycle</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success(f"✅ No anomalies detected in {selected_state}. All districts are within normal parameters.")
        else:
            st.info("No state data available for filtering")
    else:
        st.info("State column not available in data")

elif calc_mode == "⚙️ Custom Calculator":
    # Custom calculator with user inputs
    st.markdown("**Enter your own values to calculate a custom risk score:**")
    
    custom_col1, custom_col2 = st.columns(2)
    
    with custom_col1:
        st.markdown("##### Input Parameters")
        
        custom_critical = st.number_input("🔴 Critical Alerts", min_value=0, max_value=1000, value=int(critical), step=1, help="Number of critical severity alerts")
        custom_high = st.number_input("🟠 High Severity Alerts", min_value=0, max_value=1000, value=int(high), step=1, help="Number of high severity alerts")
        custom_anomaly_rate = st.slider("📈 Anomaly Rate (%)", min_value=0.0, max_value=100.0, value=float(anomaly_report['summary']['anomaly_rate']), step=0.1, help="Percentage of anomalous districts")
        
        st.markdown("##### Weight Configuration")
        weight_critical = st.slider("Critical Weight", min_value=1, max_value=20, value=10, help="Multiplier for critical alerts")
        weight_high = st.slider("High Weight", min_value=1, max_value=15, value=5, help="Multiplier for high alerts")
        weight_anomaly = st.slider("Anomaly Rate Weight", min_value=1, max_value=10, value=2, help="Multiplier for anomaly rate")
    
    with custom_col2:
        st.markdown("##### Calculated Risk Score")
        
        # Calculate custom risk score
        custom_risk_score = (custom_critical * weight_critical) + (custom_high * weight_high) + (custom_anomaly_rate * weight_anomaly)
        
        # Display breakdown
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 1rem;">
            <table style="width: 100%; color: #374151;">
                <tr><td><strong>Critical</strong></td><td>{custom_critical} × {weight_critical}</td><td style="text-align: right; color: #dc2626; font-weight: 700;">{custom_critical * weight_critical}</td></tr>
                <tr><td><strong>High</strong></td><td>{custom_high} × {weight_high}</td><td style="text-align: right; color: #ea580c; font-weight: 700;">{custom_high * weight_high}</td></tr>
                <tr><td><strong>Anomaly Rate</strong></td><td>{custom_anomaly_rate:.1f}% × {weight_anomaly}</td><td style="text-align: right; color: #f59e0b; font-weight: 700;">{custom_anomaly_rate * weight_anomaly:.1f}</td></tr>
                <tr style="border-top: 2px solid #e5e7eb;"><td colspan="2"><strong>TOTAL</strong></td><td style="text-align: right; font-size: 1.5rem; font-weight: 800; color: #000000;">{custom_risk_score:.1f}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # Risk level indicator
        if custom_risk_score >= 50:
            custom_color = "#dc2626"
            custom_label = "HIGH RISK"
            custom_action = "Immediate investigation and intervention required"
        elif custom_risk_score >= 20:
            custom_color = "#ea580c"
            custom_label = "ELEVATED RISK"
            custom_action = "Close monitoring and contingency planning needed"
        else:
            custom_color = "#16a34a"
            custom_label = "LOW RISK"
            custom_action = "Continue routine monitoring"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {custom_color}20, {custom_color}10); padding: 1.5rem; border-radius: 12px; border-left: 4px solid {custom_color}; text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: {custom_color};">{custom_risk_score:.0f}</div>
            <div style="font-size: 0.875rem; font-weight: 700; color: {custom_color};">{custom_label}</div>
            <div style="font-size: 0.75rem; color: #475569; margin-top: 0.5rem;">{custom_action}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Threshold reference
        st.markdown("""
        <div style="margin-top: 1rem; padding: 1rem; background: #f8fafc; border-radius: 8px; font-size: 0.8rem; color: #64748b;">
            <strong>Thresholds:</strong> LOW < 20 | ELEVATED 20-50 | HIGH ≥ 50
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 Tip: Not all anomalies are problems. Investigate to determine if the pattern is a data quality issue, a legitimate demographic shift, or requires policy intervention.")

