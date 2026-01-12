"""
Project Aadhaar Sanket - Signal vs Administrative Noise Separation Engine

This is the INTELLECTUAL CORE of the analytics system.

The engine classifies Aadhaar updates into:
1. ORGANIC MIGRATION SIGNALS - Genuine population movement indicators
2. ADMINISTRATIVE NOISE - Mandatory updates, policy-driven activity

Key Insight:
Not all Aadhaar updates indicate migration. Some are:
- Mandatory (child biometric updates at ages 5, 15)
- Policy-driven (government enrollment drives)
- Corrections (data fixes, not movement)

Signal Separation Logic:
- Demographic updates by adults = STRONG migration signal (weight 1.0)
- Demographic updates by youth = MODERATE signal (weight 0.6)
- Biometric updates by children = NOISE (weight 0.1)
- Biometric updates by adults = WEAK signal (weight 0.3)

This engine produces BOTH:
- Raw counts (for transparency)
- Signal-adjusted counts (for analysis)

Design Principles:
- All weights are explicit and configurable
- Logic is auditable and explainable
- No hidden transformations
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

import polars as pl

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import SIGNAL_WEIGHTS


# =============================================================================
# SIGNAL CLASSIFICATION
# =============================================================================

@dataclass
class SignalClassification:
    """Represents the classification of an update type."""
    update_type: str
    age_group: str
    weight: float
    reasoning: str
    is_noise: bool


def get_signal_weight(
    dataset_type: str,
    age_group: str
) -> Tuple[float, str]:
    """
    Get the signal weight and reasoning for an update type.
    
    Args:
        dataset_type: 'biometric' or 'demographic'
        age_group: 'age_5_17' or 'age_17_plus'
        
    Returns:
        Tuple of (weight, reasoning)
    """
    # Normalize age group key
    age_key = "age_17_plus" if "17_plus" in age_group or "18" in age_group else "age_5_17"
    
    weights = SIGNAL_WEIGHTS.get(dataset_type, {})
    weight = weights.get(age_key, 0.5)  # Default to 0.5 if not found
    
    # Document reasoning for each classification
    reasoning_map = {
        ("demographic", "age_17_plus"): 
            "Adult address change strongly indicates genuine migration or relocation",
        ("demographic", "age_5_17"): 
            "Youth demographic update may indicate family migration, reduced weight",
        ("biometric", "age_5_17"): 
            "Child biometric update is MANDATORY at ages 5 and 15, mostly administrative noise",
        ("biometric", "age_17_plus"): 
            "Adult biometric update may be re-enrollment or correction, weak migration signal",
    }
    
    reasoning = reasoning_map.get((dataset_type, age_key), "Default classification")
    
    return weight, reasoning


def classify_all_update_types() -> List[SignalClassification]:
    """
    Generate classification for all possible update type combinations.
    
    Returns:
        List of SignalClassification objects
    """
    classifications = []
    
    for dataset_type in ["demographic", "biometric"]:
        for age_group in ["age_5_17", "age_17_plus"]:
            weight, reasoning = get_signal_weight(dataset_type, age_group)
            
            classifications.append(SignalClassification(
                update_type=dataset_type,
                age_group=age_group,
                weight=weight,
                reasoning=reasoning,
                is_noise=weight < 0.3,
            ))
    
    return classifications


# =============================================================================
# SIGNAL WEIGHT APPLICATION
# =============================================================================

def apply_signal_weights_demographic(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply signal weights to demographic update data.
    
    Creates new columns:
    - signal_weight_5_17: Weight for youth updates
    - signal_weight_17_plus: Weight for adult updates
    - signal_adjusted_5_17: Weighted count for youth
    - signal_adjusted_17_plus: Weighted count for adults
    - total_signal_adjusted: Sum of weighted counts
    
    Args:
        df: DataFrame with demographic update counts
        
    Returns:
        DataFrame with signal-adjusted columns added
    """
    weight_5_17 = SIGNAL_WEIGHTS["demographic"]["age_5_17"]
    weight_17_plus = SIGNAL_WEIGHTS["demographic"]["age_17_plus"]
    
    # Identify count columns
    youth_col = "age_5_17_count"
    adult_col = "age_17_plus_count"
    
    # Apply weights
    df = df.with_columns([
        # Add weight columns for transparency
        pl.lit(weight_5_17).alias("signal_weight_5_17"),
        pl.lit(weight_17_plus).alias("signal_weight_17_plus"),
        
        # Calculate signal-adjusted counts
        (pl.col(youth_col).cast(pl.Float64) * weight_5_17).alias("signal_adjusted_5_17"),
        (pl.col(adult_col).cast(pl.Float64) * weight_17_plus).alias("signal_adjusted_17_plus"),
    ])
    
    # Calculate total signal-adjusted count
    df = df.with_columns(
        (pl.col("signal_adjusted_5_17") + pl.col("signal_adjusted_17_plus"))
        .alias("total_signal_adjusted")
    )
    
    # Also keep raw total for comparison
    df = df.with_columns(
        (pl.col(youth_col).cast(pl.Float64) + pl.col(adult_col).cast(pl.Float64))
        .alias("total_raw_count")
    )
    
    return df


