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
from enlace.core.reconciler import TableReconciler
from enlace.exceptions import (
    AugmentationError,
    ExtractionError,
    PaperNotFoundError,
    UnsupportedFormatError,
)
from enlace.extractors.camelot_extractor import CamelotExtractor, is_text_based_pdf
from enlace.models.dual_extraction import ConversionMetadata
from enlace.models.extraction import ExtractionResult
from enlace.utils.docling_utils import convert_pdf_to_markdown
from enlace.utils.docx_converter import DocxToPdfConverter, is_docx_file
from enlace.utils.ocr_backends import OCRBackendManager

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
            enable_ocr=config.enable_ocr,
            extract_figures=config.extract_figures,
            config=config,  # Pass config for VLM settings
        )

        # Initialize OCR backend manager
        self.ocr_manager = OCRBackendManager(config) if config.enable_ocr else None

        # Lazy-load augmentation components
        self.table_augmenter = None

        # Initialize Camelot components if enabled
        self.camelot_extractor = None
        self.reconciler = None
        self.docx_converter = None

        if config.enable_camelot:
            try:
                self.camelot_extractor = CamelotExtractor(
                    lattice_line_scale=config.camelot_lattice_line_scale,
                    stream_edge_tol=config.camelot_stream_edge_tol,
                    quality_threshold=config.camelot_quality_threshold,
                    min_table_size=config.camelot_min_table_size,
                    min_content_density=config.camelot_min_content_density,
                )
                self.reconciler = TableReconciler(
                    match_threshold=config.reconciliation_match_threshold,
                    reconciliation_strategy=config.reconciliation_strategy,
                )
                logger.info("Camelot dual extraction enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Camelot: {e}")
                config.enable_camelot = False

        # Initialize DOCX converter if needed
        try:
            self.docx_converter = DocxToPdfConverter(
                libreoffice_path=config.libreoffice_path
            )
        except Exception as e:
            logger.warning(f"LibreOffice not available: {e}")
            self.docx_converter = None

        logger.info(
            f"PaperExtractor initialized: ocr={config.enable_ocr}, "
            f"ocr_backend={config.ocr_backend if config.enable_ocr else 'none'}, "
            f"augmentation={config.enable_augmentation}, "
            f"figures={config.extract_figures}, "
            f"camelot={config.enable_camelot}"
        )

    def extract(
        self,
        paper_path: Path,
        cli_command: str | None = None,
        config_dict: dict | None = None,
    ) -> ExtractionResult:
        """Extract tables, figures, metadata from paper.

        Args:
            paper_path: Path to PDF or DOCX file
            cli_command: CLI command used for extraction (for reproducibility)
            config_dict: Configuration dict used (for reproducibility)

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

            # Get enlace version
            try:
                from importlib.metadata import version

                enlace_version = version("enlace")
            except Exception:
                enlace_version = "unknown"

            # Initialize result with extraction metadata
            from enlace.models.extraction import ExtractionMetadata

            result = ExtractionResult(
                paper_id=paper_id,
                source_file=paper_path,
                extraction_date=datetime.now(),
                extraction_metadata=ExtractionMetadata(
                    enlace_version=enlace_version,
                    extraction_date=datetime.now(),
                    command=cli_command,
                    config=config_dict or {},
                ),
            )

            # Step 0: Convert DOCX/DOC to PDF if needed
            pdf_path = paper_path

            if is_docx_file(paper_path):
                if self.docx_converter is None:
                    raise ExtractionError(
                        "DOCX file provided but LibreOffice is not available. "
                        "Please install LibreOffice to convert DOCX/DOC files."
                    )

                logger.info("Step 0: Converting DOCX to PDF")
                pdf_path, conv_meta = self.docx_converter.convert_to_pdf(
                    paper_path,
                    output_dir=paper_output_dir,
                    keep_pdf=self.config.keep_converted_pdfs,
                )

                result.docx_converted = True
                result.conversion_metadata = ConversionMetadata(**conv_meta)

                logger.info(
                    f"DOCX converted: {pdf_path.name} "
                    f"({conv_meta['conversion_time']:.2f}s)"
                )

            # Step 1: Convert PDF to markdown
            logger.info("Step 1: Converting to markdown")

            # Get OCR options from backend manager
            ocr_options = None
            if self.ocr_manager:
                ocr_options = self.ocr_manager.create_primary_ocr_options()
                logger.info(
                    f"Using OCR backend: {self.ocr_manager.get_backend_name(self.ocr_manager.primary_backend)}"
                )

            markdown_path, conversion_result = convert_pdf_to_markdown(
                pdf_path,  # Use converted PDF if DOCX was provided
                paper_output_dir,
                ocr_options=ocr_options,
                extract_figures=self.config.extract_figures,
                describe_pictures=self.config.describe_pictures,
            )

            # Step 2: Extract metadata
            if self.config.extract_metadata:
                logger.info("Step 2: Extracting metadata")
                result.metadata = extract_metadata(markdown_path, paper_path)

            # Step 3: Extract tables
            if self.config.extract_tables:
                logger.info("Step 3: Extracting tables")

                # Extract docling tables only if explicitly enabled
                docling_tables = []
                if self.config.enable_docling_tables:
                    tables_dict = self.parser.parse_tables_from_document(
                        conversion_result.document, paper_path.name
                    )

                    # Combine all table types
                    docling_tables = (
                        tables_dict["regression"]
                        + tables_dict["summary"]
                        + tables_dict["balance"]
                    )
                    logger.info(f"Found {len(docling_tables)} docling tables")

                # Step 3.5: Camelot table extraction (default)
                if self.config.enable_camelot and self.camelot_extractor:
                    # Check if PDF is text-based (Camelot requirement)
                    if is_text_based_pdf(pdf_path):
                        if docling_tables:
                            logger.info(
                                "Step 3.5: Running Camelot dual extraction with docling"
                            )
                        else:
                            logger.info(
                                "Step 3.5: Running Camelot table extraction (Camelot-only mode)"
                            )

                        try:
                            # Extract tables with Camelot
                            camelot_tables = self.camelot_extractor.extract_tables(
                                pdf_path
                            )

                            if camelot_tables:
                                logger.info(
                                    f"Camelot found {len(camelot_tables)} tables"
                                )

                                # Handle both Camelot-only and dual extraction modes
                                if docling_tables:
                                    # Dual extraction mode: reconcile docling + Camelot
                                    matched_pairs = self.reconciler.match_tables(
                                        docling_tables, camelot_tables
                                    )

                                    logger.info(
                                        f"Matched {len(matched_pairs)} of {len(docling_tables)} docling tables with Camelot"
                                    )

                                    # Create lookup for matched tables
                                    matched_docling = {
                                        id(d): c for d, c in matched_pairs
                                    }
                                    matched_camelot_ids = {
                                        id(c) for _, c in matched_pairs
                                    }

                                    # Process ALL docling tables (with or without Camelot match)
                                    dual_tables = []
                                    for docling_table in docling_tables:
                                        camelot_table = matched_docling.get(
                                            id(docling_table)
                                        )

                                        if camelot_table:
                                            # Matched pair - merge tables
                                            dual_table = self.reconciler.merge_tables(
                                                docling_table, camelot_table
                                            )
                                        else:
                                            # No Camelot match - create dual table with only docling
                                            dual_table = self.reconciler.merge_tables(
                                                docling_table, None
                                            )

                                        dual_tables.append(dual_table)

                                    # Find unmatched high-quality Camelot tables
                                    unmatched_camelot = [
                                        ct
                                        for ct in camelot_tables
                                        if id(ct) not in matched_camelot_ids
                                        and ct.accuracy >= 70
                                    ]

                                    if unmatched_camelot:
                                        logger.info(
                                            f"Found {len(unmatched_camelot)} high-quality unmatched Camelot tables"
                                        )
                                        # Add Camelot-only tables
                                        for camelot_table in unmatched_camelot:
                                            dual_table = self.reconciler.merge_tables(
                                                None, camelot_table
                                            )
                                            dual_tables.append(dual_table)

                                    # Sort dual tables by page number
                                    def get_page_number(dt):
                                        """Extract page number from dual extraction table."""
                                        if (
                                            dt.camelot_quality
                                            and "page" in dt.camelot_quality
                                        ):
                                            return dt.camelot_quality["page"]
                                        if dt.docling_table and hasattr(
                                            dt.docling_table, "page_number"
                                        ):
                                            page_num = dt.docling_table.page_number
                                            if page_num is not None:
                                                return page_num
                                        return 999

                                    dual_tables.sort(key=get_page_number)

                                    # Store dual extraction results
                                    result.dual_extraction_tables = dual_tables
                                    result.camelot_enabled = True
                                    result.tables = [
                                        dt.reconciled_table for dt in dual_tables
                                    ]
                                    result.tables_extracted = len(result.tables)

                                    # Calculate statistics
                                    matched_count = len(matched_pairs)
                                    docling_only = len(docling_tables) - matched_count
                                    camelot_only = len(unmatched_camelot)

                                    if matched_count > 0:
                                        avg_agreement = (
                                            sum(
                                                dt.reconciliation_metadata.agreement_rate
                                                for dt in dual_tables
                                                if dt.reconciliation_metadata.cells_total
                                                > 0
                                            )
                                            / matched_count
                                        )
                                        agreement_str = (
                                            f"{avg_agreement:.1%} avg agreement"
                                        )
                                    else:
                                        agreement_str = "no matches"

                                    logger.info(
                                        f"Dual extraction complete: {len(dual_tables)} total tables "
                                        f"({matched_count} matched, {docling_only} docling-only, "
                                        f"{camelot_only} camelot-only, {agreement_str})"
                                    )
                                else:
                                    # Camelot-only mode: no reconciliation needed
                                    dual_tables = []
                                    for camelot_table in camelot_tables:
                                        if camelot_table.accuracy >= 70:
                                            dual_table = self.reconciler.merge_tables(
                                                None, camelot_table
                                            )
                                            dual_tables.append(dual_table)

                                    # Sort by page number
                                    dual_tables.sort(
                                        key=lambda dt: dt.camelot_quality.get(
                                            "page", 999
                                        )
                                    )

                                    # Store Camelot-only results
                                    result.dual_extraction_tables = dual_tables
                                    result.camelot_enabled = True
                                    result.tables = [
                                        dt.reconciled_table for dt in dual_tables
                                    ]
                                    result.tables_extracted = len(result.tables)

                                    logger.info(
                                        f"Camelot-only extraction: {len(dual_tables)} tables extracted"
                                    )
                            else:
                                logger.info("Camelot did not find any tables")
                                if not docling_tables:
                                    result.tables = []
                                    result.tables_extracted = 0

                        except Exception as e:
                            logger.error(
                                f"Camelot extraction failed: {e}", exc_info=True
                            )
                            if docling_tables:
                                logger.warning(
                                    "Falling back to docling-only extraction"
                                )
                                result.tables = docling_tables
                                result.tables_extracted = len(docling_tables)
                            else:
                                logger.error(
                                    "No fallback available - both Camelot and docling failed"
                                )
                                result.tables = []
                                result.tables_extracted = 0
                    else:
                        logger.info(
                            "PDF appears to be scanned/image-based. "
                            "Skipping Camelot extraction (text-based PDFs only)"
                        )
                        # Use docling tables if available
                        if docling_tables:
                            result.tables = docling_tables
                            result.tables_extracted = len(docling_tables)
                else:
                    # Camelot disabled - use docling tables if available
                    if docling_tables:
                        result.tables = docling_tables
                        result.tables_extracted = len(docling_tables)
                        logger.info(
                            f"Using docling tables only: {len(docling_tables)} tables"
                        )
                    else:
                        result.tables = []
                        result.tables_extracted = 0
                        logger.warning("No table extraction method enabled")

            # Step 4: Extract figures
            if self.config.extract_figures:
                logger.info("Step 4: Extracting figures")
                result.figures = self.parser.parse_figures_from_document(
                    conversion_result.document, paper_output_dir, paper_path.stem
                )
                result.figures_extracted = len(result.figures)

                # Fix markdown references: replace hashed image names with sequential figure_*.png
                figures_dir = paper_output_dir / "figures"
                if figures_dir.exists() and markdown_path.exists():
                    # Get all image_*.png files sorted by name
                    hashed_images = sorted(figures_dir.glob("image_*.png"))

                    if hashed_images:
                        # Read markdown content
                        markdown_content = markdown_path.read_text()

                        # Replace each hashed image reference with sequential figure number
                        for idx, img_file in enumerate(hashed_images, start=1):
                            old_ref = f"figures/{img_file.name}"
                            new_ref = f"figures/figure_{idx}.png"
                            markdown_content = markdown_content.replace(
                                old_ref, new_ref
                            )
                            logger.debug(
                                f"Replaced {img_file.name} with figure_{idx}.png in markdown"
                            )

                        # Write updated markdown
                        markdown_path.write_text(markdown_content)

                        # Now remove the hashed images
                        for img_file in hashed_images:
                            try:
                                img_file.unlink()
                                logger.debug(
                                    f"Removed duplicate image: {img_file.name}"
                                )
                            except Exception as e:
                                logger.warning(f"Could not remove {img_file.name}: {e}")

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
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time_seconds = processing_time
            result.extraction_metadata.processing_time_seconds = processing_time

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

    async def augment(self, extraction: ExtractionResult) -> ExtractionResult:
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
            await self.table_augmenter.process_document(str(extraction.source_file))

            # Augment each table
            augmented_tables = []
            for table in extraction.tables:
                try:
                    # Determine table type and augment accordingly
                    table_type = self._get_table_type(table)

                    if table_type == "regression":
                        context = await self.table_augmenter.augment_regression_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )
                    elif table_type in ["summary", "descriptive"]:
                        context = (
                            await self.table_augmenter.augment_summary_stats_table(
                                table,
                                table.table_number or "unknown",
                                str(extraction.source_file),
                            )
                        )
                    elif table_type == "balance":
                        context = await self.table_augmenter.augment_balance_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )
                    else:
                        # Default to regression augmentation
                        context = await self.table_augmenter.augment_regression_table(
                            table,
                            table.table_number or "unknown",
                            str(extraction.source_file),
                        )

                    # Apply semantic context to table object
                    self._apply_augmentation_context(table, context)

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
            from enlace.augmentation_config import AugmentationConfig
            from enlace.table_augmenter import TableAugmenter

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

    def _apply_augmentation_context(self, table, context):
        """Apply TableContext to table object.

        Modifies table in place by adding semantic context fields.

        Args:
            table: RegressionTable, SummaryStatisticsTable, or BalanceTable
            context: TableContext object from augmentation

        """
        # Apply top-level context fields
        if hasattr(table, "study_context"):
            table.study_context = (
                context.study_context.model_dump() if context.study_context else None
            )

        if hasattr(table, "treatment_contexts"):
            table.treatment_contexts = [
                tc.model_dump() for tc in context.treatment_contexts
            ]

        if hasattr(table, "methods_context"):
            table.methods_context = (
                context.methods_context.model_dump()
                if context.methods_context
                else None
            )

        # Apply variable-level contexts to coefficients/variables
        if hasattr(table, "models"):
            # Regression table: apply to coefficients
            for model in table.models:
                if hasattr(model, "outcome_context") and context.outcome_contexts:
                    # Apply outcome context from dependent variable
                    dep_var = model.dependent_variable
                    if dep_var and dep_var in context.outcome_contexts:
                        model.outcome_context = context.outcome_contexts[
                            dep_var
                        ].model_dump()

                if hasattr(model, "coefficients"):
                    for coef in model.coefficients:
                        var_name = coef.variable_name
                        if var_name in context.variable_contexts:
                            var_ctx = context.variable_contexts[var_name]
                            coef.variable_context = var_ctx.model_dump()

                            # Add validation if available
                            if hasattr(var_ctx, "validation") and var_ctx.validation:
                                coef.validation = var_ctx.validation

        elif hasattr(table, "statistics"):
            # Summary stats table: apply to statistics
            for stat in table.statistics:
                var_name = stat.variable_name
                if var_name in context.variable_contexts:
                    var_ctx = context.variable_contexts[var_name]
                    if hasattr(stat, "variable_context"):
                        stat.variable_context = var_ctx.model_dump()

        elif hasattr(table, "comparisons"):
            # Balance table: apply to comparisons
            for comp in table.comparisons:
                var_name = comp.variable_name
                if var_name in context.variable_contexts:
                    var_ctx = context.variable_contexts[var_name]
                    if hasattr(comp, "variable_context"):
                        comp.variable_context = var_ctx.model_dump()

        logger.debug(
            f"Applied augmentation context to table: "
            f"{len(context.variable_contexts)} variables, "
            f"{len(context.outcome_contexts)} outcomes"
        )

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
