"""Centralized logging configuration."""

import logging
import sys
from pathlib import Path

# Create the base 'enlace' logger at module import time to ensure
# child loggers (enlace.extractor, enlace.cli, etc.) properly inherit from it
_base_logger = logging.getLogger("enlace")


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    verbose: bool = False,
    paper_id: str | None = None,
    output_dir: Path | None = None,
) -> logging.Logger:
    """Configure logging for enlace package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to (overrides paper_id/output_dir)
        verbose: Enable verbose output (sets DEBUG level)
        paper_id: Paper ID for creating log directory (output/{paper_id}/logs/)
        output_dir: Base output directory (default: "output")

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
    # Set logger to DEBUG to allow all messages through
    # Individual handlers will filter based on their levels
    logger.setLevel(logging.DEBUG)

    # Disable propagation to root logger to avoid interference from
    # third-party libraries (like docling) that configure the root logger
    logger.propagate = False

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler - respects user's level choice
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File handler - create in paper output directory if paper_id provided
    if paper_id and output_dir:
        log_dir = Path(output_dir) / paper_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "extraction.log"

    # Add file handler - always saves INFO and above
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    # Configure third-party loggers to reduce noise
    # Set httpx (used by Anthropic SDK) to WARNING to hide INFO level HTTP requests
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Set langchain loggers to WARNING to reduce verbosity
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain_core").setLevel(logging.WARNING)
    logging.getLogger("langchain_anthropic").setLevel(logging.WARNING)

    return logger
