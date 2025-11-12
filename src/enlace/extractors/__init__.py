"""Table extraction modules for enlace.

This package contains extractors for different table extraction approaches:
- camelot_extractor: Camelot-based extraction for text-based PDFs
"""

from enlace.extractors.camelot_extractor import (
    CamelotError,
    CamelotExtractor,
    CamelotNotInstalledError,
    CamelotTable,
    is_text_based_pdf,
)

__all__ = [
    "CamelotExtractor",
    "CamelotTable",
    "CamelotError",
    "CamelotNotInstalledError",
    "is_text_based_pdf",
]
