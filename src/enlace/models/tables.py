"""Pydantic models for table structures (regression, summary stats, balance tables)."""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


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

    # OCR quality metadata (optional)
    ocr_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="OCR confidence score (0.0-1.0)"
    )
    ocr_backend_used: str | None = Field(
        None,
        description="OCR backend that extracted this value (tesseract/easyocr/hybrid)",
    )
    ocr_original_text: str | None = Field(
        None, description="Original OCR text before numeric parsing"
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

    # OCR quality metadata (optional)
    ocr_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="OCR confidence score (0.0-1.0)"
    )
    ocr_backend_used: str | None = Field(
        None,
        description="OCR backend that extracted this value (tesseract/easyocr/hybrid)",
    )
    ocr_original_text: str | None = Field(
        None, description="Original OCR text before numeric parsing"
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

    # OCR quality metadata (optional)
    ocr_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="OCR confidence score (0.0-1.0)"
    )
    ocr_backend_used: str | None = Field(
        None,
        description="OCR backend that extracted this value (tesseract/easyocr/hybrid)",
    )
    ocr_original_text: str | None = Field(
        None, description="Original OCR text before numeric parsing"
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
        """Parse float values.

        Note: Parentheses are removed but NOT treated as negatives.
        They typically represent standard errors, not negative values.
        """
        if v is None or v == "":
            return None
        if isinstance(v, int | float):
            return float(v)
        try:
            v_str = str(v).strip().replace(",", "").replace("%", "").replace("*", "")
            # Remove parentheses but don't treat as negative
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
