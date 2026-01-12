# Project Aadhaar Sanket
### Explainable Demographic Intelligence from Aggregate Data

## Problem Statement
India's population is dynamic, but tracking migration velocity and demographic shifts at a granular level is challenging. Traditional census data is too slow, and raw administrative data is too noisy. This system solves the **"signal-from-noise"** problem in public data, transforming aggregate counts into actionable insights about hyper-local population stress and movement trends without compromising individual privacy.

## What This System Does
- **Ingests** massive raw UIDAI aggregate datasets (Enrolment, Update, Biometric).
- **Cleans** data using strict validation rules to reject statistical anomalies.
- **Separates** true organic migration signals from administrative corrections (noise).
- **Computes** a novel **Migration Velocity Index (MVI)** to quantify town-level influx/outflux.
- **Visualizes** demographic stress and forecasts on an interactive, policy-grade dashboard.

## Tech Stack
- **Backend**: Python, DuckDB, Polars
- **Geospatial**: H3, GeoPandas, PyDeck
- **Forecasting**: Prophet, LightGBM
- **Frontend**: Streamlit
- **Data Source**: Official UIDAI Open Data (Aggregated CSVs)

## Quick Start (One Command)

### Windows - Just Double-Click
```
start.bat
```
The script automatically installs dependencies if needed and starts the dashboard.

### Or Run Manually
```bash
# Install dependencies (first time only)
pip install -r requirements.txt

# Start dashboard
streamlit run frontend/1_National_Overview.py
```

### Run Full Pipeline (Optional)
```bash
# Process raw CSV data first
python run_pipeline.py

# Then start dashboard
streamlit run frontend/1_National_Overview.py
```

## High-Level Workflow
1. **Ingestion**: Load raw CSVs from `data/` directory.
2. **Sanitization**: Apply Great Expectations to validate row quality.
3. **Signal Processing**: Isolate demographic shifts from clerical updates.
4. **Analytics**: Calculate MVI and Spatial Stress scores.
5. **Visualization**: Render interactive maps and reports in Streamlit.

## Important Notes
- This system uses **ONLY** real, aggregated UIDAI open data.
- **NO** personally identifiable information (PII) is processed or stored.
- **NO** simulated or "dummy" data is used; all insights are derived from actual files.
- The `.venv` folder is not included in the source control; you must create it.
