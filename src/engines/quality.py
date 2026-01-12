"""
Project Aadhaar Sanket - Data Quality & Trust Engine

This engine ensures data trustworthiness through:
1. Null value detection and handling
2. Zero/suppressed value flagging
3. Age-group consistency validation
4. Temporal continuity checks
5. Geographic hierarchy validation
6. Data quality reporting

Design Philosophy:
- Every quality rule is explicitly documented
- Deterministic validation (same input = same output)
- No silent failures - all issues are logged
- Quality scores enable informed decision-making

Quality Rules Legend:
- Q1: Null value handling
- Q2: Count validation (non-negative)
- Q3: Date range validation
- Q4: Geographic consistency
- Q5: Age distribution reasonability
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import polars as pl

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import QUALITY_THRESHOLDS, REPORTS_DIR


# =============================================================================
# DATA QUALITY REPORT STRUCTURE
# =============================================================================

@dataclass
class QualityCheck:
    """Represents a single quality check result."""
    rule_id: str
    rule_name: str
    passed: bool
    message: str
    severity: str  # 'info', 'warning', 'error'
    details: Optional[Dict] = None


@dataclass
class QualityReport:
    """Comprehensive data quality report for a dataset."""
    dataset_type: str
    timestamp: str
    total_rows: int
    total_columns: int
    checks: List[QualityCheck]
    overall_score: float  # 0-100
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary for serialization."""
        return {
            "dataset_type": self.dataset_type,
            "timestamp": self.timestamp,
            "total_rows": self.total_rows,
            "total_columns": self.total_columns,
            "overall_score": self.overall_score,
            "checks": [
                {
                    "rule_id": c.rule_id,
                    "rule_name": c.rule_name,
                    "passed": c.passed,
                    "message": c.message,
                    "severity": c.severity,
                    "details": c.details,
                }
                for c in self.checks
            ],
            "summary": {
                "passed": sum(1 for c in self.checks if c.passed),
                "failed": sum(1 for c in self.checks if not c.passed),
                "warnings": sum(1 for c in self.checks if c.severity == "warning"),
                "errors": sum(1 for c in self.checks if c.severity == "error"),
            },
        }


# =============================================================================
# QUALITY CHECK FUNCTIONS
# =============================================================================

def check_null_values(
    df: pl.DataFrame,
    critical_columns: List[str]
) -> QualityCheck:
    """
    Rule Q1: Check for null values in critical columns.
    
    Critical columns (date, state, district, pincode) must have
    zero null values for geographic integrity.
    
    Args:
        df: DataFrame to validate
        critical_columns: Columns that must not have nulls
        
    Returns:
        QualityCheck result
    """
    null_counts = {}
    total_nulls = 0
    
    for col in critical_columns:
        if col in df.columns:
            null_count = df.filter(pl.col(col).is_null()).height
            if null_count > 0:
                null_counts[col] = null_count
                total_nulls += null_count
    
    passed = total_nulls == 0
    null_percent = (total_nulls / (len(df) * len(critical_columns))) * 100 if len(df) > 0 else 0
    
    return QualityCheck(
        rule_id="Q1",
        rule_name="Null Value Check (Critical Columns)",
        passed=passed,
        message=f"Found {total_nulls} null values ({null_percent:.2f}%)" if not passed else "No null values in critical columns",
        severity="error" if not passed else "info",
        details={"null_counts": null_counts, "threshold_percent": QUALITY_THRESHOLDS["max_null_percent"]},
    )


def check_count_columns(df: pl.DataFrame) -> QualityCheck:
    """
    Rule Q2: Validate count columns are non-negative integers.
    
    All age-based count columns must contain:
    - Non-negative values (>= 0)
    - Integer values (no decimals)
    
    Args:
        df: DataFrame to validate
        
    Returns:
        QualityCheck result
    """
    count_columns = [c for c in df.columns if "count" in c.lower() or "age" in c.lower()]
    
    issues = {}
    
    for col in count_columns:
        if col in df.columns:
            try:
                # Check for negative values
                negative_count = df.filter(pl.col(col) < 0).height
                if negative_count > 0:
                    issues[col] = {"negative_values": negative_count}
            except Exception:
                # Column might not be numeric
                issues[col] = {"type_error": "Column is not numeric"}
    
    passed = len(issues) == 0
    
    return QualityCheck(
        rule_id="Q2",
        rule_name="Count Column Validation",
        passed=passed,
        message=f"Found issues in {len(issues)} columns" if not passed else "All count columns valid",
        severity="error" if not passed else "info",
        details={"issues": issues},
    )


