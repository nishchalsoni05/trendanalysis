"""
Project Aadhaar Sanket - Persistence Analysis Engine

Distinguishes structural migration patterns from temporary shocks.

Persistence Score = periods_above_threshold / total_periods

Classifications:
- Structural (>0.7): Long-term migration pattern requiring infrastructure response
- Shock (<0.3): Temporary spike, likely external event
- Transitional (0.3-0.7): Evolving pattern requiring monitoring

This enables policy makers to distinguish between:
- Permanent demographic shifts (build schools, hospitals)
- Temporary events (deploy mobile services)
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import MVI_CONFIG


@dataclass
class PersistenceResult:
    """Persistence analysis result for a geographic unit."""
    geo_key: str
    persistence_score: float  # 0-1
    classification: str  # structural, shock, transitional
    periods_analyzed: int
    periods_above_threshold: int
    threshold_used: float
    explanation: str


# =============================================================================
# CONFIGURATION
# =============================================================================

PERSISTENCE_CONFIG = {
    "thresholds": {
        "mvi_elevated": 10.0,  # MVI threshold for "elevated" activity
        "structural": 0.7,      # Persistence score for structural classification
        "shock": 0.3,           # Persistence score for shock classification
    },
    "min_periods": 6,  # Minimum periods required for analysis
}


# =============================================================================
# PERSISTENCE CALCULATION
# =============================================================================

def calculate_persistence_score(
    mvi_series: pl.Series,
    threshold: float
) -> tuple[float, int, int]:
    """
    Calculate persistence score for a time series.
    
    Args:
        mvi_series: Time series of MVI values
        threshold: MVI threshold for "elevated" classification
        
    Returns:
        (persistence_score, periods_above, total_periods)
    """
    values = mvi_series.drop_nulls()
    total_periods = len(values)
    
    if total_periods == 0:
        return 0.0, 0, 0
    
    periods_above = (values > threshold).sum()
    persistence_score = periods_above / total_periods
    
    return float(persistence_score), int(periods_above), int(total_periods)


def classify_persistence(
    persistence_score: float,
    mean_mvi: float
) -> tuple[str, str]:
    """
    Classify persistence pattern.
    
    Args:
        persistence_score: Calculated persistence score (0-1)
        mean_mvi: Mean MVI value
        
    Returns:
        (classification, explanation)
    """
    cfg = PERSISTENCE_CONFIG["thresholds"]
    
    if persistence_score >= cfg["structural"]:
        return (
            "structural",
            f"Structural migration pattern ({persistence_score:.1%} persistence). "
            f"Requires long-term infrastructure planning."
        )
    elif persistence_score <= cfg["shock"]:
        return (
            "shock",
            f"Temporary shock pattern ({persistence_score:.1%} persistence). "
            f"Likely external event or data artifact."
        )
    else:
        return (
            "transitional",
            f"Transitional pattern ({persistence_score:.1%} persistence). "
            f"Evolving situation requiring continued monitoring."
        )


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_persistence(
    mvi_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date",
    threshold: float = None
) -> pl.DataFrame:
    """
    Analyze persistence patterns for each geographic unit.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
            Required columns: [geo_level, date_column, 'mvi']
        geo_level: Geographic aggregation level
        date_column: Name of date column
        threshold: MVI threshold (default: from config)
        
    Returns:
        DataFrame with persistence analysis:
            - geo_key
            - persistence_score
            - classification
            - periods_analyzed
            - periods_above_threshold
            - threshold_used
            - mean_mvi
            - explanation
    """
    if threshold is None:
        threshold = PERSISTENCE_CONFIG["thresholds"]["mvi_elevated"]
    
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
        if len(group_df) < PERSISTENCE_CONFIG["min_periods"]:
            continue
        
        mvi_series = group_df["mvi"]
        mean_mvi = float(mvi_series.mean())
        
        # Calculate persistence
        persistence_score, periods_above, total_periods = calculate_persistence_score(
            mvi_series, threshold
        )
        
        # Classify
        classification, explanation = classify_persistence(
            persistence_score, mean_mvi
        )
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "persistence_score": round(persistence_score, 3),
            "classification": classification,
            "periods_analyzed": total_periods,
            "periods_above_threshold": periods_above,
            "threshold_used": threshold,
            "mean_mvi": round(mean_mvi, 2),
            "explanation": explanation,
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_persistence_summary(persistence_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for persistence analysis.
    
    Args:
        persistence_df: Output from analyze_persistence
        
    Returns:
        Summary dictionary
    """
    total = len(persistence_df)
    
    # Count by classification
    class_counts = persistence_df.group_by("classification").agg(
        pl.count().alias("count")
    ).sort("count", descending=True)
    
    distribution = {
        row["classification"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in class_counts.to_dicts()
    }
    
    # Structural zones (high priority)
    structural_zones = persistence_df.filter(
        pl.col("classification") == "structural"
    ).sort("persistence_score", descending=True)
    
    return {
        "total_units": total,
        "distribution": distribution,
        "structural_zones": {
            "count": len(structural_zones),
            "percent": round(len(structural_zones) / total * 100, 1) if total > 0 else 0,
            "top_10": structural_zones.head(10).select([
                "geo_key", "persistence_score", "mean_mvi", "explanation"
            ]).to_dicts()
        },
        "statistics": {
            "mean_persistence": float(persistence_df["persistence_score"].mean()),
            "median_persistence": float(persistence_df["persistence_score"].median()),
            "mean_mvi": float(persistence_df["mean_mvi"].mean()),
        }
    }


def print_persistence_summary(summary: Dict):
    """Print formatted persistence summary."""
    print("\n" + "=" * 70)
    print("PERSISTENCE ANALYSIS")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    
    print("\nClassification Distribution:")
    for classification, data in summary["distribution"].items():
        print(f"  {classification:15s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    structural = summary["structural_zones"]
    print(f"\nStructural Migration Zones: {structural['count']} ({structural['percent']:.1f}%)")
    print("(Require long-term infrastructure planning)")
    
    if structural["top_10"]:
        print("\nTop 10 Structural Zones:")
        for i, zone in enumerate(structural["top_10"], 1):
            print(f"  {i:2d}. {zone['geo_key']}")
            print(f"      Persistence: {zone['persistence_score']:.1%}, Mean MVI: {zone['mean_mvi']:.1f}")
            print(f"      {zone['explanation']}")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Persistence Score: {stats['mean_persistence']:.1%}")
    print(f"  Median Persistence Score: {stats['median_persistence']:.1%}")
    print(f"  Mean MVI: {stats['mean_mvi']:.2f}")
