"""
Drill-Down Service - Data Query Engine for Evidence Pages

This module provides data queries to support drill-down navigation
and evidence display throughout the dashboard.

Features:
- Query districts by any metric filter
- Get source data for specific districts
- Explain calculations in plain English
- Retrieve contributing records for any aggregation
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import polars as pl


class DrillDownService:
    """
    Service for querying processed data to support drill-down navigation.
    
    Usage:
        service = DrillDownService()
        districts = service.get_districts_for_metric("high_mvi", {"mvi_min": 30})
        explanation = service.explain_calculation("Mumbai", "mvi")
    """
    
    def __init__(self, processed_dir: Path = None):
        """
        Initialize drill-down service.
        
        Args:
            processed_dir: Directory containing processed parquet files
        """
        self.processed_dir = processed_dir or Path("processed/parquet")
        self._cache = {}
    
    def _load_mvi_data(self) -> pl.DataFrame:
        """Load MVI data with caching."""
        if "mvi" not in self._cache:
            # In production, this would load from saved MVI parquet
            # For now, we'll compute it on the fly
            try:
                from src.engines.ingestion import load_processed_dataset
                from src.engines.signal_separation import apply_signal_weights
                from src.engines.mvi import calculate_mvi, calculate_population_base
                from src.engines.spatial import add_zone_classification
                
                demographic_df = load_processed_dataset("demographic")
                enrolment_df = load_processed_dataset("enrolment")
                
                demographic_df = apply_signal_weights(demographic_df, "demographic")
                population_df = calculate_population_base(enrolment_df, "district")
                mvi_df = calculate_mvi(demographic_df, population_df, "district")
                mvi_df = add_zone_classification(mvi_df)
                
                self._cache["mvi"] = mvi_df
            except Exception as e:
                print(f"Error loading MVI data: {e}")
                return pl.DataFrame()
        
        return self._cache["mvi"]
    
    def get_districts_for_metric(
        self,
        metric_name: str,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> pl.DataFrame:
        """
        Get all districts matching a metric criteria.
        
        Args:
            metric_name: Name of the metric (e.g., "high_mvi", "total_districts")
            filter_criteria: Optional filters (e.g., {"mvi_min": 30, "state": "Maharashtra"})
        
        Returns:
            DataFrame with matching districts
        """
        mvi_df = self._load_mvi_data()
        
        if mvi_df.is_empty():
            return pl.DataFrame()
        
        # Apply filters based on metric name
        if metric_name == "high_mvi":
            filtered = mvi_df.filter(pl.col("mvi") >= 30)
        elif metric_name == "elevated_mvi":
            filtered = mvi_df.filter((pl.col("mvi") >= 15) & (pl.col("mvi") < 30))
        elif metric_name == "total_districts":
            filtered = mvi_df
        elif metric_name == "attention_needed":
            filtered = mvi_df.filter(pl.col("mvi") >= 15)
        else:
            filtered = mvi_df
        
        # Apply additional filter criteria
        if filter_criteria:
            if "mvi_min" in filter_criteria:
                filtered = filtered.filter(pl.col("mvi") >= filter_criteria["mvi_min"])
            if "mvi_max" in filter_criteria:
                filtered = filtered.filter(pl.col("mvi") <= filter_criteria["mvi_max"])
            if "state" in filter_criteria:
                filtered = filtered.filter(pl.col("state") == filter_criteria["state"])
            if "zone_type" in filter_criteria:
                filtered = filtered.filter(pl.col("zone_type") == filter_criteria["zone_type"])
        
        return filtered
    
    def get_district_detail(self, district_name: str, state_name: Optional[str] = None) -> Dict:
        """
        Get detailed information about a specific district.
        
        Args:
            district_name: Name of the district
            state_name: Optional state name for disambiguation
        
        Returns:
            Dictionary with district details
        """
        mvi_df = self._load_mvi_data()
        
        if mvi_df.is_empty():
            return {}
        
        # Filter for district
        if state_name:
            district_data = mvi_df.filter(
                (pl.col("district") == district_name) & (pl.col("state") == state_name)
            )
        else:
            district_data = mvi_df.filter(pl.col("district") == district_name)
        
        if len(district_data) == 0:
            return {}
        
        # Get first row as dict
        row = district_data.to_dicts()[0]
        
        # Add calculation breakdown
        row["calculation_breakdown"] = self._generate_calculation_breakdown(row)
        
        return row
    
    def _generate_calculation_breakdown(self, district_row: Dict) -> Dict:
        """Generate step-by-step calculation breakdown for a district."""
        return {
            "step_1": {
                "description": "Count demographic updates in time window",
                "value": district_row.get("signal_adjusted_sum", "N/A"),
                "unit": "updates"
            },
            "step_2": {
                "description": "Get district population from enrolment data",
                "value": district_row.get("population", "N/A"),
                "unit": "people"
            },
            "step_3": {
                "description": "Calculate ratio and multiply by 100",
                "formula": "(updates / population) × 100",
                "value": district_row.get("mvi", "N/A"),
                "unit": "MVI"
            },
            "step_4": {
                "description": "Classify into MVI band",
                "value": district_row.get("mvi_band", "N/A"),
                "logic": "MVI >= 30: High Pressure, 15-30: Elevated, 5-15: Moderate, <5: Stable"
            }
        }
    
    def explain_calculation(self, district_name: str, metric: str = "mvi") -> str:
        """
        Generate plain-English explanation of how a metric was calculated.
        
        Args:
            district_name: Name of the district
            metric: Metric to explain (default: "mvi")
        
        Returns:
            Plain English explanation
        """
        district_data = self.get_district_detail(district_name)
        
        if not district_data:
            return f"Could not find data for district: {district_name}"
        
        if metric == "mvi":
            explanation = f"""
