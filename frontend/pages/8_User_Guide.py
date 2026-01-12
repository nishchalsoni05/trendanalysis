"""
Aadhaar Sanket - Dashboard Guide & Methodology

A plain-language guide to understanding the dashboard, metrics, and insights.
"""
import streamlit as st
from pathlib import Path
import sys

st.set_page_config(
    page_title="User Guide | Aadhaar Sanket",
    page_icon="📘",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Render header
st.markdown(
    styles.render_header(
        "User Guide",
        "A plain-language guide to understanding demographic intelligence"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

# =============================================================================
# SECTION 1: WHAT THIS SYSTEM DOES
# =============================================================================

st.markdown("## 🎯 What This System Does")

st.markdown("""
**Aadhaar Sanket** is a demographic intelligence system that helps government and policymakers understand **where people are moving** across India.

**The Problem It Solves:**
- Electoral rolls may be outdated if people have moved
- Urban infrastructure may be under strain in high-growth areas
- Census data from 2011 may not reflect current population distribution

**What This Dashboard Shows:**
- Which districts are experiencing high population inflow
- Which areas are stable or declining
- Early warnings when unusual migration patterns appear
- Plain-language insights for policy decisions

**What Makes It Trustworthy:**
- Uses real Aadhaar update data (not simulated)
- Separates genuine migration signals from administrative noise
- Shows confidence levels for all metrics
- Fully explainable - no black-box AI
""")

st.markdown("---")

# =============================================================================
# SECTION 2: KEY TERMS EXPLAINED
# ============================================================================

st.markdown("## 📖 Key Terms Explained")

st.markdown("### Migration Velocity Index (MVI)")
st.markdown(styles.clean_html("""
<div class="glass-card">
<strong style="color: #0F172A;">What it means:</strong> A number that shows how fast an area's population is changing relative to its size.

<strong style="color: #0F172A;">Why it matters:</strong> Helps compare migration activity across different-sized districts fairly.

<strong style="color: #0F172A;">How to read it:</strong>
<ul style="margin-top: 0.5rem; list-style-type: none; padding-left: 0;">
    <li style="margin-bottom: 0.25rem;"><strong>MVI below 5:</strong> <span style="background-color: #F0FDF4; color: #166534; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">Stable</span> - little population change</li>
    <li style="margin-bottom: 0.25rem;"><strong>MVI 5-15:</strong> <span style="background-color: #FEFCE8; color: #B45309; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">Moderate</span> - normal population movement</li>
    <li style="margin-bottom: 0.25rem;"><strong>MVI 15-30:</strong> <span style="background-color: #FFF7ED; color: #EA580C; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">Elevated</span> - significant inflow</li>
    <li style="margin-bottom: 0.25rem;"><strong>MVI above 30:</strong> <span style="background-color: #FEF2F2; color: #DC2626; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">High Pressure</span> - rapid population growth</li>
</ul>

<strong style="color: #0F172A;">Example:</strong> If District A has MVI 35 and District B has MVI 8, District A is experiencing much faster population growth.
</div>
"""), unsafe_allow_html=True)

st.markdown("### Migration Pressure")
st.markdown(styles.clean_html("""
<div class="glass-card">
<strong style="color: #0F172A;">What it means:</strong> The rate at which people are updating their Aadhaar details in a specific area.

<strong style="color: #0F172A;">Why it matters:</strong> High update rates often indicate people moving to new locations.

<strong style="color: #0F172A;">How to read it:</strong> Shown as color-coded zones on maps and charts.
</div>
"""), unsafe_allow_html=True)

st.markdown("### Zone Classifications")
st.markdown(styles.clean_html("""
<div class="glass-card">
<strong style="color: #0F172A;">What they mean:</strong> Simple categories that group areas by migration activity.

<strong style="color: #0F172A;">The Four Zones:</strong>
<ul style="margin-top: 0.5rem; list-style-type: none; padding-left: 0;">
    <li style="margin-bottom: 0.25rem;">🟢 <span style="color: #166534; font-weight: 600;">Stable</span> Low migration activity, population relatively unchanged</li>
    <li style="margin-bottom: 0.25rem;">🟡 <span style="color: #B45309; font-weight: 600;">Moderate Inflow</span> Normal population movement</li>
    <li style="margin-bottom: 0.25rem;">🟠 <span style="color: #EA580C; font-weight: 600;">Elevated</span> Higher than usual inflow, worth monitoring</li>
    <li style="margin-bottom: 0.25rem;">🔴 <span style="color: #DC2626; font-weight: 600;">High Inflow</span> Rapid population growth, may need infrastructure attention</li>
</ul>

<strong style="color: #0F172A;">Why it matters:</strong> Helps prioritize which areas need policy attention.
</div>
"""), unsafe_allow_html=True)

st.markdown("### Color Language")
st.markdown(styles.clean_html("""
<div class="glass-card">
<strong style="color: #0F172A;">Consistent Color Meanings Across the Dashboard:</strong>
<ul style="margin-top: 0.5rem; list-style-type: none; padding-left: 0;">
    <li style="margin-bottom: 0.25rem;">🔴 <strong style="color: #DC2626;">Red</strong> = High Risk / Action Required</li>
    <li style="margin-bottom: 0.25rem;">🟠 <strong style="color: #EA580C;">Orange</strong> = Elevated / Warning</li>
    <li style="margin-bottom: 0.25rem;">🟡 <strong style="color: #B45309;">Amber</strong> = Monitor / Caution</li>
    <li style="margin-bottom: 0.25rem;">🟢 <strong style="color: #166534;">Green</strong> = Stable / Good</li>
    <li style="margin-bottom: 0.25rem;">🔵 <strong style="color: #2563EB;">Blue</strong> = Information / Neutral</li>
</ul>

<strong style="color: #0F172A;">Rule of thumb:</strong> Redder = More urgent, Greener = More stable
</div>
"""), unsafe_allow_html=True)

st.markdown("### Confidence Level")
st.markdown(styles.clean_html("""
<div class="glass-card">
<strong style="color: #0F172A;">What it means:</strong> How reliable the MVI number is for a specific area.

<strong style="color: #0F172A;">Why it varies:</strong> Small districts with few people may show unstable MVI values.

<strong style="color: #0F172A;">How to read it:</strong>
<ul style="margin-top: 0.5rem; list-style-type: none; padding-left: 0;">
    <li style="margin-bottom: 0.25rem;"><strong>High Confidence:</strong> Large population, reliable metric</li>
    <li style="margin-bottom: 0.25rem;"><strong>Medium Confidence:</strong> Moderate population, generally reliable</li>
    <li style="margin-bottom: 0.25rem;"><strong>Low Confidence:</strong> Small population, interpret with caution</li>
</ul>

<strong style="color: #0F172A;">Rule of thumb:</strong> Focus on high-confidence areas for major policy decisions.
</div>
"""), unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 3: HOW MVI IS INTERPRETED
# =============================================================================

st.markdown("## 🔍 How MVI Is Interpreted")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✅ What MVI Tells You")
    st.markdown("""
    - **Relative migration activity** compared to population size
    - **Which areas** are experiencing inflow
    - **How fast** demographic change is happening
    - **Trends over time** when tracked consistently
    """)

with col2:
    st.markdown("### ❌ What MVI Does NOT Tell You")
    st.markdown("""
    - **Exact number** of people who moved
    - **Where people came from** or **where they went**
    - **Why** people are moving
    - **Future migration** with certainty
    """)

st.markdown("### Why Different-Sized Districts Can Be Compared")
st.markdown("""
MVI is **normalized by population**, like calculating a percentage.

**Example:**
- District A: 1,000 updates, 10,000 population → MVI = 100
- District B: 5,000 updates, 100,000 population → MVI = 50

Even though District B has more updates, District A has higher migration velocity relative to its size.

This is like comparing **growth rates** instead of absolute numbers.
""")

st.markdown("---")

# =============================================================================
# SECTION 4: HOW TO READ EACH PAGE
# =============================================================================

st.markdown("## 📄 How to Read Each Page")

st.markdown("### 🏠 National Overview (Home Page)")
st.markdown(styles.render_insight_card(
    "What's happening across India right now?",
    "Get a quick national snapshot before diving into specific regions. View total districts analyzed, high-pressure zones, state-level rankings, and active alerts.",
    "Use this page to prioritize which states or regions to investigate further.",
    "🏠"
), unsafe_allow_html=True)

st.markdown("### 🗺️ Migration Map")
st.markdown(styles.render_insight_card(
    "Which specific districts are experiencing migration?",
    "Interactive table and filters to find specific districts of interest. Filter by state, MVI range, or zone type to narrow down your search.",
    "Identify specific districts that need detailed investigation or resource allocation.",
    "🗺️"
), unsafe_allow_html=True)

st.markdown("### 🔥 Spatial Stress & Hotspots")
st.markdown(styles.render_insight_card(
    "Are there clusters of high-pressure areas?",
    "Identify regions where multiple adjacent districts show high migration. View zone distribution and clustered high-pressure regions by state.",
    "Plan regional interventions and infrastructure expansion for clustered areas.",
    "🔥"
), unsafe_allow_html=True)

st.markdown("### ⚠️ Forecasts & Alerts")
st.markdown(styles.render_insight_card(
    "What unusual patterns need attention?",
    "View active alerts by severity, anomaly breakdown by type, and affected regions for each alert.",
    "Prioritize investigation of critical and high-severity alerts to catch issues early.",
    "⚠️"
), unsafe_allow_html=True)

st.markdown("### 📋 Policy Insights")
st.markdown(styles.render_insight_card(
    "What should policymakers do with this information?",
    "Plain-language executive summary and insights organized by policy domain (electoral, urban planning, census). Includes recommended actions.",
    "Translate data into actionable policy recommendations and communicate with stakeholders.",
    "📋"
), unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 5: DATASETS USED
# =============================================================================

st.markdown("## 📊 Datasets Used")

st.markdown("""
This system uses **three official UIDAI datasets**. All data is aggregated and anonymized - no individual records are exposed.
""")

# Dataset preview functionality
try:
    from src.engines.ingestion import load_processed_dataset
    import polars as pl
    
    tab1, tab2, tab3 = st.tabs(["📁 Demographic Updates", "📁 Biometric Updates", "📁 Enrolment Data"])
    
    with tab1:
        st.markdown("### Demographic Update Dataset")
        st.markdown("""
        **What it represents:** Records of people updating their address or demographic details.
        
        **Why it matters:** Address changes are strong indicators of migration.
        
        **Columns:**
        - **Date:** When the update occurred
        - **State/District/Pincode:** Geographic location
        - **Age 5-17 Count:** Updates by youth
        - **Age 17+ Count:** Updates by adults
        """)
        
        try:
            demo_df = load_processed_dataset("demographic")
            st.markdown(f"**Total Records:** {len(demo_df):,}")
            
            # Show preview - paginated
            preview_df = demo_df.select([
                "date", "state", "district", "age_5_17_count", "age_17_plus_count"
            ]).head(10).to_pandas()
            
            preview_df.columns = [col.replace("_", " ").title() for col in preview_df.columns]
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            st.caption("Showing first 10 records as preview")
        except:
            st.info("Dataset not yet processed. Run the pipeline to view data.")
    
    with tab2:
        st.markdown("### Biometric Update Dataset")
        st.markdown("""
        **What it represents:** Records of people updating their biometric data (fingerprints, iris scans).
        
        **Why it matters:** Mandatory biometric updates (at ages 5 and 15) help establish population baseline.
        
        **Columns:**
        - **Date:** When the update occurred
        - **State/District/Pincode:** Geographic location
        - **Age 5-17 Count:** Biometric updates by youth
        - **Age 17+ Count:** Biometric updates by adults
        """)
        
        try:
            bio_df = load_processed_dataset("biometric")
            st.markdown(f"**Total Records:** {len(bio_df):,}")
            
            preview_df = bio_df.select([
                "date", "state", "district", "age_5_17_count", "age_17_plus_count"
            ]).head(10).to_pandas()
            
            preview_df.columns = [col.replace("_", " ").title() for col in preview_df.columns]
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            st.caption("Showing first 10 records as preview")
        except:
            st.info("Dataset not yet processed. Run the pipeline to view data.")
    
    with tab3:
        st.markdown("### Enrolment Dataset")
        st.markdown("""
        **What it represents:** Total Aadhaar enrollments by age group and location.
        
        **Why it matters:** Provides the population baseline for calculating MVI.
        
        **Columns:**
        - **Date:** When the count was recorded
        - **State/District/Pincode:** Geographic location
        - **Age 0-5 Count:** Enrollments for young children
        - **Age 5-17 Count:** Enrollments for youth
        - **Age 18+ Count:** Enrollments for adults
        """)
        
        try:
            enrol_df = load_processed_dataset("enrolment")
            st.markdown(f"**Total Records:** {len(enrol_df):,}")
            
            preview_df = enrol_df.select([
                "date", "state", "district", "age_0_5_count", "age_5_17_count", "age_18_plus_count"
            ]).head(10).to_pandas()
            
            preview_df.columns = [col.replace("_", " ").title() for col in preview_df.columns]
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            st.caption("Showing first 10 records as preview")
        except:
            st.info("Dataset not yet processed. Run the pipeline to view data.")

except Exception as e:
    st.warning("⚠️ Data preview unavailable. Ensure the pipeline has been run.")

st.markdown("---")

# =============================================================================
# SECTION 6: LIMITATIONS & RESPONSIBLE USE
# =============================================================================

st.markdown("## ⚖️ Limitations & Responsible Use")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### What This System Can Do")
    st.markdown("""
    ✅ Identify areas with high demographic activity  
    ✅ Compare migration velocity across districts  
    ✅ Detect unusual patterns requiring investigation  
    ✅ Provide directional insights for policy planning  
    ✅ Track trends over time consistently  
    """)

with col2:
    st.markdown("### What This System Cannot Do")
    st.markdown("""
    ❌ **Cannot** determine exact number of migrants  
    ❌ **Cannot** identify individuals or track specific people  
    ❌ **Cannot** explain *why* people are moving  
    ❌ **Cannot** predict future migration with certainty  
    ❌ **Cannot** replace ground-truth verification  
    """)

st.markdown("### Responsible Interpretation")
st.markdown("""
**Always remember:**
1. **Aggregate-level insights only** - This system analyzes patterns across thousands of people, not individuals
2. **Correlation ≠ Causation** - High MVI indicates activity, but doesn't explain the cause
3. **Verify before acting** - Use this as a screening tool, not the final decision
4. **Context matters** - Consider local events, policies, and seasonal patterns
5. **Privacy-preserving** - All data is aggregated and anonymized
6. **No AI Hallucinations** - All insights are based on deterministic statistical analysis
""")

st.markdown("---")

st.markdown("### 💡 Questions or Feedback?")
st.markdown("""
This dashboard is designed to support evidence-based policymaking.

If you have questions about:
- How to interpret specific metrics
- Data quality or methodology
- Policy applications

Please refer to the technical documentation or contact the system administrators.
""")

st.markdown("---")
st.caption("Aadhaar Sanket - Demographic Intelligence for Governance | Version 1.0")
