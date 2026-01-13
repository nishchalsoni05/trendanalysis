# 🎯 Aadhaar Sanket - Demographic Intelligence Platform

> **UIDAI Data Hackathon 2026 Submission**  
> Real-time migration analytics and demographic intelligence system for India

---

## 📂 Step 1: Upload Data (Most Important)

Before using the platform, you need to load the UIDAI dataset. Choose **one** of the methods below:

### Method 1: Upload via Frontend (Recommended)

1. Launch the application (instructions in Step 2 below)
2. Go to **Data Upload** section in the left sidebar
3. Upload your file (supported formats: `.csv`, `.zip`, `.rar`)
4. Click **"Run Analytics Pipeline"** button
5. Wait for pipeline completion
6. Navigate to any dashboard section to view results

---

### Method 2: Manual Upload (Alternative)

```
📁 code/
 └── 📁 data/
      └── 📁 manual/
           └── 📦 data.zip  ← Already included, Just Extract It HERE ONLY!
```

**Steps:**

1. Navigate to: `code` → `data` → `manual`
2. You'll find a pre-included ZIP file with the UIDAI hackathon dataset
3. **Extract the ZIP file** in the same folder
4. Ensure extracted files are `.csv` format
5. Launch the application (see Step 2 below)
6. The pipeline will **automatically run** when you open the dashboard

> 💡 **Tip:** You can also directly copy-paste any `.csv` files into the `data/manual/` folder

### 🤖 To Enable AI Features

1. Create a `.env` file in the root folder (if not already present)
2. Copy-paste the following content:

```
GEMINI_API_KEY=AIzaSyCQnkYCLBruXd0QwlUomRnlCBS4U81b0LY
```

> ⚠️ **Note:** Make sure not to exceed the API rate limit, or you can paste your own Gemini API key

---

## 🚀 Step 2: Installation & Running Locally

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or higher |
| Git | Latest |
| OS | Windows / Linux / Mac |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Witcher222/trendanalysis.git
cd trendanalysis

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
```

### Running the Application

#### Option A: One-Click Start (Windows)
```bash
.\start.bat
```

#### Option B: Manual Start
```bash
# Launch the dashboard
streamlit run frontend/1_Overview.py
```

The application opens at: **http://localhost:8501**

---

## 📊 Platform Overview

### Problem Statement
India lacks a real-time system to track internal migration pressure, identify emerging demographic hotspots, and inform evidence-based policy decisions. Traditional census data is delayed; administrative data is noisy.

### Our Solution
**Aadhaar Sanket** transforms official UIDAI datasets into actionable demographic intelligence:

| Feature | Description |
|---------|-------------|
| **Migration Velocity Index (MVI)** | Quantified migration pressure metric |
| **Trend Analysis** | Acceleration, persistence, seasonality detection |
| **Predictive Alerts** | Early warning for emerging hotspots |
| **AI Assistant** | Natural language query interface |
| **100% Explainable** | No ML black boxes, full transparency |

---

## 🗂️ Project Structure

```
code/
├── 📁 data/
│   └── 📁 manual/          ← Drop CSV files here
├── 📁 frontend/
│   ├── 1_Overview.py       ← Main dashboard entry
│   └── 📁 pages/           ← All dashboard pages
├── 📁 src/
│   ├── 📁 engines/         ← Core analytics engines
│   ├── 📁 ai/              ← AI integration
│   └── config.py           ← Configuration
├── 📁 tests/               ← Unit tests
├── 📁 docs/                ← Documentation
├── run_pipeline.py         ← Analytics pipeline
├── requirements.txt        ← Dependencies
└── start.bat              ← One-click launcher
```

---

## 📈 Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | National-level metrics and summary |
| **Data Upload** | Upload and process new datasets |
| **Migration Patterns** | Interactive migration analysis |
| **Trends Analysis** | Temporal trends and forecasting |
| **Spatial Stress Analysis** | Geographic pressure mapping |
| **Forecasts & Alerts** | Predictive analytics |
| **Policy Decisions** | Actionable recommendations |
| **Data Trust** | Data quality and lineage |
| **User Guide** | Documentation and help |
| **AI Assistant** | Natural language queries |
| **AI Chat** | Conversational analytics |

---

## 🔧 Technical Stack

| Category | Technologies |
|----------|--------------|
| **Data Processing** | DuckDB, Polars, PyArrow |
| **Analytics** | LightGBM, Prophet, SciPy |
| **Visualization** | Streamlit, Plotly, PyDeck |
| **Geospatial** | H3, GeoPandas, Folium |
| **AI Integration** | Google Gemini API |
| **Data Quality** | Great Expectations |

---

## 📝 Datasets Used

This platform uses official UIDAI Aadhaar datasets:

- **Enrolment Data** - New Aadhaar registrations by age, location, date
- **Demographic Updates** - Address/identity changes indicating migration
- **Biometric Updates** - Fingerprint/iris updates for verification

---

