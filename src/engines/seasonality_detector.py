"""
Project Aadhaar Sanket - Seasonality Detection Engine

Detects repeating temporal patterns in migration activity.

Uses statistical decomposition (NO ML) to identify:
- Monthly/quarterly cycles
- Recurrent peaks
- Seasonal migration zones

This distinguishes:
- Seasonal migration (harvest workers, students) → temporary resources
- Non-seasonal migration (permanent relocation) → permanent infrastructure
"""
from dataclasses import dataclass
from typing import Dict, List, Tuple
import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class SeasonalityResult:
    """Seasonality analysis result for a geographic unit."""
    geo_key: str
    is_seasonal: bool
    seasonal_period: int  # months (0 if not seasonal)
    strength: float  # 0-1 score
    peak_months: List[int]  # List of peak months
    explanation: str


# =============================================================================
# CONFIGURATION
# =============================================================================

SEASONALITY_CONFIG = {
    "autocorrelation_threshold": 0.5,  # Threshold for seasonal detection
    "peak_prominence": 0.3,  # Minimum prominence for peak detection
    "min_periods": 12,  # Minimum months required (1 year)
    "test_lags": [3, 6, 12],  # Test for quarterly, semi-annual, annual patterns
}


# =============================================================================
# AUTOCORRELATION ANALYSIS
# =============================================================================

def calculate_autocorrelation(series: np.ndarray, lag: int) -> float:
    """
    Calculate autocorrelation at given lag.
    
    Args:
        series: Time series values
        lag: Lag period
        
    Returns:
        Autocorrelation coefficient (-1 to 1)
    """
    if len(series) <= lag:
        return 0.0
    
    # Remove mean
    series_centered = series - np.mean(series)
    
    # Calculate autocorrelation
    c0 = np.dot(series_centered, series_centered) / len(series)
    c_lag = np.dot(series_centered[:-lag], series_centered[lag:]) / len(series)
    
    if c0 == 0:
        return 0.0
    
    return c_lag / c0


def detect_seasonal_period(mvi_series: pl.Series) -> Tuple[bool, int, float]:
    """
    Detect seasonal period using autocorrelation.
    
    Args:
        mvi_series: Time series of MVI values
        
    Returns:
        (is_seasonal, period, strength)
    """
    values = mvi_series.drop_nulls().to_numpy()
    
    if len(values) < SEASONALITY_CONFIG["min_periods"]:
        return False, 0, 0.0
    
    # Test different lags
    best_lag = 0
    best_corr = 0.0
    
    for lag in SEASONALITY_CONFIG["test_lags"]:
        if len(values) > lag:
            corr = calculate_autocorrelation(values, lag)
            if abs(corr) > abs(best_corr):
                best_corr = corr
                best_lag = lag
    
    # Determine if seasonal
    is_seasonal = abs(best_corr) >= SEASONALITY_CONFIG["autocorrelation_threshold"]
    strength = min(abs(best_corr), 1.0)
    
    return is_seasonal, best_lag if is_seasonal else 0, strength


# =============================================================================
# PEAK DETECTION
# =============================================================================

