"""
Aadhaar Sanket - Trends Analysis Page
Executive Intelligence Dashboard for Migration Pressure Evolution

This page answers: "How is migration pressure evolving, where is it accelerating,
and where is it becoming structurally risky?"

Sections:
1. National Trend Overview
2. Trend Heatmap (Time vs Geography)
3. Acceleration & Early Warning Panel
4. Persistence vs Shock Matrix
5. Seasonal Pattern Viewer
6. Population Impact Over Time
7. Explainable Trend Summary
"""
import streamlit as st
from pathlib import Path
import sys
import polars as pl
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Trends Analysis | Aadhaar Sanket",
    page_icon="📈",
    layout="wide",
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import centralized styling system
import frontend.styles as styles
import frontend.drill_down as drill_down
import frontend.chart_config as chart_config

# Apply global CSS
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Enforce Data Availability
from frontend.guardrails import require_data
require_data()

# Render header
st.markdown(
    styles.render_header(
        "Trends Analysis",
        "Migration pressure evolution, momentum, and structural risk indicators"
    ),
    unsafe_allow_html=True
)

st.markdown("---")

# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_trend_data():
    """Load all pre-computed trend datasets."""
    try:
        from src.engines.ingestion import load_processed_dataset
        
        data = {}
        
        # Core datasets
        data["typology"] = load_processed_dataset("trend_typology")
        data["acceleration"] = load_processed_dataset("acceleration")
        data["persistence"] = load_processed_dataset("trend_persistence")
        data["seasonality"] = load_processed_dataset("seasonality")
        data["population_impact"] = load_processed_dataset("population_impact")
        data["confidence"] = load_processed_dataset("trend_confidence")
        
        # Demographic for state mapping and time series
        data["demographic"] = load_processed_dataset("demographic")
        
        return data, True
    except Exception as e:
        st.error(f"Error loading trend data: {e}")
        return {}, False

data, available = load_trend_data()

if not available:
    st.warning("⚠️ Trend analysis data not available. Please run the analytics pipeline first.")
    st.stop()

# Prepare data
typology_df = data["typology"]
acceleration_df = data["acceleration"]
persistence_df = data["persistence"]
seasonality_df = data["seasonality"]
population_impact_df = data["population_impact"]
confidence_df = data["confidence"]
demographic_df = data["demographic"]

# Ensure proper column naming
if "mean_mvi" in typology_df.columns:
    typology_df = typology_df.rename({"mean_mvi": "mvi"})

# =============================================================================
# SECTION 1: NATIONAL TREND OVERVIEW
# =============================================================================

st.markdown("## 📊 National Trend Overview")

col1, col2, col3 = st.columns(3)

with col1:
    # Calculate summary stats from typology
    total_districts = typology_df.height
    
    st.markdown(styles.render_metric_card(
        str(total_districts),
        "Geographic Units Analyzed"
    ), unsafe_allow_html=True)

with col2:
    # High MVI zones
    if "mvi" in typology_df.columns:
        high_mvi_threshold = typology_df.select(pl.col("mvi").quantile(0.75)).item()
        high_mvi_count = typology_df.filter(pl.col("mvi") > high_mvi_threshold).height
        
        st.markdown(styles.render_metric_card(
            str(high_mvi_count),
            "High Pressure Zones",
            trend=f"Top 25% MVI",
            trend_direction="up"
        ), unsafe_allow_html=True)

with col3:
    # Accelerating zones
    high_accel_count = acceleration_df.filter(
        pl.col("acceleration_status") == "accelerating"
    ).height if "acceleration_status" in acceleration_df.columns else 0
    
    st.markdown(styles.render_metric_card(
        str(high_accel_count),
        "Accelerating Zones",
        trend="↑ Increasing Pressure",
        trend_direction="up"
    ), unsafe_allow_html=True)

# MVI Distribution
st.markdown("### Migration Velocity Distribution")

