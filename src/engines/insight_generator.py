"""
Project Aadhaar Sanket - Explainable Insight Generator

Generates plain-language summaries using template-based logic.

NO LLMs. Pure deterministic template filling.

Answers the critical questions:
- What is happening?
- Why?
- How confident are we?
- What should be done?
"""
from dataclasses import dataclass
from typing import Dict, List
import polars as pl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class Insight:
    """Generated insight for a geographic unit."""
    geo_key: str
    insight_summary: str
    key_findings: List[str]
    confidence_statement: str
    recommended_action: str


# =============================================================================
# INSIGHT TEMPLATES
# =============================================================================

SUMMARY_TEMPLATE = (
    "{geo_key} shows {trend_description} over {period}, "
    "driven by {dominant_signal}, with {acceleration_status} pressure. "
    "Confidence: {confidence_level}."
)

TREND_DESCRIPTIONS = {
    "persistent_inflow": "persistent moderate inflow",
    "emerging_inflow": "emerging inflow pattern",
    "volatile": "volatile migration activity",
    "stable": "stable baseline conditions",
    "reversal": "declining migration activity",
}

ACCELERATION_DESCRIPTIONS = {
    "accelerating": "accelerating",
    "stable": "steady",
    "decelerating": "declining",
}


# =============================================================================
# INSIGHT GENERATION
# =============================================================================

def generate_insight_summary(
    geo_key: str,
    trend_type: str,
    acceleration_class: str,
    confidence_level: str,
    period: str = "6 months",
    dominant_signal: str = "demographic updates"
) -> str:
    """Generate summary insight using template."""
    trend_desc = TREND_DESCRIPTIONS.get(trend_type, "migration activity")
    accel_desc = ACCELERATION_DESCRIPTIONS.get(acceleration_class, "steady")
    
    return SUMMARY_TEMPLATE.format(
        geo_key=geo_key,
        trend_description=trend_desc,
        period=period,
        dominant_signal=dominant_signal,
        acceleration_status=accel_desc,
        confidence_level=confidence_level
    )


def generate_key_findings(
    trend_type: str,
    trend_strength: float,
    persistence_score: float,
    affected_population: int,
    is_seasonal: bool
) -> List[str]:
    """Generate key findings list."""
    findings = []
    
    # Trend finding
    if trend_strength > 0.7:
        findings.append(f"Strong {trend_type.replace('_', ' ')} pattern (strength: {trend_strength:.2f})")
    elif trend_strength > 0.4:
        findings.append(f"Moderate {trend_type.replace('_', ' ')} pattern (strength: {trend_strength:.2f})")
    else:
        findings.append(f"Weak {trend_type.replace('_', ' ')} pattern (strength: {trend_strength:.2f})")
    
    # Persistence finding
    if persistence_score > 0.7:
        findings.append(f"Structural pattern (persistence: {persistence_score:.1%})")
    elif persistence_score < 0.3:
        findings.append(f"Temporary pattern (persistence: {persistence_score:.1%})")
    
    # Impact finding
    if affected_population > 10000:
        findings.append(f"High impact: {affected_population:,} people affected")
    elif affected_population > 1000:
        findings.append(f"Moderate impact: {affected_population:,} people affected")
    
    # Seasonality finding
    if is_seasonal:
        findings.append("Seasonal migration pattern detected")
    
    return findings


def generate_confidence_statement(
    confidence_level: str,
    confidence_score: float,
    limiting_factors: str
) -> str:
    """Generate confidence statement."""
    if confidence_level == "high":
        return f"High confidence assessment (score: {confidence_score:.2f}). {limiting_factors}"
    elif confidence_level == "medium":
        return f"Medium confidence assessment (score: {confidence_score:.2f}). Limiting factors: {limiting_factors}"
    else:
        return f"Low confidence assessment (score: {confidence_score:.2f}). Caution advised. Limiting factors: {limiting_factors}"


# =============================================================================
# MAIN GENERATION FUNCTION
# =============================================================================

