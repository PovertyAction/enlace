"""Centralized logging configuration."""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO", log_file: Path | None = None, verbose: bool = False
) -> logging.Logger:
    """Configure logging for enlace package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        verbose: Enable verbose output (sets DEBUG level)

    Returns:
        Configured logger instance

    """
    if verbose:
        level = "DEBUG"

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    logger = logging.getLogger("enlace")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
