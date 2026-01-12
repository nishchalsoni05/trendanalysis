"""
Project Aadhaar Sanket - Migration Velocity Index (MVI) Engine

This is the CORE INTELLECTUAL ASSET of the analytics system.

The Migration Velocity Index (MVI) measures the rate of demographic
change relative to population base, enabling:
- Cross-region comparability (normalized by population)
- Temporal trend analysis (rolling windows)
- Policy-relevant interpretation (action bands)

MVI Formula:
-----------
MVI = (Signal-Adjusted Updates / Population Base) × 1000

Where:
- Signal-Adjusted Updates = Output from signal separation engine
- Population Base = Total enrolments for the geographic unit
- Normalized per 1,000 population for interpretability

Interpretation Bands:
--------------------
| MVI Range | Classification | Meaning |
|-----------|----------------|---------|
| < 5       | Stable         | Minimal demographic churn |
| 5-15      | Moderate       | Normal migration activity |
| 15-30     | Elevated       | Significant population movement |
| > 30      | High Pressure  | Intense demographic stress |

Design Principles:
- MVI is explainable and defensible
- All parameters are configurable
- Uncertainty is explicitly communicated
- Edge cases are handled transparently
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import polars as pl
import numpy as np

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import MVI_CONFIG, MVI_BANDS


# =============================================================================
# MVI DATA STRUCTURES
# =============================================================================

@dataclass
class MVIResult:
    """Represents MVI calculation result for a geographic unit."""
    geo_key: str
    mvi_value: float
    band: str
    band_color: str
    population_base: int
    signal_adjusted_updates: float
    raw_updates: int
    confidence: str
    interpretation: str


# =============================================================================
# POPULATION BASE CALCULATION
# =============================================================================

def calculate_population_base(
    enrolment_df: pl.DataFrame,
    geo_level: str = "district"
) -> pl.DataFrame:
    """
    Calculate population base from enrolment data.
    
    The population base is the denominator for MVI calculation.
    It represents the total Aadhaar-registered population in each
    geographic unit.
    
    Logic:
    - Sum all age groups from enrolment data
    - Aggregate by geographic level
    - Handle missing/zero values
    
    Args:
        enrolment_df: DataFrame with enrolment counts
        geo_level: 'state', 'district', or 'pincode'
        
    Returns:
        DataFrame with population base per geographic unit
    """
    # Identify enrolment count columns
    age_columns = [c for c in enrolment_df.columns if "count" in c.lower()]
    
    if not age_columns:
        # Try alternate column names from original data
        age_columns = ["age_0_5", "age_5_17", "age_18_greater"]
        age_columns = [c for c in age_columns if c in enrolment_df.columns]
    
    if not age_columns:
        raise ValueError("No age/count columns found in enrolment data")
    
    # Define geographic grouping columns
    geo_columns = {
        "state": ["state"],
        "district": ["state", "district"],
        "pincode": ["state", "district", "pincode"],
    }
    
    group_cols = geo_columns.get(geo_level, ["state", "district"])
    existing_group_cols = [c for c in group_cols if c in enrolment_df.columns]
    
    # Calculate total population (sum of all age groups)
    enrolment_df = enrolment_df.with_columns(
        sum([pl.col(c).cast(pl.Float64) for c in age_columns]).alias("total_population")
    )
    
    # Aggregate by geographic level
    population_base = enrolment_df.group_by(existing_group_cols).agg(
        pl.col("total_population").sum().alias("population_base")
    )
    
    # Filter out zero/null population (invalid for MVI calculation)
    population_base = population_base.filter(
        pl.col("population_base") > MVI_CONFIG["min_population_threshold"]
    )
    
    return population_base


def get_latest_population_snapshot(
    enrolment_df: pl.DataFrame,
    geo_level: str = "district"
) -> pl.DataFrame:
    """
    Get the most recent population snapshot per geographic unit.
    
    For time-series analysis, we need a stable population base.
    This uses the most recent enrolment data as the denominator.
    
    Args:
        enrolment_df: DataFrame with enrolment data
        geo_level: Geographic aggregation level
        
    Returns:
        DataFrame with latest population per geography
    """
    geo_columns = {
        "state": ["state"],
        "district": ["state", "district"],
        "pincode": ["state", "district", "pincode"],
    }
    
    group_cols = geo_columns.get(geo_level, ["state", "district"])
    existing_group_cols = [c for c in group_cols if c in enrolment_df.columns]
    
    if "date" in enrolment_df.columns:
        # Get the latest date per geography
        latest = enrolment_df.group_by(existing_group_cols).agg(
            pl.col("date").max().alias("latest_date")
        )
        
        # Join back to get all columns for latest date
        enrolment_df = enrolment_df.join(
            latest,
            on=existing_group_cols,
            how="inner"
        ).filter(pl.col("date") == pl.col("latest_date"))
    
    return calculate_population_base(enrolment_df, geo_level)


# =============================================================================
# MVI CALCULATION
# =============================================================================

def calculate_mvi(
    signal_df: pl.DataFrame,
    population_df: pl.DataFrame,
    geo_level: str = "district"
) -> pl.DataFrame:
    """
    Calculate Migration Velocity Index.
    
    MVI = (Signal-Adjusted Updates / Population Base) × 1000
    
    Args:
        signal_df: DataFrame with signal-adjusted update counts
        population_df: DataFrame with population base
        geo_level: Geographic aggregation level
        
    Returns:
        DataFrame with MVI values and interpretations
    """
    geo_columns = {
        "state": ["state"],
        "district": ["state", "district"],
        "pincode": ["state", "district", "pincode"],
    }
    
    group_cols = geo_columns.get(geo_level, ["state", "district"])
    existing_group_cols = [c for c in group_cols if c in signal_df.columns]
    
    # Aggregate signals by geography
    signal_agg = signal_df.group_by(existing_group_cols).agg([
        pl.col("total_signal_adjusted").sum().alias("signal_adjusted_sum"),
        pl.col("total_raw_count").sum().alias("raw_count_sum"),
    ])
    
    # Join with population base
    mvi_df = signal_agg.join(population_df, on=existing_group_cols, how="inner")
    
    # Calculate MVI
    per_population = MVI_CONFIG["per_population"]
    
    mvi_df = mvi_df.with_columns(
        (pl.col("signal_adjusted_sum") / pl.col("population_base") * per_population)
        .alias("mvi")
    )
    
    # Classify into bands
    mvi_df = classify_mvi_bands(mvi_df)
    
    # Add confidence indicator
    mvi_df = add_confidence_indicator(mvi_df)
    
    return mvi_df


def classify_mvi_bands(df: pl.DataFrame) -> pl.DataFrame:
    """
    Classify MVI values into interpretation bands.
    
    Bands defined in config:
    - Stable: MVI < 5
    - Moderate: 5 ≤ MVI < 15
    - Elevated: 15 ≤ MVI < 30
    - High Pressure: MVI ≥ 30
    
    Args:
        df: DataFrame with 'mvi' column
        
    Returns:
        DataFrame with band classification and color
    """
    # Create band classification expression
    band_expr = pl.when(pl.col("mvi") < MVI_BANDS["stable"]["max"]).then(pl.lit("Stable"))
    band_expr = band_expr.when(pl.col("mvi") < MVI_BANDS["moderate"]["max"]).then(pl.lit("Moderate"))
    band_expr = band_expr.when(pl.col("mvi") < MVI_BANDS["elevated"]["max"]).then(pl.lit("Elevated"))
    band_expr = band_expr.otherwise(pl.lit("High Pressure"))
    
    df = df.with_columns(band_expr.alias("mvi_band"))
    
    # Add color for visualization
    color_expr = pl.when(pl.col("mvi_band") == "Stable").then(pl.lit(MVI_BANDS["stable"]["color"]))
    color_expr = color_expr.when(pl.col("mvi_band") == "Moderate").then(pl.lit(MVI_BANDS["moderate"]["color"]))
    color_expr = color_expr.when(pl.col("mvi_band") == "Elevated").then(pl.lit(MVI_BANDS["elevated"]["color"]))
    color_expr = color_expr.otherwise(pl.lit(MVI_BANDS["high_pressure"]["color"]))
    
    df = df.with_columns(color_expr.alias("mvi_color"))
    
    return df


def add_confidence_indicator(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add confidence indicator based on population size.
    
    Higher population = more reliable MVI
    Lower population = less reliable (small denominator effects)
    
    Args:
        df: DataFrame with MVI and population_base
        
    Returns:
        DataFrame with confidence indicator
    """
    min_threshold = MVI_CONFIG["min_population_threshold"]
    
    # Confidence levels based on population
    confidence_expr = (
        pl.when(pl.col("population_base") >= 10000).then(pl.lit("HIGH"))
        .when(pl.col("population_base") >= 1000).then(pl.lit("MEDIUM"))
        .when(pl.col("population_base") >= min_threshold).then(pl.lit("LOW"))
        .otherwise(pl.lit("INSUFFICIENT"))
    )
    
    df = df.with_columns(confidence_expr.alias("confidence"))
    
    return df


