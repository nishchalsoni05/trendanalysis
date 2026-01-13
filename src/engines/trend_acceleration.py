"""
Project Aadhaar Sanket - Trend Acceleration Engine

Early-warning predictive indicator system.

Calculates:
- First derivative (velocity): Rate of MVI change
- Second derivative (acceleration): Rate of velocity change

Classifications:
- Accelerating: Increasing pressure, early warning signal
- Stable: Steady state
- Decelerating: Declining pressure

This provides predictive intelligence for proactive policy response.
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class AccelerationResult:
    """Acceleration analysis result for a geographic unit."""
    geo_key: str
    velocity: float  # Current slope (MVI units per period)
    acceleration: float  # Change in slope
    classification: str  # accelerating, stable, decelerating
    warning_level: str  # high, moderate, low
    explanation: str


# =============================================================================
# CONFIGURATION
# =============================================================================

ACCELERATION_CONFIG = {
    "thresholds": {
        "velocity_high": 2.0,       # High velocity threshold
        "velocity_moderate": 0.5,   # Moderate velocity threshold
        "acceleration_high": 1.0,   # High acceleration threshold
        "acceleration_moderate": 0.3,  # Moderate acceleration threshold
    },
    "windows": {
        "velocity": 3,      # Window for velocity calculation
        "acceleration": 6,  # Window for acceleration calculation
    },
    "min_periods": 6,  # Minimum periods required
}


# =============================================================================
# DERIVATIVE CALCULATIONS
# =============================================================================

def calculate_velocity(mvi_series: pl.Series, window: int = 3) -> float:
    """
    Calculate first derivative (velocity) using recent data.
    
    Velocity = Δ(MVI) / Δt
    
    Args:
        mvi_series: Time series of MVI values
        window: Window size for calculation
        
    Returns:
        Velocity (slope) value
    """
    values = mvi_series.drop_nulls().to_numpy()
    
    if len(values) < window:
        return 0.0
    
    # Use recent window
    recent_values = values[-window:]
    x = np.arange(len(recent_values))
    
    slope, _ = np.polyfit(x, recent_values, 1)
    return float(slope)


def calculate_acceleration(mvi_series: pl.Series, window: int = 6) -> float:
    """
    Calculate second derivative (acceleration).
    
    Acceleration = Δ(velocity) / Δt
    
    Args:
        mvi_series: Time series of MVI values
        window: Window size for calculation
        
    Returns:
        Acceleration value
    """
    values = mvi_series.drop_nulls().to_numpy()
    
    if len(values) < window:
        return 0.0
    
    # Split into two halves
    mid = len(values) // 2
    first_half = values[:mid]
    second_half = values[mid:]
    
    if len(first_half) < 2 or len(second_half) < 2:
        return 0.0
    
    # Calculate slope for each half
    x1 = np.arange(len(first_half))
    slope1, _ = np.polyfit(x1, first_half, 1)
    
    x2 = np.arange(len(second_half))
    slope2, _ = np.polyfit(x2, second_half, 1)
    
    # Acceleration = change in slope
    acceleration = slope2 - slope1
    return float(acceleration)


# =============================================================================
# CLASSIFICATION LOGIC
# =============================================================================

def classify_acceleration(
    velocity: float,
    acceleration: float,
    mean_mvi: float
) -> tuple[str, str, str]:
    """
    Classify acceleration pattern and warning level.
    
    Args:
        velocity: Current velocity (slope)
        acceleration: Acceleration value
        mean_mvi: Mean MVI value
        
    Returns:
        (classification, warning_level, explanation)
    """
    cfg = ACCELERATION_CONFIG["thresholds"]
    
    # Determine classification
    if acceleration > cfg["acceleration_moderate"]:
        classification = "accelerating"
    elif acceleration < -cfg["acceleration_moderate"]:
        classification = "decelerating"
    else:
        classification = "stable"
    
    # Determine warning level
    if classification == "accelerating":
        if velocity > cfg["velocity_high"] and acceleration > cfg["acceleration_high"]:
            warning_level = "high"
            explanation = (
                f"HIGH WARNING: Rapid acceleration (accel={acceleration:.2f}) "
                f"with already high velocity (vel={velocity:.2f}). "
                f"Immediate attention required."
            )
        elif velocity > cfg["velocity_moderate"] or acceleration > cfg["acceleration_high"]:
            warning_level = "moderate"
            explanation = (
                f"MODERATE WARNING: Accelerating pressure (accel={acceleration:.2f}, "
                f"vel={velocity:.2f}). Monitor closely."
            )
        else:
            warning_level = "low"
            explanation = (
                f"Low warning: Mild acceleration detected (accel={acceleration:.2f}). "
                f"Early-stage trend."
            )
    
    elif classification == "decelerating":
        warning_level = "low"
        explanation = (
            f"Declining pressure (accel={acceleration:.2f}, vel={velocity:.2f}). "
            f"Situation improving."
        )
    
    else:  # stable
        if velocity > cfg["velocity_high"]:
            warning_level = "moderate"
            explanation = (
                f"Stable but elevated velocity (vel={velocity:.2f}). "
                f"Sustained high pressure."
            )
        else:
            warning_level = "low"
            explanation = (
                f"Stable conditions (vel={velocity:.2f}, accel={acceleration:.2f})."
            )
    
    return classification, warning_level, explanation


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_acceleration(
    mvi_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date"
) -> pl.DataFrame:
    """
    Analyze acceleration patterns for each geographic unit.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
            Required columns: [geo_level, date_column, 'mvi']
        geo_level: Geographic aggregation level
        date_column: Name of date column
        
    Returns:
        DataFrame with acceleration analysis:
            - geo_key
            - velocity
            - acceleration
            - classification
            - warning_level
            - mean_mvi
            - explanation
    """
    # Validate input
    required_cols = [geo_level, date_column, "mvi"]
    missing = [c for c in required_cols if c not in mvi_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure sorted
    mvi_df = mvi_df.sort([geo_level, date_column])
    
    # Analyze each geographic unit
    results = []
    
    for geo_key, group_df in mvi_df.group_by(geo_level):
        # Skip if insufficient data
        if len(group_df) < ACCELERATION_CONFIG["min_periods"]:
            continue
        
        mvi_series = group_df["mvi"]
        mean_mvi = float(mvi_series.mean())
        
        # Calculate derivatives
        velocity = calculate_velocity(
            mvi_series,
            ACCELERATION_CONFIG["windows"]["velocity"]
        )
        acceleration = calculate_acceleration(
            mvi_series,
            ACCELERATION_CONFIG["windows"]["acceleration"]
        )
        
        # Classify
        classification, warning_level, explanation = classify_acceleration(
            velocity, acceleration, mean_mvi
        )
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "velocity": round(velocity, 3),
            "acceleration": round(acceleration, 3),
            "classification": classification,
            "warning_level": warning_level,
            "mean_mvi": round(mean_mvi, 2),
            "explanation": explanation,
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_acceleration_summary(accel_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for acceleration analysis.
    
    Args:
        accel_df: Output from analyze_acceleration
        
    Returns:
        Summary dictionary
    """
    total = len(accel_df)
    
    # Count by classification
    class_counts = accel_df.group_by("classification").agg(
        pl.count().alias("count")
    )
    
    distribution = {
        row["classification"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in class_counts.to_dicts()
    }
    
    # Warning level distribution
    warning_counts = accel_df.group_by("warning_level").agg(
        pl.count().alias("count")
    )
    
    warning_distribution = {
        row["warning_level"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in warning_counts.to_dicts()
    }
    
    # High warning zones
    high_warning = accel_df.filter(
        pl.col("warning_level") == "high"
    ).sort("acceleration", descending=True)
    
    # Accelerating zones
    accelerating = accel_df.filter(
        pl.col("classification") == "accelerating"
    ).sort("acceleration", descending=True)
    
    return {
        "total_units": total,
        "classification_distribution": distribution,
        "warning_distribution": warning_distribution,
        "high_warning_zones": {
            "count": len(high_warning),
            "percent": round(len(high_warning) / total * 100, 1) if total > 0 else 0,
            "top_10": high_warning.head(10).select([
                "geo_key", "velocity", "acceleration", "warning_level", "explanation"
            ]).to_dicts()
        },
        "accelerating_zones": {
            "count": len(accelerating),
            "top_10": accelerating.head(10).select([
                "geo_key", "velocity", "acceleration", "explanation"
            ]).to_dicts()
        },
        "statistics": {
            "mean_velocity": float(accel_df["velocity"].mean()),
            "mean_acceleration": float(accel_df["acceleration"].mean()),
            "max_acceleration": float(accel_df["acceleration"].max()),
        }
    }


def print_acceleration_summary(summary: Dict):
    """Print formatted acceleration summary."""
    print("\n" + "=" * 70)
    print("TREND ACCELERATION ANALYSIS (Early Warning System)")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    
    print("\nClassification Distribution:")
    for classification, data in summary["classification_distribution"].items():
        print(f"  {classification:15s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    print("\nWarning Level Distribution:")
    for level, data in summary["warning_distribution"].items():
        print(f"  {level:15s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    high_warn = summary["high_warning_zones"]
    print(f"\n⚠ HIGH WARNING ZONES: {high_warn['count']} ({high_warn['percent']:.1f}%)")
    print("(Require immediate attention)")
    
    if high_warn["top_10"]:
        print("\nTop 10 High Warning Zones:")
        for i, zone in enumerate(high_warn["top_10"], 1):
            print(f"  {i:2d}. {zone['geo_key']}")
            print(f"      Velocity: {zone['velocity']:.2f}, Acceleration: {zone['acceleration']:.2f}")
            print(f"      {zone['explanation']}")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Velocity: {stats['mean_velocity']:.3f}")
    print(f"  Mean Acceleration: {stats['mean_acceleration']:.3f}")
    print(f"  Max Acceleration: {stats['max_acceleration']:.3f}")
