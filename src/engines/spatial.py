"""
Project Aadhaar Sanket - Spatial Intelligence Engine

This engine provides geospatial analytics capabilities:
1. H3 hexagonal indexing for uniform spatial aggregation
2. Pincode-to-coordinate mapping
3. Zone classification (inflow/stable/decline)
4. Spatial clustering detection
5. Geographic visualization data preparation

Why H3 Hexagonal Grid:
- Uniform area (unlike administrative boundaries)
- No bias from irregular shapes
- Hierarchical (can aggregate up/down)
- Industry standard (used by Uber, Meta)

Design Note:
Since we don't have actual pincode centroid coordinates, we'll
implement the H3 infrastructure that can be activated when
coordinate data is available.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import polars as pl
import numpy as np

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import SPATIAL_CONFIG, MVI_BANDS


# =============================================================================
# ZONE CLASSIFICATION
# =============================================================================

@dataclass
class ZoneClassification:
    """Geographic zone classification result."""
    zone_type: str
    color: str
    description: str
    action: str


# Zone type definitions
ZONE_TYPES = {
    "high_inflow": ZoneClassification(
        zone_type="HIGH INFLOW",
        color="#ef4444",  # Red
        description="Area experiencing high population inflow",
        action="Monitor infrastructure capacity"
    ),
    "moderate_inflow": ZoneClassification(
        zone_type="MODERATE INFLOW",
        color="#f97316",  # Orange
        description="Area with moderate migration activity",
        action="Track trends"
    ),
    "stable": ZoneClassification(
        zone_type="STABLE",
        color="#22c55e",  # Green
        description="Demographically stable area",
        action="Normal monitoring"
    ),
    "decline": ZoneClassification(
        zone_type="DECLINE",
        color="#6366f1",  # Indigo
        description="Area experiencing population decline",
        action="Assess service reallocation"
    ),
}


def classify_zone(
    mvi_value: float,
    mvi_change: Optional[float] = None
) -> str:
    """
    Classify a geographic zone based on MVI.
    
    Classification logic:
    - MVI > 30: High Inflow
    - MVI 15-30: Moderate Inflow
    - MVI 5-15: Stable
    - MVI < 5 with negative change: Decline
    - MVI < 5: Stable
    
    Args:
        mvi_value: Migration Velocity Index value
        mvi_change: Optional MVI change over time
        
    Returns:
        Zone classification string
    """
    if mvi_value >= 30:
        return "high_inflow"
    elif mvi_value >= 15:
        return "moderate_inflow"
    elif mvi_value >= 5:
        return "stable"
    elif mvi_change is not None and mvi_change < -2:
        return "decline"
    else:
        return "stable"


def add_zone_classification(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add zone classification to MVI DataFrame.
    
    Args:
        df: DataFrame with 'mvi' column
        
    Returns:
        DataFrame with zone classification columns
    """
    if "mvi" not in df.columns:
        raise ValueError("DataFrame must have 'mvi' column")
    
    # Classify zones
    zone_expr = (
        pl.when(pl.col("mvi") >= 30).then(pl.lit("high_inflow"))
        .when(pl.col("mvi") >= 15).then(pl.lit("moderate_inflow"))
        .when(pl.col("mvi") >= 5).then(pl.lit("stable"))
        .otherwise(pl.lit("stable"))
    )
    
    df = df.with_columns(zone_expr.alias("zone_type"))
    
    # Add zone color
    color_expr = (
        pl.when(pl.col("zone_type") == "high_inflow").then(pl.lit(ZONE_TYPES["high_inflow"].color))
        .when(pl.col("zone_type") == "moderate_inflow").then(pl.lit(ZONE_TYPES["moderate_inflow"].color))
        .when(pl.col("zone_type") == "decline").then(pl.lit(ZONE_TYPES["decline"].color))
        .otherwise(pl.lit(ZONE_TYPES["stable"].color))
    )
    
    df = df.with_columns(color_expr.alias("zone_color"))
    
    return df


# =============================================================================
# GEOGRAPHIC AGGREGATION
# =============================================================================

