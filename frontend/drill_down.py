"""
Universal Drill-Down Navigation System - Professional Design
"""

import streamlit as st
from typing import Dict, Any
import polars as pl


def init_navigation():
    """Initialize session state for drill-down navigation."""
    if "drill_down_active" not in st.session_state:
        st.session_state.drill_down_active = False
    if "drill_down_metric" not in st.session_state:
        st.session_state.drill_down_metric = None
    if "drill_down_params" not in st.session_state:
        st.session_state.drill_down_params = {}
    if "drill_down_data" not in st.session_state:
        st.session_state.drill_down_data = None


def navigate_to_metric(metric_name: str, params: Dict[str, Any] = None):
    """Navigate to evidence page for a specific metric."""
    st.session_state.drill_down_active = True
    st.session_state.drill_down_metric = metric_name
    st.session_state.drill_down_params = params or {}
    st.rerun()


def navigate_back():
    """Navigate back to main dashboard."""
    st.session_state.drill_down_active = False
    st.session_state.drill_down_metric = None
    st.session_state.drill_down_params = {}
    st.session_state.drill_down_data = None
    st.rerun()


def render_metric_button(value: str, label: str, metric_id: str, params: Dict = None, **kwargs):
    """Render a clickable metric card that opens evidence page - Clean contained design."""
    import frontend.styles as styles
    
    button_key = f"metric_btn_{metric_id}"
    trend = kwargs.get('trend', '')
    trend_direction = kwargs.get('trend_direction', 'neutral')
    
    # Icon mapping based on metric type
    icon_map = {
        'total_districts': '📊',
        'average_mvi': '📈',
        'high_mvi': '⚠️',
        'elevated_mvi': '📍'
    }
    icon = icon_map.get(metric_id, '📊')
    
    # Color mapping for icons
    color_map = {
        'total_districts': '#3B82F6',  # Blue
        'average_mvi': '#10B981',      # Green
        'high_mvi': '#EF4444',         # Red
        'elevated_mvi': '#F59E0B'      # Amber
    }
    icon_color = color_map.get(metric_id, '#6B7280')
    
    # Trend indicator
    trend_html = ''
    if trend:
        trend_color = '#10B981' if trend_direction == 'down' else ('#EF4444' if trend_direction == 'up' else '#F59E0B')
        trend_html = f'<div style="color: {trend_color}; font-size: 0.75rem; margin-top: 0.25rem;">↗ {trend}</div>'
    
    # Create the complete card with button inside
    card_html = f"""
    <div style="
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #E5E7EB;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    ">
        <div>
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 40px;
                height: 40px;
                background: {icon_color}15;
                border-radius: 8px;
                margin-bottom: 1rem;
                font-size: 1.25rem;
            ">{icon}</div>
            
            <div style="color: #6B7280; font-size: 0.875rem; margin-bottom: 0.5rem; font-weight: 500;">
                {label}
            </div>
            
            <div style="color: #1F2937; font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem;">
                {value}
            </div>
            
            {trend_html}
        </div>
    </div>
    """
    
    st.html(card_html)
    
    # Detail button below the card
    if st.button("🔍 View Details", key=button_key, use_container_width=True):
        navigate_to_metric(metric_id, params)


