"""
Project Aadhaar Sanket - Trend Typology Engine

Classifies each district/state's temporal MVI behavior into actionable categories:
- Persistent Inflow: Sustained high migration activity
- Emerging Inflow: Recent acceleration in migration
- Volatile: High variance, no clear trend
- Stable: Low variance, minimal change
- Reversal: Declining after previous growth

This engine uses deterministic statistical methods:
- Rolling mean analysis
- Linear regression for trend slope
- Variance-based stability assessment

NO ML. Pure statistical classification.
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import MVI_CONFIG


@dataclass
class TrendClassification:
    """Trend classification result for a geographic unit."""
    geo_key: str
    trend_type: str  # persistent_inflow, emerging_inflow, volatile, stable, reversal
    trend_strength: float  # 0-1 score
    slope: float  # Linear trend slope
    variance: float  # Temporal variance
    explanation: str  # Human-readable explanation


# =============================================================================
# CONFIGURATION
# =============================================================================

TREND_CONFIG = {
    "rolling_windows": {
        "short": 3,  # 3-month window
        "long": 6,   # 6-month window
    },
    "thresholds": {
        "slope_high": 2.0,      # MVI units per month
        "slope_moderate": 0.5,
        "variance_high": 10.0,  # High variance threshold
        "variance_low": 2.0,    # Low variance threshold
        "acceleration_threshold": 1.0,  # For emerging detection
    },
    "min_periods": 6,  # Minimum months of data required
}


# =============================================================================
# TREND ANALYSIS FUNCTIONS
# =============================================================================

def calculate_trend_slope(mvi_series: pl.Series) -> float:
    """
    Calculate linear trend slope using least squares regression.
    
    Args:
        mvi_series: Time series of MVI values
        
    Returns:
        Slope coefficient (MVI units per period)
    """
    if len(mvi_series) < 2:
        return 0.0
    
    # Remove nulls
    values = mvi_series.drop_nulls().to_numpy()
    if len(values) < 2:
        return 0.0
    
    # Linear regression: y = mx + b
    x = np.arange(len(values))
    slope, _ = np.polyfit(x, values, 1)
    
    return float(slope)


def calculate_variance(mvi_series: pl.Series) -> float:
    """
    Calculate temporal variance of MVI.
    
    Args:
        mvi_series: Time series of MVI values
        
    Returns:
        Variance value
    """
    values = mvi_series.drop_nulls()
    if len(values) < 2:
        return 0.0
    
    return float(values.var())


def detect_acceleration(mvi_series: pl.Series, window: int = 3) -> float:
    """
    Detect acceleration by comparing recent vs historical slope.
    
    Args:
        mvi_series: Time series of MVI values
        window: Window size for recent period
        
    Returns:
        Acceleration score (positive = accelerating)
    """
    if len(mvi_series) < window * 2:
        return 0.0
    
    values = mvi_series.drop_nulls().to_numpy()
    if len(values) < window * 2:
        return 0.0
    
    # Recent slope
    recent_x = np.arange(window)
    recent_slope, _ = np.polyfit(recent_x, values[-window:], 1)
    
    # Historical slope
    hist_x = np.arange(len(values) - window)
    hist_slope, _ = np.polyfit(hist_x, values[:-window], 1)
    
    return float(recent_slope - hist_slope)


# =============================================================================
# CLASSIFICATION LOGIC
# =============================================================================

def classify_trend_type(
    slope: float,
    variance: float,
    acceleration: float,
    mean_mvi: float
) -> Tuple[str, float, str]:
    """
    Classify trend into one of five categories.
    
    Args:
        slope: Linear trend slope
        variance: Temporal variance
        acceleration: Acceleration score
        mean_mvi: Mean MVI value
        
    Returns:
        (trend_type, strength_score, explanation)
    """
    cfg = TREND_CONFIG["thresholds"]
    
    # High variance = Volatile
    if variance > cfg["variance_high"]:
        strength = min(variance / (cfg["variance_high"] * 2), 1.0)
        return (
            "volatile",
            strength,
            f"High variance ({variance:.1f}) indicates volatile migration patterns"
        )
    
    # Negative slope after positive trend = Reversal
    if slope < -cfg["slope_moderate"] and mean_mvi > 5.0:
        strength = min(abs(slope) / cfg["slope_high"], 1.0)
        return (
            "reversal",
            strength,
            f"Declining trend (slope={slope:.2f}) after previous activity"
        )
    
    # High positive slope + acceleration = Emerging Inflow
    if slope > cfg["slope_moderate"] and acceleration > cfg["acceleration_threshold"]:
        strength = min(slope / cfg["slope_high"], 1.0)
        return (
            "emerging_inflow",
            strength,
            f"Accelerating inflow (slope={slope:.2f}, accel={acceleration:.2f})"
        )
    
    # High positive slope + low variance = Persistent Inflow
    if slope > cfg["slope_high"] and variance < cfg["variance_low"]:
        strength = min(slope / (cfg["slope_high"] * 2), 1.0)
        return (
            "persistent_inflow",
            strength,
            f"Sustained inflow (slope={slope:.2f}, low variance)"
        )
    
    # Moderate positive slope = Persistent Inflow (weaker)
    if slope > cfg["slope_moderate"]:
        strength = slope / cfg["slope_high"]
        return (
            "persistent_inflow",
            strength,
            f"Moderate sustained inflow (slope={slope:.2f})"
        )
    
    # Default: Stable
    strength = 1.0 - min(variance / cfg["variance_low"], 1.0)
    return (
        "stable",
        strength,
        f"Stable baseline (slope={slope:.2f}, variance={variance:.1f})"
    )


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_trend_typology(
    mvi_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date"
) -> pl.DataFrame:
    """
    Classify trend typology for each geographic unit.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
            Required columns: [geo_level, date_column, 'mvi']
        geo_level: Geographic aggregation level
        date_column: Name of date column
        
    Returns:
        DataFrame with trend classifications:
            - geo_key
            - trend_type
            - trend_strength
            - slope
            - variance
            - acceleration
            - mean_mvi
            - explanation
    """
    # Validate input
    required_cols = [geo_level, date_column, "mvi"]
    missing = [c for c in required_cols if c not in mvi_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure date is sorted
    mvi_df = mvi_df.sort([geo_level, date_column])
    
    # Group by geographic unit and analyze
    results = []
    
    for geo_key, group_df in mvi_df.group_by(geo_level):
        # Skip if insufficient data
        if len(group_df) < TREND_CONFIG["min_periods"]:
            continue
        
        mvi_series = group_df["mvi"]
        
        # Calculate metrics
        slope = calculate_trend_slope(mvi_series)
        variance = calculate_variance(mvi_series)
        acceleration = detect_acceleration(mvi_series)
        mean_mvi = float(mvi_series.mean())
        
        # Classify
        trend_type, strength, explanation = classify_trend_type(
            slope, variance, acceleration, mean_mvi
        )
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "trend_type": trend_type,
            "trend_strength": round(strength, 3),
            "slope": round(slope, 3),
            "variance": round(variance, 2),
            "acceleration": round(acceleration, 3),
            "mean_mvi": round(mean_mvi, 2),
            "explanation": explanation,
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_typology_summary(trend_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for trend classifications.
    
    Args:
        trend_df: Output from analyze_trend_typology
        
    Returns:
        Summary dictionary
    """
    total = len(trend_df)
    
    # Count by type
    type_counts = trend_df.group_by("trend_type").agg(
        pl.count().alias("count")
    ).sort("count", descending=True)
    
    distribution = {
        row["trend_type"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in type_counts.to_dicts()
    }
    
    # High-priority zones (persistent + emerging)
    priority_zones = trend_df.filter(
        pl.col("trend_type").is_in(["persistent_inflow", "emerging_inflow"])
    )
    
    return {
        "total_units": total,
        "distribution": distribution,
        "priority_zones": {
            "count": len(priority_zones),
            "percent": round(len(priority_zones) / total * 100, 1),
            "top_5": priority_zones.sort("trend_strength", descending=True)
                .head(5)
                .select(["geo_key", "trend_type", "trend_strength", "explanation"])
                .to_dicts()
        },
        "statistics": {
            "mean_slope": float(trend_df["slope"].mean()),
            "mean_variance": float(trend_df["variance"].mean()),
            "mean_strength": float(trend_df["trend_strength"].mean()),
        }
    }


def print_typology_summary(summary: Dict):
    """Print formatted trend summary."""
    print("\n" + "=" * 70)
    print("TREND TYPOLOGY ANALYSIS")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    
    print("\nTrend Distribution:")
    for trend_type, data in summary["distribution"].items():
        print(f"  {trend_type:20s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    print(f"\nPriority Zones (Persistent + Emerging): {summary['priority_zones']['count']} ({summary['priority_zones']['percent']:.1f}%)")
    
    print("\nTop 5 Priority Zones:")
    for i, zone in enumerate(summary["priority_zones"]["top_5"], 1):
        print(f"  {i}. {zone['geo_key']}")
        print(f"     Type: {zone['trend_type']}, Strength: {zone['trend_strength']:.2f}")
        print(f"     {zone['explanation']}")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Slope: {stats['mean_slope']:.3f}")
    print(f"  Mean Variance: {stats['mean_variance']:.2f}")
    print(f"  Mean Strength: {stats['mean_strength']:.3f}")
