"""
Project Aadhaar Sanket - Configuration Module

Central configuration for all paths, constants, and parameters.
All configuration is explicit and deterministic.
"""
from pathlib import Path
from typing import Dict, List

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = PROJECT_ROOT / "processed"

# Dataset subdirectories
BIOMETRIC_DIR = DATA_DIR / "api_data_aadhar_biometric"
DEMOGRAPHIC_DIR = DATA_DIR / "api_data_aadhar_demographic"
ENROLMENT_DIR = DATA_DIR / "api_data_aadhar_enrolment"

# Output directories
PARQUET_DIR = PROCESSED_DIR / "parquet"
REPORTS_DIR = PROCESSED_DIR / "reports"

# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

# Standardized column names after normalization
NORMALIZED_COLUMNS: Dict[str, Dict[str, str]] = {
    "biometric": {
        "date": "date",
        "state": "state",
        "district": "district",
        "pincode": "pincode",
        "bio_age_5_17": "age_5_17_count",
        "bio_age_17_": "age_17_plus_count",
    },
    "demographic": {
        "date": "date",
        "state": "state",
        "district": "district",
        "pincode": "pincode",
        "demo_age_5_17": "age_5_17_count",
        "demo_age_17_": "age_17_plus_count",
    },
    "enrolment": {
        "date": "date",
        "state": "state",
        "district": "district",
        "pincode": "pincode",
        "age_0_5": "age_0_5_count",
        "age_5_17": "age_5_17_count",
        "age_18_greater": "age_18_plus_count",
    },
}

# Geographic hierarchy levels
GEO_LEVELS: List[str] = ["state", "district", "pincode"]

# =============================================================================
# SIGNAL SEPARATION WEIGHTS
# =============================================================================
# These weights classify the strength of migration signal vs administrative noise
# Range: 0.0 (pure noise) to 1.0 (strong migration signal)

SIGNAL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "demographic": {
        # Demographic updates are strong migration signals
        # Adults changing address = likely genuine migration
        "age_17_plus": 1.0,
        # Youth updates may indicate family migration
        "age_5_17": 0.6,
    },
    "biometric": {
        # Biometric updates for children are MANDATORY (noise)
        # Rule: Children must update biometrics at ages 5, 15
        "age_5_17": 0.1,
        # Adult biometric updates are weak signals
        # May be re-enrollment, correction, not migration
        "age_17_plus": 0.3,
    },
}

# Justification for weights (documented for auditability):
# - Demographic age 17+ (1.0): Address change by adult = strong mobility indicator
# - Demographic age 5-17 (0.6): May follow family, reduced weight
# - Biometric age 5-17 (0.1): Mandatory update at 5 & 15, mostly noise
# - Biometric age 17+ (0.3): May be correction/re-enrollment, weak signal

# =============================================================================
# MVI (MIGRATION VELOCITY INDEX) CONFIGURATION
# =============================================================================

# MVI Calculation Parameters
MVI_CONFIG = {
    # Normalization factor (per X population)
    "per_population": 1000,
    # Rolling window for temporal smoothing (days)
    "rolling_window_days": 7,
    # Minimum population threshold for valid MVI
    "min_population_threshold": 100,
}

# MVI Interpretation Bands
# These classify MVI values into actionable categories
MVI_BANDS = {
    "stable": {"min": 0, "max": 5, "color": "#22c55e", "label": "Stable"},
    "moderate": {"min": 5, "max": 15, "color": "#eab308", "label": "Moderate"},
    "elevated": {"min": 15, "max": 30, "color": "#f97316", "label": "Elevated"},
    "high_pressure": {"min": 30, "max": float("inf"), "color": "#ef4444", "label": "High Pressure"},
}

# =============================================================================
# ANOMALY DETECTION CONFIGURATION
# =============================================================================

ANOMALY_CONFIG = {
    # Z-score threshold for anomaly detection
    "z_score_threshold": 2.0,
    # Minimum data points for baseline calculation
    "min_baseline_points": 7,
    # Lookback window for baseline (days)
    "baseline_window_days": 30,
}

# =============================================================================
# SPATIAL CONFIGURATION
# =============================================================================

SPATIAL_CONFIG = {
    # H3 resolution levels for different analyses
    # Resolution 4: ~1,770 km² (state-level patterns)
    # Resolution 5: ~253 km² (district-level patterns)
    # Resolution 6: ~36 km² (sub-district patterns)
    "default_resolution": 5,
    "high_resolution": 6,
    "low_resolution": 4,
}

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

# Government-style color palette
UI_COLORS = {
    "primary": "#1e3a5f",      # Navy blue
    "secondary": "#64748b",    # Slate gray
    "background": "#f8fafc",   # Light gray
    "text": "#1e293b",         # Dark slate
    "accent": "#0ea5e9",       # Sky blue
    "success": "#22c55e",      # Green
    "warning": "#eab308",      # Yellow
    "danger": "#ef4444",       # Red
}

# =============================================================================
# DATA QUALITY THRESHOLDS
# =============================================================================

QUALITY_THRESHOLDS = {
    # Maximum allowed null percentage per column
    "max_null_percent": 5.0,
    # Maximum allowed zero percentage for count columns
    "max_zero_percent": 50.0,
    # Date range validation (expected data period)
    "expected_date_start": "2025-01-01",
    "expected_date_end": "2025-12-31",
}
