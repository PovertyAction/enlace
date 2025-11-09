"""Document conversion utilities using docling.

This module provides utilities for converting PDF and DOCX files to markdown
and extracting structured content using the docling library.
"""

import logging
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import (
    ConversionResult,
    DocumentConverter,
    PdfFormatOption,
)

from enlace.exceptions import ExtractionError, UnsupportedFormatError

logger = logging.getLogger("enlace.utils.docling")


def convert_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Path,
    ocr_options=None,
    extract_figures: bool = True,
) -> tuple[Path, ConversionResult]:
    """Convert PDF to markdown using docling.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save markdown file
        ocr_options: Pre-configured OCR options (TesseractOcrOptions or EasyOcrOptions),
                    or None to disable OCR
        extract_figures: Enable figure/image extraction

    Returns:
        Tuple of (markdown_path, conversion_result)

    Raises:
        UnsupportedFormatError: If file format is not supported
        ExtractionError: If conversion fails

    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() not in [".pdf", ".docx"]:
        raise UnsupportedFormatError(pdf_path, [".pdf", ".docx"])

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / f"{pdf_path.stem}.md"

    # Check if markdown already exists
    if markdown_path.exists():
        logger.info(f"Using existing markdown: {markdown_path}")
        # Still need to convert to get ConversionResult for figures
        # In practice, we'd cache the result, but for now we'll reconvert
        pass

    try:
        # Configure pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True

        # Configure OCR
        if ocr_options is not None:
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = ocr_options
        else:
            pipeline_options.do_ocr = False

        # Configure figure extraction
        pipeline_options.generate_page_images = extract_figures
        pipeline_options.generate_picture_images = extract_figures
        pipeline_options.images_scale = 2.0  # 144 DPI resolution

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Convert document
        logger.info(f"Converting document: {pdf_path.name}")
        result = converter.convert(str(pdf_path))

        # Export to markdown
        markdown_text = result.document.export_to_markdown()

        # Save markdown
        with markdown_path.open("w", encoding="utf-8") as f:
            f.write(markdown_text)

        logger.info(f"Conversion complete: {markdown_path}")
        return markdown_path, result

    except Exception as e:
        logger.error(f"Conversion failed for {pdf_path}: {e}", exc_info=True)
        raise ExtractionError(f"Failed to convert {pdf_path.name}") from e


def get_docling_converter(
    enable_ocr: bool = False, extract_figures: bool = True
) -> DocumentConverter:
    """Create a configured DocumentConverter instance.

    Args:
        enable_ocr: Enable OCR for scanned documents
        extract_figures: Enable figure/image extraction

    Returns:
        Configured DocumentConverter instance

    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.do_ocr = enable_ocr
    pipeline_options.generate_page_images = extract_figures
    pipeline_options.generate_picture_images = extract_figures
    pipeline_options.images_scale = 2.0

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def analyze_document_structure(pdf_path: Path, config) -> dict:
    """Analyze document structure for dry-run mode.

    Performs a lightweight analysis of the document to estimate extraction
    requirements without performing full extraction or OCR.

    Args:
        pdf_path: Path to PDF file
        config: ExtractionConfig instance

    Returns:
        Dictionary with analysis results:
            - pages: Number of pages
            - tables: Number of tables detected
            - figures: Number of figures/images
            - scanned_percentage: Estimated percentage of scanned content (0-100)
            - estimated_fallback_pct: Estimated percentage requiring OCR fallback

    Raises:
        ExtractionError: If analysis fails

    """
    try:
        # Quick conversion without OCR to detect structure
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.do_ocr = False  # No OCR for dry-run
        pipeline_options.generate_page_images = False
        pipeline_options.generate_picture_images = False

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        logger.info(f"Analyzing document structure: {pdf_path.name}")
        result = converter.convert(str(pdf_path))

        # Count structural elements
        doc = result.document
        num_pages = len(doc.pages) if hasattr(doc, "pages") else 0
        num_tables = len([t for t in doc.tables]) if hasattr(doc, "tables") else 0
        num_figures = len([f for f in doc.pictures]) if hasattr(doc, "pictures") else 0

        # Estimate scanned content by checking text density
        total_text_length = len(doc.export_to_markdown())
        estimated_scanned = 0.0
        if num_pages > 0:
            avg_text_per_page = total_text_length / num_pages
            # If average text per page is low, likely scanned
            if avg_text_per_page < 500:  # Threshold for detecting scanned pages
                estimated_scanned = 80.0
            elif avg_text_per_page < 1000:
                estimated_scanned = 40.0
            else:
                estimated_scanned = 10.0

        # Estimate OCR fallback percentage based on table count
        # Tables in scanned documents often need fallback
        estimated_fallback = 20.0  # Default estimate
        if estimated_scanned > 50 and num_tables > 0:
            estimated_fallback = 30.0

        return {
            "pages": num_pages,
            "tables": num_tables,
            "figures": num_figures,
            "scanned_percentage": estimated_scanned,
            "estimated_fallback_pct": estimated_fallback,
        }

    except Exception as e:
        logger.error(f"Document analysis failed: {e}", exc_info=True)
        raise ExtractionError(f"Failed to analyze {pdf_path.name}") from e
