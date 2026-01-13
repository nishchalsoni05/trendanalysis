"""
Project Aadhaar Sanket - Custom Exception Hierarchy

This module defines a comprehensive exception hierarchy for the application.
Using domain-specific exceptions enables:
- Precise error handling at call sites
- Better error messages for debugging
- Clear separation of error types for logging/monitoring

Version: 1.0.0
"""

__all__ = [
    # Base
    "AadhaarSanketError",
    # Data Ingestion
    "DataIngestionError",
    "SchemaValidationError",
    "DateParsingError",
    "FileDiscoveryError",
    # Calculation
    "CalculationError",
    "InsufficientDataError",
    "DivisionByZeroError",
    # AI/ML
    "AIEngineError",
    "APIConnectionError",
    "ResponseValidationError",
    # Configuration
    "ConfigurationError",
]


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class AadhaarSanketError(Exception):
    """
    Base exception for all Aadhaar Sanket errors.
    
    All custom exceptions inherit from this class, enabling:
    - Catching all application errors with a single except clause
    - Distinguishing application errors from system errors
    
    Attributes:
        message: Human-readable error description
        details: Optional dictionary with additional context
    """
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} [{detail_str}]"
        return self.message


# =============================================================================
# DATA INGESTION EXCEPTIONS
# =============================================================================

class DataIngestionError(AadhaarSanketError):
    """
    Raised when data ingestion fails.
    
    This is the parent class for all ingestion-related errors including
    file discovery, schema validation, and data parsing.
    """
    pass


class FileDiscoveryError(DataIngestionError):
    """
    Raised when expected data files cannot be found.
    
    Example:
        >>> raise FileDiscoveryError(
        ...     "No CSV files found in directory",
        ...     details={"directory": "/data/enrolment", "pattern": "*.csv"}
        ... )
    """
    pass


class SchemaValidationError(DataIngestionError):
    """
    Raised when DataFrame schema does not match expected structure.
    
    This error indicates a mismatch between the CSV file structure
    and the expected column definitions in config.py.
    
    Example:
        >>> raise SchemaValidationError(
        ...     "Missing required columns",
        ...     details={"missing": ["date", "state"], "dataset": "demographic"}
        ... )
    """
    pass


class DateParsingError(DataIngestionError):
    """
    Raised when date column cannot be parsed with any supported format.
    
    Supported formats:
    - DD-MM-YYYY (UIDAI standard)
    - YYYY-MM-DD (ISO standard)
    - DD/MM/YYYY (alternate)
    
    Example:
        >>> raise DateParsingError(
        ...     "Date parsing failed for all formats",
        ...     details={"sample_values": ["2025/01/15", "2025/01/16"]}
        ... )
    """
    pass


# =============================================================================
# CALCULATION EXCEPTIONS
# =============================================================================

class CalculationError(AadhaarSanketError):
    """
    Raised when a calculation fails.
    
    This is the parent class for all calculation-related errors including
    MVI computation, anomaly detection, and trend analysis.
    """
    pass


class InsufficientDataError(CalculationError):
    """
    Raised when there is insufficient data for reliable calculation.
    
    This typically occurs when:
    - Population base is below minimum threshold
    - Time series has too few data points
    - Geographic unit has no records
    
    Example:
        >>> raise InsufficientDataError(
        ...     "Population below minimum threshold",
        ...     details={"population": 50, "threshold": 100, "district": "Example"}
        ... )
    """
    pass


class DivisionByZeroError(CalculationError):
    """
    Raised when a calculation would result in division by zero.
    
    This is a specific case of CalculationError that indicates
    an attempt to divide by a zero denominator (e.g., zero population).
    """
    pass


# =============================================================================
# AI/ML EXCEPTIONS
# =============================================================================

class AIEngineError(AadhaarSanketError):
    """
    Raised when AI/ML inference fails.
    
    This is the parent class for all AI-related errors including
    API connection issues, model failures, and response validation.
    """
    pass


class APIConnectionError(AIEngineError):
    """
    Raised when connection to external AI API fails.
    
    This includes:
    - Network connectivity issues
    - API rate limiting
    - Authentication failures
    - Timeout errors
    
    Example:
        >>> raise APIConnectionError(
        ...     "Gemini API connection failed",
        ...     details={"status_code": 429, "retry_after": 60}
        ... )
    """
    pass


class ResponseValidationError(AIEngineError):
    """
    Raised when AI response fails validation checks.
    
    This includes:
    - Empty or malformed responses
    - Responses containing forbidden content
    - Responses that don't match expected format
    """
    pass


# =============================================================================
# CONFIGURATION EXCEPTIONS
# =============================================================================

class ConfigurationError(AadhaarSanketError):
    """
    Raised when configuration is invalid or missing.
    
    This includes:
    - Missing required configuration keys
    - Invalid configuration values
    - Environment variable issues
    
    Example:
        >>> raise ConfigurationError(
        ...     "Required environment variable not set",
        ...     details={"variable": "GEMINI_API_KEY"}
        ... )
    """
    pass
