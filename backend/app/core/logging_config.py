"""
Structured JSON logging configuration for debugging and monitoring.
Provides structured logging with JSON format for easy parsing and analysis.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.
    Includes timestamp, level, logger name, message, and any extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if they exist
        if hasattr(record, "extra_fields") and record.extra_fields:
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_structured_logger(name: str) -> logging.Logger:
    """
    Get a logger configured with JSON formatting.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger


class StructuredLogger:
    """
    Wrapper for structured logging with convenience methods.
    Allows logging with additional context fields.
    """

    def __init__(self, name: str):
        self.logger = get_structured_logger(name)

    def _log(self, level: int, message: str, **kwargs):
        """Internal method to log with extra fields."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs):
        """Log info level message with optional context fields."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning level message with optional context fields."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error level message with optional context fields."""
        self._log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug level message with optional context fields."""
        self._log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical level message with optional context fields."""
        self._log(logging.CRITICAL, message, **kwargs)
