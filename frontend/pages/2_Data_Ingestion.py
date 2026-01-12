"""
UIDAI Data Upload Page - Professional Design
"""
import streamlit as st
from pathlib import Path
import sys
import shutil
import time

st.set_page_config(
    page_title="Upload Data | Aadhaar Sanket",
    page_icon="📂",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import frontend.styles as styles
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

st.markdown(
    styles.render_header(
        "Dataset Upload",
        "Hardened data ingestion with full audit trail"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

from src.engines.data_ingestion_manager import HardenedDataIngestionManager

manager = HardenedDataIngestionManager()

# Reset System Modal
@st.dialog("⚠️ Critical System Reset")
def confirm_reset():
    st.markdown("""
    <div class="alert-card-critical">
        <strong>WARNING: This action is irreversible.</strong><br>
        This will permanently delete:
        <ul>
            <li>All processed analytics data</li>
            <li>All uploaded datasets (Enrolment, Demographic, Biometric)</li>
            <li>All staging and manual files</li>
        </ul>
        System will return to factory state.
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    if col1.button("Cancel", type="secondary", use_container_width=True):
        st.rerun()
        
    if col2.button("Confirm Delete", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        if "file_uploader" in st.session_state:
            del st.session_state["file_uploader"]
            
        data_root = Path("data")
        targets = [
            data_root / "manual",
            data_root / "processed",
            data_root / "_staging_uploads",
            data_root / "api_data_aadhar_enrolment",
            data_root / "api_data_aadhar_demographic",
            data_root / "api_data_aadhar_biometric"
        ]
        
        for target in targets:
            if target.exists():
                try:
                    shutil.rmtree(target)
                except Exception:
                    pass
        
        HardenedDataIngestionManager()
        st.success("✅ System Reset Complete!")
        time.sleep(1)
        st.rerun()

col_header, col_btn = st.columns([6, 2])
with col_btn:
    if st.button("🗑️ Reset System", help="Delete ALL data and reset cache", use_container_width=True):
        confirm_reset()

# Status Display
is_valid, validation_status = manager.check_data_availability()
summary = validation_status.get("summary", {})

status_summary = {
    "enrolment": validation_status.get("summary", {}).get("enrolment_files", 0),
    "demographic": validation_status.get("summary", {}).get("demographic_files", 0),
    "biometric": validation_status.get("summary", {}).get("biometric_files", 0)
}

st.markdown("## 📊 Current Data Status")

col1, col2, col3 = st.columns(3)

def get_status_card(count, label):
    icon = "✅" if count > 0 else "❌"
    return styles.render_metric_card(f"{icon} {count}", label, trend_direction="neutral")

with col1:
    st.markdown(get_status_card(status_summary["enrolment"], "Enrolment Files"), unsafe_allow_html=True)

with col2:
    st.markdown(get_status_card(status_summary["demographic"], "Demographic Files"), unsafe_allow_html=True)

with col3:
    st.markdown(get_status_card(status_summary["biometric"], "Biometric Files"), unsafe_allow_html=True)

st.markdown("---")

# Upload Interface
st.markdown("## 📤 Upload New Data")
st.markdown("""
<div class="alert-card-info">
    <strong>Supported Formats:</strong><br>
    • <strong>Archives:</strong> ZIP, RAR, TAR, GZ (Recursive Extraction auto-enabled)<br>
    • <strong>Files:</strong> CSV (Single or Multiple)<br>
    • <strong>Logic:</strong> Content-based auto-classification. Filenames/Folders are ignored.
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "📁 Select Files (Drag & Drop)",
    accept_multiple_files=True,
    type=["csv", "zip", "tar", "gz", "rar"],
    key="file_uploader"
)

if uploaded_files:
    if st.button("🚀 Upload & Process Files", type="primary", use_container_width=True):
        st.markdown("### 🔄 Processing...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Ingesting...")
            progress_bar.progress(30)
            
            results = manager.process_upload(uploaded_files)
            
            progress_bar.progress(100)
            status_text.text("Done!")
            
            st.markdown("### 📋 Audit Log")
            with st.expander("View Processing Details", expanded=True):
                for entry in manager.log:
                    msg = entry["msg"]
                    level = entry.get("level", "INFO")
                    if level == "ERROR":
                        st.error(msg)
                    elif level == "SUCCESS":
                        st.success(msg)
                    else:
                        st.text(msg)
            
            if results["valid"]:
                 st.success("✅ Files organized! Validation scan running...")
                 time.sleep(1)
                 st.rerun()
            else:
                 st.error("❌ Validation Failed. Some required datasets are still missing.")
        
        except Exception as e:
            st.error(f"Critical Error: {e}")

# Manual Fallback
st.markdown("## 🔍 Scan Workspace (Manual Fallback)")

st.markdown("""
<div class="glass-card">
    <p style="margin-bottom: 1rem;">
        <strong>Manual Ingestion:</strong> Use this if UI upload fails or for large datasets.<br>
        1. Paste files/folders into <code>data/manual/</code><br>
        2. Click <strong>Scan Workspace</strong> below.
    </p>
</div>
""", unsafe_allow_html=True)

if st.button("🔎 Scan & Organize Workspace", use_container_width=True):
    st.markdown("### 🔄 Scanning Workspace...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        status_text.text("Scanning data/manual (recursive)...")
        progress_bar.progress(30)
        
        results = manager.scan_and_ingest_all()
        
        progress_bar.progress(100)
        status_text.text("Done!")
        
        st.markdown("### 📋 Audit Log")
        with st.expander("View Scan Details", expanded=True):
            for entry in manager.log:
                msg = entry["msg"]
                level = entry.get("level", "INFO")
                if level == "ERROR":
                    st.error(msg)
                elif level == "SUCCESS":
                    st.success(msg)
                else:
                    st.text(msg)
        
        if results["valid"]:
             st.success("✅ Files successfully organized!")
             time.sleep(1)
             st.rerun()
        else:
             st.warning("⚠️ Scan complete but some datasets are still missing.")
             
    except Exception as e:
        st.error(f"Scan Error: {e}")

st.markdown("---")

# Validation Gate
st.markdown("## ✅ Validation Gate")

if is_valid:
    st.markdown("""
    <div class="alert-card-success">
        <h4>✓ Pipeline Unlocked</h4>
        <p>All required datasets (Enrolment, Demographic, Biometric) are present.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Run Analytics Pipeline", type="primary", use_container_width=True):
        with st.spinner("Running full analytics pipeline..."):
            import subprocess
            res = subprocess.run(["python", "run_pipeline.py"], capture_output=True, text=True, cwd=str(PROJECT_ROOT))
            if res.returncode == 0:
                st.success("Pipeline Completed Successfully!")
                st.code(res.stdout)
            else:
                st.error("Pipeline Failed")
                st.code(res.stderr)
else:
    missing = validation_status.get("errors", [])
    st.markdown(f"""
    <div class="alert-card-critical">
        <h4>⚠️ Pipeline Locked</h4>
        <p>The following datasets are missing:</p>
        <ul>
            {''.join([f'<li>{m.capitalize()} Data</li>' for m in missing])}
        </ul>
        <p><strong>Action Required:</strong> Upload CSVs containing {', '.join(missing)} columns.</p>
    </div>
    """, unsafe_allow_html=True)
