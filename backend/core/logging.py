"""
Logging Configuration Module
Provides centralized logging setup for the entire application

Features:
- Console logging with colored output
- Structured log formatting
- Configurable log levels per module
- Request/response logging
"""
import logging
import sys
from typing import Optional
from core.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colored output for different log levels
    Makes logs easier to read during development
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format log record with colors"""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted = super().format(record)
        
        # Reset levelname for potential other formatters
        record.levelname = levelname
        
        return formatted


def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure application-wide logging
    
    Args:
        log_level: Optional override for log level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured root logger
    """
    # Use provided level or fall back to settings
    level = log_level or settings.log_level
    
    # Create formatter
    if settings.environment == "development":
        # Colored output for development
        formatter = ColoredFormatter(
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Standard formatter for production
        formatter = logging.Formatter(
            settings.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    # Log initialization
    root_logger.info("=" * 80)
    root_logger.info("BIM-EPD Graph RAG Application - Logging Initialized")
    root_logger.info(f"Environment: {settings.environment}")
    root_logger.info(f"Log Level: {level}")
    root_logger.info("=" * 80)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Configured logger for the module
    """
    return logging.getLogger(name)