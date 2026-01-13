
from src.engines.ingestion import load_processed_dataset
import polars as pl
import pandas as pd

class DataGateway:
    """
    Read-Only Gateway to processed analytics data for AI consumption.
    Prevents AI from accessing raw data or modifying files.
    """
    
    @staticmethod
    def get_national_summary():
        """Get high-level national stats."""
        try:
            df = load_processed_dataset("trend_typology")
            
            # Create summary dict
            summary = {
                "total_districts": len(df),
                "high_pressure_districts": len(df.filter(pl.col("zone_type") == "high_inflow")),
                "districts_with_alerts": len(df.filter(pl.col("confidence") == "Low")), # Proxy
                "average_mvi": df["mean_mvi"].mean() if "mean_mvi" in df.columns else 0
            }
            return summary
        except Exception:
            return {}

    @staticmethod
    def get_state_summary(state_name: str):
        """Get summary for a specific state."""
        try:
            df = load_processed_dataset("trend_typology")
            
            # Handle geo_key parsing if state col missing
            if "state" not in df.columns and "geo_key" in df.columns:
                 # Attempt simple split, assuming District_State format or similar
                 # This is a heuristic if ingestion didn't fully normalize
                 pass 

            if "state" in df.columns:
                state_df = df.filter(pl.col("state") == state_name)
                return state_df.to_dicts()
            return []
        except:
            return []
            
    @staticmethod
    def get_top_moving_districts(n=10):
        """Get top N districts by MVI."""
        try:
            df = load_processed_dataset("trend_typology")
            # Ensure sorting column exists
            sort_col = "mean_mvi" if "mean_mvi" in df.columns else "mvi"
            
            if sort_col in df.columns:
                return df.sort(sort_col, descending=True).head(n).to_dicts()
            return []
        except:
            return []

    @staticmethod
    def get_anomalies():
        """Get recent anomalies."""
        try:
            df = load_processed_dataset("anomalies")
            if "is_anomaly" in df.columns:
                 return df.filter(pl.col("is_anomaly") == True).head(20).to_dicts()
            return []
        except:
            return []

    @staticmethod
    def query_dataframe(query_type: str, filters: dict = None):
        """
        Generic query handler.
        Supported types: 'trend', 'anomaly', 'demographic'
        """
        try:
            target_map = {
                "trend": "trend_typology",
                "anomaly": "anomalies",
                "demographic": "demographic"
            }
            
            dataset = target_map.get(query_type)
            if not dataset:
                return None
                
            df = load_processed_dataset(dataset)
            
            # Apply basic filters if needed (simplified for now)
            # AI will mostly do in-context filtering or request specific slices
            
            return df.head(100).to_dicts() # Return sample
        except:
            return []