def apply_signal_weights_biometric(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply signal weights to biometric update data.
    
    Biometric updates are heavily down-weighted as they are
    mostly administrative (mandatory updates, re-enrollments).
    
    Args:
        df: DataFrame with biometric update counts
        
    Returns:
        DataFrame with signal-adjusted columns added
    """
    weight_5_17 = SIGNAL_WEIGHTS["biometric"]["age_5_17"]
    weight_17_plus = SIGNAL_WEIGHTS["biometric"]["age_17_plus"]
    
    youth_col = "age_5_17_count"
    adult_col = "age_17_plus_count"
    
    df = df.with_columns([
        pl.lit(weight_5_17).alias("signal_weight_5_17"),
        pl.lit(weight_17_plus).alias("signal_weight_17_plus"),
        
        (pl.col(youth_col).cast(pl.Float64) * weight_5_17).alias("signal_adjusted_5_17"),
        (pl.col(adult_col).cast(pl.Float64) * weight_17_plus).alias("signal_adjusted_17_plus"),
    ])
    
    df = df.with_columns(
        (pl.col("signal_adjusted_5_17") + pl.col("signal_adjusted_17_plus"))
        .alias("total_signal_adjusted")
    )
    
    df = df.with_columns(
        (pl.col(youth_col).cast(pl.Float64) + pl.col(adult_col).cast(pl.Float64))
        .alias("total_raw_count")
    )
    
    return df


def apply_signal_weights(
    df: pl.DataFrame,
    dataset_type: str
) -> pl.DataFrame:
    """
    Apply appropriate signal weights based on dataset type.
    
    Args:
        df: DataFrame with update counts
        dataset_type: 'biometric' or 'demographic'
        
    Returns:
        DataFrame with signal-adjusted columns
    """
    if dataset_type == "demographic":
        return apply_signal_weights_demographic(df)
    elif dataset_type == "biometric":
        return apply_signal_weights_biometric(df)
    else:
        # For enrolment data, no weighting needed
        return df


# =============================================================================
# COMBINED SIGNAL CALCULATION
# =============================================================================

def calculate_combined_migration_signal(
    demographic_df: pl.DataFrame,
    biometric_df: pl.DataFrame,
    geo_columns: List[str] = ["state", "district", "pincode", "date"]
) -> pl.DataFrame:
    """
    Combine demographic and biometric signals into unified migration metric.
    
    The combined signal gives:
    - Primary weight to demographic updates (address changes)
    - Secondary weight to biometric updates (weak signal)
    
    Args:
        demographic_df: DataFrame with demographic signals
        biometric_df: DataFrame with biometric signals
        geo_columns: Columns to join on
        
    Returns:
        DataFrame with combined migration signal
    """
    # Ensure both have signal weights applied
    if "total_signal_adjusted" not in demographic_df.columns:
        demographic_df = apply_signal_weights_demographic(demographic_df)
    
    if "total_signal_adjusted" not in biometric_df.columns:
        biometric_df = apply_signal_weights_biometric(biometric_df)
    
    # Filter to common columns for join
    existing_geo_cols = [c for c in geo_columns if c in demographic_df.columns]
    
    # Aggregate by geography and date
    demo_agg = demographic_df.group_by(existing_geo_cols).agg([
        pl.col("total_signal_adjusted").sum().alias("demo_signal"),
        pl.col("total_raw_count").sum().alias("demo_raw"),
    ])
    
    bio_agg = biometric_df.group_by(existing_geo_cols).agg([
        pl.col("total_signal_adjusted").sum().alias("bio_signal"),
        pl.col("total_raw_count").sum().alias("bio_raw"),
    ])
    
    # Join datasets
    combined = demo_agg.join(bio_agg, on=existing_geo_cols, how="outer")
    
    # Fill nulls with 0
    combined = combined.with_columns([
        pl.col("demo_signal").fill_null(0),
        pl.col("bio_signal").fill_null(0),
        pl.col("demo_raw").fill_null(0),
        pl.col("bio_raw").fill_null(0),
    ])
    
    # Calculate combined migration signal
    # Demographic signal is primary, biometric is secondary
    combined = combined.with_columns(
        (pl.col("demo_signal") + pl.col("bio_signal")).alias("combined_migration_signal")
    )
    
    combined = combined.with_columns(
        (pl.col("demo_raw") + pl.col("bio_raw")).alias("combined_raw_count")
    )
    
    # Calculate noise reduction ratio
    combined = combined.with_columns(
        pl.when(pl.col("combined_raw_count") > 0)
        .then(pl.col("combined_migration_signal") / pl.col("combined_raw_count"))
        .otherwise(0)
        .alias("signal_to_raw_ratio")
    )
    
    return combined


# =============================================================================
# TEMPORAL DAMPENING
# =============================================================================

def apply_temporal_dampening(
    df: pl.DataFrame,
    dampening_periods: List[Dict]
) -> pl.DataFrame:
    """
    Apply temporal dampening for known policy-driven periods.
    
    Some time periods have artificially high activity due to:
    - Government enrollment drives
    - Policy announcements
    - Administrative deadlines
    
    This function down-weights data from these periods.
    
    Args:
        df: DataFrame with date column
        dampening_periods: List of dicts with 'start', 'end', 'weight' keys
        
    Returns:
        DataFrame with temporal dampening applied
    """
    if "date" not in df.columns:
        return df
    
    # Start with no dampening
    df = df.with_columns(pl.lit(1.0).alias("temporal_weight"))
    
    for period in dampening_periods:
        start = period["start"]
        end = period["end"]
        weight = period.get("weight", 0.5)
        
        # Apply dampening for this period
        df = df.with_columns(
            pl.when(
                (pl.col("date") >= start) & (pl.col("date") <= end)
            )
            .then(weight)
            .otherwise(pl.col("temporal_weight"))
            .alias("temporal_weight")
        )
    
    # Apply temporal weight to signal-adjusted counts
    if "total_signal_adjusted" in df.columns:
        df = df.with_columns(
            (pl.col("total_signal_adjusted") * pl.col("temporal_weight"))
            .alias("temporal_adjusted_signal")
        )
    
    return df


# =============================================================================
# SIGNAL REPORT GENERATION
# =============================================================================

def generate_signal_report(
    df: pl.DataFrame,
    dataset_type: str
) -> Dict:
    """
    Generate a comprehensive signal separation report.
    
    Args:
        df: DataFrame with signal-adjusted columns
        dataset_type: Type of dataset
        
    Returns:
        Dictionary with signal statistics
    """
    if "total_signal_adjusted" not in df.columns:
        df = apply_signal_weights(df, dataset_type)
    
    total_raw = df.select(pl.col("total_raw_count").sum()).item()
    total_signal = df.select(pl.col("total_signal_adjusted").sum()).item()
    
    noise_removed = total_raw - total_signal
    noise_percent = (noise_removed / total_raw * 100) if total_raw > 0 else 0
    
    report = {
        "dataset_type": dataset_type,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_raw_count": float(total_raw),
            "total_signal_adjusted": float(total_signal),
            "noise_removed": float(noise_removed),
            "noise_percent": round(noise_percent, 2),
        },
        "weights_applied": SIGNAL_WEIGHTS.get(dataset_type, {}),
        "interpretation": {
            "signal_strength": "STRONG" if noise_percent < 30 else ("MODERATE" if noise_percent < 50 else "WEAK"),
            "recommendation": (
                "High-quality migration signal" if noise_percent < 30
                else "Use with caution - significant noise" if noise_percent < 50
                else "Heavy noise - interpret carefully"
            ),
        },
    }
    
    return report


def print_signal_report(report: Dict) -> None:
    """
    Print formatted signal separation report.
    
    Args:
        report: Signal report dictionary
    """
    print("\n" + "=" * 60)
    print(f"SIGNAL SEPARATION REPORT: {report['dataset_type'].upper()}")
    print("=" * 60)
    
    summary = report["summary"]
    print(f"\nRaw Count:           {summary['total_raw_count']:,.0f}")
    print(f"Signal-Adjusted:     {summary['total_signal_adjusted']:,.0f}")
    print(f"Noise Removed:       {summary['noise_removed']:,.0f} ({summary['noise_percent']:.1f}%)")
    
    print(f"\nWeights Applied:")
    for age_group, weight in report["weights_applied"].items():
        print(f"  - {age_group}: {weight}")
    
    interp = report["interpretation"]
    print(f"\nSignal Strength: {interp['signal_strength']}")
    print(f"Recommendation: {interp['recommendation']}")
    
    print("=" * 60)


# =============================================================================
# NOISE PATTERN DETECTION
# =============================================================================

def detect_mandatory_update_patterns(
    df: pl.DataFrame,
    dataset_type: str
) -> Dict:
    """
    Detect patterns consistent with mandatory updates.
    
    Mandatory biometric updates occur at ages 5 and 15.
    Spikes in child biometric updates may indicate:
    - School enrollment drives
    - Policy compliance deadlines
    
    Args:
        df: DataFrame with age-group counts
        dataset_type: 'biometric' or 'demographic'
        
    Returns:
        Dictionary with pattern analysis
    """
    if dataset_type != "biometric":
        return {"analysis": "Mandatory update detection applies only to biometric data"}
    
    youth_col = "age_5_17_count"
    adult_col = "age_17_plus_count"
    
    if youth_col not in df.columns or adult_col not in df.columns:
        return {"error": "Required columns not found"}
    
    # Calculate youth-to-adult ratio (high ratio = likely mandatory updates)
    total_youth = df.select(pl.col(youth_col).sum()).item()
    total_adult = df.select(pl.col(adult_col).sum()).item()
    
    ratio = total_youth / total_adult if total_adult > 0 else float("inf")
    
    # Expected ratio for genuine migration is low (adults move more than children)
    # High ratio suggests mandatory child updates
    expected_ratio = 0.3  # Adults should be ~3x youth for genuine migration
    
    pattern_detected = ratio > 0.5  # More than 50% youth suggests administrative activity
    
    return {
        "total_youth_updates": int(total_youth),
        "total_adult_updates": int(total_adult),
        "youth_to_adult_ratio": round(ratio, 3),
        "expected_ratio": expected_ratio,
        "mandatory_pattern_detected": pattern_detected,
        "interpretation": (
            "High youth-to-adult ratio suggests significant mandatory update activity"
            if pattern_detected
            else "Youth-to-adult ratio consistent with genuine migration patterns"
        ),
    }


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    from src.engines.ingestion import load_processed_dataset
    
    print("=" * 60)
    print("AADHAAR SANKET - SIGNAL SEPARATION ENGINE")
    print("=" * 60)
    
    # Print classification rules
    print("\nSIGNAL CLASSIFICATION RULES:")
    print("-" * 60)
    for classification in classify_all_update_types():
        noise_label = " [NOISE]" if classification.is_noise else ""
        print(f"\n{classification.update_type.upper()} - {classification.age_group}{noise_label}")
        print(f"  Weight: {classification.weight}")
        print(f"  Reason: {classification.reasoning}")
    
    # Process datasets
    print("\n" + "=" * 60)
    print("PROCESSING DATASETS")
    print("=" * 60)
    
    for dataset_type in ["biometric", "demographic"]:
        try:
            df = load_processed_dataset(dataset_type)
            df = apply_signal_weights(df, dataset_type)
            report = generate_signal_report(df, dataset_type)
            print_signal_report(report)
            
            if dataset_type == "biometric":
                patterns = detect_mandatory_update_patterns(df, dataset_type)
                print(f"\nMandatory Update Pattern Analysis:")
                print(f"  Youth-to-Adult Ratio: {patterns.get('youth_to_adult_ratio', 'N/A')}")
                print(f"  Pattern Detected: {patterns.get('mandatory_pattern_detected', 'N/A')}")
                
        except FileNotFoundError:
            print(f"\n[SKIP] Dataset {dataset_type} not found. Run ingestion first.")
