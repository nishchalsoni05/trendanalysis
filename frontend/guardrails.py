"""
Project Aadhaar Sanket - Frontend Guardrails

This module provides data availability checks and automatic pipeline
execution for the frontend. It ensures data is available before
rendering any analytics pages.
"""

import streamlit as st
from pathlib import Path
import subprocess
import sys

import frontend.styles as styles


def check_processed_data_exists() -> bool:
    """Check if processed parquet files exist."""
    from src.config import PARQUET_DIR
    
    required_files = ["enrolment.parquet", "demographic.parquet", "biometric.parquet"]
    
    for file in required_files:
        if not (PARQUET_DIR / file).exists():
            return False
    return True


def check_source_data_exists() -> bool:
    """Check if source data exists in any location (manual or api folders)."""
    from src.config import DATA_DIR
    
    # Check manual folder
    manual_dir = DATA_DIR / "manual"
    if manual_dir.exists():
        for subdir in ["enrolment", "demographic", "biometric"]:
            subpath = manual_dir / subdir
            if subpath.exists() and list(subpath.glob("*.csv")):
                return True
    
    # Check API folders
    for folder in ["api_data_aadhar_enrolment", "api_data_aadhar_demographic", "api_data_aadhar_biometric"]:
        api_path = DATA_DIR / folder
        if api_path.exists() and list(api_path.glob("*.csv")):
            return True
    
    return False


def auto_run_pipeline():
    """
    Automatically run the analytics pipeline.
    Shows a status spinner while running.
    """
    from src.config import PROJECT_ROOT
    
    with st.status("🚀 Auto-Running Analytics Pipeline...", expanded=True) as status:
        st.write("Source data detected. Processing automatically...")
        st.write("This may take a moment...")
        
        try:
            result = subprocess.run(
                [sys.executable, "run_pipeline.py"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                status.update(label="✅ Pipeline Complete!", state="complete", expanded=False)
                st.cache_data.clear()
                return True
            else:
                status.update(label="❌ Pipeline Failed", state="error")
                st.error("Pipeline execution failed. Check logs.")
                with st.expander("Error Details"):
                    st.code(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            status.update(label="❌ Pipeline Timeout", state="error")
            st.error("Pipeline took too long. Please run manually.")
            return False
        except Exception as e:
            status.update(label="❌ Pipeline Error", state="error")
            st.error(f"Error: {e}")
            return False


def require_data():
    """
    Enforce data availability on any page.
    
    Logic:
    1. If processed data exists → Allow page to load
    2. If source data exists but no processed data → Auto-run pipeline
    3. If no source data → Show upload warning
    
    This enables users to drop files in data/manual/ and have the
    system automatically process them without manual intervention.
    """
    from src.engines.data_ingestion_manager import HardenedDataIngestionManager
    
    # First, scan and organize any loose files in manual folder
    manager = HardenedDataIngestionManager()
    manager.scan_and_ingest_all()
    
    # Check current state
    has_processed = check_processed_data_exists()
    has_source = check_source_data_exists()
    
    # Case 1: Processed data exists - proceed normally
    if has_processed:
        return True
    
    # Case 2: Source exists but not processed - auto-run pipeline
    if has_source and not has_processed:
        # Only auto-run once per session to prevent loops
        if "auto_pipeline_run" not in st.session_state:
            st.session_state["auto_pipeline_run"] = True
            
            success = auto_run_pipeline()
            
            if success:
                st.rerun()  # Reload to show processed data
            else:
                st.stop()  # Stop on failure
        
        # If already ran but still no processed, show error
        st.error("Pipeline ran but processed data not found. Please check logs.")
        st.stop()
    
    # Case 3: No source data at all - show upload warning
    st.cache_data.clear()
    
    st.markdown(styles.render_header("Data Required", "Aadhaar Sanket"), unsafe_allow_html=True)
    
    st.markdown(styles.clean_html("""
    <div class="alert-card-critical">
        <h3 style="margin-top: 0;">🚫 Action Required: Upload Data</h3>
        <p>The system requires official UIDAI datasets to perform analysis.</p>
        <p><strong>Options:</strong></p>
        <ul>
            <li>Navigate to <strong>Data Upload</strong> in the sidebar to upload files</li>
            <li>Or place CSV files directly in the <code>data/manual/</code> folder and refresh</li>
        </ul>
    </div>
    """), unsafe_allow_html=True)
    
    st.stop()
