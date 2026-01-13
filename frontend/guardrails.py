
import streamlit as st
from src.engines.data_ingestion_manager import HardenedDataIngestionManager
import frontend.styles as styles

def require_data():
    """
    Enforce data availability on any page.
    
    1. Checks if source data exists (via Ingestion Manager).
    2. Triggers auto-cleanup of artifacts if source is empty.
    3. Clears Streamlit cache if data is invalid/missing.
    4. Stops page execution if data is missing.
    """
    manager = HardenedDataIngestionManager()
    is_valid, status = manager.check_data_availability()
    
    if not is_valid:
        # 1. Clear Cache (Critical to prevent showing stale data from memory)
        st.cache_data.clear()
        
        # 2. Show UI Warning
        st.markdown(styles.render_header("Data Required", "Aadhaar Sanket"), unsafe_allow_html=True)
        
        missing = status.get("errors", [])
        missing_text = ", ".join(missing) if missing else "No datasets found"
        
        st.markdown(styles.clean_html(f"""
        <div class="alert-card-critical">
            <h3 style="margin-top: 0;">🚫 Action Required: Upload Data</h3>
            <p>The system requires official UIDAI datasets to perform analysis.</p>
            <p><strong>Missing:</strong> {missing_text}</p>
            <p style="margin-top: 1rem;">Navigate to <strong>Data Ingestion</strong> in the sidebar to proceed.</p>
        </div>
        """), unsafe_allow_html=True)
        
        # 3. Stop Execution
        st.stop()
    
    return True
