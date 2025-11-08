import argparse
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling_core.types.doc import DoclingDocument, TableCell
from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS FOR STRUCTURED DATA
# ============================================================================


class RegressionCoefficient(BaseModel):
    """Model for a single regression coefficient."""

    variable_name: str = Field(description="Name of the independent variable")
    coefficient: float | None = Field(
        None, description="Point estimate of the coefficient"
    )
    std_error: float | None = Field(None, description="Standard error")
    t_statistic: float | None = Field(None, description="T-statistic")
    p_value: float | None = Field(None, description="P-value")
    ci_lower: float | None = Field(
        None, description="Lower bound of confidence interval"
    )
    ci_upper: float | None = Field(
        None, description="Upper bound of confidence interval"
    )
    significance: str | None = Field(
        None, description="Significance stars (*, **, ***)"
    )

    # Semantic augmentation fields (optional)
    variable_context: dict[str, Any] | None = Field(
        None, description="Semantic context for this variable (from RAG augmentation)"
    )
    validation: dict[str, Any] | None = Field(
        None, description="Validation result comparing parsed vs RAG-extracted value"
    )

    @field_validator(
        "coefficient",
        "std_error",
        "t_statistic",
        "p_value",
        "ci_lower",
        "ci_upper",
        mode="before",
    )
    @classmethod
    def parse_numeric(cls, v):
        """Parse numeric values from strings."""
        if v is None or v == "":
            return None
        if isinstance(v, int | float):
            return float(v)

        v_str = str(v).strip()
        v_str = re.sub(r"[*\s,\$%]", "", v_str)
        match = re.search(r"[-+]?\d*\.?\d+", v_str)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None


class RegressionModel(BaseModel):
    """Model for a single regression specification/column."""

    model_number: int = Field(description="Column/model number in the table")
    model_name: str | None = Field(None, description="Name or label of the model")
    dependent_variable: str | None = Field(None, description="Dependent variable name")
    coefficients: list[RegressionCoefficient] = Field(default_factory=list)

    # Diagnostics
    n_observations: int | None = Field(None, description="Number of observations")
    r_squared: float | None = Field(None, description="R-squared")
    adjusted_r_squared: float | None = Field(None, description="Adjusted R-squared")
    f_statistic: float | None = Field(None, description="F-statistic")

    # Standard error specification
    se_type: str | None = Field(None, description="Type of standard errors")
    cluster_variable: str | None = Field(
        None, description="Clustering variable if clustered SEs"
    )

    # Fixed effects
    fixed_effects: list[str] = Field(
        default_factory=list, description="List of fixed effects included"
    )

    # Semantic augmentation fields (optional)
    methods_context: dict[str, Any] | None = Field(
        None, description="Statistical methods context (from RAG augmentation)"
    )
    outcome_context: dict[str, Any] | None = Field(
        None, description="Outcome measurement context (from RAG augmentation)"
    )


class RegressionTable(BaseModel):
    """Complete regression table with multiple specifications."""

    table_number: str | None = Field(None, description="Table number in paper")
    title: str | None = Field(None, description="Table title/caption")
    notes: str | None = Field(None, description="Table notes and footnotes")
    models: list[RegressionModel] = Field(default_factory=list)

    # Metadata
    source_file: str | None = None
    page_number: int | None = None
    table_index: int | None = None
    context_before: str | None = Field(None, description="Text appearing before table")

    # Semantic augmentation fields (optional)
    study_context: dict[str, Any] | None = Field(
        None, description="Study design and sample context (from RAG augmentation)"
    )
    treatment_contexts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Treatment/control arm descriptions (from RAG augmentation)",
    )
    augmentation_confidence: float | None = Field(
        None, description="Overall confidence score for semantic augmentation (0-1)"
    )


class SummaryStatistic(BaseModel):
    """Model for a single variable's summary statistics."""

    variable_name: str = Field(description="Name of the variable")
    variable_label: str | None = Field(
        None, description="Descriptive label for variable"
    )

    # Sample statistics
    n_obs: int | None = Field(None, description="Number of observations")
    n_missing: int | None = Field(None, description="Number of missing values")

    # Central tendency
    mean: float | None = Field(None, description="Mean/average")
    median: float | None = Field(None, description="Median (50th percentile)")

    # Dispersion
    std_dev: float | None = Field(None, description="Standard deviation")
    variance: float | None = Field(None, description="Variance")

    # Range
    min_value: float | None = Field(None, description="Minimum value")
    max_value: float | None = Field(None, description="Maximum value")

    # Percentiles
    p10: float | None = Field(None, description="10th percentile")
    p25: float | None = Field(None, description="25th percentile (Q1)")
    p50: float | None = Field(None, description="50th percentile (median)")
    p75: float | None = Field(None, description="75th percentile (Q3)")
    p90: float | None = Field(None, description="90th percentile")

    # Additional statistics
    skewness: float | None = Field(None, description="Skewness")
    kurtosis: float | None = Field(None, description="Kurtosis")

    # Semantic augmentation fields (optional)
    variable_context: dict[str, Any] | None = Field(
        None, description="Semantic context for this variable (from RAG augmentation)"
    )

    @field_validator("n_obs", "n_missing", mode="before")
    @classmethod
    def parse_integer(cls, v):
        """Parse integer values."""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        try:
            v_str = str(v).strip().replace(",", "")
            return int(float(v_str))
        except (ValueError, AttributeError):
            return None

    @field_validator(
        "mean",
        "median",
        "std_dev",
        "variance",
        "min_value",
        "max_value",
        "p10",
        "p25",
        "p50",
        "p75",
        "p90",
        "skewness",
        "kurtosis",
        mode="before",
    )
    @classmethod
    def parse_float(cls, v):
        """Parse float values."""
        if v is None or v == "":
            return None
        if isinstance(v, int | float):
            return float(v)
        try:
            v_str = str(v).strip().replace(",", "").replace("%", "")
            return float(v_str)
        except (ValueError, AttributeError):
            return None