# =============================================================================
# TEMPORAL MVI ANALYSIS
# =============================================================================

def calculate_rolling_mvi(
    signal_df: pl.DataFrame,
    population_df: pl.DataFrame,
    geo_level: str = "district",
    window_days: int = None
) -> pl.DataFrame:
    """
    Calculate MVI with rolling temporal window.
    
    Rolling windows smooth out daily fluctuations and reveal
    underlying trends.
    
    Args:
        signal_df: DataFrame with daily signal counts
        population_df: DataFrame with population base
        geo_level: Geographic aggregation level
        window_days: Rolling window size (default from config)
        
    Returns:
        DataFrame with rolling MVI
    """
    if window_days is None:
        window_days = MVI_CONFIG["rolling_window_days"]
    
    geo_columns = {
        "state": ["state"],
        "district": ["state", "district"],
        "pincode": ["state", "district", "pincode"],
    }
    
    group_cols = geo_columns.get(geo_level, ["state", "district"])
    existing_group_cols = [c for c in group_cols if c in signal_df.columns]
    
    if "date" not in signal_df.columns:
        # No date column, calculate simple MVI
        return calculate_mvi(signal_df, population_df, geo_level)
    
    # Sort by geography and date
    signal_df = signal_df.sort(existing_group_cols + ["date"])
    
    # Apply rolling sum to signal
    rolling_df = signal_df.group_by(existing_group_cols + ["date"]).agg([
        pl.col("total_signal_adjusted").sum().alias("daily_signal"),
        pl.col("total_raw_count").sum().alias("daily_raw"),
    ]).sort(existing_group_cols + ["date"])
    
    # Calculate rolling sum
    rolling_df = rolling_df.with_columns(
        pl.col("daily_signal")
        .rolling_sum(window_size=window_days, min_periods=1)
        .over(existing_group_cols)
        .alias("rolling_signal")
    )
    
    # Join with population
    rolling_df = rolling_df.join(population_df, on=existing_group_cols, how="inner")
    
    # Calculate rolling MVI
    per_population = MVI_CONFIG["per_population"]
    
    rolling_df = rolling_df.with_columns(
        (pl.col("rolling_signal") / pl.col("population_base") * per_population)
        .alias("mvi")
    )
    
    # Classify bands
    rolling_df = classify_mvi_bands(rolling_df)
    rolling_df = add_confidence_indicator(rolling_df)
    
    return rolling_df


