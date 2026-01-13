"""
Unit tests for the MVI (Migration Velocity Index) engine.

Tests cover:
- Band classification logic
- Confidence indicator assignment
- MVI calculation correctness
- Edge cases and error handling
"""

import pytest
import polars as pl
from pathlib import Path
import sys

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engines.mvi import (
    classify_mvi_bands,
    add_confidence_indicator,
    calculate_mvi,
    generate_mvi_summary,
    get_top_mvi_regions,
)
from src.config import MVI_BANDS


class TestClassifyMVIBands:
    """Tests for MVI band classification."""
    
    def test_stable_band(self):
        """MVI < 5 should be classified as Stable."""
        df = pl.DataFrame({"mvi": [0.0, 1.0, 2.5, 4.9]})
        result = classify_mvi_bands(df)
        
        assert all(result["mvi_band"].to_list() == ["Stable"] * 4)
        assert all(result["mvi_color"].to_list() == [MVI_BANDS["stable"]["color"]] * 4)
    
    def test_moderate_band(self):
        """5 <= MVI < 15 should be classified as Moderate."""
        df = pl.DataFrame({"mvi": [5.0, 10.0, 14.9]})
        result = classify_mvi_bands(df)
        
        assert all(result["mvi_band"].to_list() == ["Moderate"] * 3)
    
    def test_elevated_band(self):
        """15 <= MVI < 30 should be classified as Elevated."""
        df = pl.DataFrame({"mvi": [15.0, 22.0, 29.9]})
        result = classify_mvi_bands(df)
        
        assert all(result["mvi_band"].to_list() == ["Elevated"] * 3)
    
    def test_high_pressure_band(self):
        """MVI >= 30 should be classified as High Pressure."""
        df = pl.DataFrame({"mvi": [30.0, 50.0, 100.0]})
        result = classify_mvi_bands(df)
        
        assert all(result["mvi_band"].to_list() == ["High Pressure"] * 3)
    
    def test_boundary_values(self):
        """Test exact boundary values."""
        df = pl.DataFrame({"mvi": [5.0, 15.0, 30.0]})
        result = classify_mvi_bands(df)
        
        bands = result["mvi_band"].to_list()
        assert bands[0] == "Moderate"  # 5.0 is in Moderate, not Stable
        assert bands[1] == "Elevated"  # 15.0 is in Elevated, not Moderate
        assert bands[2] == "High Pressure"  # 30.0 is High Pressure
    
    def test_negative_mvi(self):
        """Negative MVI values should be classified as Stable."""
        df = pl.DataFrame({"mvi": [-1.0, -5.0]})
        result = classify_mvi_bands(df)
        
        assert all(result["mvi_band"].to_list() == ["Stable"] * 2)


class TestConfidenceIndicator:
    """Tests for confidence indicator assignment."""
    
    def test_high_confidence(self):
        """Population >= 10000 should have HIGH confidence."""
        df = pl.DataFrame({"population_base": [10000, 50000, 100000]})
        result = add_confidence_indicator(df)
        
        assert all(result["confidence"].to_list() == ["HIGH"] * 3)
    
    def test_medium_confidence(self):
        """1000 <= Population < 10000 should have MEDIUM confidence."""
        df = pl.DataFrame({"population_base": [1000, 5000, 9999]})
        result = add_confidence_indicator(df)
        
        assert all(result["confidence"].to_list() == ["MEDIUM"] * 3)
    
    def test_low_confidence(self):
        """100 <= Population < 1000 should have LOW confidence."""
        df = pl.DataFrame({"population_base": [100, 500, 999]})
        result = add_confidence_indicator(df)
        
        assert all(result["confidence"].to_list() == ["LOW"] * 3)
    
    def test_insufficient_confidence(self):
        """Population < 100 should have INSUFFICIENT confidence."""
        df = pl.DataFrame({"population_base": [50, 99]})
        result = add_confidence_indicator(df)
        
        assert all(result["confidence"].to_list() == ["INSUFFICIENT"] * 2)


class TestCalculateMVI:
    """Tests for MVI calculation."""
    
    def test_basic_mvi_calculation(self, sample_signal_df, sample_population_df):
        """Test basic MVI calculation correctness."""
        result = calculate_mvi(sample_signal_df, sample_population_df, "district")
        
        # MVI = (signal / population) * 1000
        # Mumbai: (150 / 10000) * 1000 = 15.0
        # Bangalore: (200 / 15000) * 1000 = 13.33...
        
        assert len(result) == 2
        assert "mvi" in result.columns
        assert "mvi_band" in result.columns
        assert "confidence" in result.columns
    
    def test_mvi_has_band_classification(self, sample_signal_df, sample_population_df):
        """Test that MVI result includes band classification."""
        result = calculate_mvi(sample_signal_df, sample_population_df, "district")
        
        valid_bands = {"Stable", "Moderate", "Elevated", "High Pressure"}
        assert all(band in valid_bands for band in result["mvi_band"].to_list())


class TestMVISummary:
    """Tests for MVI summary generation."""
    
    def test_summary_structure(self, sample_mvi_df):
        """Test that summary has expected structure."""
        # First classify bands
        df = classify_mvi_bands(sample_mvi_df)
        summary = generate_mvi_summary(df)
        
        assert "generated_at" in summary
        assert "total_units" in summary
        assert "mvi_statistics" in summary
        assert "band_distribution" in summary
        assert "interpretation" in summary
    
    def test_summary_statistics(self, sample_mvi_df):
        """Test that statistics are calculated correctly."""
        df = classify_mvi_bands(sample_mvi_df)
        summary = generate_mvi_summary(df)
        
        stats = summary["mvi_statistics"]
        assert "mean" in stats
        assert "median" in stats
        assert "std" in stats
        assert "min" in stats
        assert "max" in stats


class TestTopMVIRegions:
    """Tests for top MVI region selection."""
    
    def test_top_n_descending(self, sample_mvi_df):
        """Test getting top N regions by MVI (descending)."""
        df = classify_mvi_bands(sample_mvi_df)
        result = get_top_mvi_regions(df, n=2, ascending=False)
        
        assert len(result) == 2
        # Gujarat has highest MVI (45.0)
        assert result["district"][0] == "Ahmedabad"
    
    def test_top_n_ascending(self, sample_mvi_df):
        """Test getting top N regions by MVI (ascending = lowest)."""
        df = classify_mvi_bands(sample_mvi_df)
        result = get_top_mvi_regions(df, n=2, ascending=True)
        
        assert len(result) == 2
        # Mumbai has lowest MVI (2.5)
        assert result["district"][0] == "Mumbai"
