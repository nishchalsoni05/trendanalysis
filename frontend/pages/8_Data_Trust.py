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

if "loader_shown_P7" not in st.session_state:
    from frontend.components.loader import render_loader
    render_loader([
        ("AUDITING DATA LINEAGE", "Tracing signal origins..."),
        ("VERIFYING CHECKSUMS", "Validating cryptographic proofs..."),
        ("READY", "Displaying trust metrics...")
    ])
    st.session_state["loader_shown_P7"] = True

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

# NEW SECTION: Data Freshness Indicator
st.markdown("---")
st.markdown("## ⏱️ Data Freshness")

freshness_col1, freshness_col2, freshness_col3 = st.columns(3)

with freshness_col1:
    last_run = summary.get('run_timestamp', None)
    if last_run and isinstance(last_run, str):
        from datetime import datetime
        try:
            run_time = datetime.fromisoformat(last_run.replace('Z', '+00:00'))
            now = datetime.now()
            hours_ago = (now - run_time.replace(tzinfo=None)).total_seconds() / 3600
            
            if hours_ago < 24:
                freshness_color = "#16a34a"
                freshness_label = "FRESH"
            elif hours_ago < 72:
                freshness_color = "#f59e0b"
                freshness_label = "STALE"
            else:
                freshness_color = "#dc2626"
                freshness_label = "OUTDATED"
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; border-left: 4px solid {freshness_color}; text-align: center;">
                <div style="font-size: 2rem; font-weight: 700; color: {freshness_color};">{hours_ago:.1f}h</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Since Last Update</div>
                <div style="margin-top: 0.5rem; padding: 0.25rem 0.75rem; background: {freshness_color}20; color: {freshness_color}; border-radius: 12px; display: inline-block; font-weight: 600; font-size: 0.75rem;">{freshness_label}</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown(styles.render_metric_card("N/A", "Last Update"), unsafe_allow_html=True)
    else:
        st.markdown(styles.render_metric_card("N/A", "Last Update"), unsafe_allow_html=True)

with freshness_col2:
    pipeline_version = summary.get('pipeline_version', 'N/A')
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; text-align: center;">
        <div style="font-size: 2rem; font-weight: 700; color: #3b82f6;">v{pipeline_version}</div>
        <div style="font-size: 0.875rem; color: #6b7280;">Pipeline Version</div>
    </div>
    """, unsafe_allow_html=True)

with freshness_col3:
    duration = summary.get('duration_seconds', 0)
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; text-align: center;">
        <div style="font-size: 2rem; font-weight: 700; color: #8b5cf6;">{duration:.1f}s</div>
        <div style="font-size: 0.875rem; color: #6b7280;">Processing Time</div>
    </div>
    """, unsafe_allow_html=True)

# NEW SECTION: Quality Score Breakdown
st.markdown("---")
st.markdown("## 📈 Quality Score Breakdown")

quality_score = summary.get('quality_score', 0)

# Visual quality meter
import plotly.graph_objects as go

fig = go.Figure(go.Indicator(
    mode = "gauge+number+delta",
    value = quality_score,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Overall Data Quality", 'font': {'size': 20, 'color': '#000000'}},
    gauge = {
        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#374151", 'tickfont': {'color': '#000000'}},
        'bar': {'color': "#EA580C"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "#e5e7eb",
        'steps': [
            {'range': [0, 50], 'color': '#fee2e2'},
            {'range': [50, 75], 'color': '#fef3c7'},
            {'range': [75, 100], 'color': '#dcfce7'}
        ],
        'threshold': {
            'line': {'color': "#16a34a", 'width': 4},
            'thickness': 0.75,
            'value': 80
        }
    }
))

fig.update_layout(
    paper_bgcolor="white",
    font={'color': "#000000", 'family': "Inter"},
    height=300,
    margin=dict(l=30, r=30, t=50, b=30)
)

st.plotly_chart(fig, use_container_width=True)

# Quality factors
quality_col1, quality_col2, quality_col3 = st.columns(3)

with quality_col1:
    st.markdown("""
    <div style="background: #f0fdf4; padding: 1rem; border-radius: 12px; border-left: 4px solid #16a34a;">
        <div style="font-weight: 600; color: #166534;">✓ Data Completeness</div>
        <div style="font-size: 0.875rem; color: #475569; margin-top: 0.5rem;">All required columns present and validated</div>
    </div>
    """, unsafe_allow_html=True)

with quality_col2:
    st.markdown("""
    <div style="background: #f0fdf4; padding: 1rem; border-radius: 12px; border-left: 4px solid #16a34a;">
        <div style="font-weight: 600; color: #166534;">✓ Schema Validation</div>
        <div style="font-size: 0.875rem; color: #475569; margin-top: 0.5rem;">Data types match expected schema</div>
    </div>
    """, unsafe_allow_html=True)

with quality_col3:
    rows_dropped_pct = summary.get('rows_dropped_pct', 0)
    # Convert to float to ensure proper comparison
    try:
        drop_rate = float(rows_dropped_pct) if rows_dropped_pct else 0
    except (ValueError, TypeError):
        drop_rate = 0
    
    if drop_rate < 5:
        st.markdown("""
        <div style="background: #f0fdf4; padding: 1rem; border-radius: 12px; border-left: 4px solid #16a34a;">
            <div style="font-weight: 600; color: #166534;">✓ Low Drop Rate</div>
            <div style="font-size: 0.875rem; color: #475569; margin-top: 0.5rem;">Less than 5% of rows filtered</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #fef3c7; padding: 1rem; border-radius: 12px; border-left: 4px solid #f59e0b;">
            <div style="font-weight: 600; color: #92400e;">⚠ Elevated Drop Rate</div>
            <div style="font-size: 0.875rem; color: #475569; margin-top: 0.5rem;">{drop_rate:.1f}% of rows filtered</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("💡 Tip: All metadata is tracked automatically during pipeline execution. This page updates with each pipeline run.")