def render_evidence_page(metric_name: str, params: Dict[str, Any]):
    """Render evidence page for a clicked metric."""
    from src.engines.drill_down_service import DrillDownService
    import frontend.styles as styles
    
    service = DrillDownService()
    
    st.markdown(
        styles.render_header(
            f"Evidence: {metric_name.replace('_', ' ').title()}",
            "Detailed breakdown and source data"
        ),
        unsafe_allow_html=True
    )
    
    if st.button("← Back to Dashboard"):
        navigate_back()
    
    st.markdown("---")
    
    try:
        data = service.get_districts_for_metric(metric_name, params)
        
        if data.is_empty():
            st.warning("No data available for this metric.")
            return
        
        # Summary stats in glass card
        st.markdown("### 📊 Summary")
        
        if "mvi" in data.columns:
            avg_mvi = data.select(pl.col("mvi").mean()).item()
            avg_mvi_str = f"{avg_mvi:.2f}"
            states = data.select("state").n_unique()
            
            st.markdown(styles.clean_html(f"""
            <div class="glass-card">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div style="flex: 1;">
                        <div class="metric-label" style="color: #64748B !important; font-size: 0.85rem;">Total Districts</div>
                        <div class="metric-value" style="color: #000000 !important; font-size: 1.5rem;">{len(data):,}</div>
                    </div>
                    <div style="border-left: 1px solid #E2E8F0; margin: 0 1rem;"></div>
                    <div style="flex: 1;">
                        <div class="metric-label" style="color: #64748B !important; font-size: 0.85rem;">Average MVI</div>
                        <div class="metric-value" style="color: #000000 !important; font-size: 1.5rem;">{avg_mvi_str}</div>
                    </div>
                    <div style="border-left: 1px solid #E2E8F0; margin: 0 1rem;"></div>
                    <div style="flex: 1;">
                        <div class="metric-label" style="color: #64748B !important; font-size: 0.85rem;">States Covered</div>
                        <div class="metric-value" style="color: #000000 !important; font-size: 1.5rem;">{states}</div>
                    </div>
                </div>
            </div>
            """), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Data table with filters
        st.markdown("### 📋 Detailed Data")
        
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            if "state" in data.columns:
                states_list = sorted(data.select("state").unique().to_series().to_list())
                selected_state = st.selectbox("Filter by State", ["All"] + states_list)
                
                if selected_state != "All":
                    data = data.filter(pl.col("state") == selected_state)
        
        with col_filter2:
            if "mvi" in data.columns:
                sort_order = st.selectbox("Sort by MVI", ["Descending", "Ascending"])
                data = data.sort("mvi", descending=(sort_order == "Descending"))
        
        display_columns = ["state", "district", "mvi", "mvi_band", "confidence", "population"]
        available_columns = [col for col in display_columns if col in data.columns]
        
        display_df = data.select(available_columns).to_pandas()
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        if st.button("📥 Export to CSV"):
            csv_data = data.select(available_columns).write_csv()
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"{metric_name}_evidence.csv",
                mime="text/csv"
            )
        
        # Calculation explanation
        st.markdown("---")
        st.markdown("### 🧮 How This Metric is Calculated")
        
        if metric_name == "total_districts":
            explanation = """
**Total Districts Analyzed**

This metric counts all districts in the processed dataset that meet quality thresholds.

**Data Sources:**
- Aadhaar Demographic Updates (2.07M rows)
- Aadhaar Enrolment Data (1.01M rows)

**Quality Filters Applied:**
- Removed districts with insufficient data (< 100 enrolment records)
- Removed districts with invalid geographic codes
- Removed duplicate entries

**Calculation:**
```
COUNT(DISTINCT district)
WHERE quality_score >= threshold
```

**Confidence:** This is a simple count, so confidence is always HIGH.
            """
        elif metric_name in ["high_mvi", "elevated_mvi"]:
            mvi_threshold = "≥ 30" if metric_name == "high_mvi" else "15-30"
            explanation = f"""
**Districts with MVI {mvi_threshold}**

This metric counts districts where the Migration Velocity Index falls in the specified range.

**Step-by-Step Process:**

1. **Calculate MVI for each district:**
   - Count demographic updates (address changes) in time window
   - Get district population from enrolment data
   - MVI = (updates / population) × 100
   - Apply signal separation to filter administrative noise

2. **Filter by MVI range:**
   - Select districts where MVI {mvi_threshold}

3. **Count results:**
   - Total districts matching criteria

**Data Quality:**
- All districts have confidence level: HIGH or MEDIUM
- Signal separation applied to remove ~15-20% administrative noise
- Population baselines from official enrolment records

**Interpretation:**
- High MVI (≥30) = Rapid demographic change, immediate attention needed
- Elevated MVI (15-30) = Significant activity, monitoring recommended
            """
        else:
            explanation = f"Calculation explanation for '{metric_name}' will be displayed here."
        
        st.markdown(styles.clean_html(f"""
        <div class="glass-card">
            {explanation}
        </div>
        """), unsafe_allow_html=True)
        
        # Source datasets
        st.markdown("---")
        st.markdown("### 📁 Source Datasets")
        
        source_data = service.get_source_datasets(metric_name)
        for source in source_data:
            st.markdown(styles.clean_html(f"""
            <div class="glass-card" style="margin-bottom: 0.5rem;">
                <strong>{source['dataset_name']}</strong><br/>
                <span style="color: #64748B; font-size: 0.9rem;">
                    Files: {source['file_count']} | Rows: {source['total_rows']:,}<br/>
                    {source['contribution']}
                </span>
            </div>
            """), unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading evidence data: {e}")
        st.exception(e)


def with_drill_down(main_page_function):
    """Decorator to add drill-down navigation to any page."""
    def wrapper():
        init_navigation()
        
        if st.session_state.drill_down_active and st.session_state.drill_down_metric:
            render_evidence_page(
                st.session_state.drill_down_metric,
                st.session_state.drill_down_params
            )
        else:
            main_page_function()
    
    return wrapper
