## 🎯 Overview

**Aadhaar Sanket** addresses a critical gap in India's data infrastructure: real-time, trustworthy monitoring and prediction of internal migration patterns. The platform processes official UIDAI datasets to provide:

- **Migration Velocity Index (MVI)** - Quantified migration pressure metrics
- **Trend Analysis** - Acceleration, persistence, and seasonality detection
- **Predictive Alerts** - Early warning system for emerging hotspots
- **Policy Recommendations** - Actionable insights for decision-makers
- **100% Explainable** - No ML black boxes, full transparency

### Problem Statement
India lacks a real-time system to track internal migration pressure, identify emerging demographic hotspots, and inform evidence-based policy. Traditional census data is too slow; administrative data is too noisy.

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
