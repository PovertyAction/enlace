"""VLM-based table extraction using Granite-Docling and Claude.

This module implements a two-pass VLM strategy for extracting tables from
research papers with high accuracy:

Pass 1: Granite-Docling-258M (fast, local, structured extraction)
Pass 2: Claude 3.5 Sonnet (optional, validation and cleanup)
"""

import logging
from pathlib import Path
from typing import Any

from enlace.core.config import ExtractionConfig
from enlace.exceptions import ExtractionError

logger = logging.getLogger("enlace.core.vlm_extractor")


class GraniteVLMExtractor:
    """Extract tables using Granite-Docling VLM."""

    def __init__(self, config: ExtractionConfig):
        """Initialize Granite-Docling VLM extractor.

        Args:
            config: Extraction configuration with VLM settings

        """
        self.config = config
        self.converter = None

        # Lazy-load docling VLM components
        self._docling_imported = False

    def _initialize_vlm_pipeline(self):
        """Initialize docling VLM pipeline with Granite-Docling."""
        if self._docling_imported:
            return

        try:
            from docling.datamodel import vlm_model_specs
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import VlmPipelineOptions
            from docling.document_converter import (
                DocumentConverter,
                PdfFormatOption,
            )
            from docling.pipeline.vlm_pipeline import VlmPipeline

            # Store imports for later use
            self._vlm_imports = {
                "vlm_model_specs": vlm_model_specs,
                "InputFormat": InputFormat,
                "VlmPipelineOptions": VlmPipelineOptions,
                "DocumentConverter": DocumentConverter,
                "PdfFormatOption": PdfFormatOption,
                "VlmPipeline": VlmPipeline,
            }

            # Determine VLM model spec based on config
            vlm_spec = self._get_vlm_model_spec()

            # Create pipeline options
            pipeline_options = VlmPipelineOptions(vlm_options=vlm_spec)

            # Create document converter with VLM pipeline
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_cls=VlmPipeline,
                        pipeline_options=pipeline_options,
                    ),
                }
            )

            self._docling_imported = True
            logger.info(
                f"Granite VLM pipeline initialized: "
                f"framework={self.config.vlm_framework}, "
                f"model={self.config.vlm_model}"
            )

        except ImportError as e:
            raise ExtractionError(
                "Failed to import docling VLM components. "
                "Install with: pip install 'docling[vlm]'"
            ) from e

    def _get_vlm_model_spec(self):
        """Get VLM model specification based on config.

        Returns:
            VLM model spec for docling pipeline

        """
        vlm_model_specs = self._vlm_imports["vlm_model_specs"]

        # Determine framework (auto, transformers, or mlx)
        framework = self.config.vlm_framework.lower()

        if framework == "auto":
            # Auto-detect: use MLX on macOS if available, otherwise Transformers
            import platform

            if platform.system() == "Darwin":  # macOS
                try:
                    import mlx  # noqa: F401

                    logger.info("Auto-detected macOS with MLX support")
                    return vlm_model_specs.GRANITEDOCLING_MLX
                except ImportError:
                    logger.info("MLX not available, falling back to Transformers")
                    return vlm_model_specs.GRANITEDOCLING_TRANSFORMERS
            else:
                logger.info("Using Transformers framework on non-macOS platform")
                return vlm_model_specs.GRANITEDOCLING_TRANSFORMERS

        elif framework == "mlx":
            return vlm_model_specs.GRANITEDOCLING_MLX

        elif framework == "transformers":
            return vlm_model_specs.GRANITEDOCLING_TRANSFORMERS

        else:
            logger.warning(
                f"Unknown VLM framework '{framework}', defaulting to Transformers"
            )
            return vlm_model_specs.GRANITEDOCLING_TRANSFORMERS

    def extract_from_pdf(self, pdf_path: Path) -> dict[str, Any]:
        """Extract tables from PDF using Granite-Docling VLM.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with extracted tables in DocTags format

        Raises:
            ExtractionError: If VLM extraction fails

        """
        if not self._docling_imported:
            self._initialize_vlm_pipeline()

        try:
            logger.info(f"Starting Granite VLM extraction: {pdf_path.name}")

            # Convert PDF with VLM pipeline
            result = self.converter.convert(source=str(pdf_path))
            doc = result.document

            # Export to multiple formats for analysis
            extraction_result = {
                "markdown": doc.export_to_markdown(),
                "tables": [],
                "metadata": {
                    "source_file": pdf_path.name,
                    "vlm_backend": "granite-docling",
                    "vlm_framework": self.config.vlm_framework,
                },
            }

            # Extract structured table data from DocTags
            for i, table in enumerate(doc.tables):
                table_data = self._parse_docling_table(table, i)
                if table_data:
                    extraction_result["tables"].append(table_data)

            logger.info(
                f"Granite VLM extraction complete: {len(extraction_result['tables'])} tables"
            )

            return extraction_result

        except Exception as e:
            logger.error(f"Granite VLM extraction failed: {e}", exc_info=True)
            raise ExtractionError(f"VLM extraction failed for {pdf_path.name}") from e

    def _parse_docling_table(self, table, table_index: int) -> dict[str, Any] | None:
        """Parse docling table object into structured format.

        Args:
            table: Docling table object
            table_index: Index of table in document

        Returns:
            Dictionary with structured table data, or None if parsing fails

        """
        try:
            table_data = {
                "table_index": table_index,
                "caption": None,
                "page_number": None,
                "rows": [],
                "num_rows": 0,
                "num_cols": 0,
            }

            # Extract caption
            if hasattr(table, "caption") and table.caption:
                caption_text = (
                    table.caption.text
                    if hasattr(table.caption, "text")
                    else str(table.caption)
                )
                # Filter out docling internal references
                if not caption_text.startswith("#/"):
                    table_data["caption"] = caption_text

            # Extract page number
            if (
                hasattr(table, "prov")
                and table.prov
                and hasattr(table.prov[0], "page_no")
            ):
                table_data["page_number"] = table.prov[0].page_no

            # Extract table grid data
            if hasattr(table, "data") and hasattr(table.data, "grid"):
                for row in table.data.grid:
                    row_data = []
                    for cell in row:
                        cell_text = cell.text.strip() if hasattr(cell, "text") else ""
                        row_data.append(cell_text)
                    table_data["rows"].append(row_data)

                table_data["num_rows"] = len(table.data.grid)
                table_data["num_cols"] = (
                    len(table.data.grid[0]) if table.data.grid else 0
                )

            return table_data if table_data["rows"] else None

        except Exception as e:
            logger.warning(f"Failed to parse table {table_index}: {e}")
            return None


