"""
Project Aadhaar Sanket - Data Ingestion & Lineage Engine

This engine handles:
1. Dynamic discovery of CSV files from the data directory
2. Schema inference and validation
3. Memory-efficient loading with DuckDB
4. Data lineage tracking (source file, timestamp, row counts)
5. Export to Parquet format for downstream processing

Design Principles:
- Pure functions with no hidden state
- Explicit error handling
- Deterministic outputs
- All transformations are documented
"""
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import duckdb
import polars as pl

# Import configuration
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.config import (
    DATA_DIR,
    BIOMETRIC_DIR,
    DEMOGRAPHIC_DIR,
    ENROLMENT_DIR,
    PARQUET_DIR,
    NORMALIZED_COLUMNS,
)


# =============================================================================
# DATASET DISCOVERY
# =============================================================================

def discover_datasets(data_path: Path = DATA_DIR) -> Dict[str, List[Path]]:
    """
    Dynamically discover all CSV files organized by dataset type.
    
    Args:
        data_path: Root directory containing dataset subdirectories
        
    Returns:
        Dictionary mapping dataset type to list of CSV file paths
        
    Raises:
        FileNotFoundError: If data directory does not exist
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")
    
    datasets: Dict[str, List[Path]] = {
        "biometric": [],
        "demographic": [],
        "enrolment": [],
    }
    
    # Map directory names to dataset types
    dir_to_type = {
        "api_data_aadhar_biometric": "biometric",
        "api_data_aadhar_demographic": "demographic",
        "api_data_aadhar_enrolment": "enrolment",
    }
    
    # Also check manual folders
    manual_dir = data_path / "manual"
    if manual_dir.exists():
        for subdir in manual_dir.iterdir():
            if subdir.is_dir() and subdir.name in ["biometric", "demographic", "enrolment"]:
                # If we find files in manual/enrolment, map them to enrolment
                current_files = datasets[subdir.name]
                new_files = sorted(subdir.glob("*.csv"))
                current_files.extend(new_files)

    for subdir in data_path.iterdir():
        if subdir.is_dir() and subdir.name in dir_to_type:
            dataset_type = dir_to_type[subdir.name]
            csv_files = sorted(subdir.glob("*.csv"))
            datasets[dataset_type].extend(csv_files)
    
    return datasets


def get_file_metadata(file_path: Path) -> Dict:
    """
    Extract metadata from a CSV file for lineage tracking.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary containing file metadata
    """
    stat = file_path.stat()
    
    # Calculate file hash for integrity verification
    with open(file_path, "rb") as f:
        # Read first 1MB for hash (performance optimization)
        file_hash = hashlib.md5(f.read(1024 * 1024)).hexdigest()
    
    return {
        "file_name": file_path.name,
        "file_path": str(file_path.absolute()),
        "size_bytes": stat.st_size,
        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "discovery_time": datetime.now().isoformat(),
        "file_hash_partial": file_hash,
    }


# =============================================================================
# DATA LOADING WITH DUCKDB
# =============================================================================

def ingest_csv_with_duckdb(
    file_path: Path,
    sample_size: Optional[int] = None
) -> pl.DataFrame:
    """
    Load a CSV file using DuckDB for memory-efficient SQL analytics.
    
    DuckDB provides:
    - Columnar execution for analytics
    - Automatic type inference
    - Efficient memory management
    
    Args:
        file_path: Path to the CSV file
        sample_size: Optional limit on rows to load (for testing)
        
    Returns:
        Polars DataFrame with loaded data
    """
    conn = duckdb.connect(":memory:")
    
    # Build query with optional limit
    limit_clause = f"LIMIT {sample_size}" if sample_size else ""
    query = f"""
        SELECT * 
        FROM read_csv_auto('{str(file_path)}', header=true)
        {limit_clause}
    """
    
    # Execute and convert to Polars
    result = conn.execute(query).fetchdf()
    conn.close()
    
    return pl.from_pandas(result)


def load_all_files_for_type(
    file_paths: List[Path],
    sample_size: Optional[int] = None
) -> pl.DataFrame:
    """
    Load and concatenate all CSV files for a dataset type.
    
    Args:
        file_paths: List of CSV file paths to load
        sample_size: Optional row limit per file
        
    Returns:
        Combined Polars DataFrame
    """
    if not file_paths:
        raise ValueError("No files provided for loading")
    
    dataframes = []
    for file_path in file_paths:
        df = ingest_csv_with_duckdb(file_path, sample_size)
        # Add source file column for lineage
        df = df.with_columns(
            pl.lit(file_path.name).alias("_source_file")
        )
        dataframes.append(df)
    
    return pl.concat(dataframes, how="vertical_relaxed")


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

def validate_required_columns(
    df: pl.DataFrame,
    dataset_type: str
) -> Tuple[bool, List[str]]:
    """
    Validate that all required columns exist in the DataFrame.
    
    This is a critical validation gate that prevents silent failures
    when CSV schemas don't match expected configuration.
    
    Args:
        df: Input DataFrame to validate
        dataset_type: One of 'biometric', 'demographic', 'enrolment'
        
    Returns:
        Tuple of (is_valid, missing_columns)
        
    Example:
        >>> is_valid, missing = validate_required_columns(df, "demographic")
        >>> if not is_valid:
        >>>     raise ValueError(f"Missing columns: {missing}")
    """
    if dataset_type not in NORMALIZED_COLUMNS:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    required_columns = set(NORMALIZED_COLUMNS[dataset_type].keys())
    actual_columns = set(df.columns)
    missing_columns = required_columns - actual_columns
    
    return (len(missing_columns) == 0, sorted(list(missing_columns)))


# =============================================================================
# COLUMN NORMALIZATION
# =============================================================================

def normalize_columns(
    df: pl.DataFrame,
    dataset_type: str
) -> pl.DataFrame:
    """
    Normalize column names to standardized schema.
    
    This ensures consistent column names across all datasets,
    enabling downstream engines to work uniformly.
    
    Args:
        df: Input DataFrame with original column names
        dataset_type: One of 'biometric', 'demographic', 'enrolment'
        
    Returns:
        DataFrame with normalized column names
    """
    if dataset_type not in NORMALIZED_COLUMNS:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    column_mapping = NORMALIZED_COLUMNS[dataset_type]
    
    # Build rename mapping for columns that exist
    rename_map = {}
    for original, normalized in column_mapping.items():
        if original in df.columns:
            rename_map[original] = normalized
    
    # Apply renaming
    df = df.rename(rename_map)
    
    # Add dataset type column
    df = df.with_columns(
        pl.lit(dataset_type).alias("dataset_type")
    )
    
    return df


def standardize_date_column(df: pl.DataFrame) -> pl.DataFrame:
    """
    Convert date column to standard format (YYYY-MM-DD) with robust parsing.
    
    Tries multiple date formats in order:
    1. DD-MM-YYYY (UIDAI standard)
    2. YYYY-MM-DD (ISO standard)
    3. DD/MM/YYYY (alternate format)
    
    Args:
        df: DataFrame with 'date' column
        
    Returns:
        DataFrame with standardized date column
        
    Raises:
        ValueError: If date column missing or all formats fail
    """
    if "date" not in df.columns:
        raise ValueError(
            "Required 'date' column missing from DataFrame. "
            "Cannot proceed with temporal analysis."
        )
    
    # Ensure date column is string type
    df = df.with_columns(
        pl.col("date").cast(pl.Utf8).alias("date")
    )
    
    # Try multiple date formats
    formats_to_try = [
        ("%d-%m-%Y", "DD-MM-YYYY (UIDAI standard)"),
        ("%Y-%m-%d", "YYYY-MM-DD (ISO standard)"),
        ("%d/%m/%Y", "DD/MM/YYYY (alternate)"),
        ("%Y-%m-%d %H:%M:%S", "YYYY-MM-DD HH:MM:SS (Timestamp)"),
        ("%Y-%m-%d %H:%M:%S.%f", "YYYY-MM-DD HH:MM:SS. micros (Timestamp)"),
    ]
    
    for fmt, description in formats_to_try:
        try:
            parsed_df = df.with_columns(
                pl.col("date").str.strptime(pl.Date, fmt, strict=True).alias("date")
            )
            # print(f"  ✓ Date parsing successful using format: {description}")
            return parsed_df
        except Exception:
            continue
    
    # If all formats fail, provide helpful error
    sample_dates = df.select("date").head(5).to_series().to_list()
    raise ValueError(
        f"Date parsing failed for all supported formats.\n"
        f"Sample date values: {sample_dates}\n"
        f"Supported formats: DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY"
    )


# =============================================================================
# DATA LINEAGE
# =============================================================================

def create_lineage_manifest(
    datasets: Dict[str, List[Path]]
) -> Dict:
    """
    Create a comprehensive data lineage manifest.
    
    The manifest documents:
    - All source files discovered
    - File metadata (size, hash, timestamps)
    - Processing timestamp
    - Dataset statistics
    
    Args:
        datasets: Dictionary of dataset types to file paths
        
    Returns:
        Lineage manifest dictionary
    """
    manifest = {
        "created_at": datetime.now().isoformat(),
        "data_root": str(DATA_DIR),
        "datasets": {},
        "summary": {
            "total_files": 0,
            "total_size_bytes": 0,
        },
    }
    
    for dataset_type, file_paths in datasets.items():
        dataset_info = {
            "file_count": len(file_paths),
            "files": [],
        }
        
        for file_path in file_paths:
            metadata = get_file_metadata(file_path)
            dataset_info["files"].append(metadata)
            manifest["summary"]["total_size_bytes"] += metadata["size_bytes"]
        
        manifest["datasets"][dataset_type] = dataset_info
        manifest["summary"]["total_files"] += len(file_paths)
    
    return manifest


def save_lineage_manifest(manifest: Dict, output_dir: Path) -> Path:
    """
    Save lineage manifest to JSON file.
    
    Args:
        manifest: Lineage manifest dictionary
        output_dir: Directory to save the manifest
        
    Returns:
        Path to saved manifest file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "data_lineage.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    return output_path


