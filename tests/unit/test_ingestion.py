"""
Unit tests for the data ingestion engine.

Tests cover:
- Dataset discovery
- CSV loading
- Schema validation
- Column normalization
- Date standardization
"""

import pytest
import polars as pl
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engines.ingestion import (
    discover_datasets,
    validate_required_columns,
    normalize_columns,
    standardize_date_column,
    ingest_csv_with_duckdb,
    load_all_files_for_type,
    deduplicate_dataframe,
)
from src.exceptions import (
    FileDiscoveryError,
    SchemaValidationError,
    DateParsingError,
)


class TestDiscoverDatasets:
    """Tests for dataset discovery."""
    
    def test_discover_empty_directory(self, temp_data_dir):
        """Empty directories should return empty lists."""
        result = discover_datasets(temp_data_dir)
        
        assert "biometric" in result
        assert "demographic" in result
        assert "enrolment" in result
        assert all(len(files) == 0 for files in result.values())
    
    def test_discover_nonexistent_directory(self, tmp_path):
        """Non-existent directory should raise FileDiscoveryError."""
        nonexistent = tmp_path / "does_not_exist"
        
        with pytest.raises(FileDiscoveryError):
            discover_datasets(nonexistent)
    
    def test_discover_csv_files(self, temp_data_dir, sample_enrolment_df):
        """Should discover CSV files in correct directories."""
        # Create a CSV file
        csv_path = temp_data_dir / "api_data_aadhar_enrolment" / "test.csv"
        sample_enrolment_df.write_csv(csv_path)
        
        result = discover_datasets(temp_data_dir)
        
        assert len(result["enrolment"]) == 1
        assert result["enrolment"][0].name == "test.csv"


class TestValidateRequiredColumns:
    """Tests for schema validation."""
    
    def test_valid_enrolment_schema(self, sample_enrolment_df):
        """Valid enrolment schema should pass validation."""
        is_valid, missing = validate_required_columns(sample_enrolment_df, "enrolment")
        
        assert is_valid
        assert len(missing) == 0
    
    def test_missing_columns(self):
        """Missing columns should be detected."""
        df = pl.DataFrame({
            "date": ["01-01-2025"],
            "state": ["Maharashtra"],
            # Missing: district, pincode, age columns
        })
        
        is_valid, missing = validate_required_columns(df, "enrolment")
        
        assert not is_valid
        assert len(missing) > 0
    
    def test_invalid_dataset_type(self, sample_enrolment_df):
        """Invalid dataset type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown dataset type"):
            validate_required_columns(sample_enrolment_df, "invalid_type")


class TestNormalizeColumns:
    """Tests for column normalization."""
    
    def test_normalize_enrolment_columns(self, sample_enrolment_df):
        """Enrolment columns should be normalized correctly."""
        result = normalize_columns(sample_enrolment_df, "enrolment")
        
        # Check that normalized names exist
        assert "age_0_5_count" in result.columns
        assert "age_5_17_count" in result.columns
        assert "age_18_plus_count" in result.columns
        
        # Check dataset_type column added
        assert "dataset_type" in result.columns
        assert result["dataset_type"][0] == "enrolment"
    
    def test_invalid_dataset_type_normalization(self, sample_enrolment_df):
        """Invalid dataset type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown dataset type"):
            normalize_columns(sample_enrolment_df, "invalid")


class TestStandardizeDateColumn:
    """Tests for date standardization."""
    
    def test_parse_uidai_format(self):
        """DD-MM-YYYY format should be parsed correctly."""
        df = pl.DataFrame({"date": ["01-01-2025", "15-06-2025"]})
        
        result = standardize_date_column(df)
        
        assert result["date"].dtype == pl.Date
    
    def test_parse_iso_format(self):
        """YYYY-MM-DD format should be parsed correctly."""
        df = pl.DataFrame({"date": ["2025-01-01", "2025-06-15"]})
        
        result = standardize_date_column(df)
        
        assert result["date"].dtype == pl.Date
    
    def test_parse_alternate_format(self):
        """DD/MM/YYYY format should be parsed correctly."""
        df = pl.DataFrame({"date": ["01/01/2025", "15/06/2025"]})
        
        result = standardize_date_column(df)
        
        assert result["date"].dtype == pl.Date
    
    def test_missing_date_column(self):
        """Missing date column should raise DateParsingError."""
        df = pl.DataFrame({"other_column": [1, 2, 3]})
        
        with pytest.raises(DateParsingError):
            standardize_date_column(df)
    
    def test_unparseable_dates(self):
        """Unparseable dates should raise DateParsingError."""
        df = pl.DataFrame({"date": ["not-a-date", "also-not-a-date"]})
        
        with pytest.raises(DateParsingError):
            standardize_date_column(df)


class TestLoadCSV:
    """Tests for CSV loading."""
    
    def test_load_csv_file(self, temp_csv_file):
        """Should load CSV file successfully."""
        result = ingest_csv_with_duckdb(temp_csv_file)
        
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3  # Sample data has 3 rows
    
    def test_load_with_sample_size(self, temp_csv_file):
        """Should respect sample_size limit."""
        result = ingest_csv_with_duckdb(temp_csv_file, sample_size=1)
        
        assert len(result) == 1
    
    def test_load_multiple_files(self, temp_data_dir, sample_enrolment_df):
        """Should load and concatenate multiple files."""
        # Create two CSV files
        dir_path = temp_data_dir / "api_data_aadhar_enrolment"
        sample_enrolment_df.write_csv(dir_path / "file1.csv")
        sample_enrolment_df.write_csv(dir_path / "file2.csv")
        
        files = sorted(dir_path.glob("*.csv"))
        result = load_all_files_for_type(files)
        
        assert len(result) == 6  # 3 rows × 2 files
        assert "_source_file" in result.columns


class TestDeduplication:
    """Tests for data deduplication."""
    
    def test_removes_duplicate_rows(self):
        """Should remove duplicate rows."""
        df = pl.DataFrame({
            "date": ["01-01-2025", "01-01-2025", "02-01-2025"],
            "state": ["Maharashtra", "Maharashtra", "Maharashtra"],
            "district": ["Mumbai", "Mumbai", "Mumbai"],
            "pincode": [400001, 400001, 400001],
            "value": [100, 100, 200],
            "_source_file": ["file1.csv", "file2.csv", "file1.csv"],
        })
        
        result, removed = deduplicate_dataframe(df)
        
        assert removed == 1  # One duplicate removed
        assert len(result) == 2  # Two unique rows remain
    
    def test_preserves_unique_rows(self):
        """Should preserve all unique rows."""
        df = pl.DataFrame({
            "date": ["01-01-2025", "02-01-2025"],
            "state": ["Maharashtra", "Gujarat"],
            "value": [100, 200],
            "_source_file": ["file1.csv", "file1.csv"],
        })
        
        result, removed = deduplicate_dataframe(df)
        
        assert removed == 0
        assert len(result) == 2
    
    def test_ignores_source_file_column(self):
        """Should ignore _source_file when comparing rows."""
        # Same data, different source files
        df = pl.DataFrame({
            "date": ["01-01-2025", "01-01-2025"],
            "value": [100, 100],
            "_source_file": ["file1.csv", "file2.csv"],  # Different sources
        })
        
        result, removed = deduplicate_dataframe(df)
        
        assert removed == 1  # Should be deduplicated
        assert len(result) == 1