class ClaudeCleanupExtractor:
    """Validate and clean VLM extractions using Claude 3.5 Sonnet."""

    def __init__(self, config: ExtractionConfig):
        """Initialize Claude cleanup extractor.

        Args:
            config: Extraction configuration with Claude settings

        """
        self.config = config
        self.client = None

        # Lazy-load Anthropic client
        self._anthropic_imported = False

    def _initialize_claude_client(self):
        """Initialize Anthropic Claude client."""
        if self._anthropic_imported:
            return

        try:
            import anthropic

            api_key = self.config.claude_api_key
            if not api_key:
                raise ExtractionError(
                    "Claude API key not found. Set ENLACE_CLAUDE_API_KEY environment variable."
                )

            self.client = anthropic.Anthropic(api_key=api_key)
            self._anthropic_imported = True

            logger.info(
                f"Claude cleanup client initialized: {self.config.claude_model}"
            )

        except ImportError as e:
            raise ExtractionError(
                "Failed to import anthropic package. "
                "Install with: pip install anthropic"
            ) from e

    async def cleanup_extraction(
        self,
        granite_extraction: dict[str, Any],
        pdf_path: Path,
        paper_text: str,
    ) -> dict[str, Any]:
        """Validate and clean Granite extraction using Claude.

        Args:
            granite_extraction: Extraction result from Granite-Docling
            pdf_path: Path to PDF file for visual context
            paper_text: Full paper text for cross-validation

        Returns:
            Cleaned and validated extraction result

        Raises:
            ExtractionError: If Claude cleanup fails

        """
        if not self._anthropic_imported:
            self._initialize_claude_client()

        # TODO: Implement Claude cleanup pass in Phase 9.2.3
        logger.warning("Claude cleanup pass not yet implemented (Phase 9.2.3)")
        return granite_extraction
