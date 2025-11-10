"""Table and figure parsing from research papers.

This module provides the TableParser class for extracting and parsing tables
and figures from academic papers using docling.
"""

import logging
import re
from pathlib import Path
from typing import Any

from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling_core.types.doc import DoclingDocument, PictureItem, TableCell

from enlace.models.figures import Figure
from enlace.models.tables import (
    BalanceStatistic,
    BalanceTable,
    RegressionCoefficient,
    RegressionModel,
    RegressionTable,
    SummaryStatistic,
    SummaryStatisticsTable,
)

logger = logging.getLogger("enlace.core.parser")


class TableParser:
    """Parse structured tables and figures from research papers."""

    def __init__(
        self,
        enable_ocr: bool = False,
        extract_figures: bool = True,
        config=None,
    ):
        """Initialize table parser.

        Args:
            enable_ocr: Enable OCR for scanned documents
            extract_figures: Extract figures/images from documents
            config: Optional ExtractionConfig for VLM settings

        """
        self.enable_ocr = enable_ocr
        self.extract_figures = extract_figures
        self.config = config

        # VLM extractor (lazy-loaded)
        self.vlm_extractor = None

        # Configure docling converter
        table_structure_options = TableStructureOptions(do_cell_matching=True)
        pdf_pipeline_options = PdfPipelineOptions(
            do_table_structure=True,
            do_ocr=enable_ocr,
            table_structure_options=table_structure_options,
            generate_page_images=extract_figures,
            generate_picture_images=extract_figures,
            images_scale=2.0,
        )

        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(pipeline_options=pdf_pipeline_options)
            }
        )

    def parse_tables_from_document(
        self, doc: DoclingDocument, source_file: str
    ) -> dict[str, list]:
        """Parse all tables from a docling document.

        Args:
            doc: Docling document with tables
            source_file: Name of source file for metadata

        Returns:
            Dictionary with lists of regression, summary, and balance tables

        """
        regression_tables = []
        summary_tables = []
        balance_tables = []

        for i, table in enumerate(doc.tables):
            # Get table structure
            structure = self._get_table_structure(table)
            rows = structure["data"]
            caption = structure["caption"]
            page_no = structure["page"]

            # Analyze OCR confidence
            ocr_analysis = self._analyze_ocr_confidence(structure)
            if ocr_analysis["has_confidence_data"]:
                logger.debug(
                    f"Table {i + 1} OCR confidence: "
                    f"avg={ocr_analysis['avg_confidence']:.2f if ocr_analysis['avg_confidence'] else 'N/A'}, "
                    f"low_conf_cells={ocr_analysis['low_confidence_cells']}/{ocr_analysis['total_cells']}"
                )
                if ocr_analysis["needs_fallback"]:
                    logger.warning(
                        f"Table {i + 1} has {ocr_analysis['low_confidence_cells']} low-confidence cells "
                        "(>20% of total) - may benefit from fallback OCR"
                    )

            # Get context text before table
            context = self._get_text_before_table(doc, table)

            # Classify and parse table
            if self._is_balance_table(rows, caption):
                balance_table = self._parse_balance_table(
                    rows, caption, page_no, source_file, i + 1, context
                )
                if balance_table and balance_table.comparisons:
                    balance_tables.append(balance_table)

            elif self._is_summary_stats_table(rows, caption):
                summary_table = self._parse_summary_stats_table(
                    rows, caption, page_no, source_file, i + 1, context
                )
                if summary_table and summary_table.statistics:
                    summary_tables.append(summary_table)

            elif self._is_regression_table(rows, caption):
                regression_table = self._parse_regression_table(
                    rows, caption, page_no, source_file, i + 1, context
                )
                if regression_table and regression_table.models:
                    regression_tables.append(regression_table)

        logger.info(
            f"Parsed {len(regression_tables)} regression, "
            f"{len(summary_tables)} summary, {len(balance_tables)} balance tables"
        )

        return {
            "regression": regression_tables,
            "summary": summary_tables,
            "balance": balance_tables,
        }

    def parse_figures_from_document(
        self, doc: DoclingDocument, output_dir: Path, file_stem: str
    ) -> list[Figure]:
        """Extract figures from docling document.

        Args:
            doc: Docling document with pictures
            output_dir: Directory to save figure images
            file_stem: Base filename for saved files

        Returns:
            List of Figure objects with metadata

        """
        if not self.extract_figures:
            return []

        figures = []
        figures_dir = output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)

        figure_num = 1
        for element, _level in doc.iterate_items():
            if not isinstance(element, PictureItem):
                continue

            picture = element
            figure_id = f"figure_{figure_num}"

            # Extract caption
            caption = self._extract_picture_caption(picture)

            # Extract vision model annotation if available
            annotation = None
            if hasattr(picture, "captions") and picture.captions:
                # Vision model descriptions are stored in captions
                for cap in picture.captions:
                    if hasattr(cap, "text") and cap.text:
                        annotation = cap.text.strip()
                        break

            # Extract page number
            page_no = None
            if (
                hasattr(picture, "prov")
                and picture.prov
                and hasattr(picture.prov[0], "page_no")
            ):
                page_no = picture.prov[0].page_no

            # Save image
            image_path = None
            image_width = None
            image_height = None
            quality_score = 0.0

            try:
                image = picture.get_image(doc)
                if image is not None:
                    image_filename = f"{figure_id}.png"
                    image_filepath = figures_dir / image_filename

                    with image_filepath.open("wb") as fp:
                        image.save(fp, "PNG")

                    image_path = f"figures/{image_filename}"

                    if hasattr(image, "size"):
                        image_width, image_height = image.size

                    quality_score = 1.0
                    logger.debug(
                        f"Saved {figure_id}: page {page_no}, {image_width}x{image_height}px"
                    )
            except Exception as e:
                logger.warning(f"Failed to save {figure_id}: {e}")

            # Extract figure number from caption
            figure_number = None
            if caption:
                fig_match = re.search(
                    r"(?:Figure|Fig\.?)\s+(\d+[A-Za-z]?)", caption, re.IGNORECASE
                )
                if fig_match:
                    figure_number = fig_match.group(1)

            figure = Figure(
                figure_id=figure_id,
                figure_number=figure_number,
                caption=caption if caption else None,
                page_number=page_no,
                image_path=image_path,
                image_format="png" if image_path else None,
                image_width=image_width,
                image_height=image_height,
                quality_score=quality_score,
                annotation=annotation,
            )

            figures.append(figure)
            figure_num += 1

        logger.info(f"Extracted {len(figures)} figures")
        return figures

    # ========================================================================
    # TABLE STRUCTURE EXTRACTION
    # ========================================================================

    def _get_table_structure(self, table) -> dict[str, Any]:
        """Extract table structure and metadata."""
        structure = {
            "data": [],
            "ocr_metadata": [],  # NEW: OCR metadata per cell
            "num_rows": 0,
            "num_cols": 0,
            "caption": "",
            "page": None,
        }

        # Extract table data and OCR metadata
        if hasattr(table, "data"):
            table_data = table.data
            if hasattr(table_data, "grid"):
                # Extract both data and OCR metadata
                for row in table_data.grid:
                    data_row = []
                    metadata_row = []
                    for cell in row:
                        text, metadata = self._extract_cell_value(cell)
                        data_row.append(text)
                        metadata_row.append(metadata)

                    structure["data"].append(data_row)
                    structure["ocr_metadata"].append(metadata_row)

                structure["num_rows"] = len(table_data.grid)
                structure["num_cols"] = (
                    len(table_data.grid[0]) if table_data.grid else 0
                )

        # Extract caption
        if hasattr(table, "caption") and table.caption:
            caption_text = (
                table.caption.text
                if hasattr(table.caption, "text")
                else str(table.caption)
            )
            # Filter out docling internal references
            if not caption_text.startswith("#/"):
                structure["caption"] = caption_text

        # Extract page number
        if hasattr(table, "prov") and table.prov and hasattr(table.prov[0], "page_no"):
            structure["page"] = table.prov[0].page_no

        return structure

    def _extract_cell_value(self, cell: TableCell) -> tuple[str, dict[str, Any]]:
        """Extract text and OCR metadata from table cell.

        Returns:
            Tuple of (cell_text, ocr_metadata_dict)

        """
        if cell and hasattr(cell, "text"):
            text = cell.text.strip()

            # Extract OCR confidence if available
            metadata = {
                "text": text,
                "confidence": None,
                "backend": "unknown",
            }

            # Try to get confidence from docling cell object
            # Note: Actual field names depend on docling implementation
            if hasattr(cell, "confidence"):
                metadata["confidence"] = cell.confidence
            elif hasattr(cell, "ocr_confidence"):
                metadata["confidence"] = cell.ocr_confidence

            return text, metadata

        return "", {"text": "", "confidence": None, "backend": "unknown"}

    def _analyze_ocr_confidence(
        self, table_structure: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze OCR confidence for a table structure.

        Args:
            table_structure: Table structure dict with ocr_metadata

        Returns:
            Dict with confidence analysis results

        """
        if "ocr_metadata" not in table_structure:
            return {
                "has_confidence_data": False,
                "low_confidence_cells": 0,
                "total_cells": 0,
                "avg_confidence": None,
                "needs_fallback": False,
            }

        # Analyze confidence scores
        confidences = []
        low_conf_cells = 0
        total_cells = 0

        for row_metadata in table_structure["ocr_metadata"]:
            for cell_meta in row_metadata:
                if cell_meta.get("confidence") is not None:
                    total_cells += 1
                    conf = cell_meta["confidence"]
                    confidences.append(conf)

                    # Check if below threshold
                    if hasattr(self, "config") and hasattr(
                        self.config, "ocr_confidence_threshold"
                    ):
                        threshold = self.config.ocr_confidence_threshold
                    else:
                        threshold = 0.8  # Default threshold

                    if conf < threshold:
                        low_conf_cells += 1

        # Calculate statistics
        avg_confidence = sum(confidences) / len(confidences) if confidences else None

        # Determine if fallback OCR needed (>20% low confidence cells)
        needs_fallback = False
        if total_cells > 0 and (low_conf_cells / total_cells) > 0.2:
            needs_fallback = True

        return {
            "has_confidence_data": len(confidences) > 0,
            "low_confidence_cells": low_conf_cells,
            "total_cells": total_cells,
            "avg_confidence": avg_confidence,
            "needs_fallback": needs_fallback,
        }

    def _get_text_before_table(
        self, doc: DoclingDocument, table, num_items: int = 3
    ) -> str:
        """Extract text appearing before table for context."""
        context_text = []

        for item, _level in doc.iterate_items():
            if item == table:
                break

            if hasattr(item, "text") and item.text:
                context_text.append(item.text)
                if len(context_text) > num_items:
                    context_text.pop(0)

        return " ".join(context_text) if context_text else ""

    def _calculate_table_quality(self, table) -> dict[str, Any]:
        """Calculate quality metrics for a parsed regression table.

        Args:
            table: Parsed RegressionTable object

        Returns:
            Dictionary with quality metrics:
                - null_se_rate: Proportion of missing standard errors (0.0-1.0)
                - null_coef_rate: Proportion of missing coefficients (0.0-1.0)
                - avg_ocr_confidence: Average OCR confidence if available
                - needs_vlm: Boolean indicating if VLM fallback recommended

        """
        if not hasattr(table, "models") or not table.models:
            return {
                "null_se_rate": 1.0,
                "null_coef_rate": 1.0,
                "avg_ocr_confidence": None,
                "needs_vlm": True,
            }

        total_coefficients = 0
        missing_se = 0
        missing_coef = 0
        ocr_confidences = []

        for model in table.models:
            if not hasattr(model, "coefficients"):
                continue

            for coef in model.coefficients:
                total_coefficients += 1

                # Check for missing standard error
                if coef.std_error is None:
                    missing_se += 1

                # Check for missing coefficient
                if coef.coefficient is None:
                    missing_coef += 1

                # Collect OCR confidence if available
                if hasattr(coef, "ocr_confidence") and coef.ocr_confidence is not None:
                    ocr_confidences.append(coef.ocr_confidence)

        # Calculate rates
        null_se_rate = (
            missing_se / total_coefficients if total_coefficients > 0 else 1.0
        )
        null_coef_rate = (
            missing_coef / total_coefficients if total_coefficients > 0 else 1.0
        )
        avg_ocr_confidence = (
            sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else None
        )

        # Determine if VLM fallback is needed based on config thresholds
        needs_vlm = False
        if self.config and self.config.enable_vlm:
            if null_se_rate > self.config.vlm_null_se_threshold:
                needs_vlm = True
                logger.debug(
                    f"VLM trigger: null_se_rate={null_se_rate:.2%} > "
                    f"threshold={self.config.vlm_null_se_threshold:.2%}"
                )
            elif null_coef_rate > self.config.vlm_null_coef_threshold:
                needs_vlm = True
                logger.debug(
                    f"VLM trigger: null_coef_rate={null_coef_rate:.2%} > "
                    f"threshold={self.config.vlm_null_coef_threshold:.2%}"
                )
            elif (
                avg_ocr_confidence is not None
                and avg_ocr_confidence < self.config.vlm_confidence_threshold
            ):
                needs_vlm = True
                logger.debug(
                    f"VLM trigger: avg_ocr_confidence={avg_ocr_confidence:.2f} < "
                    f"threshold={self.config.vlm_confidence_threshold:.2f}"
                )

        return {
            "null_se_rate": null_se_rate,
            "null_coef_rate": null_coef_rate,
            "avg_ocr_confidence": avg_ocr_confidence,
            "total_coefficients": total_coefficients,
            "missing_se": missing_se,
            "missing_coef": missing_coef,
            "needs_vlm": needs_vlm,
        }

    def _extract_picture_caption(self, picture: PictureItem) -> str:
        """Extract caption from picture element."""
        caption = ""

        if hasattr(picture, "caption") and picture.caption:
            if hasattr(picture.caption, "text"):
                caption = picture.caption.text.strip()
            else:
                caption = str(picture.caption).strip()

            # Filter docling internal references
            if caption.startswith("#/"):
                caption = ""

        # Fallback to self_ref
        if not caption and hasattr(picture, "self_ref"):
            ref = picture.self_ref.strip() if picture.self_ref else ""
            if ref and not ref.startswith("#/"):
                caption = ref

        return caption

    # ========================================================================
    # TABLE TYPE CLASSIFICATION
    # ========================================================================

    def _is_regression_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is regression results."""
        caption_lower = caption.lower()

        regression_keywords = [
            "regression",
            "estimation",
            "coefficient",
            "model",
            "ols",
            "logit",
            "probit",
            "iv",
            "2sls",
            "fixed effects",
        ]
        if any(kw in caption_lower for kw in regression_keywords):
            return True

        table_text = " ".join([" ".join(row) for row in rows[:10]]).lower()

        if any(
            pattern in table_text
            for pattern in [
                "dependent variable",
                "standard error",
                "robust",
                "clustered",
            ]
        ):
            return True

        return bool(re.search(r"\*{1,3}", table_text))

    def _is_summary_stats_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is summary statistics."""
        caption_lower = caption.lower()

        summary_keywords = [
            "summary statistics",
            "descriptive statistics",
            "descriptive",
            "summary",
            "variable description",
        ]
        if any(kw in caption_lower for kw in summary_keywords):
            return True

        table_text = " ".join([" ".join(row) for row in rows[:5]]).lower()

        stat_columns = ["mean", "std", "min", "max", "median", "p25", "p75", "obs", "n"]
        return sum(1 for col in stat_columns if col in table_text) >= 3

    def _is_balance_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is balance/comparison table."""
        caption_lower = caption.lower()

        balance_keywords = [
            "balance",
            "comparison",
            "baseline characteristics",
            "treatment and control",
            "randomization check",
            "covariate balance",
            "orthogonality",
        ]
        if any(kw in caption_lower for kw in balance_keywords):
            return True

        table_text = " ".join([" ".join(row) for row in rows[:5]]).lower()

        comparison_patterns = [
            "control",
            "treatment",
            "difference",
            "p-value",
            "baseline",
            "endline",
        ]
        return sum(1 for pattern in comparison_patterns if pattern in table_text) >= 2

    # ========================================================================
    # REGRESSION TABLE PARSING
    # ========================================================================

    def _parse_regression_table(
        self,
        rows: list[list[str]],
        caption: str,
        page_no: int | None,
        source_file: str,
        table_index: int,
        context: str | None,
    ) -> RegressionTable | None:
        """Parse regression table into structured model."""
        if not rows or len(rows) == 0:
            return None

        reg_table = RegressionTable(
            title=caption,
            page_number=page_no,
            source_file=source_file,
            table_index=table_index,
            context_before=context,
        )

        # Find header row
        header_row_idx = self._find_regression_header(rows)
        if header_row_idx is None:
            return None

        header = rows[header_row_idx]
        n_models = len([col for col in header[1:] if col.strip()])
        model_labels = [col.strip() for col in header[1 : 1 + n_models]]

        # Initialize models
        for i, label in enumerate(model_labels):
            model = RegressionModel(
                model_number=i + 1, model_name=label if label else f"Model {i + 1}"
            )
            reg_table.models.append(model)

        # Extract dependent variable
        dep_var = self._extract_dependent_variable(rows[: header_row_idx + 2])
        if dep_var:
            for model in reg_table.models:
                model.dependent_variable = dep_var

        # Parse coefficient rows
        data_start_idx = header_row_idx + 1
        i = data_start_idx
        while i < len(rows):
            row = rows[i]

            if len(row) == 0 or not row[0].strip():
                i += 1
                continue

            var_name = row[0].strip()

            # Handle diagnostic rows
            if self._is_diagnostic_row(var_name):
                self._parse_diagnostic_row(var_name, row[1:], reg_table.models)
                i += 1
                continue

            # Handle fixed effects rows
            if self._is_fixed_effects_row(var_name):
                self._parse_fixed_effects_row(var_name, row[1:], reg_table.models)
                i += 1
                continue

            # Handle SE type rows
            if self._is_se_type_row(var_name):
                self._parse_se_type_row(var_name, row[1:], reg_table.models)
                i += 1
                continue

            # Parse coefficient row
            has_se_row = (
                i + 1 < len(rows)
                and rows[i + 1][0].strip() == ""
                and any("(" in str(cell) for cell in rows[i + 1])
            )

            for model_idx, model in enumerate(reg_table.models):
                col_idx = model_idx + 1

                if col_idx >= len(row):
                    continue

                coef_text = row[col_idx].strip()

                if not coef_text or coef_text == "-":
                    continue

                coef = RegressionCoefficient(variable_name=var_name)

                # Extract coefficient value and significance
                coef_match = re.match(r"([-+]?\d*\.?\d+)\s*(\*{0,3})", coef_text)
                if coef_match:
                    coef.coefficient = float(coef_match.group(1))
                    coef.significance = (
                        coef_match.group(2) if coef_match.group(2) else None
                    )

                # Extract standard error
                if has_se_row and col_idx < len(rows[i + 1]):
                    se_text = rows[i + 1][col_idx].strip()
                    se_match = re.search(r"\(([-+]?\d*\.?\d+)\)", se_text)
                    if se_match:
                        coef.std_error = float(se_match.group(1))

                model.coefficients.append(coef)

            i += 2 if has_se_row else 1

        # Extract notes
        notes = self._extract_table_notes(rows)
        reg_table.notes = notes

        return reg_table

    def _find_regression_header(self, rows: list[list[str]]) -> int | None:
        """Find header row for regression table."""
        for i, row in enumerate(rows):
            if len(row) > 1:
                header_pattern = r"^\(?\d+\)?$|^Model\s*\d+$"
                if any(
                    re.match(header_pattern, cell.strip(), re.IGNORECASE)
                    for cell in row[1:]
                    if cell.strip()
                ):
                    return i

        for i, row in enumerate(rows):
            if any("dependent" in cell.lower() for cell in row):
                return i + 1 if i + 1 < len(rows) else i

        return 0

    def _extract_dependent_variable(self, header_rows: list[list[str]]) -> str | None:
        """Extract dependent variable name."""
        for row in header_rows:
            for cell in row:
                if "dependent variable" in cell.lower():
                    parts = cell.split(":")
                    if len(parts) > 1:
                        return parts[1].strip()
        return None

    def _is_diagnostic_row(self, var_name: str) -> bool:
        """Check if row contains diagnostic statistics."""
        var_lower = var_name.lower()
        diagnostics = [
            "observations",
            "r-squared",
            "r2",
            "adjusted r",
            "f-statistic",
            "n =",
            "sample size",
            "aic",
            "bic",
            "log likelihood",
        ]
        return any(diag in var_lower for diag in diagnostics)

    def _is_fixed_effects_row(self, var_name: str) -> bool:
        """Check if row specifies fixed effects."""
        var_lower = var_name.lower()
        return "fixed effect" in var_lower or var_lower.endswith(" fe")

    def _is_se_type_row(self, var_name: str) -> bool:
        """Check if row specifies standard error type."""
        var_lower = var_name.lower()
        return any(
            se_type in var_lower
            for se_type in ["standard errors", "clustered", "robust", "se clustered"]
        )

    def _parse_diagnostic_row(
        self, var_name: str, values: list[str], models: list[RegressionModel]
    ):
        """Parse diagnostic statistics."""
        var_lower = var_name.lower()

        for value, model in zip(values, models):
            if not value.strip() or value.strip() == "-":
                continue

            value_clean = value.strip().replace(",", "")

            try:
                if "observation" in var_lower or "n =" in var_lower:
                    model.n_observations = int(float(value_clean))
                elif "r-squared" in var_lower or "r2" in var_lower:
                    if "adjusted" in var_lower:
                        model.adjusted_r_squared = float(value_clean)
                    else:
                        model.r_squared = float(value_clean)
                elif "f-statistic" in var_lower:
                    model.f_statistic = float(value_clean)
            except (ValueError, AttributeError):
                pass

    def _parse_fixed_effects_row(
        self, var_name: str, values: list[str], models: list[RegressionModel]
    ):
        """Parse fixed effects specification."""
        fe_name = var_name.replace("FE", "").replace("Fixed Effects", "").strip()

        for value, model in zip(values, models):
            value_clean = value.strip().lower()
            if fe_name and value_clean in ["yes", "y", "✓", "x"]:
                model.fixed_effects.append(fe_name)

    def _parse_se_type_row(
        self, var_name: str, values: list[str], models: list[RegressionModel]
    ):
        """Parse standard error type."""
        for value, model in zip(values, models):
            value_clean = value.strip()
            if value_clean:
                model.se_type = value_clean

                if "cluster" in value_clean.lower():
                    cluster_match = re.search(
                        r"cluster[^a-z]*([a-z_]+)", value_clean, re.IGNORECASE
                    )
                    if cluster_match:
                        model.cluster_variable = cluster_match.group(1)

    # ========================================================================
    # SUMMARY STATISTICS TABLE PARSING
    # ========================================================================

    def _parse_summary_stats_table(
        self,
        rows: list[list[str]],
        caption: str,
        page_no: int | None,
        source_file: str,
        table_index: int,
        context: str | None,
    ) -> SummaryStatisticsTable | None:
        """Parse summary statistics table."""
        if not rows or len(rows) == 0:
            return None

        sum_table = SummaryStatisticsTable(
            title=caption,
            page_number=page_no,
            source_file=source_file,
            table_index=table_index,
            context_before=context,
        )

        # Find header row
        header_row_idx = self._find_sumstats_header(rows)
        if header_row_idx is None:
            header_row_idx = 0

        header = rows[header_row_idx]

        # Map column indices to statistic types
        col_map = self._map_sumstats_columns(header)

        # Parse data rows
        for i in range(header_row_idx + 1, len(rows)):
            row = rows[i]

            if len(row) == 0 or not row[0].strip():
                continue

            var_name = row[0].strip()

            if self._is_footer_row(var_name):
                break

            stat = SummaryStatistic(variable_name=var_name)

            for col_idx, stat_type in col_map.items():
                if col_idx < len(row):
                    value = row[col_idx].strip()
                    if value and value != "-":
                        setattr(stat, stat_type, value)

            sum_table.statistics.append(stat)

        # Extract notes
        notes = self._extract_table_notes(rows)
        sum_table.notes = notes

        return sum_table

    def _find_sumstats_header(self, rows: list[list[str]]) -> int | None:
        """Find header row for summary statistics."""
        for i, row in enumerate(rows):
            row_lower = " ".join(row).lower()
            if any(
                keyword in row_lower
                for keyword in ["mean", "std", "min", "max", "obs", "n"]
            ):
                return i
        return 0

    def _map_sumstats_columns(self, header: list[str]) -> dict[int, str]:
        """Map column indices to summary statistic field names."""
        col_map = {}

        for i, col_name in enumerate(header):
            col_lower = col_name.lower().strip()

            if i == 0:
                continue

            if "obs" in col_lower or col_lower == "n":
                col_map[i] = "n_obs"
            elif "mean" in col_lower:
                col_map[i] = "mean"
            elif "std" in col_lower or "sd" in col_lower:
                col_map[i] = "std_dev"
            elif "median" in col_lower or col_lower == "p50":
                col_map[i] = "median"
            elif "min" in col_lower:
                col_map[i] = "min_value"
            elif "max" in col_lower:
                col_map[i] = "max_value"
            elif col_lower in ["p10", "10th"]:
                col_map[i] = "p10"
            elif col_lower in ["p25", "25th", "q1"]:
                col_map[i] = "p25"
            elif col_lower in ["p75", "75th", "q3"]:
                col_map[i] = "p75"
            elif col_lower in ["p90", "90th"]:
                col_map[i] = "p90"

        return col_map

    # ========================================================================
    # BALANCE TABLE PARSING
    # ========================================================================

    def _parse_balance_table(
        self,
        rows: list[list[str]],
        caption: str,
        page_no: int | None,
        source_file: str,
        table_index: int,
        context: str | None,
    ) -> BalanceTable | None:
        """Parse balance/comparison table."""
        if not rows or len(rows) == 0:
            return None

        balance_table = BalanceTable(
            title=caption,
            page_number=page_no,
            source_file=source_file,
            table_index=table_index,
            context_before=context,
        )

        # Find header row
        header_row_idx = self._find_balance_header(rows)
        if header_row_idx is None:
            header_row_idx = 0

        header = rows[header_row_idx]

        # Map columns and extract group labels
        col_map, group_labels = self._map_balance_columns(header)

        if "control_label" in group_labels:
            balance_table.control_label = group_labels["control_label"]
        if "treatment_label" in group_labels:
            balance_table.treatment_label = group_labels["treatment_label"]
        if "group3_label" in group_labels:
            balance_table.group3_label = group_labels["group3_label"]

        # Parse data rows
        for i in range(header_row_idx + 1, len(rows)):
            row = rows[i]

            if len(row) == 0 or not row[0].strip():
                continue

            var_name = row[0].strip()

            if self._is_footer_row(var_name):
                break

            balance_stat = BalanceStatistic(variable_name=var_name)

            # Check for SD row
            has_sd_row = (
                i + 1 < len(rows)
                and rows[i + 1][0].strip() == ""
                and any("(" in str(cell) for cell in rows[i + 1])
            )

            # Extract values
            for col_idx, field_info in col_map.items():
                if col_idx >= len(row):
                    continue

                value = row[col_idx].strip()

                # Handle mean/SD pairs
                if field_info["type"] in [
                    "control_mean",
                    "treatment_mean",
                    "group3_mean",
                ]:
                    if value and value != "-":
                        mean_match = re.match(r"([-+]?\d*\.?\d+)\s*(\*{0,3})", value)
                        if mean_match:
                            setattr(
                                balance_stat, field_info["type"], mean_match.group(1)
                            )
                            if mean_match.group(2):
                                balance_stat.significance = mean_match.group(2)

                    # Extract SD
                    if has_sd_row and col_idx < len(rows[i + 1]):
                        sd_text = rows[i + 1][col_idx].strip()
                        sd_match = re.search(r"\(([-+]?\d*\.?\d+)\)", sd_text)
                        if sd_match:
                            sd_field = field_info["type"].replace("mean", "sd")
                            setattr(balance_stat, sd_field, sd_match.group(1))

                elif value and value != "-":
                    setattr(balance_stat, field_info["type"], value)

            balance_table.comparisons.append(balance_stat)

        # Extract notes
        notes = self._extract_table_notes(rows)
        balance_table.notes = notes

        return balance_table

    def _find_balance_header(self, rows: list[list[str]]) -> int | None:
        """Find header row for balance table."""
        for i, row in enumerate(rows):
            row_lower = " ".join(row).lower()
            if any(
                keyword in row_lower
                for keyword in ["control", "treatment", "difference"]
            ):
                return i
        return 0

    def _map_balance_columns(
        self, header: list[str]
    ) -> tuple[dict[int, dict[str, str]], dict[str, str]]:
        """Map column indices to balance table fields."""
        col_map = {}
        group_labels = {}

        for i, col_name in enumerate(header):
            col_lower = col_name.lower().strip()

            if i == 0:
                continue

            # Control group
            if "control" in col_lower or col_lower.startswith("(1)"):
                if not group_labels.get("control_label"):
                    group_labels["control_label"] = (
                        col_name if "mean" not in col_lower else "Control"
                    )

                if "mean" in col_lower or not any(
                    x in col_lower for x in ["sd", "n", "obs"]
                ):
                    col_map[i] = {"type": "control_mean", "group": "control"}

            # Treatment group
            elif (
                "treatment" in col_lower
                or "treated" in col_lower
                or col_lower.startswith("(2)")
            ):
                if not group_labels.get("treatment_label"):
                    group_labels["treatment_label"] = (
                        col_name if "mean" not in col_lower else "Treatment"
                    )

                if "mean" in col_lower or not any(
                    x in col_lower for x in ["sd", "n", "obs"]
                ):
                    col_map[i] = {"type": "treatment_mean", "group": "treatment"}

            # Comparison columns
            elif "diff" in col_lower:
                col_map[i] = {"type": "difference", "group": "comparison"}
            elif "p-value" in col_lower or "p value" in col_lower:
                col_map[i] = {"type": "p_value", "group": "comparison"}

        return col_map, group_labels

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _is_footer_row(self, var_name: str) -> bool:
        """Check if row is part of table footer."""
        var_lower = var_name.lower()
        footer_indicators = ["note:", "notes:", "source:", "*", "significant"]
        return any(indicator in var_lower for indicator in footer_indicators)

    def _extract_table_notes(self, rows: list[list[str]]) -> str | None:
        """Extract notes from bottom of table."""
        notes = []
        for row in rows[-5:]:
            row_text = " ".join(row).strip()
            if row_text and (
                row_text.startswith("Note")
                or row_text.startswith("*")
                or "standard error" in row_text.lower()
                or "significant" in row_text.lower()
            ):
                notes.append(row_text)

        return " ".join(notes) if notes else None
