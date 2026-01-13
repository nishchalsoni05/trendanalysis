# 🇮🇳 Aadhaar Sanket
### National Migration Intelligence & Demographic Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Transforming UIDAI Data into Actionable Intelligence**  
> Explainable, deterministic, and privacy-preserving migration pressure analytics for data-driven governance.

---

## 📋 Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Navigation Guide](#navigation-guide)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Data Privacy](#data-privacy)

---

## 🎯 Overview

**Aadhaar Sanket** addresses a critical gap in India's data infrastructure: real-time, trustworthy monitoring and prediction of internal migration patterns. The platform processes official UIDAI datasets to provide:

- **Migration Velocity Index (MVI)** - Quantified migration pressure metrics
- **Trend Analysis** - Acceleration, persistence, and seasonality detection
- **Predictive Alerts** - Early warning system for emerging hotspots
- **Policy Recommendations** - Actionable insights for decision-makers
- **100% Explainable** - No ML black boxes, full transparency

### Problem Statement
India lacks a real-time system to track internal migration pressure, identify emerging demographic hotspots, and inform evidence-based policy. Traditional census data is too slow; administrative data is too noisy.

### Our Solution
Aadhaar Sanket solves the **"signal-from-noise"** problem by:
1. Separating true migration signals from clerical updates
2. Computing a novel Migration Velocity Index (MVI)
3. Providing explainable, trustworthy analytics at district-level granularity
4. Maintaining strict privacy through aggregated-only processing

---

## ✨ Key Features

### 📊 Real-Time Intelligence
- Live MVI tracking across 700+ districts
- State and district-level aggregations
- Zone classification (high inflow, stable, decline)

### 📈 Trend Analysis
- Acceleration detection (next crisis zones)
- Persistence vs shock classification
- Seasonal pattern identification
- Population impact quantification

### 🚨 Predictive Alerts
- Confidence-scored forecasts
- Anomaly detection
- Early warning system

### 🏛️ Policy Decisions
- Executive-grade recommendations
- Resource allocation strategies
- Explainable justifications

### 🔒 Privacy-First
- No PII exposure
- District-level granularity only
- Statistical masking
- Offline-first architecture

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Git (for cloning)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/aadhaar-sanket.git
cd aadhaar-sanket
```

2. **Create virtual environment** (recommended)
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the Application

#### Option 1: One-Click Start (Recommended)
```bash
# Windows - Double-click or run:
.\start.bat

# Linux/Mac
./start.sh
```

#### Option 2: Manual Start
```bash
# 1. (Optional) Run analytics pipeline first
python run_pipeline.py

# 2. Launch dashboard
streamlit run frontend/1_National_Overview.py
```

The application will open at **http://localhost:8501**

---

## 🧭 Navigation Guide

The platform features a **government-grade top navigation bar** for intuitive access:

### Primary Navigation Tabs

| Tab | Description | Has Sidebar? |
|-----|-------------|--------------|
| 🏠 **Home** | Landing page with overview and KPIs | No |
| 📊 **Dashboard** | Comprehensive national analytics | Yes |
| 🤖 **AI Intelligence** | Future AI capabilities (coming soon) | No |
| 📈 **Trends** | Migration pressure evolution analysis | No |
| 📉 **Analytics** | Dropdown menu with deep-dive pages | Yes |
| 🏛️ **Decisions** | Policy recommendations | No |
| 📘 **User Guide** | Documentation and help | No |
| ℹ️ **About** | Project info and methodology | No |

### Analytics Dropdown (Deep Dive Pages)
- **Migration Patterns** - Trend types and zone distribution
- **Spatial Stress** - Hotspot detection and clustering
- **Forecasts & Alerts** - Predictive analytics
- **Data Trust** - Quality metrics and confidence scores

---

## ⚙️ Technology Stack

### Backend & Analytics
- **Polars** - High-performance data processing
- **Python 3.11+** - Core analytics engine
- **Prophet** - Time-series forecasting
- **Deterministic Algorithms** - No ML black boxes for core logic

### Frontend & Visualization
- **Streamlit** - Interactive dashboard framework
- **Plotly** - Publication-grade interactive charts
- **Custom CSS** - Government portal aesthetics

### Data Source
- **UIDAI Open Data** - Official aggregated datasets (Enrolment, Demographic Updates, Biometric Updates)

---

## 📁 Project Structure

```
aadhaar-sanket/
├── frontend/
│   ├── Home.py                 # Landing page (NEW ENTRY POINT)
│   ├── Dashboard.py            # Main analytics dashboard
│   ├── AI_Intelligence.py      # AI features (coming soon)
│   ├── About.py                # Project information
│   ├── navigation.py           # Top navigation component
│   ├── styles.py               # Global CSS and styling
│   ├── chart_config.py         # Chart theming
│   └── pages/
│       ├── 2_Data_Ingestion.py
│       ├── 3_Migration_Patterns.py
│       ├── 4_Spatial_Stress_Analysis.py
│       ├── 4_Trends_Analysis.py
│       ├── 5_Forecasts_and_Alerts.py
│       ├── 6_Policy_Decisions.py
│       ├── 7_Data_Trust.py
│       └── 8_User_Guide.py
├── src/
│   ├── config.py
│   └── engines/
│       ├── ingestion.py
│       ├── mvi.py
│       ├── signal_separation.py
│       ├── spatial.py
│       ├── trend_analysis.py
│       ├── forecasting.py
│       └── ...
├── data/                       # Place your CSV files here
│   ├── manual/
│   └── processed/
├── run_pipeline.py             # Analytics pipeline executor
├── start.bat                   # Windows quick start
├── requirements.txt
└── README.md
```

---

## 🔒 Data Privacy & Ethics

### Privacy-First Design
- ✅ **No PII Exposure** - Only aggregated, anonymized data
- ✅ **District-Level Granularity** - No individual/household tracking
- ✅ **Statistical Masking** - Small counts suppressed
- ✅ **Offline Processing** - No cloud dependencies
- ✅ **Explainable Logic** - Full transparency, no black boxes

### Ethical Framework
Migration intelligence is for **welfare, not surveillance**. This platform:
- Identifies areas needing infrastructure support
- Enables proactive resource allocation
- Supports evidence-based policy
- Maintains individual privacy at all times

### Important Note
This is a **demonstration platform**. Production deployment requires formal data sharing agreements with UIDAI and compliance with all applicable regulations.

---

## 📖 How It Works

1. **Data Ingestion** - Load official UIDAI CSV files
2. **Quality Validation** - Strict statistical checks
3. **Signal Separation** - Filter out clerical noise
4. **MVI Calculation** - Compute migration pressure index
5. **Trend Analysis** - Classify patterns (structural, seasonal, etc.)
6. **Forecasting** - Generate confidence-scored predictions
7. **Visualization** - Interactive government-grade dashboard

---

#

## 🏆 Acknowledgments

- **UIDAI** for open data initiative
- **Smart India Hackathon 2024** for the opportunity
- All contributors and reviewers

---

**Built for Smart India Hackathon 2024 | Privacy-Preserving Analytics | Government-Grade Intelligence**

