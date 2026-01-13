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

st.markdown("---")
st.caption("💡 Tip: Not all anomalies are problems. Investigate to determine if the pattern is a data quality issue, a legitimate demographic shift, or requires policy intervention.")
