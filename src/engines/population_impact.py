"""
Project Aadhaar Sanket - Population Impact Trend Engine

Analyzes absolute impact (not just rates) of migration patterns.

While MVI measures rate of change, this engine tracks:
- Total population affected
- Growth/decline of affected population over time
- Absolute impact classification

This complements MVI by answering:
- "How many people are actually affected?" (magnitude)
- "Is the affected population growing?" (trend)

Critical for resource allocation decisions.
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class PopulationImpactResult:
    """Population impact analysis result for a geographic unit."""
    geo_key: str
    affected_population: int  # Absolute number
    affected_growth_rate: float  # Month-over-month %
    impact_classification: str  # high, moderate, low
    total_population: int
    affected_percent: float
    explanation: str


# =============================================================================
# CONFIGURATION
# =============================================================================

IMPACT_CONFIG = {
    "thresholds": {
        "high_impact_absolute": 10000,  # 10k+ people
        "moderate_impact_absolute": 1000,  # 1k+ people
        "high_impact_percent": 5.0,  # 5%+ of population
        "moderate_impact_percent": 1.0,  # 1%+ of population
        "high_growth_rate": 20.0,  # 20%+ month-over-month
        "moderate_growth_rate": 10.0,  # 10%+ month-over-month
    },
    "min_periods": 3,  # Minimum periods for growth calculation
}


# =============================================================================
# POPULATION IMPACT CALCULATION
# =============================================================================

def calculate_affected_population(
    mvi: float,
    total_population: int
) -> int:
    """
    Calculate absolute affected population from MVI.
    
    MVI = (Updates / Population) × 1000
    Therefore: Affected = (MVI × Population) / 1000
    
    Args:
        mvi: Migration Velocity Index value
        total_population: Total population base
        
    Returns:
        Estimated affected population
    """
    if total_population == 0:
        return 0
    
    affected = (mvi * total_population) / 1000
    return int(affected)


def calculate_growth_rate(affected_series: pl.Series) -> float:
    """
    Calculate month-over-month growth rate of affected population.
    
    Args:
        affected_series: Time series of affected population
        
    Returns:
        Average growth rate (percentage)
    """
    values = affected_series.drop_nulls().to_numpy()
    
    if len(values) < 2:
        return 0.0
    
    # Calculate period-over-period growth rates
    growth_rates = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            growth = ((values[i] - values[i-1]) / values[i-1]) * 100
            growth_rates.append(growth)
    
    if not growth_rates:
        return 0.0
    
    return float(np.mean(growth_rates))


def classify_impact(
    affected_population: int,
    affected_percent: float,
    growth_rate: float,
    total_population: int
) -> tuple[str, str]:
    """
    Classify population impact severity.
    
    Args:
        affected_population: Absolute affected count
        affected_percent: Percentage of total population
        growth_rate: Month-over-month growth rate
        total_population: Total population
        
    Returns:
        (classification, explanation)
    """
    cfg = IMPACT_CONFIG["thresholds"]
    
    # Determine impact level
    if (affected_population >= cfg["high_impact_absolute"] or 
        affected_percent >= cfg["high_impact_percent"]):
        classification = "high"
        impact_desc = "High impact"
    elif (affected_population >= cfg["moderate_impact_absolute"] or 
          affected_percent >= cfg["moderate_impact_percent"]):
        classification = "moderate"
        impact_desc = "Moderate impact"
    else:
        classification = "low"
        impact_desc = "Low impact"
    
    # Add growth context
    if growth_rate >= cfg["high_growth_rate"]:
        growth_desc = f"rapidly growing ({growth_rate:+.1f}% per month)"
    elif growth_rate >= cfg["moderate_growth_rate"]:
        growth_desc = f"growing ({growth_rate:+.1f}% per month)"
    elif growth_rate <= -cfg["moderate_growth_rate"]:
        growth_desc = f"declining ({growth_rate:+.1f}% per month)"
    else:
        growth_desc = f"stable ({growth_rate:+.1f}% per month)"
    
    explanation = (
        f"{impact_desc}: {affected_population:,} people affected "
        f"({affected_percent:.1f}% of {total_population:,}), {growth_desc}."
    )
    
    return classification, explanation


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_population_impact(
    mvi_df: pl.DataFrame,
    population_df: pl.DataFrame,
    geo_level: str = "district",
    date_column: str = "date"
) -> pl.DataFrame:
    """
    Analyze population impact for each geographic unit.
    
    Args:
        mvi_df: DataFrame with temporal MVI data
            Required columns: [geo_level, date_column, 'mvi']
        population_df: DataFrame with population data
            Required columns: [geo_level, 'population_base']
        geo_level: Geographic aggregation level
        date_column: Name of date column
        
    Returns:
        DataFrame with population impact analysis:
            - geo_key
            - affected_population (latest)
            - affected_growth_rate
            - impact_classification
            - total_population
            - affected_percent
            - explanation
    """
    # Validate input
    required_mvi_cols = [geo_level, date_column, "mvi"]
    missing = [c for c in required_mvi_cols if c not in mvi_df.columns]
    if missing:
        raise ValueError(f"Missing required MVI columns: {missing}")
    
    required_pop_cols = [geo_level, "population_base"]
    missing = [c for c in required_pop_cols if c not in population_df.columns]
    if missing:
        raise ValueError(f"Missing required population columns: {missing}")
    
    # Ensure sorted
    mvi_df = mvi_df.sort([geo_level, date_column])
    
    # Analyze each geographic unit
    results = []
    
    for geo_key, group_df in mvi_df.group_by(geo_level):
        # Skip if insufficient data
        if len(group_df) < IMPACT_CONFIG["min_periods"]:
            continue
        
        # Get population base
        pop_row = population_df.filter(
            pl.col(geo_level) == (geo_key[0] if isinstance(geo_key, tuple) else geo_key)
        )
        
        if len(pop_row) == 0:
            continue
        
        total_population = int(pop_row["population_base"][0])
        
        # Calculate affected population time series
        affected_series = group_df.select(
            (pl.col("mvi") * total_population / 1000).alias("affected")
        )["affected"]
        
        # Latest affected population
        latest_affected = int(affected_series[-1])
        affected_percent = (latest_affected / total_population * 100) if total_population > 0 else 0
        
        # Growth rate
        growth_rate = calculate_growth_rate(affected_series)
        
        # Classify
        classification, explanation = classify_impact(
            latest_affected, affected_percent, growth_rate, total_population
        )
        
        results.append({
            "geo_key": geo_key[0] if isinstance(geo_key, tuple) else geo_key,
            "affected_population": latest_affected,
            "affected_growth_rate": round(growth_rate, 2),
            "impact_classification": classification,
            "total_population": total_population,
            "affected_percent": round(affected_percent, 2),
            "explanation": explanation,
        })
    
    return pl.DataFrame(results)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_impact_summary(impact_df: pl.DataFrame) -> Dict:
    """
    Generate summary statistics for population impact analysis.
    
    Args:
        impact_df: Output from analyze_population_impact
        
    Returns:
        Summary dictionary
    """
    total = len(impact_df)
    
    # Count by classification
    class_counts = impact_df.group_by("impact_classification").agg(
        pl.count().alias("count")
    )
    
    distribution = {
        row["impact_classification"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in class_counts.to_dicts()
    }
    
    # High impact zones
    high_impact = impact_df.filter(
        pl.col("impact_classification") == "high"
    ).sort("affected_population", descending=True)
    
    # Growing impact zones
    growing_impact = impact_df.filter(
        pl.col("affected_growth_rate") > IMPACT_CONFIG["thresholds"]["moderate_growth_rate"]
    ).sort("affected_growth_rate", descending=True)
    
    # Total affected population
    total_affected = int(impact_df["affected_population"].sum())
    total_population = int(impact_df["total_population"].sum())
    
    return {
        "total_units": total,
        "distribution": distribution,
        "total_affected_population": total_affected,
        "total_population": total_population,
        "overall_affected_percent": round(total_affected / total_population * 100, 2) if total_population > 0 else 0,
        "high_impact_zones": {
            "count": len(high_impact),
            "percent": round(len(high_impact) / total * 100, 1) if total > 0 else 0,
            "top_10": high_impact.head(10).select([
                "geo_key", "affected_population", "affected_percent", 
                "affected_growth_rate", "explanation"
            ]).to_dicts()
        },
        "growing_impact_zones": {
            "count": len(growing_impact),
            "top_10": growing_impact.head(10).select([
                "geo_key", "affected_population", "affected_growth_rate", "explanation"
            ]).to_dicts()
        },
        "statistics": {
            "mean_affected": int(impact_df["affected_population"].mean()),
            "median_affected": int(impact_df["affected_population"].median()),
            "mean_growth_rate": float(impact_df["affected_growth_rate"].mean()),
        }
    }


def print_impact_summary(summary: Dict):
    """Print formatted population impact summary."""
    print("\n" + "=" * 70)
    print("POPULATION IMPACT ANALYSIS")
    print("=" * 70)
    
    print(f"\nTotal Units Analyzed: {summary['total_units']}")
    print(f"Total Affected Population: {summary['total_affected_population']:,}")
    print(f"Total Population: {summary['total_population']:,}")
    print(f"Overall Affected: {summary['overall_affected_percent']:.2f}%")
    
    print("\nImpact Classification Distribution:")
    for classification, data in summary["distribution"].items():
        print(f"  {classification:15s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    high_impact = summary["high_impact_zones"]
    print(f"\nHigh Impact Zones: {high_impact['count']} ({high_impact['percent']:.1f}%)")
    print("(Require significant resource allocation)")
    
    if high_impact["top_10"]:
        print("\nTop 10 High Impact Zones:")
        for i, zone in enumerate(high_impact["top_10"], 1):
            print(f"  {i:2d}. {zone['geo_key']}")
            print(f"      Affected: {zone['affected_population']:,} ({zone['affected_percent']:.1f}%)")
            print(f"      Growth: {zone['affected_growth_rate']:+.1f}% per month")
            print(f"      {zone['explanation']}")
    
    growing = summary["growing_impact_zones"]
    if growing["count"] > 0:
        print(f"\nGrowing Impact Zones: {growing['count']}")
        print("(Accelerating resource needs)")
    
    print("\nOverall Statistics:")
    stats = summary["statistics"]
    print(f"  Mean Affected Population: {stats['mean_affected']:,}")
    print(f"  Median Affected Population: {stats['median_affected']:,}")
    print(f"  Mean Growth Rate: {stats['mean_growth_rate']:+.2f}% per month")