class SummaryStatisticsTable(BaseModel):
    """Complete summary statistics table."""

    table_number: str | None = Field(None, description="Table number in paper")
    title: str | None = Field(None, description="Table title/caption")
    notes: str | None = Field(None, description="Table notes")
    statistics: list[SummaryStatistic] = Field(default_factory=list)

    # Table-level metadata
    total_observations: int | None = Field(None, description="Total sample size")
    sample_description: str | None = Field(
        None, description="Description of the sample"
    )
    source_file: str | None = None
    page_number: int | None = None
    table_index: int | None = None
    context_before: str | None = Field(None, description="Text appearing before table")

    # Semantic augmentation fields (optional)
    study_context: dict[str, Any] | None = Field(
        None, description="Study design and sample context (from RAG augmentation)"
    )
    treatment_contexts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Treatment/control arm descriptions (from RAG augmentation)",
    )
    augmentation_confidence: float | None = Field(
        None, description="Overall confidence score for semantic augmentation (0-1)"
    )


class BalanceStatistic(BaseModel):
    """Model for balance table comparison between groups."""

    variable_name: str = Field(description="Name of the variable")
    variable_label: str | None = Field(None, description="Descriptive label")

    # Control/baseline group
    control_mean: float | None = Field(None, description="Control group mean")
    control_sd: float | None = Field(
        None, description="Control group standard deviation"
    )
    control_n: int | None = Field(None, description="Control group sample size")

    # Treatment/comparison group
    treatment_mean: float | None = Field(None, description="Treatment group mean")
    treatment_sd: float | None = Field(
        None, description="Treatment group standard deviation"
    )
    treatment_n: int | None = Field(None, description="Treatment group sample size")

    # Additional groups (for multi-arm trials)
    group3_mean: float | None = Field(None, description="Third group mean")
    group3_sd: float | None = Field(None, description="Third group standard deviation")
    group3_n: int | None = Field(None, description="Third group sample size")

    # Comparison statistics
    difference: float | None = Field(None, description="Difference between groups")
    difference_se: float | None = Field(
        None, description="Standard error of difference"
    )
    t_statistic: float | None = Field(None, description="T-statistic for difference")
    p_value: float | None = Field(None, description="P-value for difference test")
    significance: str | None = Field(None, description="Significance stars")
    normalized_difference: float | None = Field(
        None, description="Normalized/standardized difference"
    )

    # Semantic augmentation fields (optional)
    variable_context: dict[str, Any] | None = Field(
        None, description="Semantic context for this variable (from RAG augmentation)"
    )

    @field_validator("control_n", "treatment_n", "group3_n", mode="before")
    @classmethod
    def parse_integer(cls, v):
        """Parse integer values."""
        if v is None or v == "":
            return None
        if isinstance(v, int):
            return v
        try:
            v_str = str(v).strip().replace(",", "")
            return int(float(v_str))
        except (ValueError, AttributeError):
            return None

    @field_validator(
        "control_mean",
        "control_sd",
        "treatment_mean",
        "treatment_sd",
        "group3_mean",
        "group3_sd",
        "difference",
        "difference_se",
        "t_statistic",
        "p_value",
        "normalized_difference",
        mode="before",
    )
    @classmethod
    def parse_float(cls, v):
        """Parse float values."""
        if v is None or v == "":
            return None
        if isinstance(v, int | float):
            return float(v)
        try:
            v_str = str(v).strip().replace(",", "").replace("%", "").replace("*", "")
            v_str = re.sub(r"[()]", "", v_str)
            return float(v_str)
        except (ValueError, AttributeError):
            return None


