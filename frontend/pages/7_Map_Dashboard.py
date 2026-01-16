"""
Aadhaar Sanket - Interactive Map Dashboard
Visualizes migration trends and patterns on a detailed Indian political map.
"""
import streamlit as st
import plotly.express as px
import polars as pl
import json
import os
from pathlib import Path
import sys

# Setup Path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import frontend.styles as styles
from frontend.components.loader import render_loader

st.set_page_config(layout="wide", page_title="Map Dashboard | Aadhaar Sanket", page_icon="🗺️")

# Apply Global Styles
st.markdown(styles.get_global_css(), unsafe_allow_html=True)

# Custom CSS for Map Dashboard visibility
st.markdown("""
<style>
    /* Fix Widget Labels */
    .stSelectbox label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Style Dropdown Box (Main Container) */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #000000 !important;
    }
    
    /* Fix Dropdown Arrow styling - Force Black */
    .stSelectbox div[data-baseweb="select"] svg {
        fill: #000000 !important;
        stroke: #000000 !important;
        color: #000000 !important;
    }
    
    /* Fix Dropdown Menu Popover Background */
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
    }
    
    /* Fix Dropdown Menu Text Options to Black */
    div[data-baseweb="popover"] li {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Hover state for options */
    div[data-baseweb="popover"] li:hover {
        background-color: #f1f5f9 !important;
        color: #000000 !important;
    }
    
    /* Selected option state */
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #e2e8f0 !important;
        color: #000000 !important;
    }
    
    /* Fix Download Button */
    .stDownloadButton button {
        background-color: #EA580C !important;
        color: white !important;
        border: none !important;
    }
    .stDownloadButton button:hover {
        background-color: #c2410c !important;
    }

    /* Fix Radio Button Text (Standard Map / Stress Monitor) */
    div[role="radiogroup"] p {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* Fix Expander Header (Understanding the Metrics) - STRICT OVERRIDE */
    div[data-testid="stExpander"] > details > summary {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
    }
    
    div[data-testid="stExpander"] > details > summary:hover {
        background-color: #f8fafc !important;
        color: #000000 !important;
    }

    div[data-testid="stExpander"] > details > summary p {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stExpander"] > details > summary svg {
        fill: #000000 !important;
        color: #000000 !important;
    }
    
    div[data-testid="stExpander"] details {
        border-color: #e2e8f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper: Load Data
@st.cache_data
def load_data():
    # Load GeoJSON
    geojson_path = os.path.join(PROJECT_ROOT, "frontend", "assets", "india_districts.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    
    # Load Processed Data
    # prioritizing trend typology as the main layer
    trend_path = os.path.join(PROJECT_ROOT, "processed", "parquet", "trend_typology.parquet")
    if os.path.exists(trend_path):
        import duckdb
        df = duckdb.read_parquet(trend_path).pl()
    else:
        df = pl.DataFrame()
        
    return geojson, df

# Header
st.markdown(styles.render_header("🇮🇳 National Migration Map", "Interactive district-level analysis of migration trends"), unsafe_allow_html=True)

# Load Data
geojson, df = load_data()

if df.is_empty():
    st.error("No data found. Please run the pipeline first.")
    st.stop()

# Prepare Data for Map
# Mapping GeoJSON 'NAME_2' to 'geo_key' (district)
# We might need fuzzy matching later, but for now exact match
# We should also ensure state matching if possible ('NAME_1')

# Create a display DataFrame
display_df = df.clone()
display_df = display_df.with_columns([
    pl.col("trend_type").str.replace("_", " ").str.to_titlecase().alias("Trend"),
    pl.col("trend_strength").alias("Strength"),
    pl.col("slope").alias("Growth Rate"),
    pl.col("variance").alias("Volatility")
])

# Mode Selection
mode = st.radio(
    "View Mode", 
    ["Standard Map", "Stress Monitor"], 
    horizontal=True, 
    label_visibility="collapsed"
)

if mode == "Standard Map":
    # Filters
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("### 🛠️ Controls")
        
        metric = st.selectbox(
            "Select Metric to Visualize",
            ["Trend Type", "Growth Rate", "Volatility", "Strength"]
        )
        
        st.markdown("---")
        st.markdown("### 📥 Download")
        
        # Download CSV
        csv = display_df.write_csv()
        st.download_button(
            "📄 Download Data (CSV)",
            csv,
            "migration_map_data.csv",
            "text/csv",
            use_container_width=True
        )
        
        st.info("Hover over districts to see detailed statistics. Use the camera icon on the map to download the image.")

    with col2:
        # Render Map
        st.markdown("### 🗺️ Interactive Map")
        
        if metric == "Trend Type":
            color_col = "Trend"
            color_scale = None # Categorical
            # Custom colors for trends
            color_discrete = {
                "Persistent Inflow": "#DC2626", # Red
                "Emerging Inflow": "#F59E0B",   # Amber
                "Volatile": "#7C3AED",          # Purple
                "Stable": "#10B981",            # Green
                "Reversal": "#3B82F6"           # Blue
            }
        else:
            color_col = metric
            color_scale = "Viridis" # Continuous
            color_discrete = None

        # Loader Simulation
        map_placeholder = st.empty()
        with map_placeholder.container():
            st.markdown("""
            <style>
            .map-loader {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 400px;
                background: #f8fafc;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            .scanner {
                width: 100%;
                height: 4px;
                background: linear-gradient(90deg, transparent, #3B82F6, transparent);
                animation: scan 2s linear infinite;
            }
            @keyframes scan { 0% { transform: translateY(-50px); } 100% { transform: translateY(50px); } }
            </style>
            <div class="map-loader">
                <h3 style="color: #475569;">Render Network...</h3>
                <span style="color: #94a3b8;">Calibrating Geospatial Coordinates</span>
                <div style="margin-top: 20px; width: 50px; height: 50px; border: 3px solid #cbd5e1; border-top-color: #3B82F6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            </div>
            """, unsafe_allow_html=True)
        
        # We need to map the dataframe 'geo_key' to GeoJSON 'NAME_2'
        # GeoJSON property key for district is properties.NAME_2
        
        fig = px.choropleth_mapbox(
            display_df.to_pandas(),
            geojson=geojson,
            locations="geo_key",
            featureidkey="properties.NAME_2",
            color=color_col,
            color_discrete_map=color_discrete if metric == "Trend Type" else None,
            color_continuous_scale=color_scale,
            hover_name="geo_key",
            hover_data={
                "geo_key": False,
                "Trend": True,
                "Growth Rate": True,
                "Volatility": True,
                "explanation": True
            },
            mapbox_style="carto-positron",
            center={"lat": 22.0, "lon": 78.0},
            zoom=4,
            opacity=0.7,
            height=700
        )
        
        fig.update_traces(
            hovertemplate="<b style='color: white; font-size: 16px;'>%{hovertext}</b><br><br>" +
                          "<span style='color: white;'>Trend: %{customdata[0]}</span><br>" +
                          "<span style='color: white;'>Growth Rate: %{customdata[1]}</span><br>" +
                          "<span style='color: white;'>Volatility: %{customdata[2]}</span><br>" +
                          "<i style='color: #cbd5e1;'>%{customdata[3]}</i><extra></extra>"
        )

        fig.update_layout(
            paper_bgcolor="white", # Remove black background
            plot_bgcolor="white",
            margin=dict(l=0, r=0, t=0, b=0),
            hoverlabel=dict(
                bgcolor="#000000",  # Keep tooltip black for contrast
                font_color="white", 
                font_size=14,
                font_family="Inter, sans-serif",
                bordercolor="#333333"
            ),
            legend=dict(
                font=dict(color="black"),      # Black Text
                bgcolor="rgba(255,255,255,0.9)", # White Background
                bordercolor="#cbd5e1",
                borderwidth=1,
                title_font=dict(color="black"),
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            coloraxis_colorbar=dict(
                title_font=dict(color="black"), # Black Text
                tickfont=dict(color="black"),   # Black Text
                bgcolor="rgba(255,255,255,0.9)", # White Background
                bordercolor="#cbd5e1",
                borderwidth=1
            )
        )
        
        # clear loader and show map
        map_placeholder.empty()
        st.plotly_chart(fig, use_container_width=True)

    # Detailed Data View
    st.markdown("---")
    st.markdown("### 📋 District Details")
    st.dataframe(display_df.select([
        "geo_key", "Trend", "Growth Rate", "Volatility", "explanation"
    ]), use_container_width=True)

elif mode == "Stress Monitor":
    st.markdown("### 🔥 Spatial Stress Monitor")
    
    col_map, col_list = st.columns([2, 1])
    
    # Mock Data for Stress Monitor
    # This simulates the "Lovable" reference image
    cities = [
        {
            "name": "Delhi NCR", "lat": 28.7041, "lon": 77.1025, "stress": 92, "status": "Severe", "color": "#EF4444", "growth": "+4.2%",
            "reason": "Unchecked urban sprawl combined with high seasonal labor influx from UP/Bihar.",
            "solution": "Develop satellite townships and enforce rapid transit connectivity to disperse density."
        },
        {
            "name": "Mumbai Metro", "lat": 19.0760, "lon": 72.8777, "stress": 91, "status": "Severe", "color": "#EF4444", "growth": "+3.8%",
            "reason": "Critical infrastructure saturation; affordable housing deficit driving slum expansion.",
            "solution": "Accelerate slum rehabilitation projects and decentralize commercial zones."
        },
        {
            "name": "Bangalore Urban", "lat": 12.9716, "lon": 77.5946, "stress": 85, "status": "High", "color": "#F59E0B", "growth": "+5.1%",
            "reason": "Explosive IT sector growth attracting skilled workforce faster than civic planning.",
            "solution": "Enhance water infrastructure and expand metro grid to peripheral IT hubs."
        },
        {
            "name": "Chennai Metro", "lat": 13.0827, "lon": 80.2707, "stress": 78, "status": "High", "color": "#F59E0B", "growth": "+2.9%",
            "reason": "Industrial corridor expansion adding pressure on water resources.",
            "solution": "Invest in sustainable water management and industrial housing zones."
        },
        {
            "name": "Hyderabad Metro", "lat": 17.3850, "lon": 78.4867, "stress": 72, "status": "Moderate", "color": "#3B82F6", "growth": "+4.5%",
            "reason": "Balanced growth but trending towards high density in western corridor.",
            "solution": "Proactive zoning regulations for new commercial districts."
        },
        {
            "name": "Pune Metro", "lat": 18.5204, "lon": 73.8567, "stress": 68, "status": "Moderate", "color": "#3B82F6", "growth": "+3.6%",
            "reason": "Education and auto-hub migration creating localized pockets of stress.",
            "solution": "Strengthen public transport links between educational and industrial zones."
        },
        {
            "name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "stress": 32, "status": "Stable", "color": "#10B981", "growth": "+1.1%",
            "reason": "Well-planned urban expansion keeping pace with migration.",
            "solution": "Maintain current successful town planning schemes (TP Schemes)."
        }
    ]
    
    cities_df = pl.DataFrame(cities)
    
    with col_map:
        # Minimalist Glowing Map
        fig = px.scatter_mapbox(
            cities_df.to_pandas(),
            lat="lat",
            lon="lon",
            size="stress",
            color="status",
            color_discrete_map={
                "Severe": "#EF4444",
                "High": "#F59E0B",
                "Moderate": "#3B82F6",
                "Stable": "#10B981"
            },
            hover_name="name",
            hover_data={"lat": False, "lon": False, "stress": True, "growth": True},
            zoom=3.5,
            height=600,
            mapbox_style="carto-positron",
            opacity=0.8,
            title="Population Pressure Hotspots"
        )
        
        fig.update_traces(marker=dict(sizeref=0.5, sizemode='area'))
        
        fig.update_layout(
             paper_bgcolor="white",
             plot_bgcolor="white",
             margin=dict(l=0, r=0, t=30, b=0),
             legend=dict(
                orientation="h",
                yanchor="bottom",
                y=0.02,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#e2e8f0",
                borderwidth=1
             )
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Legend for map
        st.markdown("""
        <div style='display: flex; justify-content: center; gap: 20px; font-size: 0.8rem; color: #64748b;'>
            <div style='display: flex; align-items: center; gap: 5px;'><span style='width: 10px; height: 10px; background: #EF4444; border-radius: 50%;'></span> Severe (>90%)</div>
            <div style='display: flex; align-items: center; gap: 5px;'><span style='width: 10px; height: 10px; background: #F59E0B; border-radius: 50%;'></span> High (75-90%)</div>
            <div style='display: flex; align-items: center; gap: 5px;'><span style='width: 10px; height: 10px; background: #3B82F6; border-radius: 50%;'></span> Moderate (50-75%)</div>
            <div style='display: flex; align-items: center; gap: 5px;'><span style='width: 10px; height: 10px; background: #10B981; border-radius: 50%;'></span> Stable (<50%)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_list:
        st.markdown("#### 🚨 Critical Stress Zones")
        
        for city in cities:
            # Determine card style based on status
            bg_color = "white"
            border_color = city["color"] + "40" # low opacity
            
            # Card Header
            st.markdown(styles.clean_html(f"""
            <div style="
                background: white;
                border: 1px solid {city['color']};
                border-left: 4px solid {city['color']};
                border-radius: 12px;
                padding: 12px;
                margin-bottom: 0px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="color: #1f2937; font-size: 1rem;">{city['name']}</strong>
                    <span style="
                        background: {city['color']}20;
                        color: {city['color']};
                        font-size: 0.7rem;
                        font-weight: 700;
                        padding: 2px 8px;
                        border-radius: 12px;
                        text-transform: uppercase;
                    ">{city['status']}</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">
                    <span>Pressure Index</span>
                    <span style="color: {city['color']}; font-weight: 600;">{city['growth']}</span>
                </div>
                
                <div style="
                    width: 100%;
                    height: 6px;
                    background: #f1f5f9;
                    border-radius: 3px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {city['stress']}%;
                        height: 100%;
                        background: {city['color']};
                        border-radius: 3px;
                    "></div>
                </div>
                
                <div style="text-align: right; font-size: 0.7rem; color: #94a3b8; margin-top: 4px;">
                    {city['stress']}% Saturation
                </div>
            </div>
            """), unsafe_allow_html=True)
            
            # Actionable Insight Expander (Reason & Solution)
            with st.expander(f"💡 Why & How to Fix ({city['name']})"):
                 st.markdown(f"""
                 <div style="font-size: 0.85rem; color: #334155;">
                    <div style="margin-bottom: 8px;">
                        <strong style="color: #DC2626;">🔻 Root Cause:</strong><br>
                        {city['reason']}
                    </div>
                    <div>
                        <strong style="color: #16A34A;">✅ Strategic Solution:</strong><br>
                        {city['solution']}
                    </div>
                 </div>
                 """, unsafe_allow_html=True)
            
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# Vocabulary / Instruction Guide
st.markdown("---")
st.markdown("### 📖 Guide to Map Terminology")

with st.expander("Understanding the Metrics", expanded=True):
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 📊 Trend Categories")
        st.markdown("""
        - **🔴 Persistent Inflow**: Sustained high migration activity over a long period.
        - **🟠 Emerging Inflow**: Recently accelerating migration patterns indicating a new hotspot.
        - **🟣 Volatile**: Highly fluctuating migration numbers (jumps up and down), often indicating seasonal work or temporary displacement.
        - **🟢 Stable**: Consistent population levels with low variance.
        - **🔵 Reversal**: Declining migration numbers after a previous period of growth.
        """)
        
    with col_b:
        st.markdown("#### 📉 Statistical Metrics")
        st.markdown("""
        - **Growth Rate**: The speed at which migration is increasing or decreasing. Positive values mean growth; negative values mean decline.
        - **Volatility**: A measure of unpredictability. High volatility means the migration pattern is erratic and hard to forecast.
        - **Strength (0-1)**: A confidence score. A score close to 1.0 means the detected trend (e.g., "Persistent Inflow") is very clear and strong.
        """)
        
    st.info("💡 **Tip:** Use the 'Select Metric' dropdown at the top to color-code the map by these different values.")

