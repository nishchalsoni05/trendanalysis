"""
Project Aadhaar Sanket - Trend Confidence Engine

Quantifies reliability of trend assessments using:
- Data completeness
- Signal-to-noise ratio
- Consistency score

Outputs confidence levels (high/medium/low) with limiting factors.
Critical for honest, transparent analytics.
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class ConfidenceResult:
    """Confidence assessment for a geographic unit."""
    geo_key: str
    confidence_score: float  # 0-1
    confidence_level: str  # high, medium, low
    data_completeness: float
    signal_to_noise: float
    consistency_score: float
    limiting_factors: List[str]


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIDENCE_CONFIG = {
    "thresholds": {
        "high_confidence": 0.7,
        "medium_confidence": 0.5,
        "min_data_points": 6,
        "completeness_threshold": 0.8,
        "snr_threshold": 2.0,
    },
    "weights": {
        "completeness": 0.4,
        "signal_to_noise": 0.3,
        "consistency": 0.3,
    }
}


# =============================================================================
# CONFIDENCE METRICS
# =============================================================================

def calculate_data_completeness(series: pl.Series) -> float:
    """Calculate data completeness (non-null ratio)."""
    total = len(series)
    if total == 0:
        return 0.0
    non_null = series.drop_nulls().len()
    return non_null / total


def calculate_signal_to_noise(series: pl.Series) -> float:
    """
    Calculate signal-to-noise ratio.
    SNR = mean / std
    """
    values = series.drop_nulls()
    if len(values) < 2:
        return 0.0
    
    mean = float(values.mean())
    std = float(values.std())
    
    if std == 0:
        return 10.0  # Perfect signal
    
    return abs(mean / std)


def calculate_consistency(series: pl.Series) -> float:
    """
    Calculate consistency using coefficient of variation.
    Lower CV = higher consistency
    """
    values = series.drop_nulls()
    if len(values) < 2:
        return 0.0
    
    mean = float(values.mean())
    std = float(values.std())
    
    if mean == 0:
        return 0.0
    
    cv = std / abs(mean)
    # Convert to 0-1 score (lower CV = higher score)
    consistency = 1 / (1 + cv)
    return min(consistency, 1.0)


def calculate_confidence_score(
    completeness: float,
    snr: float,
    consistency: float
) -> float:
    """
    Calculate weighted confidence score.
    
    Args:
        completeness: Data completeness (0-1)
        snr: Signal-to-noise ratio
        consistency: Consistency score (0-1)
        
    Returns:
        Confidence score (0-1)
    """
    weights = CONFIDENCE_CONFIG["weights"]
    
    # Normalize SNR to 0-1 scale
    snr_normalized = min(snr / 5.0, 1.0)
    
    score = (
        weights["completeness"] * completeness +
        weights["signal_to_noise"] * snr_normalized +
        weights["consistency"] * consistency
    )
    
    return min(score, 1.0)


def identify_limiting_factors(
    completeness: float,
    snr: float,
    consistency: float,
    data_points: int
) -> List[str]:
    """Identify factors limiting confidence."""
    factors = []
    cfg = CONFIDENCE_CONFIG["thresholds"]
    
    if data_points < cfg["min_data_points"]:
        factors.append(f"Insufficient data ({data_points} periods)")
    
    if completeness < cfg["completeness_threshold"]:
        factors.append(f"Missing data ({completeness:.0%} complete)")
    
    if snr < cfg["snr_threshold"]:
        factors.append(f"High noise (SNR={snr:.1f})")
    
    if consistency < 0.5:
        factors.append("High variability")
    
    if not factors:
        factors.append("None - high quality data")
    
    return factors


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_trend_confidence(
    mvi_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date"
) -> pl.DataFrame:
    """
    Assess confidence for each geographic unit's trend.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
        geo_level: Geographic aggregation level
        date_column: Name of date column
        
    Returns:
        DataFrame with confidence assessment
    """
    required_cols = [geo_level, date_column, "mvi"]
    missing = [c for c in required_cols if c not in mvi_df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    mvi_df = mvi_df.sort([geo_level, date_column])
    
    results = []
    
    for geo_key, group_df in mvi_df.group_by(geo_level):
        mvi_series = group_df["mvi"]
        data_points = len(group_df)
        
        # Calculate metrics
        completeness = calculate_data_completeness(mvi_series)
        snr = calculate_signal_to_noise(mvi_series)
        consistency = calculate_consistency(mvi_series)
        
        # Calculate confidence score
        confidence_score = calculate_confidence_score(completeness, snr, consistency)
        
        # Classify confidence level
        cfg = CONFIDENCE_CONFIG["thresholds"]
        if confidence_score >= cfg["high_confidence"]:
            confidence_level = "high"
        elif confidence_score >= cfg["medium_confidence"]:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Identify limiting factors
        limiting_factors = identify_limiting_factors(
            completeness, snr, consistency, data_points
        )
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "confidence_score": round(confidence_score, 3),
            "confidence_level": confidence_level,
            "data_completeness": round(completeness, 3),
            "signal_to_noise": round(snr, 2),
            "consistency_score": round(consistency, 3),
            "data_points": data_points,
            "limiting_factors": "; ".join(limiting_factors),
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_confidence_summary(confidence_df: pl.DataFrame) -> Dict:
    """Generate summary statistics for confidence analysis."""
    total = len(confidence_df)
    
    # Count by level
    level_counts = confidence_df.group_by("confidence_level").agg(
        pl.count().alias("count")
    )
    
    distribution = {
        row["confidence_level"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in level_counts.to_dicts()
    }
    
    # High confidence zones
    high_conf = confidence_df.filter(
        pl.col("confidence_level") == "high"
    ).sort("confidence_score", descending=True)
    
    # Low confidence zones (need attention)
    low_conf = confidence_df.filter(
        pl.col("confidence_level") == "low"
    ).sort("confidence_score")
    
    return {
        "total_units": total,
        "distribution": distribution,
        "high_confidence_zones": {
            "count": len(high_conf),
            "percent": round(len(high_conf) / total * 100, 1) if total > 0 else 0,
        },
        "low_confidence_zones": {
            "count": len(low_conf),
            "percent": round(len(low_conf) / total * 100, 1) if total > 0 else 0,
            "top_10": low_conf.head(10).select([
                "geo_key", "confidence_score", "limiting_factors"
            ]).to_dicts()
        },
        "statistics": {
            "mean_confidence": float(confidence_df["confidence_score"].mean()),
            "mean_completeness": float(confidence_df["data_completeness"].mean()),
            "mean_snr": float(confidence_df["signal_to_noise"].mean()),
        }
    }


def print_confidence_summary(summary: Dict):
    """Print formatted confidence summary."""
    print("\n" + "=" * 70)
    print("TREND CONFIDENCE ANALYSIS")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    
    print("\nConfidence Level Distribution:")
    for level, data in summary["distribution"].items():
        print(f"  {level:15s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    high = summary["high_confidence_zones"]
    print(f"\nHigh Confidence Zones: {high['count']} ({high['percent']:.1f}%)")
    print("(Reliable for decision-making)")
    
    low = summary["low_confidence_zones"]
    print(f"\nLow Confidence Zones: {low['count']} ({low['percent']:.1f}%)")
    print("(Require data quality improvement)")
    
    if low["top_10"]:
        print("\nTop 10 Low Confidence Zones (Priority for Data Improvement):")
        for i, zone in enumerate(low["top_10"], 1):
            print(f"  {i:2d}. {zone['geo_key']}")
            print(f"      Confidence: {zone['confidence_score']:.2f}")
            print(f"      Limiting Factors: {zone['limiting_factors']}")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Confidence Score: {stats['mean_confidence']:.3f}")
    print(f"  Mean Data Completeness: {stats['mean_completeness']:.1%}")
    print(f"  Mean Signal-to-Noise: {stats['mean_snr']:.2f}")
