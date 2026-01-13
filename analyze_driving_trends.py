import duckdb
import polars as pl
import os

# Configuration
DATA_DIR = r"c:\Users\Nishchal Soni\Downloads\uidai\code\processed\parquet"
TREND_FILE = os.path.join(DATA_DIR, "trend_typology.parquet")
BIO_FILE = os.path.join(DATA_DIR, "biometric.parquet")
DEMO_FILE = os.path.join(DATA_DIR, "demographic.parquet")

def load_data():
    """Load necessary parquet files."""
    print("Loading data...")
    try:
        trends = pl.from_arrow(duckdb.read_parquet(TREND_FILE).arrow())
        # We only need counts from interaction files, so we can aggregate early if possible, 
        # but for simplicity and flexibility with duckdb integration, let's just load them.
        # Actually, let's use DuckDB directly for efficient aggregation of large files.
        pass 
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def analyze():
    print("Initializing DuckDB connection...")
    con = duckdb.connect()

    print("Aggregating Interaction Counts...")
    # Aggregate Biometric interactions by District
    bio_query = f"""
    SELECT state, district, count(*) as bio_count
    FROM read_parquet('{BIO_FILE}')
    GROUP BY state, district
    """
    bio_counts = con.sql(bio_query).pl()
    
    # Aggregate Demographic interactions by District
    demo_query = f"""
    SELECT state, district, count(*) as demo_count
    FROM read_parquet('{DEMO_FILE}')
    GROUP BY state, district
    """
    demo_counts = con.sql(demo_query).pl()

    # Load Trends
    print("Loading Trends...")
    trends = con.sql(f"SELECT * FROM read_parquet('{TREND_FILE}')").pl()

    # Join Data
    print("Joining Datasets...")
    # Outer join to capture all districts
    interactions = bio_counts.join(
        demo_counts, on=["state", "district"], how="outer"
    ).fill_null(0)
    
    interactions = interactions.with_columns(
        (pl.col("bio_count") + pl.col("demo_count")).alias("total_interactions")
    )

    # Convert geo_key in trends (which seems to be district name) to match join keys if necessary
    # Based on previous inspection, trend_typology has 'geo_key'. 
    # Let's assume geo_key maps to 'district'. 
    # Note: 'geo_key' in trend_typology.parquet might be just the district name based on previous valid inspection 'Adilabad'.
    
    # Join Interactions with Trends
    # We join on 'district' = 'geo_key'
    # NOTE: There might be state-level trends too, but let's focus on district level as that's usually where the specific 'geo_key' comes from in the previous file dump.
    
    final_df = interactions.join(
        trends, left_on="district", right_on="geo_key", how="inner"
    )

    # Aggregate by Trend Type
    print("Calculating aggregates...")
    trend_summary = final_df.group_by("trend_type").agg([
        pl.sum("total_interactions").alias("total_volume"),
        pl.count("district").alias("district_count"),
        pl.max("total_interactions").alias("max_district_volume")
    ]).sort("total_volume", descending=True)
    
    # Calculate percentage
    total_vol = trend_summary["total_volume"].sum()
    trend_summary = trend_summary.with_columns(
        (pl.col("total_volume") / total_vol * 100).round(1).alias("percentage")
    )

    with open("analysis_results.txt", "w", encoding="utf-8") as f:
        f.write("WHICH TRENDS ARE DRIVING INTERACTIONS?\n")
        f.write("="*60 + "\n")
        f.write(str(trend_summary) + "\n\n")
        
        if len(trend_summary) > 0:
            top_trend = trend_summary[0, "trend_type"]
            f.write(f"Top Districts for '{top_trend}':\n")
            
            top_districts = final_df.filter(
                pl.col("trend_type") == top_trend
            ).sort("total_interactions", descending=True).head(5)
            
            f.write(str(top_districts.select([
                "state", "district", "total_interactions", "explanation"
            ])))
            
    print("Analysis saved to analysis_results.txt")


if __name__ == "__main__":
    analyze()
