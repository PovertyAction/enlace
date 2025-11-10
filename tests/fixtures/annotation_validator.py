"""Pydantic models for validating ground truth annotations.

This module provides validation for benchmark test annotations, ensuring
they conform to the expected schema and can be used for accuracy testing.
"""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class GroundTruthCoefficient(BaseModel):
    """Ground truth for a single regression coefficient."""

    variable_name: str
    coefficient: float | None = None
    std_error: float | None = None
    t_statistic: float | None = None
    p_value: float | None = None
    significance: str | None = Field(None, pattern=r"^\*{1,3}$")
    ci_lower: float | None = None
    ci_upper: float | None = None


class GroundTruthModel(BaseModel):
    """Ground truth for a single regression model."""

    model_number: int
    dependent_variable: str | None = None
    coefficients: list[GroundTruthCoefficient]
    n_observations: int | None = None
    r_squared: float | None = None
    adjusted_r_squared: float | None = None
    f_statistic: float | None = None
    se_type: str | None = None
    fixed_effects: list[str] = Field(default_factory=list)
    clustering: str | None = None


class GroundTruthStatistic(BaseModel):
    """Ground truth for a summary statistic."""

    variable_name: str
    n_obs: int | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    p10: float | None = None
    p25: float | None = None
    p50: float | None = None
    p75: float | None = None
    p90: float | None = None


class GroundTruthComparison(BaseModel):
    """Ground truth for a balance table comparison."""

    variable_name: str
    control_mean: float | None = None
    control_sd: float | None = None
    control_n: int | None = None
    treatment_mean: float | None = None
    treatment_sd: float | None = None
    treatment_n: int | None = None
    difference: float | str | None = None  # Allow string for values like ".04**"
    p_value: float | None = None
    normalized_difference: float | None = None


class GroundTruthTable(BaseModel):
    """Ground truth for a single table."""

    table_id: str
    table_number: str | None = None
    title: str | None = None
    page_number: int | None = None
    table_type: str = Field(
        ..., pattern=r"^(regression|summary_statistics|balance|other)$"
    )
    notes: str | None = None

    # For regression tables
    models: list[GroundTruthModel] = Field(default_factory=list)

    # For summary statistics tables
    statistics: list[GroundTruthStatistic] = Field(default_factory=list)

    # For balance tables
    comparisons: list[GroundTruthComparison] = Field(default_factory=list)

    @field_validator("models", "statistics", "comparisons")
    @classmethod
    def check_table_type_consistency(cls, v, info):
        """Validate that table content matches declared type."""
        if info.data.get("table_type") == "regression" and info.field_name == "models":
            if not v:
                raise ValueError("Regression tables must have at least one model")
        elif (
            info.data.get("table_type") == "summary_statistics"
            and info.field_name == "statistics"
        ):
            if not v:
                raise ValueError(
                    "Summary statistics tables must have at least one statistic"
                )
        elif (
            info.data.get("table_type") == "balance"
            and info.field_name == "comparisons"
            and not v
        ):
            raise ValueError("Balance tables must have at least one comparison")
        return v


class GroundTruthFigure(BaseModel):
    """Ground truth for a figure."""

    figure_id: str
    figure_number: str | None = None
    caption: str | None = None
    page_number: int | None = None
    figure_type: str | None = Field(
        None, pattern=r"^(chart|diagram|map|photo|plot|other)$"
    )


class PaperMetadata(BaseModel):
    """Ground truth for paper metadata."""

    title: str
    authors: list[str]
    year: int
    doi: str | None = None
    journal: str | None = None
    abstract: str | None = None

    @field_validator("year")
    @classmethod
    def validate_year(cls, v):
        """Validate year is reasonable."""
        if v < 1900 or v > datetime.now().year + 1:
            raise ValueError(f"Invalid year: {v}")
        return v


class SemanticContext(BaseModel):
    """Optional semantic context for augmentation benchmarking."""

    variable_definitions: dict[str, str] = Field(default_factory=dict)
    treatment_description: str | None = None
    study_design: str | None = None
    population_description: str | None = None


class GroundTruth(BaseModel):
    """Complete ground truth data for a paper."""

    metadata: PaperMetadata
    tables: list[GroundTruthTable]
    figures: list[GroundTruthFigure] = Field(default_factory=list)
    semantic_context: SemanticContext = Field(default_factory=SemanticContext)


class Annotation(BaseModel):
    """Complete annotation file structure."""

    paper_id: str
    source_file: str
    annotation_date: datetime = Field(default_factory=datetime.now)
    annotator: str | None = None
    ground_truth: GroundTruth

    @field_validator("source_file")
    @classmethod
    def validate_source_file(cls, v):
        """Validate source file path format."""
        if not v.endswith(".pdf"):
            raise ValueError("Source file must be a PDF")
        return v

    def save(self, output_path: Path) -> None:
        """Save annotation to JSON file.

        Args:
            output_path: Path to save annotation JSON

        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2, exclude_none=True))

    @classmethod
    def load(cls, annotation_path: Path) -> "Annotation":
        """Load annotation from JSON file.

        Args:
            annotation_path: Path to annotation JSON

        Returns:
            Validated Annotation instance

        Raises:
            FileNotFoundError: If annotation file doesn't exist
            ValidationError: If annotation doesn't match schema

        """
        if not annotation_path.exists():
            raise FileNotFoundError(f"Annotation not found: {annotation_path}")

        with annotation_path.open("r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
