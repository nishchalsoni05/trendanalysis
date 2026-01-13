"""
Project Aadhaar Sanket - Policy Action Mapper

Converts analytics into actionable policy recommendations.

Maps: Trend Pattern → Recommended Policy Action

This is the CRITICAL bridge between analytics and decision-making.

NO ML. Pure rule-based mapping with explicit rationale.
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class PolicyRecommendation:
    """Policy recommendation for a geographic unit."""
    geo_key: str
    primary_action: str
    priority: str  # high, medium, low
    timeframe: str
    rationale: str
    supporting_metrics: Dict


# =============================================================================
# POLICY MAPPING RULES
# =============================================================================

POLICY_RULES = {
    # (trend_type, impact_level, confidence_level) -> action
    ("persistent_inflow", "high", "high"): {
        "action": "Infrastructure Planning & Expansion",
        "priority": "high",
        "timeframe": "6-12 months",
        "details": "Permanent infrastructure: schools, hospitals, housing"
    },
    ("persistent_inflow", "moderate", "high"): {
        "action": "Enhanced Service Capacity",
        "priority": "medium",
        "timeframe": "3-6 months",
        "details": "Scale up existing services, monitor growth"
    },
    ("emerging_inflow", "high", "high"): {
        "action": "Early Intervention & Monitoring",
        "priority": "high",
        "timeframe": "1-3 months",
        "details": "Deploy rapid assessment teams, prepare resources"
    },
    ("emerging_inflow", "moderate", "medium"): {
        "action": "Enhanced Monitoring",
        "priority": "medium",
        "timeframe": "3-6 months",
        "details": "Track trend development, prepare contingency plans"
    },
    ("volatile", "high", "medium"): {
        "action": "Data Quality Audit",
        "priority": "high",
        "timeframe": "Immediate",
        "details": "Investigate data collection processes, verify patterns"
    },
    ("volatile", "moderate", "low"): {
        "action": "Improve Data Collection",
        "priority": "medium",
        "timeframe": "1-3 months",
        "details": "Enhance monitoring systems, increase data frequency"
    },
    ("stable", "low", "high"): {
        "action": "Routine Monitoring",
        "priority": "low",
        "timeframe": "Ongoing",
        "details": "Maintain current service levels, periodic review"
    },
    ("reversal", "moderate", "high"): {
        "action": "Resource Reallocation Assessment",
        "priority": "medium",
        "timeframe": "3-6 months",
        "details": "Evaluate resource redistribution opportunities"
    },
}

# Seasonal pattern overrides
SEASONAL_RULES = {
    ("seasonal", "high"): {
        "action": "Temporary Resource Deployment",
        "priority": "medium",
        "timeframe": "Seasonal (recurring)",
        "details": "Mobile services, temporary facilities during peak months"
    },
    ("seasonal", "moderate"): {
        "action": "Seasonal Capacity Planning",
        "priority": "low",
        "timeframe": "Seasonal (recurring)",
        "details": "Flexible staffing, temporary resource allocation"
    },
}


# =============================================================================
# MAPPING LOGIC
# =============================================================================

def map_to_policy_action(
    trend_type: str,
    impact_classification: str,
    confidence_level: str,
    is_seasonal: bool = False,
    acceleration_warning: str = None
) -> Dict:
    """
    Map analytics to policy recommendation.
    
    Args:
        trend_type: From trend typology
        impact_classification: From population impact
        confidence_level: From trend confidence
        is_seasonal: From seasonality detection
        acceleration_warning: From acceleration analysis
        
    Returns:
        Policy recommendation dict
    """
    # Check seasonal override
    if is_seasonal:
        key = ("seasonal", impact_classification)
        if key in SEASONAL_RULES:
            return SEASONAL_RULES[key]
    
    # Check acceleration override
    if acceleration_warning == "high":
        return {
            "action": "Urgent Intervention Required",
            "priority": "high",
            "timeframe": "Immediate",
            "details": "Rapidly accelerating situation requires immediate attention"
        }
    
    # Standard mapping
    key = (trend_type, impact_classification, confidence_level)
    
    if key in POLICY_RULES:
        return POLICY_RULES[key]
    
    # Fallback based on partial match
    # Try without confidence level
    for (t, i, c), action in POLICY_RULES.items():
        if t == trend_type and i == impact_classification:
            return action
    
    # Default
    return {
        "action": "Standard Monitoring",
        "priority": "low",
        "timeframe": "Ongoing",
        "details": "Continue routine monitoring and assessment"
    }


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def generate_policy_recommendations(
    trend_df: pl.DataFrame,
    impact_df: pl.DataFrame,
    confidence_df: pl.DataFrame,
    seasonality_df: pl.DataFrame = None,
    acceleration_df: pl.DataFrame = None
) -> pl.DataFrame:
    """
    Generate policy recommendations by combining all analytics.
    
    Args:
        trend_df: Trend typology results
        impact_df: Population impact results
        confidence_df: Confidence assessment results
        seasonality_df: Optional seasonality results
        acceleration_df: Optional acceleration results
        
    Returns:
        DataFrame with policy recommendations
    """
    # Merge all analytics
    combined = trend_df.select(["geo_key", "trend_type", "trend_strength"])
    
    # Join impact
    if "geo_key" in impact_df.columns:
        combined = combined.join(
            impact_df.select(["geo_key", "impact_classification", "affected_population"]),
            on="geo_key",
            how="left"
        )
    
    # Join confidence
    if "geo_key" in confidence_df.columns:
        combined = combined.join(
            confidence_df.select(["geo_key", "confidence_level", "confidence_score"]),
            on="geo_key",
            how="left"
        )
    
    # Join seasonality
    if seasonality_df is not None and "geo_key" in seasonality_df.columns:
        combined = combined.join(
            seasonality_df.select(["geo_key", "is_seasonal"]),
            on="geo_key",
            how="left"
        )
    else:
        combined = combined.with_columns(pl.lit(False).alias("is_seasonal"))
    
    # Join acceleration
    if acceleration_df is not None and "geo_key" in acceleration_df.columns:
        combined = combined.join(
            acceleration_df.select(["geo_key", "warning_level"]),
            on="geo_key",
            how="left"
        )
    else:
        combined = combined.with_columns(pl.lit("low").alias("warning_level"))
    
    # Generate recommendations
    recommendations = []
    
    for row in combined.to_dicts():
        policy = map_to_policy_action(
            trend_type=row.get("trend_type", "stable"),
            impact_classification=row.get("impact_classification", "low"),
            confidence_level=row.get("confidence_level", "medium"),
            is_seasonal=row.get("is_seasonal", False),
            acceleration_warning=row.get("warning_level", "low")
        )
        
        # Build rationale
        rationale = (
            f"{row.get('trend_type', 'stable').replace('_', ' ').title()} trend "
            f"with {row.get('impact_classification', 'low')} impact "
            f"({row.get('affected_population', 0):,} people affected). "
            f"Confidence: {row.get('confidence_level', 'medium')}. "
            f"{policy['details']}"
        )
        
        recommendations.append({
            "geo_key": row["geo_key"],
            "primary_action": policy["action"],
            "priority": policy["priority"],
            "timeframe": policy["timeframe"],
            "rationale": rationale,
            "trend_type": row.get("trend_type", "stable"),
            "impact_level": row.get("impact_classification", "low"),
            "confidence": row.get("confidence_level", "medium"),
            "affected_population": row.get("affected_population", 0),
        })
    
    return pl.DataFrame(recommendations)


# =============================================================================
# SUMMARY & REPORTING
# =============================================================================

def generate_policy_summary(policy_df: pl.DataFrame) -> Dict:
    """Generate summary of policy recommendations."""
    total = len(policy_df)
    
    # Count by priority
    priority_counts = policy_df.group_by("priority").agg(
        pl.count().alias("count")
    )
    
    priority_dist = {
        row["priority"]: {
            "count": row["count"],
            "percent": round(row["count"] / total * 100, 1)
        }
        for row in priority_counts.to_dicts()
    }
    
    # High priority actions
    high_priority = policy_df.filter(
        pl.col("priority") == "high"
    ).sort("affected_population", descending=True)
    
    # Action type distribution
    action_counts = policy_df.group_by("primary_action").agg(
        pl.count().alias("count")
    ).sort("count", descending=True)
    
    return {
        "total_units": total,
        "priority_distribution": priority_dist,
        "high_priority_actions": {
            "count": len(high_priority),
            "percent": round(len(high_priority) / total * 100, 1) if total > 0 else 0,
            "top_10": high_priority.head(10).select([
                "geo_key", "primary_action", "timeframe", "affected_population", "rationale"
            ]).to_dicts()
        },
        "action_types": {
            row["primary_action"]: row["count"]
            for row in action_counts.to_dicts()
        }
    }


def print_policy_summary(summary: Dict):
    """Print formatted policy summary."""
    print("\n" + "=" * 70)
    print("POLICY DECISION FRAMEWORK")
    print("=" * 70)
    
    print(f"\nTotal Geographic Units: {summary['total_units']}")
    
    print("\nPriority Distribution:")
    for priority, data in summary["priority_distribution"].items():
        print(f"  {priority.upper():10s}: {data['count']:4d} ({data['percent']:5.1f}%)")
    
    high_pri = summary["high_priority_actions"]
    print(f"\n🔴 HIGH PRIORITY ACTIONS: {high_pri['count']} ({high_pri['percent']:.1f}%)")
    print("(Require immediate executive attention)")
    
    if high_pri["top_10"]:
        print("\nTop 10 High Priority Zones:")
        for i, zone in enumerate(high_pri["top_10"], 1):
            print(f"\n  {i:2d}. {zone['geo_key']}")
            print(f"      Action: {zone['primary_action']}")
            print(f"      Timeframe: {zone['timeframe']}")
            print(f"      Affected Population: {zone['affected_population']:,}")
            print(f"      Rationale: {zone['rationale']}")
    
    print("\nAction Type Distribution:")
    for action, count in list(summary["action_types"].items())[:5]:
        print(f"  {action}: {count}")