def generate_insights(
    trend_df: pl.DataFrame,
    persistence_df: pl.DataFrame,
    impact_df: pl.DataFrame,
    confidence_df: pl.DataFrame,
    acceleration_df: pl.DataFrame,
    seasonality_df: pl.DataFrame,
    policy_df: pl.DataFrame
) -> pl.DataFrame:
    """
    Generate comprehensive insights by combining all analytics.
    
    Args:
        trend_df: Trend typology results
        persistence_df: Persistence analysis results
        impact_df: Population impact results
        confidence_df: Confidence assessment results
        acceleration_df: Acceleration analysis results
        seasonality_df: Seasonality detection results
        policy_df: Policy recommendations
        
    Returns:
        DataFrame with generated insights
    """
    # Merge all analytics
    combined = trend_df.select(["geo_key", "trend_type", "trend_strength"])
    
    # Join all other analytics
    for df, cols in [
        (persistence_df, ["geo_key", "persistence_score"]),
        (impact_df, ["geo_key", "affected_population"]),
        (confidence_df, ["geo_key", "confidence_level", "confidence_score", "limiting_factors"]),
        (acceleration_df, ["geo_key", "classification"]),
        (seasonality_df, ["geo_key", "is_seasonal"]),
        (policy_df, ["geo_key", "primary_action"]),
    ]:
        if "geo_key" in df.columns:
            combined = combined.join(
                df.select([c for c in cols if c in df.columns]),
                on="geo_key",
                how="left"
            )
    
    # Generate insights
    insights = []
    
    for row in combined.to_dicts():
        # Generate summary
        summary = generate_insight_summary(
            geo_key=row["geo_key"],
            trend_type=row.get("trend_type", "stable"),
            acceleration_class=row.get("classification", "stable"),
            confidence_level=row.get("confidence_level", "medium")
        )
        
        # Generate key findings
        findings = generate_key_findings(
            trend_type=row.get("trend_type", "stable"),
            trend_strength=row.get("trend_strength", 0.5),
            persistence_score=row.get("persistence_score", 0.5),
            affected_population=row.get("affected_population", 0),
            is_seasonal=row.get("is_seasonal", False)
        )
        
        # Generate confidence statement
        conf_statement = generate_confidence_statement(
            confidence_level=row.get("confidence_level", "medium"),
            confidence_score=row.get("confidence_score", 0.5),
            limiting_factors=row.get("limiting_factors", "None")
        )
        
        insights.append({
            "geo_key": row["geo_key"],
            "insight_summary": summary,
            "key_findings": "; ".join(findings),
            "confidence_statement": conf_statement,
            "recommended_action": row.get("primary_action", "Standard Monitoring"),
        })
    
    return pl.DataFrame(insights)


# =============================================================================
# REPORTING
# =============================================================================

def print_insights(insights_df: pl.DataFrame, limit: int = 10):
    """Print formatted insights."""
    print("\n" + "=" * 70)
    print("EXPLAINABLE INSIGHTS")
    print("=" * 70)
    
    for i, row in enumerate(insights_df.head(limit).to_dicts(), 1):
        print(f"\n{i}. {row['geo_key']}")
        print(f"   {row['insight_summary']}")
        print(f"\n   Key Findings:")
        for finding in row['key_findings'].split("; "):
            print(f"   • {finding}")
        print(f"\n   {row['confidence_statement']}")
        print(f"\n   Recommended Action: {row['recommended_action']}")
        print("-" * 70)


def export_insights_to_json(insights_df: pl.DataFrame, output_path: str):
    """Export insights to JSON for frontend consumption."""
    import json
    from datetime import datetime
    from pathlib import Path
    
    insights_list = []
    for row in insights_df.to_dicts():
        insights_list.append({
            "geo_key": row["geo_key"],
            "summary": row["insight_summary"],
            "findings": row["key_findings"].split("; "),
            "confidence": row["confidence_statement"],
            "action": row["recommended_action"],
        })
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_insights": len(insights_list),
            "insights": insights_list
        }, f, indent=2)
    
    print(f"\nInsights exported to: {output_file}")
