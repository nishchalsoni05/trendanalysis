"""
Data Quality Dashboard Page

Comprehensive view of data quality metrics, pipeline stages,
and processing provenance for full transparency.
"""
import streamlit as st
from pathlib import Path
import sys
import json

st.set_page_config(
    page_title="Data Quality & Trust | Aadhaar Sanket",
    page_icon="🛡️",
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

# Render header
st.markdown(
    styles.render_header(
        "Data Quality & Trust",
        "Complete transparency into data processing and quality metrics"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

# Load metadata
try:
    from src.engines.metadata_tracker import MetadataTracker
    metadata = MetadataTracker.load()
    summary = metadata.get("summary", {})
    stages = metadata.get("stages", {})
except ImportError:
    summary = {}
    stages = {}

# Executive Summary
st.markdown("## 🎯 Executive Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        styles.render_metric_card(
            f"{summary.get('quality_score', 0):.1f}",
            "Overall Quality Score",
            trend="✓" if summary.get('quality_score', 0) > 80 else "⚠️",
            trend_direction="up" if summary.get('quality_score', 0) > 80 else "neutral"
        ),
        unsafe_allow_html=True
    )

with col2:
    rows_ingested = summary.get('total_rows_ingested', 'N/A')
    st.markdown(
        styles.render_metric_card(
            f"{rows_ingested:,}" if isinstance(rows_ingested, int) else str(rows_ingested),
            "Total Rows Processed"
        ),
        unsafe_allow_html=True
    )

with col3:
    rows_dropped = summary.get('total_rows_dropped', 0)
    st.markdown(
        styles.render_metric_card(
            f"{rows_dropped:,}" if isinstance(rows_dropped, int) else str(rows_dropped),
            "Rows Dropped/Filtered"
        ),
        unsafe_allow_html=True
    )

with col4:
    drop_pct = summary.get('rows_dropped_pct', 0)
    st.markdown(
        styles.render_metric_card(
            f"{drop_pct:.2f}%" if isinstance(drop_pct, (int, float)) else "N/A",
            "Drop Rate"
        ),
        unsafe_allow_html=True
    )

st.markdown("---")

# Pipeline Metadata
st.markdown("## ⚙️ Pipeline Execution Metadata")

col1, col2 = st.columns(2)

with col1:
    # UPDATED COLORS FOR LIGHT THEME
    st.markdown(styles.clean_html(f"""
    <div class="glass-card">
        <h4 style="margin-top: 0;">Run Information</h4>
        <table style="width: 100%;">
            <tr>
                <td style="padding: 0.5rem 0; font-weight: 600;">Run ID:</td>
                <td style="text-align: right; font-family: monospace;">{summary.get('run_id', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 0.5rem 0; font-weight: 600;">Pipeline Version:</td>
                <td style="text-align: right;">v{summary.get('pipeline_version', 'N/A')}</td>
            </tr>
            <tr>
                <td style="padding: 0.5rem 0; font-weight: 600;">Timestamp:</td>
                <td style="text-align: right;">{summary.get('run_timestamp', 'N/A')[:19] if isinstance(summary.get('run_timestamp'), str) else 'N/A'}</td>
            </tr>
            <tr>
                <td style="padding: 0.5rem 0; font-weight: 600;">Duration:</td>
                <td style="text-align: right;">{summary.get('duration_seconds', 'N/A')} seconds</td>
            </tr>
        </table>
    </div>
    """), unsafe_allow_html=True)

with col2:
    st.markdown(styles.clean_html(f"""
    <div class="glass-card">
        <h4 style="color: #166534; margin-top: 0;">Deterministic Guarantee</h4>
        <p style="margin-bottom: 1rem;">
            This pipeline is <strong>100% deterministic</strong>. Running it multiple times 
            with the same input data will produce <strong>identical results</strong>.
        </p>
        <div style="background: #F0FDF4; padding: 1rem; border-radius: 8px; border-left: 4px solid #166534;">
            <strong style="color: #166534;">✓ DETERMINISTIC</strong><br/>
            <span style="font-size: 0.9rem;">
                All calculations are reproducible<br/>
                No randomness or sampling<br/>
                No ML black boxes
            </span>
        </div>
    </div>
    """), unsafe_allow_html=True)

st.markdown("---")

# Stage-by-Stage Breakdown
st.markdown("## 📋 Stage-by-Stage Quality Metrics")

if stages:
    for stage_name, stage_data in stages.items():
        with st.expander(f"📌 {stage_name.replace('_', ' ').title()}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Using render_metric_card instead of st.metric for consistency
                if stage_data.get('input_rows') is not None:
                    st.markdown(styles.render_metric_card(f"{stage_data['input_rows']:,}", "Input Rows"), unsafe_allow_html=True)
                
            with col2:
                if stage_data.get('rows_dropped') is not None:
                    st.markdown(styles.render_metric_card(f"{stage_data['rows_dropped']:,}", "Rows Dropped"), unsafe_allow_html=True)
            
            with col3:
                if stage_data.get('quality_score') is not None:
                    st.markdown(styles.render_metric_card(f"{stage_data['quality_score']:.1f}/100", "Quality Score"), unsafe_allow_html=True)
            
            # Drop reasons if available
            if stage_data.get('drop_reasons'):
                st.markdown("**Reasons for Row drops:**")
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                for reason, count in stage_data['drop_reasons'].items():
                    st.markdown(f"- <span style='color: #DC2626;'>{count:,} rows</span>: {reason.replace('_', ' ').title()}", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No stage-level metrics available. Run the pipeline with metadata tracking enabled.")

st.markdown("---")

# Data Provenance
st.markdown("## 🗂️ Data Provenance")

# Load data lineage
lineage_file = Path("processed/data_lineage.json")

if lineage_file.exists():
    try:
        with open(lineage_file, 'r') as f:
            lineage = json.load(f)
        
        # Dataset breakdown
        for dataset_name, dataset_info in lineage.get('datasets', {}).items():
            with st.expander(f"📊 {dataset_name.title()} Dataset ({dataset_info.get('file_count', 0)} files)"):
                for file_info in dataset_info.get('files', []):
                    st.markdown(styles.clean_html(f"""
                    <div class="glass-card">
                        <strong style="font-size: 1rem; display: block; margin-bottom: 0.25rem;">{file_info.get('file_name', 'Unknown')}</strong>
                        <div style="font-size: 0.85rem; line-height: 1.5;">
                            <span style="display: inline-block; margin-right: 1rem;">Size: <strong>{file_info.get('size_bytes', 0) / (1024*1024):.2f} MB</strong></span>
                            <span style="display: inline-block; margin-right: 1rem;">Modified: {file_info.get('modified_time', 'Unknown')[:10]}</span>
                            <div style="margin-top: 0.25rem;">
                                Hash: <code style="color: #EA580C; background: #FFF7ED; padding: 2px 6px; border-radius: 4px; font-family: monospace; border: 1px solid #FFEDD5;">{file_info.get('file_hash_partial', 'N/A')}</code>
                            </div>
                        </div>
                    </div>
                    """), unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading data lineage: {e}")
else:
    st.info("No data lineage available. Run the pipeline to generate lineage metadata.")

st.markdown("---")
st.caption("💡 Tip: All metadata is tracked automatically during pipeline execution. This page updates with each pipeline run.")