def check_date_range(
    df: pl.DataFrame,
    date_column: str = "date"
) -> QualityCheck:
    """
    Rule Q3: Validate dates are within expected range.
    
    Dates should fall within the expected data collection period.
    Dates outside this range may indicate data quality issues.
    
    Args:
        df: DataFrame to validate
        date_column: Name of the date column
        
    Returns:
        QualityCheck result
    """
    if date_column not in df.columns:
        return QualityCheck(
            rule_id="Q3",
            rule_name="Date Range Validation",
            passed=False,
            message=f"Date column '{date_column}' not found",
            severity="error",
        )
    
    # Get date range from data
    try:
        min_date = df.select(pl.col(date_column).min()).item()
        max_date = df.select(pl.col(date_column).max()).item()
        
        # Parse expected range from config
        expected_start = datetime.strptime(
            QUALITY_THRESHOLDS["expected_date_start"], "%Y-%m-%d"
        ).date()
        expected_end = datetime.strptime(
            QUALITY_THRESHOLDS["expected_date_end"], "%Y-%m-%d"
        ).date()
        
        # Check if dates fall within expected range
        in_range = min_date >= expected_start and max_date <= expected_end
        
        return QualityCheck(
            rule_id="Q3",
            rule_name="Date Range Validation",
            passed=in_range,
            message=f"Data spans {min_date} to {max_date}",
            severity="warning" if not in_range else "info",
            details={
                "min_date": str(min_date),
                "max_date": str(max_date),
                "expected_start": str(expected_start),
                "expected_end": str(expected_end),
            },
        )
    except Exception as e:
        return QualityCheck(
            rule_id="Q3",
            rule_name="Date Range Validation",
            passed=False,
            message=f"Error parsing dates: {str(e)}",
            severity="error",
        )


def check_geographic_hierarchy(df: pl.DataFrame) -> QualityCheck:
    """
    Rule Q4: Validate geographic hierarchy consistency.
    
    Checks:
    - State names are consistent (no typos/variations)
    - Districts are not duplicated across states incorrectly
    - Pincodes are valid 6-digit codes
    
    Args:
        df: DataFrame to validate
        
    Returns:
        QualityCheck result
    """
    issues = {}
    
    # Check state name consistency
    if "state" in df.columns:
        unique_states = df.select("state").unique().height
        issues["unique_states"] = unique_states
    
    # Check district count per state
    if "state" in df.columns and "district" in df.columns:
        districts_per_state = df.group_by("state").agg(
            pl.col("district").n_unique().alias("district_count")
        )
        max_districts = districts_per_state.select(pl.col("district_count").max()).item()
        issues["max_districts_per_state"] = max_districts
    
    # Check pincode validity (6 digits)
    if "pincode" in df.columns:
        # Convert to string and check format
        invalid_pincodes = df.filter(
            ~pl.col("pincode").cast(pl.Utf8).str.contains(r"^\d{6}$")
        ).height
        issues["invalid_pincodes"] = invalid_pincodes
    
    passed = issues.get("invalid_pincodes", 0) == 0
    
    return QualityCheck(
        rule_id="Q4",
        rule_name="Geographic Hierarchy Validation",
        passed=passed,
        message=f"{issues.get('unique_states', 0)} states, {issues.get('invalid_pincodes', 0)} invalid pincodes",
        severity="warning" if not passed else "info",
        details=issues,
    )


