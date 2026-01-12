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

st.markdown("# ⚠️ Forecasts & Early Warnings")
st.markdown("Monitor anomalies and anticipate demographic pressure")

st.markdown("---")

try:
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base
    from src.engines.spatial import add_zone_classification
    from src.engines.anomaly import detect_mvi_anomalies, generate_anomaly_report, generate_alerts
    import polars as pl
    
    # Load and process data
    demographic_df = load_processed_dataset("demographic")
    enrolment_df = load_processed_dataset("enrolment")
    
    demographic_df = apply_signal_weights(demographic_df, "demographic")
    population_df = calculate_population_base(enrolment_df, "district")
    mvi_df = calculate_mvi(demographic_df, population_df, "district")
    mvi_df = add_zone_classification(mvi_df)
    
    # Run anomaly detection
    anomaly_df = detect_mvi_anomalies(mvi_df)
    anomaly_report = generate_anomaly_report(anomaly_df)
    alerts = generate_alerts(anomaly_df)
    
    # Alert summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical = anomaly_report["by_severity"].get("CRITICAL", 0)
        st.metric("Critical Alerts", critical, delta=None)
        
    with col2:
        high = anomaly_report["by_severity"].get("HIGH", 0)
        st.metric("High Severity", high, delta=None)
        
    with col3:
        total = anomaly_report["summary"]["anomaly_count"]
        rate = anomaly_report["summary"]["anomaly_rate"]
        st.metric("Total Anomalies", f"{total} ({rate:.1f}%)")
    
    st.markdown("---")
    
    # Active Alerts
    st.markdown("### 🚨 Active Alerts")
    
    if alerts:
        for alert in alerts:
            if alert.severity == "CRITICAL":
                st.error(f"**{alert.title}**\n\n{alert.summary}")
            elif alert.severity == "HIGH":
                st.warning(f"**{alert.title}**\n\n{alert.summary}")
            else:
                st.info(f"**{alert.title}**\n\n{alert.summary}")
            
            if alert.affected_regions:
                with st.expander("Affected Regions"):
                    for region in alert.affected_regions[:10]:
                        st.write(f"• {region}")
    else:
        st.success("✓ No active alerts requiring attention")
    
    st.markdown("---")
    
    # Anomaly breakdown
    st.markdown("### 📊 Anomaly Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By Type**")
        for atype, count in anomaly_report["by_type"].items():
            if atype != "NORMAL":
                st.write(f"• {atype}: {count}")
    
    with col2:
        st.markdown("**By Severity**")
        for severity, count in anomaly_report["by_severity"].items():
            if severity != "NORMAL":
                st.write(f"• {severity}: {count}")
    
    # Detailed anomaly list
    st.markdown("---")
    st.markdown("### 📋 Anomaly Details")
    
    anomalies_only = anomaly_df.filter(pl.col("is_anomaly") == True).sort("z_score", descending=True)
    
    if len(anomalies_only) > 0:
        display_df = anomalies_only.select([
            "state", "district", "mvi", "z_score", "anomaly_type", "severity"
        ]).head(20).to_pandas()
        
        display_df["z_score"] = display_df["z_score"].round(2)
        display_df["mvi"] = display_df["mvi"].round(2)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No anomalies detected in current data")
    
    # Recommendations
    st.markdown("---")
    st.markdown("### 📝 Recommendations")
    
    risk_level = anomaly_report["interpretation"]["risk_level"]
    recommendation = anomaly_report["interpretation"]["recommendation"]
    
    if risk_level == "HIGH":
        st.error(f"**Risk Level: {risk_level}**\n\n{recommendation}")
    elif risk_level == "MEDIUM":
        st.warning(f"**Risk Level: {risk_level}**\n\n{recommendation}")
    else:
        st.success(f"**Risk Level: {risk_level}**\n\n{recommendation}")

except FileNotFoundError:
    st.warning("⚠️ Data not yet processed. Run the pipeline first.")
except Exception as e:
    st.error(f"Error: {e}")