def calculate_mvi_change(
    mvi_df: pl.DataFrame,
    geo_level: str = "district"
) -> pl.DataFrame:
    """
    Calculate MVI change over time (velocity of velocity).
    
    This shows acceleration/deceleration of migration activity.
    
    Args:
        mvi_df: DataFrame with temporal MVI
        geo_level: Geographic level
        
    Returns:
        DataFrame with MVI change indicators
    """
    geo_columns = {
        "state": ["state"],
        "district": ["state", "district"],
        "pincode": ["state", "district", "pincode"],
    }
    
    group_cols = geo_columns.get(geo_level, ["state", "district"])
    existing_group_cols = [c for c in group_cols if c in mvi_df.columns]
    
    if "date" not in mvi_df.columns:
        return mvi_df
    
    # Sort and calculate lag
    mvi_df = mvi_df.sort(existing_group_cols + ["date"])
    
    mvi_df = mvi_df.with_columns(
        pl.col("mvi")
        .shift(1)
        .over(existing_group_cols)
        .alias("mvi_prev")
    )
    
    # Calculate change
    mvi_df = mvi_df.with_columns(
        (pl.col("mvi") - pl.col("mvi_prev")).alias("mvi_change")
    )
    
    # Classify change direction
    change_direction = (
        pl.when(pl.col("mvi_change") > 1).then(pl.lit("ACCELERATING"))
        .when(pl.col("mvi_change") < -1).then(pl.lit("DECELERATING"))
        .otherwise(pl.lit("STABLE"))
    )
    
    mvi_df = mvi_df.with_columns(change_direction.alias("mvi_direction"))
    
    return mvi_df


# =============================================================================
# COMPARATIVE MVI ANALYSIS
# =============================================================================

def calculate_relative_mvi(
    mvi_df: pl.DataFrame,
    reference_level: str = "state"
) -> pl.DataFrame:
    """
    Calculate MVI relative to a reference level.
    
    This enables comparison:
    - District MVI relative to state average
    - State MVI relative to national average
    
    Args:
        mvi_df: DataFrame with MVI values
        reference_level: Level for reference calculation
        
    Returns:
        DataFrame with relative MVI
    """
    # Calculate reference MVI (mean at reference level)
    if reference_level == "national":
        reference_mvi = mvi_df.select(pl.col("mvi").mean()).item()
        mvi_df = mvi_df.with_columns(pl.lit(reference_mvi).alias("reference_mvi"))
    elif reference_level == "state" and "state" in mvi_df.columns:
        state_avg = mvi_df.group_by("state").agg(
            pl.col("mvi").mean().alias("reference_mvi")
        )
        mvi_df = mvi_df.join(state_avg, on="state", how="left")
    else:
        return mvi_df
    
    # Calculate relative MVI
    mvi_df = mvi_df.with_columns(
        (pl.col("mvi") / pl.col("reference_mvi") * 100).alias("relative_mvi")
    )
    
    # Interpret relative MVI
    relative_interpretation = (
        pl.when(pl.col("relative_mvi") > 150).then(pl.lit("SIGNIFICANTLY ABOVE AVERAGE"))
        .when(pl.col("relative_mvi") > 100).then(pl.lit("ABOVE AVERAGE"))
        .when(pl.col("relative_mvi") < 50).then(pl.lit("SIGNIFICANTLY BELOW AVERAGE"))
        .when(pl.col("relative_mvi") < 100).then(pl.lit("BELOW AVERAGE"))
        .otherwise(pl.lit("AT AVERAGE"))
    )
    
    mvi_df = mvi_df.with_columns(relative_interpretation.alias("relative_position"))
    
    return mvi_df