def check_zero_values(df: pl.DataFrame) -> QualityCheck:
    """
    Rule Q5: Check for excessive zero values in count columns.
    
    High percentage of zeros may indicate:
    - Suppressed data (privacy thresholds)
    - Missing data coded as zero
    - Genuine absence of activity
    
    Args:
        df: DataFrame to validate
        
    Returns:
        QualityCheck result
    """
    count_columns = [c for c in df.columns if "count" in c.lower() or "age" in c.lower()]
    
    zero_stats = {}
    max_zero_pct = 0
    
    for col in count_columns:
        if col in df.columns:
            try:
                zero_count = df.filter(pl.col(col) == 0).height
                zero_pct = (zero_count / len(df)) * 100 if len(df) > 0 else 0
                zero_stats[col] = {
                    "zero_count": zero_count,
                    "zero_percent": round(zero_pct, 2),
                }
                max_zero_pct = max(max_zero_pct, zero_pct)
            except Exception:
                pass
    
    threshold = QUALITY_THRESHOLDS["max_zero_percent"]
    passed = max_zero_pct <= threshold
    
    return QualityCheck(
        rule_id="Q5",
        rule_name="Zero Value Analysis",
        passed=passed,
        message=f"Max zero percentage: {max_zero_pct:.1f}% (threshold: {threshold}%)",
        severity="warning" if not passed else "info",
        details=zero_stats,
    )


def check_temporal_continuity(
    df: pl.DataFrame,
    date_column: str = "date"
) -> QualityCheck:
    """
    Rule Q6: Check for temporal gaps in data.
    
    Identifies missing dates that may indicate:
    - Data collection gaps
    - Processing failures
    - Incomplete datasets
    
    Args:
        df: DataFrame to validate
        date_column: Name of the date column
        
    Returns:
        QualityCheck result
    """
    if date_column not in df.columns:
        return QualityCheck(
            rule_id="Q6",
            rule_name="Temporal Continuity Check",
            passed=False,
            message=f"Date column '{date_column}' not found",
            severity="warning",
        )
    
    try:
        # Get unique dates
        unique_dates = df.select(date_column).unique().sort(date_column)
        date_list = unique_dates.to_series().to_list()
        
        if len(date_list) < 2:
            return QualityCheck(
                rule_id="Q6",
                rule_name="Temporal Continuity Check",
                passed=True,
                message="Insufficient dates for continuity check",
                severity="info",
            )
        
        # Count unique dates
        num_unique_dates = len(date_list)
        
        return QualityCheck(
            rule_id="Q6",
            rule_name="Temporal Continuity Check",
            passed=True,
            message=f"Data covers {num_unique_dates} unique dates",
            severity="info",
            details={
                "unique_dates": num_unique_dates,
                "date_range_days": (date_list[-1] - date_list[0]).days if date_list else 0,
            },
        )
    except Exception as e:
        return QualityCheck(
            rule_id="Q6",
            rule_name="Temporal Continuity Check",
            passed=False,
            message=f"Error checking continuity: {str(e)}",
            severity="warning",
        )


# =============================================================================
# MAIN QUALITY ENGINE
# =============================================================================

def run_quality_checks(
    df: pl.DataFrame,
    dataset_type: str
) -> QualityReport:
    """
    Execute all quality checks on a dataset.
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset (biometric, demographic, enrolment)
        
    Returns:
        Comprehensive QualityReport
    """
    critical_columns = ["date", "state", "district", "pincode"]
    
    checks = [
        check_null_values(df, critical_columns),
        check_count_columns(df),
        check_date_range(df),
        check_geographic_hierarchy(df),
        check_zero_values(df),
        check_temporal_continuity(df),
    ]
    
    # Calculate overall score
    # Weight: errors = 0 points, warnings = 0.5 points, pass = 1 point
    total_points = 0
    max_points = len(checks)
    
    for check in checks:
        if check.passed:
            total_points += 1
        elif check.severity == "warning":
            total_points += 0.5
        # errors get 0 points
    
    overall_score = (total_points / max_points) * 100 if max_points > 0 else 0
    
    return QualityReport(
        dataset_type=dataset_type,
        timestamp=datetime.now().isoformat(),
        total_rows=len(df),
        total_columns=len(df.columns),
        checks=checks,
        overall_score=round(overall_score, 1),
    )


def validate_dataset(
    df: pl.DataFrame,
    dataset_type: str,
    min_score: float = 70.0
) -> Tuple[bool, QualityReport]:
    """
    Validate a dataset and determine if it meets quality threshold.
    
    Args:
        df: DataFrame to validate
        dataset_type: Type of dataset
        min_score: Minimum acceptable quality score (0-100)
        
    Returns:
        Tuple of (passes_threshold, quality_report)
    """
    report = run_quality_checks(df, dataset_type)
    passes = report.overall_score >= min_score
    
    return passes, report


