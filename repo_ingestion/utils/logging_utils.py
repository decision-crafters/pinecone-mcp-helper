"""
Logging utilities for the repository ingestion pipeline.

This module provides functions for setting up logging for the pipeline.
"""

import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging for the application.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If provided, logs will be written to this file
                  in addition to the console.
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # Add console handler to root logger
    root_logger.addHandler(console_handler)

    # Add file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Suppress overly verbose logging from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("git").setLevel(logging.WARNING)
