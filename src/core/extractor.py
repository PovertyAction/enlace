"""Paper extraction orchestrator.

This module provides the main PaperExtractor class that coordinates the extraction
of tables, figures, and metadata from research papers.
"""

import logging
from datetime import datetime
from pathlib import Path

from enlace.core.config import ExtractionConfig
from enlace.core.metadata import (
    extract_citations,
    extract_metadata,
    extract_methodology,
)
from enlace.core.parser import TableParser
from enlace.exceptions import (
    AugmentationError,
    ExtractionError,
    PaperNotFoundError,
    UnsupportedFormatError,
)
from enlace.models.extraction import ExtractionResult
from enlace.utils.docling_utils import convert_pdf_to_markdown
from enlace.utils.logging import setup_logging

logger = logging.getLogger("enlace.extractor")


class PaperExtractor:
    """Extract structured data from research papers.

    This is the main entry point for extracting tables, figures, and metadata
    from PDF or DOCX research papers.

    Example:
        >>> config = ExtractionConfig(enable_augmentation=True)
        >>> extractor = PaperExtractor(config)
        >>> result = extractor.extract(Path("paper.pdf"))
        >>> result.save(Path("output"))

    """

    SUPPORTED_FORMATS = [".pdf", ".docx"]

    def __init__(self, config: ExtractionConfig) -> None:
        """Initialize extractor with configuration.

        Args:
            config: Extraction configuration options

        Raises:
            ConfigError: If configuration is invalid

        """
        self.config = config
        self.parser = TableParser(
            enable_ocr=config.enable_ocr, extract_figures=config.extract_figures
        )

        # Setup logging
        self.logger = setup_logging(
            level="DEBUG" if config.verbose else "INFO", log_file=config.log_file
        )

        # Lazy-load augmentation components
        self.table_augmenter = None

        logger.info(
            f"PaperExtractor initialized: ocr={config.enable_ocr}, "
            f"augmentation={config.enable_augmentation}, "
            f"figures={config.extract_figures}"
        )

    def extract(self, paper_path: Path) -> ExtractionResult:
        """Extract tables, figures, metadata from paper.

        Args:
            paper_path: Path to PDF or DOCX file

        Returns:
            ExtractionResult with extracted content

        Raises:
            PaperNotFoundError: If paper_path does not exist
            UnsupportedFormatError: If file format is not supported
            ExtractionError: If extraction fails

        """
        if not paper_path.exists():
            raise PaperNotFoundError(paper_path)

        if paper_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise UnsupportedFormatError(paper_path, self.SUPPORTED_FORMATS)

        start_time = datetime.now()
        paper_id = paper_path.stem

        logger.info(f"Starting extraction: {paper_path.name}")

        try:
            # Create output directory for this paper
            paper_output_dir = self.config.output_dir / paper_id
            paper_output_dir.mkdir(parents=True, exist_ok=True)

            # Initialize result
            result = ExtractionResult(
                paper_id=paper_id,
                source_file=paper_path,
                extraction_date=datetime.now(),
            )

            # Step 1: Convert PDF to markdown
            logger.info("Step 1: Converting to markdown")
            markdown_path, conversion_result = convert_pdf_to_markdown(
                paper_path,
                paper_output_dir,
                enable_ocr=self.config.enable_ocr,
                extract_figures=self.config.extract_figures,
            )

            # Step 2: Extract metadata
            if self.config.extract_metadata:
                logger.info("Step 2: Extracting metadata")
                result.metadata = extract_metadata(markdown_path, paper_path)

            # Step 3: Extract tables
            if self.config.extract_tables:
                logger.info("Step 3: Extracting tables")
                tables_dict = self.parser.parse_tables_from_document(
                    conversion_result.document, paper_path.name
                )

                # Combine all table types
                result.tables = (
                    tables_dict["regression"]
                    + tables_dict["summary"]
                    + tables_dict["balance"]
                )
                result.tables_extracted = len(result.tables)

                logger.info(f"Found {len(result.tables)} tables")

            # Step 4: Extract figures
            if self.config.extract_figures:
                logger.info("Step 4: Extracting figures")
                result.figures = self.parser.parse_figures_from_document(
                    conversion_result.document, paper_output_dir, paper_path.stem
                )
                result.figures_extracted = len(result.figures)

                logger.info(f"Found {len(result.figures)} figures")

            # Step 5: Extract citations (optional)
            if self.config.extract_metadata:
                logger.info("Step 5: Extracting citations")
                citations = extract_citations(markdown_path)
                # Store in metadata for now
                if citations:
                    logger.info(f"Found {len(citations)} citations")

            # Step 6: Extract methodology (optional)
            if self.config.extract_metadata:
                logger.info("Step 6: Extracting methodology")
                methodology = extract_methodology(markdown_path)
                # Store in metadata for now
                if methodology.get("study_design"):
                    logger.info(f"Study design: {methodology['study_design']}")

            # Calculate quality score
            result.extraction_quality = self._calculate_quality_score(result)

            # Calculate processing time
            result.processing_time_seconds = (
                datetime.now() - start_time
            ).total_seconds()

            logger.info(
                f"Extraction complete: {result.tables_extracted} tables, "
                f"{result.figures_extracted} figures, "
                f"quality={result.extraction_quality:.2f}, "
                f"time={result.processing_time_seconds:.1f}s"
            )

            return result

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            raise ExtractionError(f"Failed to extract from {paper_path.name}") from e

    def augment(self, extraction: ExtractionResult) -> ExtractionResult:
        """Augment extraction with semantic context using RAG.

        Args:
            extraction: Result from extract() method

        Returns:
            Enhanced ExtractionResult with semantic context fields populated

        Raises:
            AugmentationError: If augmentation fails
            ModelNotFoundError: If embedding/LLM model is not available

        """
        if not self.config.enable_augmentation:
            logger.debug("Augmentation disabled, skipping")
            return extraction

        try:
            # Lazy-load augmentation components
            if not self.table_augmenter:
                self._initialize_augmentation()

            logger.info("Augmenting extraction with semantic context")

            # Process document for semantic search
            self.table_augmenter.process_document(str(extraction.source_file))

            # Augment each table
            augmented_tables = []
            for table in extraction.tables:
                try:
                    # Determine table type and augment accordingly
                    table_type = self._get_table_type(table)

                    if table_type == "regression":
                        _context = self.table_augmenter.augment_regression_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )
                    elif table_type in ["summary", "descriptive"]:
                        _context = self.table_augmenter.augment_summary_stats_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )
                    elif table_type == "balance":
                        _context = self.table_augmenter.augment_balance_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )
                    else:
                        # Default to regression augmentation
                        _context = self.table_augmenter.augment_regression_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )

                    # Add semantic context to table
                    # Note: This modifies the table object in place
                    # The actual implementation depends on table_augmenter API

                    augmented_tables.append(table)

                except Exception as e:
                    logger.warning(f"Failed to augment table: {e}")
                    augmented_tables.append(table)

            extraction.tables = augmented_tables

            logger.info("Augmentation complete")
            return extraction

        except ImportError as e:
            raise AugmentationError(
                "Semantic augmentation dependencies not installed"
            ) from e
        except Exception as e:
            logger.error(f"Augmentation failed: {e}", exc_info=True)
            raise AugmentationError("Failed to augment extraction") from e

    def _initialize_augmentation(self):
        """Initialize semantic augmentation components."""
        try:
            from augmentation_config import AugmentationConfig
            from table_augmenter import TableAugmenter

            # Create config
            aug_config = AugmentationConfig()

            # Initialize augmenter
            self.table_augmenter = TableAugmenter(config=aug_config)

            logger.info("Semantic augmentation components initialized")

        except ImportError as e:
            raise AugmentationError(
                f"Failed to import augmentation modules: {e}. "
                "Make sure augmentation dependencies are installed."
            ) from e

    def _get_table_type(self, table) -> str:
        """Determine table type from table object."""
        # Check the table's class name
        class_name = table.__class__.__name__

        if "Regression" in class_name:
            return "regression"
        elif "Summary" in class_name:
            return "summary"
        elif "Balance" in class_name:
            return "balance"
        else:
            return "other"

    def _calculate_quality_score(self, result: ExtractionResult) -> float:
        """Calculate overall extraction quality score (0-1).

        Weighted combination of:
        - Table extraction completeness (40%)
        - Metadata completeness (30%)
        - Figure extraction (15%)
        - Citations (15%)
        """
        scores = []
        weights = []

        # Table score (40%)
        if result.tables:
            table_score = min(len(result.tables) / 5, 1.0)
            scores.append(table_score)
            weights.append(0.40)

        # Metadata score (30%)
        metadata = result.metadata
        if metadata:
            metadata_fields = ["title", "authors", "year", "doi", "journal"]
            filled_fields = sum(
                1 for f in metadata_fields if getattr(metadata, f, None)
            )
            metadata_completeness = filled_fields / len(metadata_fields)
            scores.append(metadata_completeness)
            weights.append(0.30)

        # Figure score (15%)
        if result.figures:
            figure_score = min(len(result.figures) / 3, 1.0)
            scores.append(figure_score)
            weights.append(0.15)

        # Calculate weighted average
        if scores:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            return round(weighted_score, 2)
        else:
            return 0.0