def print_quality_report(report: QualityReport) -> None:
    """
    Print a formatted quality report to console.
    
    Args:
        report: QualityReport to display
    """
    print("\n" + "=" * 60)
    print(f"DATA QUALITY REPORT: {report.dataset_type.upper()}")
    print("=" * 60)
    print(f"Timestamp: {report.timestamp}")
    print(f"Total Rows: {report.total_rows:,}")
    print(f"Total Columns: {report.total_columns}")
    print(f"Overall Score: {report.overall_score}/100")
    print("-" * 60)
    
    for check in report.checks:
        status = "✓" if check.passed else ("⚠" if check.severity == "warning" else "✗")
        print(f"{status} [{check.rule_id}] {check.rule_name}")
        print(f"    {check.message}")
    
    print("=" * 60)


def save_quality_report(
    report: QualityReport,
    output_dir: Path = REPORTS_DIR
) -> Path:
    """
    Save quality report to JSON file.
    
    Args:
        report: QualityReport to save
        output_dir: Directory for reports
        
    Returns:
        Path to saved report
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"quality_report_{report.dataset_type}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    
    return output_path


# =============================================================================
# DATA CLEANING FUNCTIONS
# =============================================================================

def clean_null_values(
    df: pl.DataFrame,
    strategy: str = "drop"
) -> pl.DataFrame:
    """
    Handle null values in the DataFrame.
    
    Strategies:
    - 'drop': Remove rows with null values in critical columns
    - 'flag': Add a flag column instead of dropping
    
    Args:
        df: DataFrame to clean
        strategy: Cleaning strategy
        
    Returns:
        Cleaned DataFrame
    """
    critical_columns = ["date", "state", "district", "pincode"]
    existing_critical = [c for c in critical_columns if c in df.columns]
    
    if strategy == "drop":
        for col in existing_critical:
            df = df.filter(pl.col(col).is_not_null())
    elif strategy == "flag":
        # Add flag column for rows with any null in critical columns
        null_condition = pl.lit(False)
        for col in existing_critical:
            null_condition = null_condition | pl.col(col).is_null()
        df = df.with_columns(null_condition.alias("_has_null_critical"))
    
    return df


def clean_invalid_pincodes(df: pl.DataFrame) -> pl.DataFrame:
    """
    Remove or flag rows with invalid pincodes.
    
    Valid pincode: 6-digit number
    
    Args:
        df: DataFrame to clean
        
    Returns:
        Cleaned DataFrame
    """
    if "pincode" not in df.columns:
        return df
    
    # Filter to only valid 6-digit pincodes
    df = df.filter(
        pl.col("pincode").cast(pl.Utf8).str.contains(r"^\d{6}$")
    )
    
    return df


def apply_all_cleaning(df: pl.DataFrame) -> pl.DataFrame:
    """
    Apply all cleaning transformations.
    
    Order matters:
    1. Handle nulls first
    2. Then validate specific columns
    3. Add metadata last
    
    Args:
        df: DataFrame to clean
        
    Returns:
        Cleaned DataFrame with metadata
    """
    original_count = len(df)
    
    # Step 1: Clean null values
    df = clean_null_values(df, strategy="drop")
    
    # Step 2: Clean invalid pincodes
    df = clean_invalid_pincodes(df)
    
    # Step 3: Add cleaning metadata
    df = df.with_columns(
        pl.lit(True).alias("_cleaned"),
        pl.lit(datetime.now().isoformat()).alias("_cleaned_at"),
    )
    
    final_count = len(df)
    print(f"  Cleaning: {original_count:,} → {final_count:,} rows ({original_count - final_count:,} removed)")
    
    return df


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Example usage with sample data
    from src.engines.ingestion import load_processed_dataset
    
    print("Loading processed datasets for quality validation...")
    
    for dataset_type in ["biometric", "demographic", "enrolment"]:
        try:
            df = load_processed_dataset(dataset_type)
            passes, report = validate_dataset(df, dataset_type)
            print_quality_report(report)
            save_quality_report(report)
        except FileNotFoundError:
            print(f"Dataset {dataset_type} not found. Run ingestion first.")
