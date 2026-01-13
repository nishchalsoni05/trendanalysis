"""
Pytest configuration and shared fixtures.

This module provides fixtures that are available to all tests:
- Sample DataFrames for testing
- Temporary directories for file-based tests
- Mock configurations
"""

import pytest
import polars as pl
from pathlib import Path
import tempfile
import shutil


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_enrolment_df() -> pl.DataFrame:
    """
    Create a sample enrolment DataFrame for testing.
    
    Returns:
        DataFrame with realistic enrolment data structure.
    """
    return pl.DataFrame({
        "date": ["01-01-2025", "02-01-2025", "03-01-2025"],
        "state": ["Maharashtra", "Maharashtra", "Karnataka"],
        "district": ["Mumbai", "Pune", "Bangalore"],
        "pincode": ["400001", "411001", "560001"],
        "age_0_5": [100, 80, 120],
        "age_5_17": [200, 180, 220],
        "age_18_greater": [500, 450, 550],
    })


@pytest.fixture
def sample_demographic_df() -> pl.DataFrame:
    """
    Create a sample demographic DataFrame for testing.
    
    Returns:
        DataFrame with realistic demographic data structure.
    """
    return pl.DataFrame({
        "date": ["01-01-2025", "02-01-2025", "03-01-2025"],
        "state": ["Maharashtra", "Maharashtra", "Karnataka"],
        "district": ["Mumbai", "Pune", "Bangalore"],
        "pincode": ["400001", "411001", "560001"],
        "demo_age_5_17": [50, 40, 60],
        "demo_age_17_": [150, 130, 170],
    })


@pytest.fixture
def sample_biometric_df() -> pl.DataFrame:
    """
    Create a sample biometric DataFrame for testing.
    
    Returns:
        DataFrame with realistic biometric data structure.
    """
    return pl.DataFrame({
        "date": ["01-01-2025", "02-01-2025", "03-01-2025"],
        "state": ["Maharashtra", "Maharashtra", "Karnataka"],
        "district": ["Mumbai", "Pune", "Bangalore"],
        "pincode": ["400001", "411001", "560001"],
        "bio_age_5_17": [30, 25, 35],
        "bio_age_17_": [80, 70, 90],
    })


@pytest.fixture
def sample_mvi_df() -> pl.DataFrame:
    """
    Create a sample MVI DataFrame for testing.
    
    Returns:
        DataFrame with MVI values for testing classification.
    """
    return pl.DataFrame({
        "state": ["Maharashtra", "Karnataka", "Tamil Nadu", "Gujarat"],
        "district": ["Mumbai", "Bangalore", "Chennai", "Ahmedabad"],
        "mvi": [2.5, 12.0, 22.0, 45.0],
        "population_base": [15000, 12000, 8000, 5000],
    })


@pytest.fixture
def sample_signal_df() -> pl.DataFrame:
    """
    Create a sample signal DataFrame for MVI testing.
    
    Returns:
        DataFrame with signal-adjusted counts.
    """
    return pl.DataFrame({
        "state": ["Maharashtra", "Karnataka"],
        "district": ["Mumbai", "Bangalore"],
        "total_signal_adjusted": [150.0, 200.0],
        "total_raw_count": [200, 250],
    })


@pytest.fixture
def sample_population_df() -> pl.DataFrame:
    """
    Create a sample population DataFrame for MVI testing.
    
    Returns:
        DataFrame with population base.
    """
    return pl.DataFrame({
        "state": ["Maharashtra", "Karnataka"],
        "district": ["Mumbai", "Bangalore"],
        "population_base": [10000.0, 15000.0],
    })


# =============================================================================
# FILE SYSTEM FIXTURES
# =============================================================================

@pytest.fixture
def temp_data_dir():
    """
    Create a temporary data directory structure for testing.
    
    Yields:
        Path to temporary directory (cleaned up after test).
    """
    temp_dir = Path(tempfile.mkdtemp())
    
    # Create subdirectories matching expected structure
    (temp_dir / "api_data_aadhar_enrolment").mkdir()
    (temp_dir / "api_data_aadhar_demographic").mkdir()
    (temp_dir / "api_data_aadhar_biometric").mkdir()
    (temp_dir / "manual").mkdir()
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_csv_file(temp_data_dir, sample_enrolment_df):
    """
    Create a temporary CSV file for testing.
    
    Args:
        temp_data_dir: Temporary directory fixture
        sample_enrolment_df: Sample data fixture
    
    Yields:
        Path to temporary CSV file.
    """
    csv_path = temp_data_dir / "api_data_aadhar_enrolment" / "test_data.csv"
    sample_enrolment_df.write_csv(csv_path)
    yield csv_path


# =============================================================================
# CONFIGURATION FIXTURES
# =============================================================================

@pytest.fixture
def mock_config(monkeypatch, temp_data_dir):
    """
    Mock configuration to use temporary directories.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
        temp_data_dir: Temporary directory fixture
    """
    import src.config as config
    
    monkeypatch.setattr(config, "DATA_DIR", temp_data_dir)
    monkeypatch.setattr(config, "PROCESSED_DIR", temp_data_dir / "processed")
    monkeypatch.setattr(config, "PARQUET_DIR", temp_data_dir / "processed" / "parquet")
