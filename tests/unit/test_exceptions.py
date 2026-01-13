"""
Unit tests for custom exceptions.

Tests cover:
- Exception hierarchy
- Message formatting
- Details dictionary handling
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.exceptions import (
    AadhaarSanketError,
    DataIngestionError,
    SchemaValidationError,
    DateParsingError,
    FileDiscoveryError,
    CalculationError,
    InsufficientDataError,
    AIEngineError,
    ConfigurationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance."""
    
    def test_data_ingestion_inherits_base(self):
        """DataIngestionError should inherit from AadhaarSanketError."""
        exc = DataIngestionError("Test error")
        assert isinstance(exc, AadhaarSanketError)
    
    def test_schema_validation_inherits_ingestion(self):
        """SchemaValidationError should inherit from DataIngestionError."""
        exc = SchemaValidationError("Test error")
        assert isinstance(exc, DataIngestionError)
        assert isinstance(exc, AadhaarSanketError)
    
    def test_calculation_error_inherits_base(self):
        """CalculationError should inherit from AadhaarSanketError."""
        exc = CalculationError("Test error")
        assert isinstance(exc, AadhaarSanketError)
    
    def test_ai_engine_error_inherits_base(self):
        """AIEngineError should inherit from AadhaarSanketError."""
        exc = AIEngineError("Test error")
        assert isinstance(exc, AadhaarSanketError)


class TestExceptionMessages:
    """Tests for exception message formatting."""
    
    def test_simple_message(self):
        """Exception with simple message."""
        exc = AadhaarSanketError("Simple message")
        assert str(exc) == "Simple message"
        assert exc.message == "Simple message"
    
    def test_message_with_details(self):
        """Exception with details dictionary."""
        exc = SchemaValidationError(
            "Missing columns",
            details={"missing": ["date", "state"]}
        )
        
        assert exc.message == "Missing columns"
        assert exc.details == {"missing": ["date", "state"]}
        assert "missing" in str(exc)
    
    def test_empty_details(self):
        """Exception with no details."""
        exc = AadhaarSanketError("Error", details=None)
        assert exc.details == {}


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""
    
    def test_catch_specific_exception(self):
        """Catching specific exception type."""
        with pytest.raises(SchemaValidationError):
            raise SchemaValidationError("Schema error")
    
    def test_catch_parent_exception(self):
        """Catching parent exception catches child."""
        with pytest.raises(DataIngestionError):
            raise SchemaValidationError("Schema error")
    
    def test_catch_base_exception(self):
        """Catching base exception catches all children."""
        with pytest.raises(AadhaarSanketError):
            raise InsufficientDataError("Not enough data")
    
    def test_exception_details_preserved(self):
        """Details are preserved when catching."""
        try:
            raise FileDiscoveryError(
                "File not found",
                details={"path": "/data/test.csv"}
            )
        except FileDiscoveryError as e:
            assert e.details["path"] == "/data/test.csv"
