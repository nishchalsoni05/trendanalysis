"""
Project Aadhaar Sanket - Input Validation Module

This module provides decorators and utilities for validating function
inputs at runtime. Using decorators enables:
- Declarative validation (clear intent)
- Separation of validation from business logic
- Consistent error messages across the codebase

Version: 1.0.0
"""

from functools import wraps
from typing import Any, Callable, List, Optional, Set, TypeVar, Union
from pathlib import Path

import polars as pl

from src.exceptions import (
    SchemaValidationError,
    InsufficientDataError,
    ConfigurationError,
)
from src.logging_config import get_logger

__all__ = [
    "validate_dataframe_columns",
    "validate_not_empty",
    "validate_geo_level",
    "validate_path_exists",
    "validate_positive",
    "validate_in_range",
    "ValidationResult",
]

logger = get_logger(__name__)

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


# =============================================================================
# VALIDATION RESULT
# =============================================================================

class ValidationResult:
    """
    Result of a validation check.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of error messages if validation failed
    """
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def add_error(self, message: str) -> None:
        """Add an error message and mark as invalid."""
        self.is_valid = False
        self.errors.append(message)
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        return self


# =============================================================================
# DATAFRAME VALIDATORS
# =============================================================================

def validate_dataframe_columns(
    required_columns: List[str],
    param_name: str = "df"
) -> Callable[[F], F]:
    """
    Decorator to validate that a DataFrame has required columns.
    
    Args:
        required_columns: List of column names that must be present
        param_name: Name of the DataFrame parameter to validate
    
    Returns:
        Decorator function
    
    Example:
        >>> @validate_dataframe_columns(["date", "state", "district"])
        ... def process_data(df: pl.DataFrame) -> pl.DataFrame:
        ...     return df
    
    Raises:
        SchemaValidationError: If required columns are missing
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Find the DataFrame in args or kwargs
            df = kwargs.get(param_name)
            if df is None and args:
                # Assume first positional arg is the DataFrame
                df = args[0]
            
            if df is None:
                raise SchemaValidationError(
                    f"Parameter '{param_name}' is required",
                    details={"function": func.__name__}
                )
            
            if not isinstance(df, pl.DataFrame):
                raise SchemaValidationError(
                    f"Expected pl.DataFrame, got {type(df).__name__}",
                    details={"function": func.__name__, "param": param_name}
                )
            
            # Check for missing columns
            actual_columns = set(df.columns)
            required_set = set(required_columns)
            missing = required_set - actual_columns
            
            if missing:
                logger.error(
                    f"Schema validation failed in {func.__name__}: "
                    f"missing columns {sorted(missing)}"
                )
                raise SchemaValidationError(
                    f"Missing required columns: {sorted(missing)}",
                    details={
                        "function": func.__name__,
                        "missing": sorted(missing),
                        "available": sorted(actual_columns)[:10],  # First 10
                    }
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_dataframe_not_empty(param_name: str = "df") -> Callable[[F], F]:
    """
    Decorator to validate that a DataFrame is not empty.
    
    Args:
        param_name: Name of the DataFrame parameter to validate
    
    Returns:
        Decorator function
    
    Raises:
        InsufficientDataError: If DataFrame has zero rows
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            df = kwargs.get(param_name)
            if df is None and args:
                df = args[0]
            
            if df is not None and len(df) == 0:
                logger.warning(f"Empty DataFrame passed to {func.__name__}")
                raise InsufficientDataError(
                    "DataFrame is empty",
                    details={"function": func.__name__, "param": param_name}
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# PARAMETER VALIDATORS
# =============================================================================

def validate_not_empty(param_name: str) -> Callable[[F], F]:
    """
    Decorator to validate that a parameter is not None or empty.
    
    Args:
        param_name: Name of the parameter to validate
    
    Returns:
        Decorator function
    
    Example:
        >>> @validate_not_empty("file_paths")
        ... def load_files(file_paths: List[Path]) -> pl.DataFrame:
        ...     return pl.concat([pl.read_csv(p) for p in file_paths])
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            value = kwargs.get(param_name)
            
            if value is None:
                raise ValueError(f"Parameter '{param_name}' cannot be None")
            
            if hasattr(value, "__len__") and len(value) == 0:
                raise ValueError(f"Parameter '{param_name}' cannot be empty")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_geo_level(param_name: str = "geo_level") -> Callable[[F], F]:
    """
    Decorator to validate geographic level parameter.
    
    Valid values: 'state', 'district', 'pincode'
    
    Args:
        param_name: Name of the geo_level parameter
    
    Returns:
        Decorator function
    """
    VALID_GEO_LEVELS = {"state", "district", "pincode"}
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            geo_level = kwargs.get(param_name, "district")
            
            if geo_level not in VALID_GEO_LEVELS:
                raise ValueError(
                    f"Invalid {param_name}: '{geo_level}'. "
                    f"Must be one of: {sorted(VALID_GEO_LEVELS)}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_path_exists(param_name: str) -> Callable[[F], F]:
    """
    Decorator to validate that a path exists.
    
    Args:
        param_name: Name of the path parameter
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            path = kwargs.get(param_name)
            if path is None and args:
                path = args[0] if isinstance(args[0], (str, Path)) else None
            
            if path is not None:
                path = Path(path)
                if not path.exists():
                    raise FileNotFoundError(
                        f"Path does not exist: {path}"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_positive(param_name: str) -> Callable[[F], F]:
    """
    Decorator to validate that a numeric parameter is positive.
    
    Args:
        param_name: Name of the numeric parameter
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            value = kwargs.get(param_name)
            
            if value is not None and value <= 0:
                raise ValueError(
                    f"Parameter '{param_name}' must be positive, got {value}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_in_range(
    param_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> Callable[[F], F]:
    """
    Decorator to validate that a numeric parameter is within a range.
    
    Args:
        param_name: Name of the numeric parameter
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
    
    Returns:
        Decorator function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            value = kwargs.get(param_name)
            
            if value is not None:
                if min_value is not None and value < min_value:
                    raise ValueError(
                        f"Parameter '{param_name}' must be >= {min_value}, got {value}"
                    )
                if max_value is not None and value > max_value:
                    raise ValueError(
                        f"Parameter '{param_name}' must be <= {max_value}, got {value}"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# COMPOSITE VALIDATION
# =============================================================================

def validate_dataset_type(param_name: str = "dataset_type") -> Callable[[F], F]:
    """
    Decorator to validate dataset type parameter.
    
    Valid values: 'biometric', 'demographic', 'enrolment'
    
    Args:
        param_name: Name of the dataset_type parameter
    
    Returns:
        Decorator function
    """
    VALID_TYPES = {"biometric", "demographic", "enrolment"}
    
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            dataset_type = kwargs.get(param_name)
            
            if dataset_type is not None and dataset_type not in VALID_TYPES:
                raise ValueError(
                    f"Invalid {param_name}: '{dataset_type}'. "
                    f"Must be one of: {sorted(VALID_TYPES)}"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
