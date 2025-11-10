"""Document conversion utilities using docling.

This module provides utilities for converting PDF and DOCX files to markdown
and extracting structured content using the docling library.
"""

import logging
import os
from pathlib import Path

from enlace.exceptions import ExtractionError, UnsupportedFormatError

logger = logging.getLogger("enlace.utils.docling")

# Set TESSDATA_PREFIX before docling imports tesserocr
# This must happen before any docling imports that might trigger tesserocr initialization
from enlace.utils.ocr_options import _detect_tessdata_path  # noqa: E402

if "TESSDATA_PREFIX" not in os.environ and (tessdata_path := _detect_tessdata_path()):
    os.environ["TESSDATA_PREFIX"] = tessdata_path
    logger.debug(f"Set TESSDATA_PREFIX={tessdata_path}")

from docling.datamodel.base_models import InputFormat  # noqa: E402
from docling.datamodel.pipeline_options import (  # noqa: E402
    PdfPipelineOptions,
    granite_picture_description,
)
from docling.document_converter import (  # noqa: E402
    ConversionResult,
    DocumentConverter,
    PdfFormatOption,
)
from docling_core.types.doc.base import ImageRefMode  # noqa: E402


def _add_picture_annotations(markdown_path: Path, result: ConversionResult) -> None:
    """Add vision model annotations to pictures in markdown.

    Args:
        markdown_path: Path to the markdown file
        result: Docling conversion result with picture descriptions

    """
    # Read the markdown file
    with markdown_path.open("r", encoding="utf-8") as f:
        content = f.read()

    # Build a mapping of image filenames to their descriptions
    image_descriptions = {}
    for pic in result.document.pictures:
        if pic.captions:
            # Get the first caption text
            description = pic.captions[0].text if pic.captions else None
            if description and pic.image and pic.image.uri:
                # Extract filename from URI
                uri_str = str(pic.image.uri)
                if "image_" in uri_str:
                    # Extract the image filename
                    filename = uri_str.split("/")[-1] if "/" in uri_str else uri_str
                    image_descriptions[filename] = description

    # Replace image references with annotated versions
    import re

    lines = content.split("\n")
    new_lines = []

    for line in lines:
        new_lines.append(line)
        # Check if this line contains an image reference
        match = re.match(r"!\[.*?\]\((.*?)\)", line)
        if match:
            image_path = match.group(1)
            # Extract filename from path
            filename = image_path.split("/")[-1]
            if filename in image_descriptions:
                # Add annotation on the next line
                annotation = image_descriptions[filename]
                new_lines.append(f"VISION MODEL ANNOTATION: {annotation}")
                new_lines.append("")  # Add blank line for readability

    # Write back the modified content
    with markdown_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    logger.info(f"Added {len(image_descriptions)} vision model annotations")


def convert_pdf_to_markdown(
    pdf_path: Path,
    output_dir: Path,
    ocr_options=None,
    extract_figures: bool = True,
    describe_pictures: bool = False,
) -> tuple[Path, ConversionResult]:
    """Convert PDF to markdown using docling.

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save markdown file
        ocr_options: Pre-configured OCR options (TesseractOcrOptions or EasyOcrOptions),
                    or None to disable OCR
        extract_figures: Enable figure/image extraction
        describe_pictures: Enable vision model annotations for images (default: False)

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

        # Configure picture description with local vision model
        if describe_pictures and extract_figures:
            pipeline_options.do_picture_description = True
            pipeline_options.picture_description_options = granite_picture_description
            logger.info("Picture description enabled with Granite Vision model")

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Convert document
        logger.info(f"Converting document: {pdf_path.name}")
        result = converter.convert(str(pdf_path))

        # Save markdown with externally referenced images
        # Images will be saved to figures/ subdirectory with relative paths
        # artifacts_dir should be relative to the markdown file location
        result.document.save_as_markdown(
            markdown_path,
            artifacts_dir=Path("figures"),
            image_mode=ImageRefMode.REFERENCED,
        )

        # Post-process to add vision model annotations
        if describe_pictures and extract_figures:
            _add_picture_annotations(markdown_path, result)

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
