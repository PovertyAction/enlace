"""OCR configuration helpers for docling.

This module provides utilities for creating OCR options for different backends
supported by docling (Tesseract, EasyOCR).
"""

import logging
import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path

from docling.datamodel.pipeline_options import EasyOcrOptions, TesseractOcrOptions

logger = logging.getLogger("enlace.ocr_options")


class OCRBackend(Enum):
    """Supported OCR backends."""

    AUTO = "auto"
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


def _check_tessdata_env() -> str | None:
    """Check TESSDATA_PREFIX environment variable.

    Returns:
        Path to tessdata directory, or None if not found

    """
    if tessdata := os.environ.get("TESSDATA_PREFIX"):
        tessdata_path = Path(tessdata)
        if tessdata_path.exists():
            logger.debug(f"Found tessdata via TESSDATA_PREFIX: {tessdata_path}")
            return str(tessdata_path)
    return None


def _parse_tessdata_from_output(output: str) -> str | None:
    """Parse tessdata path from tesseract --list-langs output.

    Args:
        output: Output from tesseract --list-langs command

    Returns:
        Path to tessdata directory, or None if not found

    """
    # Parse output like: List of available languages in "/path/to/tessdata/" (3):
    for line in output.split("\n"):
        if "available languages in" not in line:
            continue

        # Extract path between quotes
        start = line.find('"') + 1
        end = line.find('"', start)
        if start > 0 and end > start:
            tessdata_path = Path(line[start:end])
            if tessdata_path.exists():
                logger.debug(f"Detected tessdata path: {tessdata_path}")
                return str(tessdata_path)

    return None


def _detect_tessdata_path() -> str | None:
    """Detect tessdata directory path.

    Returns:
        Path to tessdata directory, or None if not found

    """
    # Check TESSDATA_PREFIX environment variable
    if path := _check_tessdata_env():
        return path

    # Try to find tesseract executable
    tesseract_bin = shutil.which("tesseract")
    if not tesseract_bin:
        logger.warning("tesseract executable not found in PATH")
        return None

    # Get tessdata path from tesseract
    try:
        result = subprocess.run(
            [tesseract_bin, "--list-langs"],
            capture_output=True,
            text=True,
            check=False,
        )
        # Output can be in stdout or stderr depending on tesseract version
        output = result.stdout or result.stderr
        return _parse_tessdata_from_output(output)

    except Exception as e:
        logger.warning(f"Failed to detect tessdata path: {e}")
        return None


def create_tesseract_options(languages: list[str]) -> TesseractOcrOptions | None:
    """Create Tesseract OCR options.

    Args:
        languages: List of language codes (e.g., ['eng', 'fra', 'spa'])

    Returns:
        Configured TesseractOcrOptions, or None if Tesseract is not available

    """
    tessdata_path = _detect_tessdata_path()

    if tessdata_path:
        logger.debug(f"Using tessdata path: {tessdata_path}")
        return TesseractOcrOptions(
            lang=languages,
            path=tessdata_path,
            force_full_page_ocr=False,  # Only OCR images/scanned regions
        )
    else:
        logger.warning(
            "Tesseract not properly configured (tessdata path not found). "
            "Set TESSDATA_PREFIX environment variable or install tesseract with language data. "
            "Falling back to alternative OCR backend."
        )
        return None


def create_easyocr_options(
    languages: list[str], use_gpu: bool, confidence_threshold: float
) -> EasyOcrOptions:
    """Create EasyOCR options.

    Args:
        languages: List of language codes (e.g., ['en', 'fr', 'es'])
        use_gpu: Whether to use GPU acceleration (requires CUDA)
        confidence_threshold: Minimum confidence threshold (0.0-1.0)

    Returns:
        Configured EasyOcrOptions

    """
    return EasyOcrOptions(
        lang=languages,
        use_gpu=use_gpu,
        confidence_threshold=confidence_threshold,
        force_full_page_ocr=False,  # Only OCR images/scanned regions
    )