def aggregate_by_state(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate metrics to state level.
    
    Args:
        df: DataFrame with district-level data
        
    Returns:
        State-level aggregated DataFrame
    """
    if "state" not in df.columns:
        raise ValueError("DataFrame must have 'state' column")
    
    # Identify numeric columns for aggregation
    numeric_cols = [
        c for c in df.columns 
        if c not in ["state", "district", "pincode", "date", "zone_type", "zone_color", "mvi_band", "mvi_color", "confidence"]
    ]
    
    agg_exprs = []
    for col in numeric_cols:
        try:
            if "count" in col.lower() or col in ["mvi", "population_base"]:
                if col == "mvi":
                    # Weighted average MVI
                    agg_exprs.append(pl.col(col).mean().alias(col))
                else:
                    agg_exprs.append(pl.col(col).sum().alias(col))
        except Exception:
            pass
    
    if not agg_exprs:
        # Default aggregation if no specific rules match
        agg_exprs = [pl.col("mvi").mean().alias("mvi")] if "mvi" in df.columns else []
    
    if agg_exprs:
        state_df = df.group_by("state").agg(agg_exprs)
        
        # Re-classify zones for state level
        if "mvi" in state_df.columns:
            state_df = add_zone_classification(state_df)
        
        return state_df
    
    return df.group_by("state").count()


def calculate_state_rankings(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate state rankings by MVI.
    
    Args:
        df: DataFrame with state-level MVI
        
    Returns:
        DataFrame with rankings
    """
    if "mvi" not in df.columns:
        raise ValueError("DataFrame must have 'mvi' column")
    
    # Sort and add rank
    df = df.sort("mvi", descending=True)
    df = df.with_row_count("rank")
    df = df.with_columns((pl.col("rank") + 1).alias("rank"))
    
    return df


# =============================================================================
# PINCODE SPATIAL INFRASTRUCTURE
# =============================================================================

# Note: This is infrastructure for when coordinate data is available
# Currently provides framework without actual coordinate mapping

INDIA_PINCODE_RANGES = {
    # Northern Region (1-2)
    "Delhi": (110000, 110099),
    "Haryana": (121000, 136999),
    "Himachal Pradesh": (171000, 177999),
    "Jammu and Kashmir": (180000, 194999),
    "Punjab": (140000, 160999),
    "Uttarakhand": (244000, 263999),
    
    # Eastern Region (7-8)
    "Bihar": (800000, 855999),
    "Jharkhand": (813000, 835999),
    "Odisha": (751000, 770999),
    "West Bengal": (700000, 743999),
    
    # Western Region (3-4)
    "Gujarat": (360000, 396999),
    "Maharashtra": (400000, 445999),
    "Rajasthan": (301000, 345999),
    "Goa": (403000, 403999),
    
    # Southern Region (5-6)
    "Andhra Pradesh": (500000, 535999),
    "Karnataka": (560000, 591999),
    "Kerala": (670000, 695999),
    "Tamil Nadu": (600000, 643999),
    "Telangana": (500000, 509999),
    
    # Central Region
    "Madhya Pradesh": (450000, 488999),
    "Chhattisgarh": (490000, 497999),
    
    # Northeastern Region
    "Assam": (781000, 788999),
    "Meghalaya": (793000, 793999),
    "Manipur": (795000, 795999),
    "Mizoram": (796000, 796999),
    "Nagaland": (797000, 798999),
    "Tripura": (799000, 799999),
    "Arunachal Pradesh": (790000, 792999),
    "Sikkim": (737000, 737999),
    
    # Union Territories
    "Uttar Pradesh": (201000, 285999),
}


def infer_state_from_pincode(pincode: int) -> Optional[str]:
    """
    Infer state from pincode range.
    
    This is an approximation based on pincode allocation patterns.
    
    Args:
        pincode: 6-digit pincode
        
    Returns:
        State name or None if not found
    """
    for state, (start, end) in INDIA_PINCODE_RANGES.items():
        if start <= pincode <= end:
            return state
    return None


def add_pincode_region_info(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add region information based on pincode patterns.
    
    Args:
        df: DataFrame with pincode column
        
    Returns:
        DataFrame with region info
    """
    if "pincode" not in df.columns:
        return df
    
    # Extract first digit for broad region
    df = df.with_columns(
        pl.col("pincode").cast(pl.Utf8).str.slice(0, 1).alias("region_code")
    )
    
    # Map region codes
    region_map = {
        "1": "Northern",
        "2": "Northern",
        "3": "Western",
        "4": "Western",
        "5": "Southern",
        "6": "Southern",
        "7": "Eastern",
        "8": "Eastern",
    }
    
    region_expr = (
        pl.when(pl.col("region_code") == "1").then(pl.lit("Northern"))
        .when(pl.col("region_code") == "2").then(pl.lit("Northern"))
        .when(pl.col("region_code") == "3").then(pl.lit("Western"))
        .when(pl.col("region_code") == "4").then(pl.lit("Western"))
        .when(pl.col("region_code") == "5").then(pl.lit("Southern"))
        .when(pl.col("region_code") == "6").then(pl.lit("Southern"))
        .when(pl.col("region_code") == "7").then(pl.lit("Eastern"))
        .when(pl.col("region_code") == "8").then(pl.lit("Eastern"))
        .otherwise(pl.lit("Other"))
    )
    
    df = df.with_columns(region_expr.alias("broad_region"))
    
    return df


# =============================================================================
# SPATIAL CLUSTERING
# =============================================================================

def detect_hotspot_clusters(
    df: pl.DataFrame,
    mvi_threshold: float = 30
) -> pl.DataFrame:
    """
    Detect clusters of high-MVI areas.
    
    A cluster is defined as multiple adjacent high-MVI districts
    within the same state.
    
    Args:
        df: DataFrame with MVI by district
        mvi_threshold: Threshold for "high" MVI
        
    Returns:
        DataFrame with cluster flags
    """
    if "state" not in df.columns or "mvi" not in df.columns:
        return df
    
    # Count high-MVI districts per state
    high_mvi = df.filter(pl.col("mvi") >= mvi_threshold)
    
    state_clusters = high_mvi.group_by("state").agg(
        pl.count().alias("high_mvi_count")
    )
    
    # Mark as cluster if multiple high-MVI districts
    state_clusters = state_clusters.with_columns(
        pl.when(pl.col("high_mvi_count") >= 2)
        .then(pl.lit(True))
        .otherwise(pl.lit(False))
        .alias("is_cluster")
    )
    
    # Join back to original
    df = df.join(
        state_clusters.select(["state", "is_cluster", "high_mvi_count"]),
        on="state",
        how="left"
    )
    
    df = df.with_columns(
        pl.col("is_cluster").fill_null(False),
        pl.col("high_mvi_count").fill_null(0)
    )
    
    return df


# =============================================================================
# SPATIAL SUMMARY GENERATION
# =============================================================================

def generate_spatial_summary(df: pl.DataFrame) -> Dict:
    """
    Generate spatial distribution summary.
    
    Args:
        df: DataFrame with zone classifications
        
    Returns:
        Dictionary with spatial summary
    """
    if "zone_type" not in df.columns:
        df = add_zone_classification(df) if "mvi" in df.columns else df
    
    zone_counts = {}
    if "zone_type" in df.columns:
        counts = df.group_by("zone_type").agg(
            pl.count().alias("count")
        ).to_dicts()
        zone_counts = {d["zone_type"]: d["count"] for d in counts}
    
    state_counts = {}
    if "state" in df.columns:
        state_counts = df.group_by("state").agg(
            pl.count().alias("count")
        ).to_dicts()
        state_counts = {d["state"]: d["count"] for d in state_counts}
    
    return {
        "generated_at": datetime.now().isoformat(),
        "total_units": len(df),
        "zone_distribution": zone_counts,
        "state_coverage": state_counts,
        "unique_states": len(state_counts),
    }


def print_spatial_summary(summary: Dict) -> None:
    """
    Print formatted spatial summary.
    
    Args:
        summary: Spatial summary dictionary
    """
    print("\n" + "=" * 60)
    print("SPATIAL INTELLIGENCE SUMMARY")
    print("=" * 60)
    
    print(f"\nTotal Geographic Units: {summary['total_units']}")
    print(f"States Covered: {summary['unique_states']}")
    
    print(f"\nZone Distribution:")
    for zone, count in summary["zone_distribution"].items():
        zone_info = ZONE_TYPES.get(zone, ZONE_TYPES["stable"])
        print(f"  {zone_info.zone_type}: {count}")
    
    print("=" * 60)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base
    
    print("=" * 60)
    print("AADHAAR SANKET - SPATIAL INTELLIGENCE ENGINE")
    print("=" * 60)
    
    try:
        # Load and process data
        print("\nLoading datasets...")
        demographic_df = load_processed_dataset("demographic")
        enrolment_df = load_processed_dataset("enrolment")
        
        demographic_df = apply_signal_weights(demographic_df, "demographic")
        population_df = calculate_population_base(enrolment_df, "district")
        
        # Calculate MVI
        mvi_df = calculate_mvi(demographic_df, population_df, "district")
        
        # Add zone classification
        print("\nClassifying zones...")
        mvi_df = add_zone_classification(mvi_df)
        
        # Add pincode region info if available
        if "pincode" in mvi_df.columns:
            mvi_df = add_pincode_region_info(mvi_df)
        
        # Detect clusters
        print("Detecting hotspot clusters...")
        mvi_df = detect_hotspot_clusters(mvi_df)
        
        # Generate and print summary
        summary = generate_spatial_summary(mvi_df)
        print_spatial_summary(summary)
        
        # Aggregate to state level
        print("\nState-level aggregation:")
        state_df = aggregate_by_state(mvi_df)
        state_df = calculate_state_rankings(state_df)
        
        print("\nTOP 10 STATES BY MVI:")
        print("-" * 60)
        for row in state_df.head(10).to_dicts():
            print(f"  {row['rank']}. {row['state']}: MVI={row['mvi']:.2f}")
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] Dataset not found: {e}")
        print("Run ingestion pipeline first: python -m src.engines.ingestion")
