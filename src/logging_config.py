"""
Project Aadhaar Sanket - Structured Logging Configuration

This module provides centralized logging configuration for the application.
All modules should obtain their logger via get_logger() to ensure
consistent formatting and behavior.

Features:
- Structured log format with timestamp, level, and module
- Configurable log levels via environment variable
- File and console handlers
- No duplicate handlers on repeated imports

Version: 1.0.0
"""

import logging
import sys
from pathlib import Path
from typing import Optional

__all__ = ["get_logger", "setup_logging", "LogLevel"]


# =============================================================================
# CONSTANTS
# =============================================================================

# Default log format: timestamp | level | module | message
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels enum for type safety
class LogLevel:
    """Enumeration of valid log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# LOGGING SETUP
# =============================================================================

_logger_initialized = False


def setup_logging(
    level: str = LogLevel.INFO,
    log_file: Optional[Path] = None,
    format_string: str = DEFAULT_FORMAT
) -> logging.Logger:
    """
    Configure the root application logger.
    
    This function should be called once at application startup.
    Subsequent calls will return the existing logger without
    reconfiguration (to prevent duplicate handlers).
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Can also be set via AADHAAR_SANKET_LOG_LEVEL env var.
        log_file: Optional path to write logs to file.
        format_string: Custom format string for log messages.
    
    Returns:
        Configured root logger for the application.
    
    Example:
        >>> logger = setup_logging(level="DEBUG")
        >>> logger.info("Application started")
        2025-01-13 21:30:00 | INFO     | aadhaar_sanket | Application started
    """
    global _logger_initialized
    
    # Get or create the root application logger
    logger = logging.getLogger("aadhaar_sanket")
    
    # Prevent duplicate handlers on repeated calls
    if _logger_initialized:
        return logger
    
    # Check environment variable for level override
    import os
    env_level = os.environ.get("AADHAAR_SANKET_LOG_LEVEL", "").upper()
    if env_level in (LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, 
                     LogLevel.ERROR, LogLevel.CRITICAL):
        level = env_level
    
    # Set logging level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(format_string, datefmt=DEFAULT_DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger (avoid duplicate logs)
    logger.propagate = False
    
    _logger_initialized = True
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    This is the preferred way to obtain a logger in any module.
    The returned logger is a child of the application root logger,
    inheriting its configuration.
    
    Args:
        name: Module name, typically __name__
    
    Returns:
        Logger instance for the module.
    
    Example:
        >>> from src.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    # Ensure root logger is configured
    if not _logger_initialized:
        setup_logging()
    
    # Return child logger
    return logging.getLogger(f"aadhaar_sanket.{name}")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> None:
    """
    Log an exception with full traceback.
    
    This utility function provides consistent exception logging
    across the application.
    
    Args:
        logger: Logger instance to use
        exc: Exception to log
        context: Optional context string describing where the error occurred
    """
    if context:
        logger.error(f"{context}: {type(exc).__name__}: {exc}", exc_info=True)
    else:
        logger.error(f"{type(exc).__name__}: {exc}", exc_info=True)


def log_dataframe_info(logger: logging.Logger, df, name: str = "DataFrame") -> None:
    """
    Log summary information about a DataFrame.
    
    Useful for debugging data pipeline issues.
    
    Args:
        logger: Logger instance to use
        df: Polars or Pandas DataFrame
        name: Descriptive name for the DataFrame
    """
    try:
        rows = len(df)
        cols = len(df.columns)
        col_names = list(df.columns)[:5]  # First 5 columns
        logger.debug(f"{name}: {rows:,} rows × {cols} cols. Sample cols: {col_names}")
    except Exception as e:
        logger.warning(f"Could not log DataFrame info for {name}: {e}")