def detect_peaks(mvi_series: pl.Series, dates: pl.Series) -> List[int]:
    """
    Detect recurring peak months.
    
    Args:
        mvi_series: Time series of MVI values
        dates: Corresponding dates
        
    Returns:
        List of peak months (1-12)
    """
    if len(mvi_series) < 12:
        return []
    
    # Create month-indexed aggregation
    df = pl.DataFrame({
        "date": dates,
        "mvi": mvi_series
    })
    
    # Extract month and calculate mean by month
    monthly_avg = (
        df.with_columns(
            pl.col("date").dt.month().alias("month")
        )
        .group_by("month")
        .agg(pl.col("mvi").mean().alias("avg_mvi"))
        .sort("month")
    )
    
    if len(monthly_avg) < 3:
        return []
    
    # Find peaks (months with above-average MVI)
    overall_mean = monthly_avg["avg_mvi"].mean()
    threshold = overall_mean * (1 + SEASONALITY_CONFIG["peak_prominence"])
    
    peak_months = monthly_avg.filter(
        pl.col("avg_mvi") > threshold
    )["month"].to_list()
    
    return peak_months


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_seasonality(
    mvi_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date"
) -> pl.DataFrame:
    """
    Analyze seasonality patterns for each geographic unit.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
            Required columns: [geo_level, date_column, 'mvi']
        geo_level: Geographic aggregation level
        date_column: Name of date column
        
    Returns:
        DataFrame with seasonality analysis:
            - geo_key
            - is_seasonal
            - seasonal_period
            - strength
            - peak_months
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
        if len(group_df) < SEASONALITY_CONFIG["min_periods"]:
            continue
        
        mvi_series = group_df["mvi"]
        date_series = group_df[date_column]
        
        # Detect seasonal period
        is_seasonal, period, strength = detect_seasonal_period(mvi_series)
        
        # Detect peak months
        peak_months = detect_peaks(mvi_series, date_series) if is_seasonal else []
        
        # Generate explanation
        if is_seasonal:
            period_name = {3: "quarterly", 6: "semi-annual", 12: "annual"}.get(period, f"{period}-month")
            peak_str = f"peaks in months {peak_months}" if peak_months else "no clear peaks"
            explanation = (
                f"Seasonal pattern detected ({period_name} cycle, strength={strength:.2f}). "
                f"{peak_str}. Likely temporary migration."
            )
        else:
            explanation = f"No seasonal pattern detected (strength={strength:.2f}). Likely permanent migration."
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "is_seasonal": is_seasonal,
            "seasonal_period": period,
            "strength": round(strength, 3),
            "peak_months": peak_months,
            "explanation": explanation,
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_seasonality_summary(seasonality_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for seasonality analysis.
    
    Args:
        seasonality_df: Output from analyze_seasonality
        
    Returns:
        Summary dictionary
    """
    total = len(seasonality_df)
    
    # Count seasonal vs non-seasonal
    seasonal_count = seasonality_df.filter(pl.col("is_seasonal") == True).height
    non_seasonal_count = total - seasonal_count
    
    # Period distribution
    period_counts = seasonality_df.filter(
        pl.col("is_seasonal") == True
    ).group_by("seasonal_period").agg(
        pl.count().alias("count")
    )
    
    period_distribution = {
        row["seasonal_period"]: row["count"]
        for row in period_counts.to_dicts()
    }
    
    # Seasonal zones
    seasonal_zones = seasonality_df.filter(
        pl.col("is_seasonal") == True
    ).sort("strength", descending=True)
    
    return {
        "total_units": total,
        "seasonal_count": seasonal_count,
        "seasonal_percent": round(seasonal_count / total * 100, 1) if total > 0 else 0,
        "non_seasonal_count": non_seasonal_count,
        "period_distribution": period_distribution,
        "seasonal_zones": {
            "top_10": seasonal_zones.head(10).select([
                "geo_key", "seasonal_period", "strength", "peak_months", "explanation"
            ]).to_dicts()
        },
        "statistics": {
            "mean_strength": float(seasonality_df["strength"].mean()),
            "max_strength": float(seasonality_df["strength"].max()),
        }
    }


def print_seasonality_summary(summary: Dict):
    """Print formatted seasonality summary."""
    print("\n" + "=" * 70)
    print("SEASONALITY DETECTION ANALYSIS")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    print(f"Seasonal Zones: {summary['seasonal_count']} ({summary['seasonal_percent']:.1f}%)")
    print(f"Non-Seasonal Zones: {summary['non_seasonal_count']}")
    
    if summary["period_distribution"]:
        print("\nSeasonal Period Distribution:")
        for period, count in summary["period_distribution"].items():
            period_name = {3: "Quarterly", 6: "Semi-Annual", 12: "Annual"}.get(period, f"{period}-Month")
            print(f"  {period_name:15s}: {count:4d} zones")
    
    seasonal_zones = summary["seasonal_zones"]["top_10"]
    if seasonal_zones:
        print("\nTop 10 Seasonal Zones:")
        for i, zone in enumerate(seasonal_zones, 1):
            period_name = {3: "quarterly", 6: "semi-annual", 12: "annual"}.get(
                zone["seasonal_period"], f"{zone['seasonal_period']}-month"
            )
            print(f"  {i:2d}. {zone['geo_key']}")
            print(f"      Period: {period_name}, Strength: {zone['strength']:.2f}")
            print(f"      Peak Months: {zone['peak_months']}")
            print(f"      {zone['explanation']}")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Strength: {stats['mean_strength']:.3f}")
    print(f"  Max Strength: {stats['max_strength']:.3f}")
    
    print("\nPolicy Implications:")
    print("  - Seasonal zones: Deploy temporary/mobile resources")
    print("  - Non-seasonal zones: Plan permanent infrastructure")
