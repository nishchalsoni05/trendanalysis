"""
Project Aadhaar Sanket - Anomaly Detection Engine

This engine detects unusual patterns in migration data:
1. Z-score based anomaly detection
2. Temporal baseline comparison
3. Seasonal vs structural anomaly classification
4. Alert generation with severity levels

Anomaly Types:
- SPIKE: Sudden increase significantly above historical baseline
- DROP: Sudden decrease significantly below baseline
- VOLATILITY: Unusual fluctuation in typically stable areas
- STRUCTURAL: Sustained deviation indicating fundamental change

Design Principles:
- Transparent, auditable detection logic
- No black-box ML for anomaly detection
- Explicit thresholds and reasoning
- Actionable alerts with context
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import polars as pl
import numpy as np

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import ANOMALY_CONFIG


# =============================================================================
# ANOMALY DATA STRUCTURES
# =============================================================================

@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_id: str
    location: str
    date: str
    anomaly_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    z_score: float
    expected_value: float
    actual_value: float
    description: str
    recommended_action: str


@dataclass
class Alert:
    """Actionable alert for stakeholders."""
    alert_id: str
    timestamp: str
    severity: str
    title: str
    summary: str
    affected_regions: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


# =============================================================================
# STATISTICAL FUNCTIONS
# =============================================================================

def calculate_z_score(
    value: float,
    mean: float,
    std: float
) -> float:
    """
    Calculate Z-score for a value.
    
    Z-score measures how many standard deviations a value
    is from the mean.
    
    Formula: Z = (X - μ) / σ
    
    Args:
        value: The observed value
        mean: Historical mean
        std: Historical standard deviation
        
    Returns:
        Z-score (0 if std is 0)
    """
    if std == 0 or std is None:
        return 0.0
    return (value - mean) / std


def calculate_baseline_statistics(
    series: pl.Series,
    exclude_latest: int = 1
) -> Tuple[float, float]:
    """
    Calculate baseline mean and std for a series.
    
    Excludes the latest N values to avoid including
    the value being tested in the baseline.
    
    Args:
        series: Polars series of values
        exclude_latest: Number of recent values to exclude
        
    Returns:
        Tuple of (mean, std)
    """
    values = series.to_list()
    
    if len(values) <= exclude_latest:
        return (0.0, 0.0)
    
    baseline = values[:-exclude_latest] if exclude_latest > 0 else values
    
    if not baseline:
        return (0.0, 0.0)
    
    mean = np.mean(baseline)
    std = np.std(baseline)
    
    return (float(mean), float(std))


# =============================================================================
# ANOMALY DETECTION
# =============================================================================

def detect_anomalies_in_series(
    df: pl.DataFrame,
    value_column: str,
    geo_columns: List[str],
    z_threshold: float = None
) -> pl.DataFrame:
    """
    Detect anomalies in a time series by geographic unit.
    
    Args:
        df: DataFrame with time series data
        value_column: Column containing values to analyze
        geo_columns: Geographic grouping columns
        z_threshold: Z-score threshold (default from config)
        
    Returns:
        DataFrame with anomaly flags and scores
    """
    if z_threshold is None:
        z_threshold = ANOMALY_CONFIG["z_score_threshold"]
    
    if value_column not in df.columns:
        raise ValueError(f"Column {value_column} not found in DataFrame")
    
    existing_geo = [c for c in geo_columns if c in df.columns]
    
    # Calculate rolling mean and std per geography
    # Using a simple approach without date-based windowing if no date column
    
    if "date" in df.columns and existing_geo:
        # Sort by geography and date
        df = df.sort(existing_geo + ["date"])
        
        window_days = ANOMALY_CONFIG.get("baseline_window_days", 30)
        min_periods = ANOMALY_CONFIG.get("min_baseline_points", 7)
        
        # Calculate rolling statistics
        df = df.with_columns([
            pl.col(value_column)
            .rolling_mean(window_size=window_days, min_periods=min_periods)
            .over(existing_geo)
            .alias("_rolling_mean"),
            
            pl.col(value_column)
            .rolling_std(window_size=window_days, min_periods=min_periods)
            .over(existing_geo)
            .alias("_rolling_std"),
        ])
        
        # Replace null std with 0
        df = df.with_columns(
            pl.col("_rolling_std").fill_null(0).alias("_rolling_std")
        )
        
        # Calculate Z-score
        df = df.with_columns(
            pl.when(pl.col("_rolling_std") > 0)
            .then((pl.col(value_column) - pl.col("_rolling_mean")) / pl.col("_rolling_std"))
            .otherwise(0)
            .alias("z_score")
        )
    else:
        # Static analysis without temporal context
        overall_mean = df.select(pl.col(value_column).mean()).item()
        overall_std = df.select(pl.col(value_column).std()).item()
        
        if overall_std and overall_std > 0:
            df = df.with_columns(
                ((pl.col(value_column) - overall_mean) / overall_std).alias("z_score")
            )
        else:
            df = df.with_columns(pl.lit(0.0).alias("z_score"))
    
    # Flag anomalies
    df = df.with_columns(
        (pl.col("z_score").abs() > z_threshold).alias("is_anomaly")
    )
    
    # Classify anomaly type
    df = df.with_columns(
        pl.when(pl.col("z_score") > z_threshold)
        .then(pl.lit("SPIKE"))
        .when(pl.col("z_score") < -z_threshold)
        .then(pl.lit("DROP"))
        .otherwise(pl.lit("NORMAL"))
        .alias("anomaly_type")
    )
    
    # Add severity based on Z-score magnitude
    df = df.with_columns(
        pl.when(pl.col("z_score").abs() > 4)
        .then(pl.lit("CRITICAL"))
        .when(pl.col("z_score").abs() > 3)
        .then(pl.lit("HIGH"))
        .when(pl.col("z_score").abs() > z_threshold)
        .then(pl.lit("MEDIUM"))
        .otherwise(pl.lit("NORMAL"))
        .alias("severity")
    )
    
    return df


def detect_mvi_anomalies(
    mvi_df: pl.DataFrame,
    z_threshold: float = None
) -> pl.DataFrame:
    """
    Detect anomalies in MVI values.
    
    Args:
        mvi_df: DataFrame with MVI values
        z_threshold: Z-score threshold
        
    Returns:
        DataFrame with anomaly detection results
    """
    geo_columns = ["state", "district"]
    
    return detect_anomalies_in_series(
        df=mvi_df,
        value_column="mvi",
        geo_columns=geo_columns,
        z_threshold=z_threshold
    )


# =============================================================================
# STRUCTURAL VS SEASONAL ANALYSIS
# =============================================================================

def classify_anomaly_pattern(
    df: pl.DataFrame,
    min_consecutive_days: int = 7
) -> pl.DataFrame:
    """
    Classify anomalies as structural or transient.
    
    Structural anomalies: Sustained deviation over time
    Transient anomalies: Temporary spikes/drops
    
    Args:
        df: DataFrame with anomaly flags
        min_consecutive_days: Days required for structural classification
        
    Returns:
        DataFrame with pattern classification
    """
    if "is_anomaly" not in df.columns:
        return df
    
    if "date" not in df.columns:
        # Cannot determine pattern without dates
        df = df.with_columns(pl.lit("UNKNOWN").alias("pattern_type"))
        return df
    
    geo_columns = ["state", "district"]
    existing_geo = [c for c in geo_columns if c in df.columns]
    
    if not existing_geo:
        df = df.with_columns(pl.lit("UNKNOWN").alias("pattern_type"))
        return df
    
    # Count consecutive anomaly days per geography
    df = df.sort(existing_geo + ["date"])
    
    # For simplicity, we'll mark areas with high anomaly frequency as structural
    anomaly_pct = df.group_by(existing_geo).agg(
        (pl.col("is_anomaly").sum() / pl.count() * 100).alias("anomaly_pct")
    )
    
    # Join back
    df = df.join(anomaly_pct, on=existing_geo, how="left")
    
    # Classify
    df = df.with_columns(
        pl.when((pl.col("is_anomaly")) & (pl.col("anomaly_pct") > 30))
        .then(pl.lit("STRUCTURAL"))
        .when(pl.col("is_anomaly"))
        .then(pl.lit("TRANSIENT"))
        .otherwise(pl.lit("NORMAL"))
        .alias("pattern_type")
    )
    
    return df


# =============================================================================
# ALERT GENERATION
# =============================================================================

def generate_alerts(
    df: pl.DataFrame,
    min_severity: str = "MEDIUM"
) -> List[Alert]:
    """
    Generate actionable alerts from anomaly data.
    
    Args:
        df: DataFrame with anomaly detection results
        min_severity: Minimum severity to include
        
    Returns:
        List of Alert objects
    """
    if "is_anomaly" not in df.columns:
        return []
    
    severity_order = {"NORMAL": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    min_level = severity_order.get(min_severity, 1)
    
    # Filter to anomalies meeting severity threshold
    anomalies = df.filter(
        pl.col("is_anomaly") & 
        (pl.col("severity").map_elements(
            lambda x: severity_order.get(x, 0), return_dtype=pl.Int64
        ) >= min_level)
    )
    
    if len(anomalies) == 0:
        return []
    
    alerts = []
    
    # Group by severity for summary alerts
    for severity in ["CRITICAL", "HIGH", "MEDIUM"]:
        severity_anomalies = anomalies.filter(pl.col("severity") == severity)
        
        if len(severity_anomalies) == 0:
            continue
        
        # Get affected regions
        affected_regions = []
        if "state" in severity_anomalies.columns:
            if "district" in severity_anomalies.columns:
                affected_regions = [
                    f"{r['district']}, {r['state']}"
                    for r in severity_anomalies.select(["state", "district"]).unique().to_dicts()
                ][:10]  # Limit to 10
            else:
                affected_regions = severity_anomalies.select("state").unique().to_series().to_list()[:10]
        
        # Create summary alert
        alert = Alert(
            alert_id=f"ALERT-{severity}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            severity=severity,
            title=f"{severity} Migration Anomalies Detected",
            summary=f"{len(severity_anomalies)} geographic units showing {severity.lower()} anomalies",
            affected_regions=affected_regions,
            metrics={
                "count": len(severity_anomalies),
                "max_z_score": float(severity_anomalies.select(pl.col("z_score").max()).item()),
            }
        )
        alerts.append(alert)
    
    return alerts


def format_alert_message(alert: Alert) -> str:
    """
    Format an alert as a readable message.
    
    Args:
        alert: Alert object
        
    Returns:
        Formatted string message
    """
    regions_text = ", ".join(alert.affected_regions[:5])
    if len(alert.affected_regions) > 5:
        regions_text += f" (+{len(alert.affected_regions) - 5} more)"
    
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 ALERT: {alert.title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Severity: {alert.severity}
Timestamp: {alert.timestamp}

{alert.summary}

Affected Regions: {regions_text}

Metrics:
  - Anomalous Units: {alert.metrics.get('count', 'N/A')}
  - Max Z-Score: {alert.metrics.get('max_z_score', 0):.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# =============================================================================
# REPORTING
# =============================================================================

def generate_anomaly_report(df: pl.DataFrame) -> Dict:
    """
    Generate comprehensive anomaly detection report.
    
    Args:
        df: DataFrame with anomaly detection results
        
    Returns:
        Dictionary with report data
    """
    if "is_anomaly" not in df.columns:
        return {"error": "No anomaly detection performed"}
    
    total = len(df)
    anomaly_count = df.filter(pl.col("is_anomaly")).height
    
    # Breakdown by type
    type_breakdown = {}
    if "anomaly_type" in df.columns:
        counts = df.group_by("anomaly_type").agg(pl.count().alias("count")).to_dicts()
        type_breakdown = {d["anomaly_type"]: d["count"] for d in counts}
    
    # Breakdown by severity
    severity_breakdown = {}
    if "severity" in df.columns:
        counts = df.group_by("severity").agg(pl.count().alias("count")).to_dicts()
        severity_breakdown = {d["severity"]: d["count"] for d in counts}
    
    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_units": total,
            "anomaly_count": anomaly_count,
            "anomaly_rate": round(anomaly_count / total * 100, 2) if total > 0 else 0,
        },
        "by_type": type_breakdown,
        "by_severity": severity_breakdown,
        "interpretation": {
            "risk_level": (
                "HIGH" if severity_breakdown.get("CRITICAL", 0) > 0
                else "MEDIUM" if severity_breakdown.get("HIGH", 0) > 0
                else "LOW"
            ),
            "recommendation": (
                "Immediate attention required" if severity_breakdown.get("CRITICAL", 0) > 0
                else "Monitor closely" if severity_breakdown.get("HIGH", 0) > 0
                else "Normal monitoring"
            ),
        }
    }


def print_anomaly_report(report: Dict) -> None:
    """
    Print formatted anomaly report.
    
    Args:
        report: Anomaly report dictionary
    """
    print("\n" + "=" * 60)
    print("ANOMALY DETECTION REPORT")
    print("=" * 60)
    
    if "error" in report:
        print(f"\nError: {report['error']}")
        return
    
    summary = report["summary"]
    print(f"\nTotal Geographic Units: {summary['total_units']}")
    print(f"Anomalies Detected: {summary['anomaly_count']} ({summary['anomaly_rate']:.1f}%)")
    
    print(f"\nBy Type:")
    for atype, count in report["by_type"].items():
        print(f"  {atype}: {count}")
    
    print(f"\nBy Severity:")
    for severity, count in report["by_severity"].items():
        print(f"  {severity}: {count}")
    
    interp = report["interpretation"]
    print(f"\nRisk Level: {interp['risk_level']}")
    print(f"Recommendation: {interp['recommendation']}")
    
    print("=" * 60)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    from src.engines.ingestion import load_processed_dataset
    from src.engines.signal_separation import apply_signal_weights
    from src.engines.mvi import calculate_mvi, calculate_population_base
    
    print("=" * 60)
    print("AADHAAR SANKET - ANOMALY DETECTION ENGINE")
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
        
        # Detect anomalies
        print("\nDetecting anomalies...")
        anomaly_df = detect_mvi_anomalies(mvi_df)
        
        # Classify patterns
        anomaly_df = classify_anomaly_pattern(anomaly_df)
        
        # Generate report
        report = generate_anomaly_report(anomaly_df)
        print_anomaly_report(report)
        
        # Generate alerts
        print("\nGenerating alerts...")
        alerts = generate_alerts(anomaly_df, min_severity="MEDIUM")
        
        if alerts:
            print(f"\n{len(alerts)} alerts generated:")
            for alert in alerts:
                print(format_alert_message(alert))
        else:
            print("\nNo alerts to report.")
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] Dataset not found: {e}")
        print("Run ingestion pipeline first.")