if "mvi" in typology_df.columns:
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=typology_df["mvi"].to_list(),
        nbinsx=50,
        marker_color="#EA580C",
        name="MVI Distribution"
    ))
    
    fig.update_layout(
        title=dict(text="Distribution of Migration Velocity Index Across All Zones", font=dict(color="#111827")),
        xaxis=dict(title=dict(text="MVI (Updates per 1000 Population)", font=dict(color="#111827")), tickfont=dict(color="#1F2937"), gridcolor="rgba(0,0,0,0.1)"),
        yaxis=dict(title=dict(text="Number of Zones", font=dict(color="#111827")), tickfont=dict(color="#1F2937"), gridcolor="rgba(0,0,0,0.1)"),
        plot_bgcolor="#FAF9F6",
        paper_bgcolor="#FAF9F6",
        font=dict(color="#1F2937"),
        height=350,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================================================================
# SECTION 2: TREND TYPE BREAKDOWN
# =============================================================================

st.markdown("## 🎯 Trend Type Classification")

if "trend_type" in typology_df.columns:
    # Count by trend type
    trend_counts = typology_df.group_by("trend_type").agg(
        pl.count().alias("count")
    ).sort("count", descending=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=trend_counts["trend_type"].to_list(),
            values=trend_counts["count"].to_list(),
            marker=dict(colors=["#DC2626", "#EA580C", "#F59E0B", "#16A34A"]),
            hole=0.4
        )])
        
        fig.update_layout(
            title=dict(text="Geographic Units by Trend Type", font=dict(color="#111827")),
            plot_bgcolor="#FAF9F6",
            paper_bgcolor="#FAF9F6",
            font=dict(color="#1F2937"),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("""
        <div class="glass-card">
            <h4 style="margin-top: 0;">Trend Type Definitions</h4>
            <div style="line-height: 2;">
                <div><span class="badge badge-critical">STRUCTURAL</span> - Sustained, long-term pressure</div>
                <div><span class="badge badge-warning">SEASONAL</span> - Cyclical, predictable patterns</div>
                <div><span class="badge badge-warning">CYCLICAL</span> - Repeating patterns</div>
                <div><span class="badge badge-info">VOLATILE</span> - High variability, erratic</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Top zones by type
        if trend_counts.height > 0:
            top_type = trend_counts.head(1)
            st.markdown(f"""
            <div class="alert-card-info">
                <strong>Dominant Pattern:</strong> <strong>{top_type["trend_type"].item().capitalize()}</strong> 
                accounts for <strong>{top_type["count"].item()}</strong> zones 
                ({top_type["count"].item() / total_districts * 100:.1f}% of total)
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# SECTION 3: ACCELERATION & EARLY WARNING PANEL
# =============================================================================

st.markdown("## ⚡ Acceleration & Early Warning Panel")
st.markdown("**Purpose**: Identify zones where migration pressure is *increasing* rapidly (next crisis zones)")

if "acceleration" in acceleration_df.columns and "geo_key" in acceleration_df.columns:
    # Join MVI data with acceleration
    accel_analysis = acceleration_df.join(
        typology_df.select(["geo_key", "mvi"]),
        on="geo_key",
        how="left"
    )
    
    # Create scatter plot
    fig = px.scatter(
        accel_analysis.to_pandas(),
        x="mvi",
        y="acceleration",
        color="acceleration_status" if "acceleration_status" in accel_analysis.columns else None,
        hover_data=["geo_key"],
        color_discrete_map={
            "accelerating": "#DC2626",
            "stable": "#94A3B8",
            "decelerating": "#16A34A"
        } if "acceleration_status" in accel_analysis.columns else None,
        title="Migration Pressure vs Acceleration",
        labels={
            "mvi": "Current MVI (Migration Velocity)",
            "acceleration": "Acceleration (Rate of Change)"
        },
        template="plotly_white"
    )
    
    # Add quadrant lines
    if accel_analysis.height > 0:
        median_mvi = accel_analysis.select(pl.col("mvi").median()).item()
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(0,0,0,0.3)", opacity=0.8)
        fig.add_vline(x=median_mvi, line_dash="dash", line_color="rgba(0,0,0,0.3)", opacity=0.8)
        
        # Add quadrant labels
        max_mvi = accel_analysis.select(pl.col("mvi").max()).item()
        max_accel = accel_analysis.select(pl.col("acceleration").max()).item()
        
        fig.add_annotation(
            x=max_mvi * 0.9, y=max_accel * 0.9,
            text="⚠️ CRITICAL<br>(High + Accelerating)",
            showarrow=False,
            font=dict(size=11, color="#FFFFFF", family="Inter", weight="bold"),
            bgcolor="rgba(220, 38, 38, 0.9)",
            bordercolor="#DC2626",
            borderwidth=2,
            borderpad=6
        )
    
    fig.update_layout(
        height=500,
        template="plotly_dark",
        legend_title="Acceleration Status"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Critical zones table
    if "acceleration_status" in accel_analysis.columns:
        critical_zones = accel_analysis.filter(
            (pl.col("acceleration_status") == "accelerating") &
            (pl.col("mvi") > accel_analysis.select(pl.col("mvi").median()).item())
        ).sort("acceleration", descending=True).head(10)
        
        if critical_zones.height > 0:
            st.markdown("### 🚨 Top 10 Critical Early Warning Zones")
            st.dataframe(
                critical_zones.select(["geo_key", "mvi", "acceleration", "acceleration_status"]).to_pandas(),
                use_container_width=True,
                hide_index=True
            )
else:
    st.info("Acceleration data not available.")

st.markdown("---")

# =============================================================================
# SECTION 4: PERSISTENCE VS SHOCK MATRIX
# =============================================================================

st.markdown("## 🎯 Persistence vs Shock Matrix")
st.markdown("**Purpose**: Distinguish structural migration from temporary anomalies")

if "persistence_score" in persistence_df.columns and "geo_key" in persistence_df.columns:
    # Join persistence with MVI
    persist_analysis = persistence_df.join(
        typology_df.select(["geo_key", "mvi"]),
        on="geo_key",
        how="left"
    )
    
    # Create quadrant chart
    fig = px.scatter(
        persist_analysis.to_pandas(),
        x="persistence_score",
        y="mvi",
        color="persistence_classification" if "persistence_classification" in persist_analysis.columns else None,
        hover_data=["geo_key"],
        color_discrete_map={
            "structural": "#DC2626",
            "transitional": "#EA580C",
            "shock": "#FCD34D"
        } if "persistence_classification" in persist_analysis.columns else None,
        title="Persistence vs Migration Magnitude",
        labels={
            "persistence_score": "Persistence Score (0 = Shock, 1 = Structural)",
            "mvi": "Migration Velocity Index"
        }
    )
    
    # Add quadrant lines
    if persist_analysis.height > 0:
        median_persist = persist_analysis.select(pl.col("persistence_score").median()).item()
        median_mvi = persist_analysis.select(pl.col("mvi").median()).item()
        
        fig.add_hline(y=median_mvi, line_dash="dash", line_color="rgba(0,0,0,0.3)", opacity=0.5)
        fig.add_vline(x=median_persist, line_dash="dash", line_color="rgba(0,0,0,0.3)", opacity=0.5)
        
        # Add quadrant labels
        max_persist = persist_analysis.select(pl.col("persistence_score").max()).item()
        max_mvi = persist_analysis.select(pl.col("mvi").max()).item()
        
        fig.add_annotation(
            x=max_persist * 0.9, y=max_mvi * 0.9,
            text="🔴 STRUCTURAL PRESSURE<br>(High + Persistent)",
            showarrow=False,
            font=dict(size=11, color="#FFFFFF", family="Inter", weight="bold"),
            bgcolor="rgba(220, 38, 38, 0.9)",
            bordercolor="#DC2626",
            borderwidth=2,
            borderpad=6
        )
        
        fig.add_annotation(
            x=0.1, y=max_mvi * 0.9,
            text="⚠️ SHOCK ANOMALIES<br>(High but Temporary)",
            showarrow=False,
            font=dict(size=11, color="#FFFFFF", family="Inter", weight="bold"),
            bgcolor="rgba(234, 88, 12, 0.9)",
            bordercolor="#EA580C",
            borderwidth=2,
            borderpad=6
        )
        
        fig.add_annotation(
            x=max_persist * 0.9, y=median_mvi * 0.3,
            text="✅ STABLE ZONES<br>(Low + Persistent)",
            showarrow=False,
            font=dict(size=11, color="#FFFFFF", family="Inter", weight="bold"),
            bgcolor="rgba(22, 163, 74, 0.9)",
            bordercolor="#16A34A",
            borderwidth=2,
            borderpad=6
        )
    
    fig.update_layout(
        height=500,
        legend_title="Classification"
    )
    chart_config.apply_dark_theme(fig)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Persistence data not available.")

st.markdown("---")

# =============================================================================
# SECTION 5: SEASONAL PATTERN VIEWER
# =============================================================================

st.markdown("## 📅 Seasonal Pattern Viewer")

if seasonality_df.height > 0 and "is_seasonal" in seasonality_df.columns:
    seasonal_count = seasonality_df.filter(pl.col("is_seasonal") == True).height
    total_count = seasonality_df.height
    seasonal_pct = (seasonal_count / total_count * 100) if total_count > 0 else 0
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Show seasonal zones on map/chart
        if "seasonal_strength" in seasonality_df.columns:
            fig = go.Figure()
            
            # Histogram of seasonal strength
            seasonal_zones = seasonality_df.filter(pl.col("is_seasonal") == True)
            
            if seasonal_zones.height > 0:
                fig.add_trace(go.Histogram(
                    x=seasonal_zones["seasonal_strength"].to_list(),
                    nbinsx=30,
                    marker_color="#EA580C",
                    name="Seasonal Strength"
                ))
                
                fig.update_layout(
                    title="Distribution of Seasonal Pattern Strength",
                    xaxis_title="Seasonal Strength Score (0-1)",
                    yaxis_title="Number of Zones",
                    height=350
                )
                chart_config.apply_dark_theme(fig)
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No zones with detected seasonal patterns.")
        else:
            st.info("Seasonal strength data not available.")
    
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin-top: 0;">Seasonality Summary</h4>
            <div style="margin-top: 1.5rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #EA580C;">{seasonal_pct:.1f}%</div>
                <div style="font-size: 0.875rem; font-weight: 600; color: #555; margin-top: 0.5rem;">
                    OF ZONES SHOW SEASONAL PATTERNS
                </div>
                <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="font-size: 1.5rem; font-weight: 700;">{seasonal_count}</div>
                    <div style="font-size: 0.875rem; color: #555;">Seasonal Zones</div>
                </div>
                <div style="margin-top: 1rem;">
                    <div style="font-size: 1.5rem; font-weight: 700;">{total_count - seasonal_count}</div>
                    <div style="font-size: 0.875rem; color: #555;">Non-Seasonal Zones</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="alert-card-info">
        <strong>Seasonality Implications:</strong><br>
        • <strong>{seasonal_count} zones</strong> require predictive planning around peak periods<br>
        • Non-seasonal zones may indicate structural or erratic migration patterns<br>
        • Seasonal forecasting can improve resource allocation efficiency
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Seasonal pattern data not available.")

st.markdown("---")

# =============================================================================
# SECTION 6: POPULATION IMPACT ANALYSIS
# =============================================================================

st.markdown("## 👥 Population Impact Analysis")
st.markdown("**Purpose**: Translate MVI rates into absolute human impact")

if population_impact_df.height > 0 and "affected_population" in population_impact_df.columns:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Impact classification breakdown
        if "impact_classification" in population_impact_df.columns:
            impact_counts = population_impact_df.group_by("impact_classification").agg([
                pl.count().alias("zone_count"),
                pl.col("affected_population").sum().alias("total_affected")
            ]).sort("total_affected", descending=True)
            
            fig = go.Figure()
            
            color_map = {
                "high": "#DC2626",
                "moderate": "#EA580C",
                "low": "#FCD34D"
            }
            
            fig.add_trace(go.Bar(
                x=impact_counts["impact_classification"].to_list(),
                y=impact_counts["total_affected"].to_list(),
                marker_color=[color_map.get(x, "#94A3B8") for x in impact_counts["impact_classification"].to_list()],
                text=impact_counts["total_affected"].to_list(),
                texttemplate='%{text:,.0f}',
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Total Population Affected by Impact Level",
                xaxis_title="Impact Classification",
                yaxis_title="Population Affected",
                height=400,
                showlegend=False
            )
            chart_config.apply_dark_theme(fig)
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Simple distribution
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=population_impact_df["affected_population"].to_list(),
                nbinsx=40,
                marker_color="#EA580C"
            ))
            
            fig.update_layout(
                title="Distribution of Affected Population Across Zones",
                xaxis_title="Affected Population",
                yaxis_title="Number of Zones",
                height=400
            )
            chart_config.apply_dark_theme(fig)
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Summary stats
        total_affected = population_impact_df.select(pl.col("affected_population").sum()).item()
        max_affected = population_impact_df.select(pl.col("affected_population").max()).item()
        
        st.markdown(f"""
        <div class="glass-card">
            <h4 style="margin-top: 0;">Impact Summary</h4>
            <div style="margin-top: 1.5rem;">
                <div style="font-size: 2rem; font-weight: 800; color: #DC2626;">{total_affected:,.0f}</div>
                <div style="font-size: 0.875rem; font-weight: 600; color: #555; margin-top: 0.5rem;">
                    TOTAL POPULATION UNDER PRESSURE
                </div>
                <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid rgba(0,0,0,0.1);">
                    <div style="font-size: 1.5rem; font-weight: 700;">{max_affected:,.0f}</div>
                    <div style="font-size: 0.875rem; color: #555;">Max in Single Zone</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Population impact data not available.")

st.markdown("---")

# =============================================================================
# SECTION 7: EXPLAINABLE TREND SUMMARY
# =============================================================================

st.markdown("## 🧠 Explainable Trend Summary")

# Geography selector
col1, col2 = st.columns([3, 1])

with col1:
    selected_geo = st.selectbox(
        "Select Geography for Detailed Analysis",
        typology_df["geo_key"].to_list() if "geo_key" in typology_df.columns else []
    )

if selected_geo:
    # Get data for selected geography
    geo_typology = typology_df.filter(pl.col("geo_key") == selected_geo)
    geo_accel = acceleration_df.filter(pl.col("geo_key") == selected_geo) if "geo_key" in acceleration_df.columns else None
    geo_persist = persistence_df.filter(pl.col("geo_key") == selected_geo) if "geo_key" in persistence_df.columns else None
    geo_confidence = confidence_df.filter(pl.col("geo_key") == selected_geo) if "geo_key" in confidence_df.columns else None
    
    if geo_typology.height > 0:
        st.markdown(f"### Analysis: **{selected_geo}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mvi_val = geo_typology["mvi"].item()
            trend_type = geo_typology["trend_type"].item() if "trend_type" in geo_typology.columns else "Unknown"
            
            st.markdown(styles.render_metric_card(
                f"{mvi_val:.2f}",
                "Current MVI",
                trend=f"Type: {trend_type.capitalize()}",
                trend_direction="neutral"
            ), unsafe_allow_html=True)
        
        with col2:
            if geo_accel is not None and geo_accel.height > 0:
                accel_status = geo_accel["acceleration_status"].item() if "acceleration_status" in geo_accel.columns else "Unknown"
                accel_val = geo_accel["acceleration"].item() if "acceleration" in geo_accel.columns else 0
                
                trend_dir = "up" if "accelerating" in accel_status.lower() else "down" if "decelerating" in accel_status.lower() else "neutral"
                
                st.markdown(styles.render_metric_card(
                    accel_status.capitalize(),
                    "Acceleration Status",
                    trend=f"Rate: {accel_val:.3f}",
                    trend_direction=trend_dir
                ), unsafe_allow_html=True)
        
        with col3:
            if geo_persist is not None and geo_persist.height > 0:
                persist_class = geo_persist["persistence_classification"].item() if "persistence_classification" in geo_persist.columns else "Unknown"
                persist_score = geo_persist["persistence_score"].item() if "persistence_score" in geo_persist.columns else 0
                
                st.markdown(styles.render_metric_card(
                    persist_class.capitalize(),
                    "Persistence Type",
                    trend=f"Score: {persist_score:.2f}",
                    trend_direction="neutral"
                ),  unsafe_allow_html=True)
        
        # Explainable summary
        st.markdown("### 📝 Plain Language Explanation")
        
        explanation_html = f"""
        <div class="glass-card" style="border-left: 4px solid #EA580C;">
            <h4 style="margin-top: 0;">What This Means</h4>
        """
        
        # Build explanation
        if "trend_type" in geo_typology.columns:
            trend_type = geo_typology["trend_type"].item()
            if trend_type == "structural":
                explanation_html += "<p><strong>Trend Pattern:</strong> This area shows <span style='color: #DC2626;'>sustained, long-term migration pressure</span>. This is not a temporary spike.</p>"
            elif trend_type == "seasonal":
                explanation_html += "<p><strong>Trend Pattern:</strong> Migration here follows <span style='color: #EA580C;'>predictable seasonal cycles</span>. Planning should account for peak periods.</p>"
            elif trend_type == "volatile":
                explanation_html += "<p><strong>Trend Pattern:</strong> This area shows <span style='color: #F59E0B;'>high variability</span> with no clear trend. Requires adaptive monitoring.</p>"
            else:
                explanation_html += f"<p><strong>Trend Pattern:</strong> {trend_type.capitalize()} migration behavior detected.</p>"
        
        if geo_accel is not None and geo_accel.height > 0 and "acceleration_status" in geo_accel.columns:
            accel_status = geo_accel["acceleration_status"].item()
            if accel_status == "accelerating":
                explanation_html += "<p><strong>Momentum:</strong> Pressure is <span style='color: #DC2626;'>increasing rapidly</span>. This zone requires immediate attention.</p>"
            elif accel_status == "decelerating":
                explanation_html += "<p><strong>Momentum:</strong> Pressure is <span style='color: #16A34A;'>decreasing</span>. Situation improving.</p>"
            else:
                explanation_html += "<p><strong>Momentum:</strong> Pressure is stable (no significant acceleration).</p>"
        
        if geo_persist is not None and geo_persist.height > 0 and "persistence_classification" in geo_persist.columns:
            persist_class = geo_persist["persistence_classification"].item()
            if persist_class == "structural":
                explanation_html += "<p><strong>Duration:</strong> This is <span style='color: #DC2626;'>persistent, structural migration</span> requiring long-term policy intervention.</p>"
            elif persist_class == "shock":
                explanation_html += "<p><strong>Duration:</strong> This appears to be a <span style='color: #FCD34D;'>temporary shock or anomaly</span>. Monitor for recurrence.</p>"
            else:
                explanation_html += "<p><strong>Duration:</strong> Pattern is transitional/evolving.</p>"
        
        if geo_confidence is not None and geo_confidence.height > 0 and "confidence_level" in geo_confidence.columns:
            conf_level = geo_confidence["confidence_level"].item()
            conf_colors = {"high": "#16A34A", "medium": "#EA580C", "low": "#DC2626"}
            explanation_html += f"<p><strong>Confidence:</strong> Analysis confidence is <span style='color: {conf_colors.get(conf_level, '#555')};'>{conf_level.upper()}</span> based on data quality and stability metrics.</p>"
        
        explanation_html += "</div>"
        
        st.markdown(styles.clean_html(explanation_html), unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("### 💡 Recommended Actions")
        
        recommendations = []
        
        if geo_accel is not None and geo_accel.height > 0 and "acceleration_status" in geo_accel.columns:
            if geo_accel["acceleration_status"].item() == "accelerating":
                recommendations.append("🚨 Activate early warning protocols and enhanced monitoring")
        
        if geo_persist is not None and geo_persist.height > 0 and "persistence_classification" in geo_persist.columns:
            if geo_persist["persistence_classification"].item() == "structural":
                recommendations.append("📋 Develop long-term infrastructure and service capacity plans")
        
        if "trend_type" in geo_typology.columns and geo_typology["trend_type"].item() == "seasonal":
            recommendations.append("📅 Implement seasonal resource allocation strategies")
        
        if mvi_val > typology_df.select(pl.col("mvi").quantile(0.75)).item():
            recommendations.append("⚡ Priority zone for immediate policy intervention")
        
        if not recommendations:
            recommendations.append("✅ Continue standard monitoring protocols")
        
        for rec in recommendations:
            st.markdown(f"- {rec}")

st.markdown("---")
st.caption("💡 All trend indicators are computed deterministically from historical data. Zero ML black boxes used.")
