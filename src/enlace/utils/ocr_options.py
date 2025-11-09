"""OCR configuration helpers for docling.

This module provides utilities for creating OCR options for different backends
supported by docling (Tesseract, EasyOCR).
"""

from enum import Enum

from docling.datamodel.pipeline_options import EasyOcrOptions, TesseractOcrOptions


class OCRBackend(Enum):
    """Supported OCR backends."""

    AUTO = "auto"
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"


def create_tesseract_options(languages: list[str]) -> TesseractOcrOptions:
    """Create Tesseract OCR options.

    Args:
        languages: List of language codes (e.g., ['eng', 'fra', 'spa'])

    Returns:
        Configured TesseractOcrOptions

    """
    return TesseractOcrOptions(
        lang=languages,
        force_full_page_ocr=False,  # Only OCR images/scanned regions
    )


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