class BalanceTable(BaseModel):
    """Complete balance/comparison table."""

    table_number: str | None = Field(None, description="Table number in paper")
    title: str | None = Field(None, description="Table title/caption")
    notes: str | None = Field(None, description="Table notes")
    comparisons: list[BalanceStatistic] = Field(default_factory=list)

    # Group labels
    control_label: str | None = Field(
        "Control", description="Label for control/baseline group"
    )
    treatment_label: str | None = Field(
        "Treatment", description="Label for treatment group"
    )
    group3_label: str | None = Field(
        None, description="Label for third group if applicable"
    )

    # Overall balance test
    joint_f_statistic: float | None = Field(
        None, description="F-statistic for joint orthogonality test"
    )
    joint_p_value: float | None = Field(None, description="P-value for joint test")

    # Metadata
    source_file: str | None = None
    page_number: int | None = None
    table_index: int | None = None
    context_before: str | None = Field(None, description="Text appearing before table")

    # Semantic augmentation fields (optional)
    study_context: dict[str, Any] | None = Field(
        None, description="Study design and sample context (from RAG augmentation)"
    )
    treatment_contexts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Treatment/control arm descriptions (from RAG augmentation)",
    )
    augmentation_confidence: float | None = Field(
        None, description="Overall confidence score for semantic augmentation (0-1)"
    )


class Figure(BaseModel):
    """Model for extracted figure/image from research paper."""

    figure_id: str = Field(description="Unique identifier for this figure")
    figure_number: str | None = Field(None, description="Figure number from paper")
    caption: str | None = Field(None, description="Figure caption/title")
    page_number: int | None = Field(
        None, description="Page number where figure appears"
    )

    # Image file information
    image_path: str | None = Field(
        None, description="Relative path to saved image file"
    )
    image_format: str | None = Field(None, description="Image format (png, jpg, etc)")
    image_width: int | None = Field(None, description="Image width in pixels")
    image_height: int | None = Field(None, description="Image height in pixels")

    # Classification
    figure_type: str | None = Field(
        None,
        description="Type of figure (chart, diagram, photo, map, etc)",
    )

    # Quality metrics
    quality_score: float | None = Field(
        None, description="Extraction quality score (0-1)"
    )

    # Metadata
    source_file: str | None = None
    context_before: str | None = Field(None, description="Text appearing before figure")

    # Semantic augmentation fields (optional)
    figure_context: dict[str, Any] | None = Field(
        None, description="Semantic context describing the figure content"
    )


# ============================================================================
# MAIN EXTRACTOR CLASS
# ============================================================================