# =============================================================================
# PARQUET EXPORT
# =============================================================================

def export_to_parquet(
    df: pl.DataFrame,
    output_path: Path,
    compression: str = "snappy"
) -> Path:
    """
    Export DataFrame to Parquet format for analytics.
    
    Parquet provides:
    - Columnar storage (efficient for analytics)
    - Compression (reduced storage)
    - Schema preservation
    - Deterministic outputs
    
    Args:
        df: DataFrame to export
        output_path: Target path for Parquet file
        compression: Compression algorithm (default: snappy)
        
    Returns:
        Path to saved Parquet file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_path, compression=compression)
    return output_path


# =============================================================================
# MAIN INGESTION PIPELINE
# =============================================================================

def run_ingestion_pipeline(
    data_path: Path = DATA_DIR,
    output_path: Path = PARQUET_DIR,
    sample_size: Optional[int] = None
) -> Dict:
    """
    Execute the complete data ingestion pipeline.
    
    Steps:
    1. Discover all CSV files
    2. Create lineage manifest
    3. Load and normalize each dataset
    4. Export to Parquet
    5. Return processing summary
    
    Args:
        data_path: Root data directory
        output_path: Output directory for Parquet files
        sample_size: Optional row limit per file (for testing)
        
    Returns:
        Processing summary with statistics
    """
    print("=" * 60)
    print("AADHAAR SANKET - DATA INGESTION ENGINE")
    print("=" * 60)
    
    # Step 1: Discover datasets
    print("\n[1/5] Discovering datasets...")
    datasets = discover_datasets(data_path)
    
    # Dataset coverage report
    print("\n[DATASET COVERAGE REPORT]")
    total_files = 0
    for dtype in ["biometric", "demographic", "enrolment"]:
        file_count = len(datasets.get(dtype, []))
        total_files += file_count
        if file_count == 0:
            print(f"  ⚠️  {dtype}: NO FILES FOUND")
        else:
            print(f"  ✓  {dtype}: {file_count} files")
    
    # Fail if ALL datasets are empty
    if total_files == 0:
        raise FileNotFoundError(
            "No CSV files found in any dataset directory.\\n"
            f"Checked directories:\\n"
            f"  - {BIOMETRIC_DIR}\\n"
            f"  - {DEMOGRAPHIC_DIR}\\n"
            f"  - {ENROLMENT_DIR}\\n"
            "Please ensure CSV files are placed in the correct subdirectories."
        )
    
    # Step 2: Create lineage manifest
    print("\n[2/5] Creating data lineage manifest...")
    manifest = create_lineage_manifest(datasets)
    manifest_path = save_lineage_manifest(manifest, output_path.parent)
    print(f"  - Manifest saved to: {manifest_path}")
    
    # Step 3-4: Load, normalize, and export each dataset
    summary = {
        "processed_at": datetime.now().isoformat(),
        "datasets": {},
        "output_files": [],
    }
    
    for dataset_type, file_paths in datasets.items():
        if not file_paths:
            print(f"\n[SKIP] No files for {dataset_type}")
            continue
        
        print(f"\n[3/5] Processing {dataset_type}...")
        
        # Load all files
        df = load_all_files_for_type(file_paths, sample_size)
        print(f"  - Loaded {len(df):,} rows")
        
        # VALIDATION GATE: Check required columns exist
        print(f"  - Validating schema...")
        is_valid, missing_columns = validate_required_columns(df, dataset_type)
        if not is_valid:
            raise ValueError(
                f"Schema validation FAILED for {dataset_type}.\\n"
                f"Missing required columns: {missing_columns}\\n"
                f"Expected columns: {list(NORMALIZED_COLUMNS[dataset_type].keys())}\\n"
                f"Actual columns: {df.columns}\\n"
                f"\\nThis indicates a mismatch between CSV headers and config.py.\\n"
                f"Please verify the CSV file structure matches NORMALIZED_COLUMNS."
            )
        print(f"  \u2713 Schema validation passed")
        
        # Normalize columns (only if validation passed)
        df = normalize_columns(df, dataset_type)
        
        # Standardize dates (will raise error if parsing fails)
        df = standardize_date_column(df)
        
        # Export to Parquet
        parquet_path = output_path / f"{dataset_type}.parquet"
        export_to_parquet(df, parquet_path)
        print(f"  - Exported to: {parquet_path}")
        
        summary["datasets"][dataset_type] = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": df.columns,
            "output_file": str(parquet_path),
        }
        summary["output_files"].append(str(parquet_path))
    
    print("\n[5/5] Ingestion complete!")
    print(f"  - Total datasets processed: {len(summary['datasets'])}")
    
    return summary


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def load_processed_dataset(
    dataset_type: str,
    parquet_dir: Path = PARQUET_DIR
) -> pl.DataFrame:
    """
    Load a previously processed dataset from Parquet.
    
    Args:
        dataset_type: One of 'biometric', 'demographic', 'enrolment'
        parquet_dir: Directory containing Parquet files
        
    Returns:
        Polars DataFrame
    """
    parquet_path = parquet_dir / f"{dataset_type}.parquet"
    
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {parquet_path}. "
            "Run ingestion pipeline first."
        )
    
    return pl.read_parquet(parquet_path)


def get_dataset_schema(dataset_type: str) -> Dict[str, str]:
    """
    Get the normalized schema for a dataset type.
    
    Args:
        dataset_type: One of 'biometric', 'demographic', 'enrolment'
        
    Returns:
        Dictionary of column names and their expected meanings
    """
    return NORMALIZED_COLUMNS.get(dataset_type, {})


def save_dataset(
    df: pl.DataFrame,
    dataset_name: str,
    output_dir: Path = PARQUET_DIR
) -> Path:
    """
    Save specific dataset to Parquet.
    
    Args:
        df: DataFrame to save
        dataset_name: Name of the dataset (e.g., 'trend_typology')
        output_dir: Directory to save to
        
    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{dataset_name}.parquet"
    if hasattr(df, "write_parquet"):
        df.write_parquet(output_path)
    else:
        # Fallback if it's not a polars DF (shouldn't happen with strict typing)
        raise ValueError(f"Expected Polars DataFrame, got {type(df)}")
    return output_path


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Run ingestion pipeline when executed directly
    summary = run_ingestion_pipeline()
    
    # Print summary
    print("\n" + "=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    for dtype, info in summary["datasets"].items():
        print(f"\n{dtype.upper()}:")
        print(f"  Rows: {info['row_count']:,}")
        print(f"  Columns: {info['columns']}")
