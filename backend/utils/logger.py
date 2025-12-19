"""Structured logging configuration.

This module provides a configured logger with structured output
for better debugging and monitoring.
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format.
    
    This makes logs easier to parse and analyze in production environments.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: The log record to format
        
        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        return json.dumps(log_data)


class SimpleFormatter(logging.Formatter):
    """Human-readable formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record in readable format."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level_colors = {
            "DEBUG": "\033[36m",    # Cyan
            "INFO": "\033[32m",     # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",    # Red
            "CRITICAL": "\033[35m", # Magenta
        }
        reset = "\033[0m"
        
        color = level_colors.get(record.levelname, "")
        level = f"{color}{record.levelname}{reset}"
        
        message = f"[{timestamp}] {level} {record.name}: {record.getMessage()}"
        
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message


def setup_logger(
    name: str,
    level: int = logging.INFO,
    structured: bool = False
) -> logging.Logger:
    """Set up and configure a logger.
    
    Args:
        name: Logger name (usually __name__ of the module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: If True, use JSON formatting; if False, use readable format
    
    Returns:
        Configured logger instance
    
    Examples:
        >>> logger = setup_logger(__name__, level=logging.DEBUG)
        >>> logger.info("Server started")
        [2025-01-15 10:30:00] INFO backend.server: Server started
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set formatter based on environment
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = SimpleFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with default configuration.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