class AcademicTableExtractor:
    """Extract and parse structured data from academic papers.
    Handles regression tables, summary statistics, and balance tables.
    """

    def __init__(self, enable_ocr: bool = False, extract_figures: bool = True):
        """Initialize document converter with optimized settings.

        Args:
            enable_ocr: Whether to enable OCR for scanned documents
            extract_figures: Whether to extract figures/images from documents

        """
        # Configure PDF pipeline for optimal table extraction
        table_structure_options = TableStructureOptions(do_cell_matching=True)

        pdf_pipeline_options = PdfPipelineOptions(
            do_table_structure=True,
            do_ocr=enable_ocr,
            table_structure_options=table_structure_options,
            # Enable figure extraction
            generate_page_images=extract_figures,
            generate_picture_images=extract_figures,
            images_scale=2.0,  # 144 DPI resolution (scale=1 is 72 DPI)
        )

        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(
                    pipeline_options=pdf_pipeline_options,
                ),
                "docx": WordFormatOption(),
            }
        )

        self.extract_figures = extract_figures

    def extract_cell_value(self, cell: TableCell) -> str:
        """Extract text value from a table cell."""
        if cell and hasattr(cell, "text"):
            return cell.text.strip()
        return ""

    def get_table_structure(self, table) -> dict[str, Any]:
        """Extract comprehensive table structure information."""
        structure = {
            "data": [],
            "num_rows": 0,
            "num_cols": 0,
            "caption": "",
            "page": None,
        }

        # Extract table data
        if hasattr(table, "data"):
            table_data = table.data
            # TableData has num_rows, num_cols attributes and a grid property
            if hasattr(table_data, "grid"):
                structure["data"] = [
                    [self.extract_cell_value(cell) for cell in row]
                    for row in table_data.grid
                ]
                structure["num_rows"] = (
                    table_data.num_rows
                    if hasattr(table_data, "num_rows")
                    else len(table_data.grid)
                )
                structure["num_cols"] = (
                    table_data.num_cols
                    if hasattr(table_data, "num_cols")
                    else (len(table_data.grid[0]) if table_data.grid else 0)
                )
            else:
                # Fallback for older API
                structure["data"] = [
                    [self.extract_cell_value(cell) for cell in row]
                    for row in table_data
                ]
                structure["num_rows"] = (
                    len(table_data) if hasattr(table_data, "__len__") else 0
                )
                structure["num_cols"] = (
                    len(table_data[0]) if structure["num_rows"] > 0 else 0
                )

        # Extract caption
        if hasattr(table, "caption") and table.caption:
            structure["caption"] = (
                table.caption.text
                if hasattr(table.caption, "text")
                else str(table.caption)
            )

        # Extract page number
        if hasattr(table, "prov") and table.prov and hasattr(table.prov[0], "page_no"):
            structure["page"] = table.prov[0].page_no

        return structure

    def get_text_before_table(
        self, doc: DoclingDocument, table, num_items: int = 3
    ) -> str:
        """Extract text that appears before a table (e.g., section headers)."""
        context_text = []

        for item in doc.iterate_items():
            if item == table:
                break

            if hasattr(item, "text") and item.text:
                context_text.append(item.text)
                if len(context_text) > num_items:
                    context_text.pop(0)

        return " ".join(context_text) if context_text else ""

    # ========================================================================
    # TABLE TYPE CLASSIFICATION
    # ========================================================================

    def is_regression_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is a regression results table."""
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

    def is_summary_stats_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is a summary statistics table."""
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

    def is_balance_table(self, rows: list[list[str]], caption: str = "") -> bool:
        """Determine if table is a balance/comparison table."""
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

    def parse_regression_table(
        self,
        rows: list[list[str]],
        caption: str = "",
        page_no: int = None,
        source_file: str = None,
        table_index: int = None,
        context: str = None,
    ) -> RegressionTable | None:
        """Parse a regression table into structured RegressionTable model."""
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

        if notes:
            self._parse_notes_for_diagnostics(notes, reg_table.models)

        return reg_table

    def _find_regression_header(self, rows: list[list[str]]) -> int | None:
        """Find the header row for regression table."""
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

    def _parse_notes_for_diagnostics(self, notes: str, models: list[RegressionModel]):
        """Extract diagnostic info from notes."""
        notes_lower = notes.lower()

        if "cluster" in notes_lower:
            cluster_match = re.search(r"cluster[^a-z]*([a-z_]+)", notes_lower)
            if cluster_match:
                cluster_var = cluster_match.group(1)
                for model in models:
                    if not model.se_type:
                        model.se_type = "clustered"
                    if not model.cluster_variable:
                        model.cluster_variable = cluster_var

        if "robust" in notes_lower:
            for model in models:
                if not model.se_type:
                    model.se_type = "robust"

    # ========================================================================
    # SUMMARY STATISTICS TABLE PARSING
    # ========================================================================

    def parse_summary_stats_table(
        self,
        rows: list[list[str]],
        caption: str = "",
        page_no: int = None,
        source_file: str = None,
        table_index: int = None,
        context: str = None,
    ) -> SummaryStatisticsTable | None:
        """Parse summary statistics table into structured model."""
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

        if notes:
            n_match = re.search(r"N\s*=\s*([0-9,]+)", notes)
            if n_match:
                sum_table.total_observations = int(n_match.group(1).replace(",", ""))

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
            elif "var" in col_lower and "variable" not in col_lower:
                col_map[i] = "variance"
            elif "skew" in col_lower:
                col_map[i] = "skewness"
            elif "kurt" in col_lower:
                col_map[i] = "kurtosis"

        return col_map

    # ========================================================================
    # BALANCE TABLE PARSING
    # ========================================================================

    def parse_balance_table(
        self,
        rows: list[list[str]],
        caption: str = "",
        page_no: int = None,
        source_file: str = None,
        table_index: int = None,
        context: str = None,
    ) -> BalanceTable | None:
        """Parse balance/comparison table into structured model."""
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

            # Check for joint test statistics
            if "joint" in var_name.lower() or "f-stat" in var_name.lower():
                self._parse_joint_test(var_name, row, balance_table, col_map)
                continue

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
                elif "sd" in col_lower or "std" in col_lower:
                    col_map[i] = {"type": "control_sd", "group": "control"}
                elif "n" in col_lower or "obs" in col_lower:
                    col_map[i] = {"type": "control_n", "group": "control"}

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
                elif "sd" in col_lower or "std" in col_lower:
                    col_map[i] = {"type": "treatment_sd", "group": "treatment"}
                elif "n" in col_lower or "obs" in col_lower:
                    col_map[i] = {"type": "treatment_n", "group": "treatment"}

            # Third group
            elif col_lower.startswith("(3)"):
                if not group_labels.get("group3_label"):
                    group_labels["group3_label"] = col_name

                if "mean" in col_lower or not any(
                    x in col_lower for x in ["sd", "n", "obs"]
                ):
                    col_map[i] = {"type": "group3_mean", "group": "group3"}
                elif "sd" in col_lower or "std" in col_lower:
                    col_map[i] = {"type": "group3_sd", "group": "group3"}
                elif "n" in col_lower or "obs" in col_lower:
                    col_map[i] = {"type": "group3_n", "group": "group3"}

            # Comparison columns
            elif "diff" in col_lower:
                if "se" in col_lower or "std" in col_lower:
                    col_map[i] = {"type": "difference_se", "group": "comparison"}
                else:
                    col_map[i] = {"type": "difference", "group": "comparison"}
            elif "p-value" in col_lower or "p value" in col_lower:
                col_map[i] = {"type": "p_value", "group": "comparison"}
            elif "t-stat" in col_lower or "t stat" in col_lower:
                col_map[i] = {"type": "t_statistic", "group": "comparison"}
            elif "normalized" in col_lower or "standard" in col_lower:
                col_map[i] = {"type": "normalized_difference", "group": "comparison"}

        return col_map, group_labels

    def _parse_joint_test(
        self, var_name: str, row: list[str], balance_table: BalanceTable, col_map: dict
    ):
        """Parse joint orthogonality test."""
        var_lower = var_name.lower()

        if "f-stat" in var_lower or "f stat" in var_lower:
            for i, val in enumerate(row[1:], 1):
                if val.strip():
                    try:
                        balance_table.joint_f_statistic = float(
                            val.strip().replace(",", "")
                        )
                        break
                    except ValueError:
                        pass

        if "p-value" in var_lower or "p value" in var_lower:
            for i, val in enumerate(row[1:], 1):
                if val.strip():
                    try:
                        balance_table.joint_p_value = float(
                            val.strip().replace(",", "")
                        )
                        break
                    except ValueError:
                        pass

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

    # ========================================================================
    # FIGURE EXTRACTION METHODS
    # ========================================================================

    def extract_figures_from_document(
        self, doc: DoclingDocument, output_dir: Path, file_stem: str
    ) -> list[Figure]:
        """Extract all figures/pictures from a docling document.

        Args:
            doc: Docling document with pictures
            output_dir: Directory to save figure images
            file_stem: Base name for saved files

        Returns:
            List of Figure objects with metadata and saved image paths

        """
        if not self.extract_figures:
            return []

        # Import PictureItem for type checking
        from docling_core.types.doc import PictureItem

        figures = []
        figures_dir = output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)

        figure_num = 1
        # Use iterate_items() to traverse document elements
        for element, _level in doc.iterate_items():
            if not isinstance(element, PictureItem):
                continue

            picture = element
            figure_id = f"figure_{figure_num}"

            # Extract caption with multiple fallback strategies
            caption = ""

            # Strategy 1: Direct caption attribute
            if hasattr(picture, "caption") and picture.caption:
                if hasattr(picture.caption, "text"):
                    caption = picture.caption.text.strip()
                else:
                    caption = str(picture.caption).strip()

                # Ignore docling internal references like "#/pictures/0"
                if caption.startswith("#/"):
                    caption = ""

            # Strategy 2: Check picture references
            if not caption and hasattr(picture, "self_ref"):
                ref = picture.self_ref.strip() if picture.self_ref else ""
                if ref and not ref.startswith("#/"):
                    caption = ref

            # Extract page number
            page_no = None
            if (
                hasattr(picture, "prov")
                and picture.prov
                and hasattr(picture.prov[0], "page_no")
            ):
                page_no = picture.prov[0].page_no

            # Save image using get_image() method
            image_path = None
            image_format = "png"
            image_width = None
            image_height = None
            quality_score = 0.0

            try:
                # Use get_image() method to retrieve the image
                image = picture.get_image(doc)
                if image is not None:
                    image_filename = f"{figure_id}.png"
                    image_filepath = figures_dir / image_filename

                    # Save image as PNG
                    with image_filepath.open("wb") as fp:
                        image.save(fp, "PNG")

                    image_path = f"figures/{image_filename}"

                    # Get image dimensions
                    if hasattr(image, "size"):
                        image_width, image_height = image.size

                    quality_score = 1.0
                    logger.info(
                        f"Saved {figure_id}: page {page_no}, {image_width}x{image_height}px"
                    )
                else:
                    logger.warning(f"No image data available for {figure_id}")
                    quality_score = 0.0
            except Exception as e:
                logger.warning(f"Failed to save figure {figure_id}: {str(e)}")
                quality_score = 0.0

            # Extract figure number from caption if available
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
                image_format=image_format if image_path else None,
                image_width=image_width,
                image_height=image_height,
                quality_score=quality_score,
            )

            figures.append(figure)
            figure_num += 1

        return figures

    # ========================================================================
    # MAIN EXTRACTION METHOD
    # ========================================================================

    def extract_structured_tables(
        self, file_path: str, output_dir: str = "structured_output"
    ) -> dict[str, Any]:
        """Extract all tables from a document and parse into structured format.

        Args:
            file_path: Path to PDF or DOCX file
            output_dir: Directory to save structured outputs

        Returns:
            Dictionary containing all extracted table types

        """
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        print(f"Processing: {file_path.name}")

        # Convert document
        result = self.converter.convert(str(file_path))
        doc = result.document

        regression_tables = []
        summary_tables = []
        balance_tables = []

        # Extract tables
        for i, table in enumerate(doc.tables):
            # Get table structure
            structure = self.get_table_structure(table)
            rows = structure["data"]
            caption = structure["caption"]
            page_no = structure["page"]

            # Get context
            context = self.get_text_before_table(doc, table)

            # Classify and parse
            if self.is_balance_table(rows, caption):
                balance_table = self.parse_balance_table(
                    rows, caption, page_no, file_path.name, i + 1, context
                )

                if balance_table and balance_table.comparisons:
                    balance_tables.append(balance_table)

                    # Save JSON
                    output_file = (
                        output_dir
                        / f"{file_path.stem}_balance_{len(balance_tables)}.json"
                    )
                    with open(output_file, "w") as f:
                        f.write(balance_table.model_dump_json(indent=2))

                    print(
                        f"  ✓ Balance Table {len(balance_tables)}: {len(balance_table.comparisons)} variables"
                    )

            elif self.is_summary_stats_table(rows, caption):
                sum_table = self.parse_summary_stats_table(
                    rows, caption, page_no, file_path.name, i + 1, context
                )

                if sum_table and sum_table.statistics:
                    summary_tables.append(sum_table)

                    # Save JSON
                    output_file = (
                        output_dir
                        / f"{file_path.stem}_summary_{len(summary_tables)}.json"
                    )
                    with open(output_file, "w") as f:
                        f.write(sum_table.model_dump_json(indent=2))

                    print(
                        f"  ✓ Summary Table {len(summary_tables)}: {len(sum_table.statistics)} variables"
                    )

            elif self.is_regression_table(rows, caption):
                reg_table = self.parse_regression_table(
                    rows, caption, page_no, file_path.name, i + 1, context
                )

                if reg_table and reg_table.models:
                    regression_tables.append(reg_table)

                    # Save JSON
                    output_file = (
                        output_dir
                        / f"{file_path.stem}_regression_{len(regression_tables)}.json"
                    )
                    with open(output_file, "w") as f:
                        f.write(reg_table.model_dump_json(indent=2))

                    print(
                        f"  ✓ Regression Table {len(regression_tables)}: {len(reg_table.models)} models"
                    )

        # Extract figures
        figures = []
        if self.extract_figures:
            print("\nExtracting figures...")
            figures = self.extract_figures_from_document(
                doc, output_dir, file_path.stem
            )

            # Save figure metadata
            for figure in figures:
                if figure.quality_score > 0:
                    output_file = output_dir / "figures" / f"{figure.figure_id}.json"
                    with open(output_file, "w") as f:
                        f.write(figure.model_dump_json(indent=2))

                    print(
                        f"  ✓ {figure.figure_id}: page {figure.page_number}, "
                        f"{figure.image_width}x{figure.image_height}px"
                    )

        # Create summary
        summary = {
            "file_name": file_path.name,
            "regression_tables": len(regression_tables),
            "summary_tables": len(summary_tables),
            "balance_tables": len(balance_tables),
            "figures": len(figures),
        }

        summary_df = pd.DataFrame([summary])
        summary_df.to_csv(
            output_dir / f"{file_path.stem}_extraction_summary.csv", index=False
        )

        print(f"\n{'=' * 60}")
        print(
            f"Extraction complete: {len(regression_tables)} regression, "
            f"{len(summary_tables)} summary, {len(balance_tables)} balance tables, "
            f"{len(figures)} figures"
        )
        print(f"{'=' * 60}\n")

        return {
            "regression_tables": regression_tables,
            "summary_tables": summary_tables,
            "balance_tables": balance_tables,
            "figures": figures,
            "summary": summary,
        }

    # ========================================================================
    # CONVERSION TO DATAFRAMES
    # ========================================================================

    def regression_to_dataframe(self, reg_table: RegressionTable) -> pd.DataFrame:
        """Convert regression table to pandas DataFrame."""
        rows = []

        for model in reg_table.models:
            for coef in model.coefficients:
                row = {
                    "source_file": reg_table.source_file,
                    "table_index": reg_table.table_index,
                    "table_title": reg_table.title,
                    "page": reg_table.page_number,
                    "model": model.model_name or f"Model {model.model_number}",
                    "model_number": model.model_number,
                    "dependent_variable": model.dependent_variable,
                    "variable": coef.variable_name,
                    "coefficient": coef.coefficient,
                    "std_error": coef.std_error,
                    "t_statistic": coef.t_statistic,
                    "p_value": coef.p_value,
                    "significance": coef.significance,
                    "ci_lower": coef.ci_lower,
                    "ci_upper": coef.ci_upper,
                    "n_obs": model.n_observations,
                    "r_squared": model.r_squared,
                    "adjusted_r_squared": model.adjusted_r_squared,
                    "se_type": model.se_type,
                    "cluster_variable": model.cluster_variable,
                    "fixed_effects": ", ".join(model.fixed_effects)
                    if model.fixed_effects
                    else None,
                }
                rows.append(row)

        return pd.DataFrame(rows)

    def summary_stats_to_dataframe(
        self, sum_table: SummaryStatisticsTable
    ) -> pd.DataFrame:
        """Convert summary statistics to DataFrame."""
        rows = []

        for stat in sum_table.statistics:
            row = stat.model_dump()
            row["source_file"] = sum_table.source_file
            row["table_index"] = sum_table.table_index
            row["table_title"] = sum_table.title
            row["page"] = sum_table.page_number
            rows.append(row)

        return pd.DataFrame(rows)

    def balance_to_dataframe(self, balance_table: BalanceTable) -> pd.DataFrame:
        """Convert balance table to DataFrame."""
        rows = []

        for comparison in balance_table.comparisons:
            row = comparison.model_dump()
            row["source_file"] = balance_table.source_file
            row["table_index"] = balance_table.table_index
            row["table_title"] = balance_table.title
            row["page"] = balance_table.page_number
            row["control_label"] = balance_table.control_label
            row["treatment_label"] = balance_table.treatment_label
            if balance_table.group3_label:
                row["group3_label"] = balance_table.group3_label
            rows.append(row)

        return pd.DataFrame(rows)

    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================

    def batch_extract(
        self, input_dir: str, output_dir: str = "batch_output"
    ) -> pd.DataFrame:
        """Batch process multiple papers.

        Args:
            input_dir: Directory containing PDF/DOCX files
            output_dir: Directory to save outputs

        Returns:
            Summary DataFrame

        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # Find all files
        files = list(input_dir.glob("*.pdf")) + list(input_dir.glob("*.docx"))

        print(f"Found {len(files)} files to process\n")

        all_summaries = []
        all_regression_dfs = []
        all_summary_dfs = []
        all_balance_dfs = []

        for file_path in files:
            try:
                # Create subdirectory for this file
                file_output_dir = output_dir / file_path.stem
                file_output_dir.mkdir(exist_ok=True)

                # Extract tables
                results = self.extract_structured_tables(
                    str(file_path), str(file_output_dir)
                )

                # Convert to DataFrames
                for reg_table in results["regression_tables"]:
                    df = self.regression_to_dataframe(reg_table)
                    all_regression_dfs.append(df)
                    df.to_csv(
                        file_output_dir
                        / f"regression_{reg_table.table_index}_data.csv",
                        index=False,
                    )

                for sum_table in results["summary_tables"]:
                    df = self.summary_stats_to_dataframe(sum_table)
                    all_summary_dfs.append(df)
                    df.to_csv(
                        file_output_dir / f"summary_{sum_table.table_index}_data.csv",
                        index=False,
                    )

                for balance_table in results["balance_tables"]:
                    df = self.balance_to_dataframe(balance_table)
                    all_balance_dfs.append(df)
                    df.to_csv(
                        file_output_dir
                        / f"balance_{balance_table.table_index}_data.csv",
                        index=False,
                    )

                all_summaries.append(results["summary"])

            except Exception as e:
                print(f"Error processing {file_path.name}: {str(e)}\n")
                continue

        # Combine all DataFrames
        if all_regression_dfs:
            combined_regression = pd.concat(all_regression_dfs, ignore_index=True)
            combined_regression.to_csv(output_dir / "all_regressions.csv", index=False)

        if all_summary_dfs:
            combined_summary = pd.concat(all_summary_dfs, ignore_index=True)
            combined_summary.to_csv(output_dir / "all_summary_stats.csv", index=False)

        if all_balance_dfs:
            combined_balance = pd.concat(all_balance_dfs, ignore_index=True)
            combined_balance.to_csv(output_dir / "all_balance_tables.csv", index=False)

        # Create overall summary
        summary_df = pd.DataFrame(all_summaries)
        summary_df.to_csv(output_dir / "overall_summary.csv", index=False)

        print(f"\n{'=' * 60}")
        print("BATCH EXTRACTION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Files processed: {len(all_summaries)}")
        print(f"Total regression tables: {summary_df['regression_tables'].sum()}")
        print(f"Total summary tables: {summary_df['summary_tables'].sum()}")
        print(f"Total balance tables: {summary_df['balance_tables'].sum()}")
        print(f"Results saved to: {output_dir}")

        return summary_df


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# if __name__ == "__main__":
#     # Initialize extractor
#     extractor = AcademicTableExtractor(enable_ocr=False)

#     # Example 1: Extract from single paper
#     print("=" * 60)
#     print("EXAMPLE 1: Single Paper Extraction")
#     print("=" * 60)

#     results = extractor.extract_structured_tables(
#         "path/to/paper.pdf", output_dir="structured_output"
#     )

#     # Access structured data
#     print("\nRegression Tables:")
#     for reg_table in results["regression_tables"]:
#         print(f"\n  Table {reg_table.table_index}: {reg_table.title}")
#         print(f"  Page: {reg_table.page_number}")
#         for model in reg_table.models:
#             print(f"    {model.model_name}:")
#             print(f"      N={model.n_observations}, R²={model.r_squared}")
#             print(f"      SE type: {model.se_type}")
#             print(f"      Coefficients: {len(model.coefficients)}")

#     print("\nSummary Statistics Tables:")
#     for sum_table in results["summary_tables"]:
#         print(f"\n  Table {sum_table.table_index}: {sum_table.title}")
#         df = extractor.summary_stats_to_dataframe(sum_table)
#         print(f"  Variables: {len(sum_table.statistics)}")
#         print(df[["variable_name", "n_obs", "mean", "std_dev"]].head())

#     print("\nBalance Tables:")
#     for balance_table in results["balance_tables"]:
#         print(f"\n  Table {balance_table.table_index}: {balance_table.title}")
#         print(
#             f"  Groups: {balance_table.control_label} vs {balance_table.treatment_label}"
#         )
#         df = extractor.balance_to_dataframe(balance_table)
#         print(f"  Variables: {len(balance_table.comparisons)}")
#         print(
#             df[
#                 [
#                     "variable_name",
#                     "control_mean",
#                     "treatment_mean",
#                     "difference",
#                     "p_value",
#                 ]
#             ].head()
#         )

#     # Example 2: Batch processing
#     print("\n" + "=" * 60)
#     print("EXAMPLE 2: Batch Processing")
#     print("=" * 60)

#     # summary = extractor.batch_extract(
#     #     input_dir="path/to/papers",
#     #     output_dir="batch_structured_output"
#     # )
#     # print(summary)

#     # Example 3: Working with extracted Pydantic models
#     print("\n" + "=" * 60)
#     print("EXAMPLE 3: Working with Pydantic Models")
#     print("=" * 60)

#     if results["regression_tables"]:
#         reg_table = results["regression_tables"][0]

#         # Access as structured data
#         print(f"\nTable: {reg_table.title}")
#         print(f"Models: {len(reg_table.models)}")

#         for model in reg_table.models:
#             print(f"\n  {model.model_name}:")
#             print(f"    Dependent variable: {model.dependent_variable}")
#             print(f"    Observations: {model.n_observations}")
#             print(f"    R-squared: {model.r_squared}")
#             print(f"    SE type: {model.se_type}")

#             if model.fixed_effects:
#                 print(f"    Fixed effects: {', '.join(model.fixed_effects)}")

#             print(f"    Coefficients:")
#             for coef in model.coefficients[:5]:  # Show first 5
#                 sig = coef.significance or ""
#                 se = f"({coef.std_error:.3f})" if coef.std_error else ""
#                 print(f"      {coef.variable_name}: {coef.coefficient:.3f}{sig} {se}")

#         # Export as JSON
#         json_output = reg_table.model_dump_json(indent=2)
#         print(f"\nJSON export available (first 500 chars):")
#         print(json_output[:500] + "...")

#         # Convert to DataFrame for analysis
#         df = extractor.regression_to_dataframe(reg_table)
#         print(f"\nDataFrame shape: {df.shape}")
#         print(df.head())

# Replace the __main__ block with this:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract structured tables from academic papers (PDF/DOCX)"
    )
    parser.add_argument(
        "input_path", help="Path to PDF or DOCX file, or directory for batch processing"
    )
    parser.add_argument(
        "-o",
        "--output",
        default="structured_output",
        help="Output directory (default: structured_output)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all files in input directory (batch mode)",
    )
    parser.add_argument(
        "--ocr", action="store_true", help="Enable OCR for scanned documents"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "both"],
        default="both",
        help="Output format (default: both)",
    )

    args = parser.parse_args()

    # Initialize extractor
    extractor = AcademicTableExtractor(enable_ocr=args.ocr)

    input_path = Path(args.input_path)

    if args.batch or input_path.is_dir():
        # Batch processing
        print("Running in batch mode...")
        summary = extractor.batch_extract(
            input_dir=str(input_path), output_dir=args.output
        )
        print("\nBatch processing complete!")
        print(summary)
    else:
        # Single file processing
        print(f"Processing single file: {input_path.name}")
        results = extractor.extract_structured_tables(
            str(input_path), output_dir=args.output
        )

        # Print summary
        print("\n" + "=" * 60)
        print("EXTRACTION SUMMARY")
        print("=" * 60)
        print(f"File: {input_path.name}")
        print(f"Regression tables: {len(results['regression_tables'])}")
        print(f"Summary statistics tables: {len(results['summary_tables'])}")
        print(f"Balance tables: {len(results['balance_tables'])}")

        # Show details
        for i, reg_table in enumerate(results["regression_tables"], 1):
            print(f"\nRegression Table {i}: {reg_table.title}")
            print(f"  Models: {len(reg_table.models)}")
            for model in reg_table.models:
                print(
                    f"    {model.model_name}: {len(model.coefficients)} coefficients, N={model.n_observations}"
                )

        for i, sum_table in enumerate(results["summary_tables"], 1):
            print(f"\nSummary Table {i}: {sum_table.title}")
            print(f"  Variables: {len(sum_table.statistics)}")

        for i, bal_table in enumerate(results["balance_tables"], 1):
            print(f"\nBalance Table {i}: {bal_table.title}")
            print(f"  Variables: {len(bal_table.comparisons)}")

        print(f"\nResults saved to: {args.output}/")
