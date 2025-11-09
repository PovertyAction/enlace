"""OCR backend management and configuration.

This module provides the OCRBackendManager class for selecting and configuring
OCR backends based on the extraction configuration.
"""

import logging

from enlace.core.config import ExtractionConfig
from enlace.utils.ocr_options import (
    OCRBackend,
    create_easyocr_options,
    create_tesseract_options,
)

logger = logging.getLogger("enlace.ocr_backends")


class OCRBackendManager:
    """Manages OCR backend selection and configuration."""

    def __init__(self, config: ExtractionConfig):
        """Initialize OCR backend manager.

        Args:
            config: Extraction configuration with OCR settings

        """
        self.config = config
        self.primary_backend = self._determine_primary_backend()
        self.fallback_backend = self._determine_fallback_backend()

        logger.info(
            f"OCR Backend Manager initialized: primary={self.primary_backend.value}, "
            f"fallback={self.fallback_backend.value if self.fallback_backend else None}, "
            f"hybrid={config.hybrid_ocr_enabled}"
        )

    def _determine_primary_backend(self) -> OCRBackend:
        """Determine primary OCR backend based on config.

        Returns:
            Primary OCR backend to use

        """
        if self.config.ocr_backend == "auto":
            return OCRBackend.TESSERACT  # Fast primary engine
        elif self.config.ocr_backend == "tesseract":
            return OCRBackend.TESSERACT
        elif self.config.ocr_backend == "easyocr":
            return OCRBackend.EASYOCR
        else:
            logger.warning(
                f"Unknown OCR backend '{self.config.ocr_backend}', "
                "defaulting to Tesseract"
            )
            return OCRBackend.TESSERACT

    def _determine_fallback_backend(self) -> OCRBackend | None:
        """Determine fallback OCR backend for hybrid approach.

        Returns:
            Fallback OCR backend, or None if hybrid disabled

        """
        if not self.config.hybrid_ocr_enabled:
            return None

        if self.config.ocr_backend == "auto":
            return OCRBackend.EASYOCR  # More accurate fallback

        # No fallback if specific backend chosen (not in auto mode)
        return None

    def create_primary_ocr_options(self):
        """Create docling OCR options for primary backend.

        Returns:
            Configured OCR options for docling

        """
        if self.primary_backend == OCRBackend.TESSERACT:
            return create_tesseract_options(self.config.ocr_languages)
        elif self.primary_backend == OCRBackend.EASYOCR:
            return create_easyocr_options(
                self.config.ocr_languages,
                self.config.ocr_use_gpu,
                self.config.ocr_confidence_threshold,
            )
        return None

    def create_fallback_ocr_options(self):
        """Create docling OCR options for fallback backend.

        Returns:
            Configured OCR options for fallback, or None if no fallback

        """
        if self.fallback_backend is None:
            return None

        if self.fallback_backend == OCRBackend.EASYOCR:
            return create_easyocr_options(
                self.config.ocr_languages,
                self.config.ocr_use_gpu,
                self.config.ocr_confidence_threshold,
            )

        return None

    def get_backend_name(self, backend: OCRBackend | None) -> str:
        """Get human-readable backend name.

        Args:
            backend: OCR backend enum

        Returns:
            Backend name as string

        """
        if backend is None:
            return "none"
        return backend.value
