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
    enable_ocr: bool = False,
    extract_figures: bool = True,
) -> tuple[Path, ConversionResult]:
    """Convert PDF to markdown using docling.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save markdown file
        enable_ocr: Enable OCR for scanned documents
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
        pipeline_options.do_ocr = enable_ocr

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