# =============================================================================
# MVI REPORTING
# =============================================================================

def generate_mvi_summary(mvi_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for MVI distribution.
    
    Args:
        mvi_df: DataFrame with MVI values
        
    Returns:
        Dictionary with summary statistics
    """
    band_counts = mvi_df.group_by("mvi_band").agg(
        pl.count().alias("count")
    ).to_dicts()
    
    band_distribution = {d["mvi_band"]: d["count"] for d in band_counts}
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_units": len(mvi_df),
        "mvi_statistics": {
            "mean": round(mvi_df.select(pl.col("mvi").mean()).item(), 2),
            "median": round(mvi_df.select(pl.col("mvi").median()).item(), 2),
            "std": round(mvi_df.select(pl.col("mvi").std()).item(), 2),
            "min": round(mvi_df.select(pl.col("mvi").min()).item(), 2),
            "max": round(mvi_df.select(pl.col("mvi").max()).item(), 2),
        },
        "band_distribution": band_distribution,
        "interpretation": {
            "high_pressure_count": band_distribution.get("High Pressure", 0),
            "elevated_count": band_distribution.get("Elevated", 0),
            "attention_needed": band_distribution.get("High Pressure", 0) + band_distribution.get("Elevated", 0),
        },
    }


def get_top_mvi_regions(
    mvi_df: pl.DataFrame,
    n: int = 10,
    ascending: bool = False
) -> pl.DataFrame:
    """
    Get top/bottom regions by MVI.
    
    Args:
        mvi_df: DataFrame with MVI values
        n: Number of regions to return
        ascending: If True, return lowest MVI (stable areas)
        
    Returns:
        DataFrame with top/bottom regions
    """
    return mvi_df.sort("mvi", descending=not ascending).head(n)


def print_mvi_report(summary: Dict) -> None:
    """
    Print formatted MVI summary report.
    
    Args:
        summary: MVI summary dictionary
    """
    print("\n" + "=" * 60)
    print("MIGRATION VELOCITY INDEX (MVI) REPORT")
    print("=" * 60)
    
    print(f"\nTotal Geographic Units: {summary['total_units']}")
    
    stats = summary["mvi_statistics"]
    print(f"\nMVI Statistics:")
    print(f"  Mean:   {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Std:    {stats['std']:.2f}")
    print(f"  Range:  {stats['min']:.2f} - {stats['max']:.2f}")
    
    print(f"\nBand Distribution:")
    for band, count in summary["band_distribution"].items():
        print(f"  {band}: {count}")
    
    attention = summary["interpretation"]["attention_needed"]
    print(f"\n⚠ Regions Needing Attention: {attention}")
    
    print("=" * 60)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    
    print("=" * 60)
    print("AADHAAR SANKET - MIGRATION VELOCITY INDEX ENGINE")
    print("=" * 60)
    
    try:
        # Load datasets
        print("\nLoading datasets...")
        demographic_df = load_processed_dataset("demographic")
        enrolment_df = load_processed_dataset("enrolment")
        
        # Apply signal weights
        print("Applying signal weights...")
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        
        # Calculate population base
        print("Calculating population base...")
        population_df = calculate_population_base(enrolment_df, "district")
        print(f"  Population base for {len(population_df)} districts")
        
        # Calculate MVI
        print("\nCalculating Migration Velocity Index...")
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        
        # Generate summary
        summary = generate_mvi_summary(mvi_df)
        print_mvi_report(summary)
        
        # Show top regions
        print("\nTOP 10 HIGH-PRESSURE REGIONS:")
        print("-" * 60)
        top_regions = get_top_mvi_regions(mvi_df, 10)
        for row in top_regions.to_dicts():
            print(f"  {row.get('district', 'N/A')}, {row.get('state', 'N/A')}: MVI={row['mvi']:.2f} [{row['mvi_band']}]")
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] Dataset not found: {e}")
        print("Run ingestion pipeline first: python -m src.engines.ingestion")