How MVI was calculated for {district_name}, {district_data.get('state')}:

Step 1: Count demographic updates
We counted all address change requests from Aadhaar Demographic Update dataset
during the analysis period. This district had {district_data.get('signal_adjusted_sum', 'N/A')} 
genuine migration-related updates (after filtering administrative noise).

Step 2: Get population baseline
We used the Aadhaar Enrolment dataset to determine the district's population.
Population: {district_data.get('population', 'N/A'):,} residents.

Step 3: Calculate velocity
MVI = (Updates / Population) × 100
MVI = ({district_data.get('signal_adjusted_sum', 'N/A')} / {district_data.get('population', 'N/A')}) × 100
MVI = {district_data.get('mvi', 'N/A'):.2f}

Step 4: Classify
With MVI of {district_data.get('mvi', 'N/A'):.2f}, this district is classified as:
**{district_data.get('mvi_band', 'N/A')}**

Data sources used:
✓ Demographic Updates: api_data_aadhar_demographic (2.07M rows)
✓ Enrolment Data: api_data_aadhar_enrolment (1.01M rows)
✓ Time Window: Full dataset period
✓ Signal Separation: Applied (noise filtered)

Confidence: {district_data.get('confidence', 'N/A')}
"""
            return explanation.strip()
        
        return f"Explanation for metric '{metric}' not yet implemented."
    
    def get_source_datasets(self, district_name: str) -> List[Dict]:
        """
        Get information about source datasets that contributed to a district's metrics.
        
        Args:
            district_name: Name of the district
        
        Returns:
            List of dataset information dictionaries
        """
        return [
            {
                "dataset_name": "Aadhaar Demographic Updates",
                "file_count": 5,
                "total_rows": 2071700,
                "relevance": "Primary source for migration signals",
                "contribution": "Address change requests indicate migration"
            },
            {
                "dataset_name": "Aadhaar Enrolment Data",
                "file_count": 3,
                "total_rows": 1006029,
                "relevance": "Population baseline",
                "contribution": "Provides denominator for MVI calculation"
            },
            {
                "dataset_name": "Aadhaar Biometric Updates",
                "file_count": 4,
                "total_rows": 1861108,
                "relevance": "Noise filtering",
                "contribution": "Helps separate administrative updates from genuine migration"
            }
        ]
    
    def get_contributing_records(
        self,
        district_name: str,
        state_name: Optional[str] = None,
        limit: int = 100
    ) -> pl.DataFrame:
        """
        Get sample of raw records that contributed to a district's metrics.
        
        Args:
            district_name: Name of the district
            state_name: Optional state name
            limit: Maximum number of records to return
        
        Returns:
            DataFrame with contributing records
        """
        try:
            from src.engines.ingestion import load_processed_dataset
            
            demographic_df = load_processed_dataset("demographic")
            
            # Filter for district
            if state_name:
                filtered = demographic_df.filter(
                    (pl.col("district") == district_name) & (pl.col("state") == state_name)
                )
            else:
                filtered = demographic_df.filter(pl.col("district") == district_name)
            
            return filtered.head(limit)
        
        except Exception as e:
            print(f"Error getting contributing records: {e}")
            return pl.DataFrame()
    
    def export_evidence_csv(self, data: pl.DataFrame, output_path: Path):
        """
        Export evidence data to CSV for external verification.
        
        Args:
            data: DataFrame to export
            output_path: Path to save CSV file
        """
        try:
            data.write_csv(output_path)
            print(f"✓ Evidence exported to {output_path}")
        except Exception as e:
            print(f"Error exporting CSV: {e}")


# Example usage
if __name__ == "__main__":
    service = DrillDownService()
    
    # Get high MVI districts
    print("High MVI Districts:")
    high_mvi = service.get_districts_for_metric("high_mvi")
    if not high_mvi.is_empty():
        print(high_mvi.select(["state", "district", "mvi"]).head(10))
    
    # Get explanation for a specific district
    if not high_mvi.is_empty():
        first_district = high_mvi.select("district").head(1).item()
        print(f"\n{service.explain_calculation(first_district)}")
