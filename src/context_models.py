"""Pydantic models for semantic context augmentation.

This module defines models for rich semantic context extracted from
research papers to augment parsed table data.
"""

from typing import Any

from pydantic import BaseModel, Field


class VariableContext(BaseModel):
    """Rich semantic context for a variable in a table.

    Provides detailed information about what a variable measures,
    how it's operationalized, units, and data sources.
    """

    variable_name: str = Field(description="Name of the variable")
    definition: str | None = Field(
        None, description="What this variable measures or represents"
    )
    units: str | None = Field(None, description="Units of measurement")
    measurement_method: str | None = Field(
        None, description="How the variable was measured or collected"
    )
    data_source: str | None = Field(
        None, description="Source of data (survey, administrative, etc.)"
    )
    scale_range: str | None = Field(None, description="Valid range or scale of values")
    coding: str | None = Field(None, description="Coding scheme (e.g., 1=Yes, 0=No)")
    source_sections: list[str] = Field(
        default_factory=list, description="Paper sections where info was found"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in extracted context (0-1)"
    )
    embedding_similarity: float | None = Field(
        None, ge=0.0, le=1.0, description="Semantic similarity score"
    )


class TreatmentContext(BaseModel):
    """Detailed description of treatment/intervention arm.

    Critical for understanding what the treatment actually was
    and enabling comparison across studies during harmonization.
    """

    arm_name: str = Field(
        description="Name of treatment arm (e.g., Treatment, Control)"
    )
    description: str | None = Field(
        None, description="Detailed description of what this arm received"
    )
    duration: str | None = Field(None, description="Duration of intervention")
    intensity: str | None = Field(None, description="Intensity, dosage, or frequency")
    delivery_mechanism: str | None = Field(
        None, description="How intervention was delivered"
    )
    timing: str | None = Field(
        None, description="When intervention occurred (dates, timeline)"
    )
    cost_if_applicable: str | None = Field(
        None, description="Cost of intervention per participant"
    )
    compliance_rate: float | None = Field(
        None, ge=0.0, le=1.0, description="Treatment compliance/take-up rate"
    )
    source_sections: list[str] = Field(
        default_factory=list, description="Paper sections where info was found"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in extracted context (0-1)"
    )


class StudyContext(BaseModel):
    """Overall study design and sample context.

    Provides information about study design, sample characteristics,
    and methodology needed for quality assessment and harmonization.
    """

    population_description: str | None = Field(
        None, description="Description of study population"
    )
    sample_size: int | None = Field(None, gt=0, description="Total sample size")
    study_design: str | None = Field(
        None,
        description="Type of study design (RCT, quasi-experimental, observational)",
    )
    randomization_unit: str | None = Field(
        None, description="Unit of randomization if RCT (individual, cluster, etc.)"
    )
    geographic_setting: str | None = Field(
        None, description="Geographic location and setting"
    )
    time_period: str | None = Field(None, description="Time period of data collection")
    inclusion_criteria: list[str] = Field(
        default_factory=list, description="Study inclusion criteria"
    )
    exclusion_criteria: list[str] = Field(
        default_factory=list, description="Study exclusion criteria"
    )
    attrition_rate: float | None = Field(
        None, ge=0.0, le=1.0, description="Attrition/dropout rate"
    )
    power_calculation: str | None = Field(
        None, description="Power calculation details if reported"
    )
    source_sections: list[str] = Field(
        default_factory=list, description="Paper sections where info was found"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in extracted context (0-1)"
    )


class MethodsContext(BaseModel):
    """Statistical methods and analysis details for a specific table.

    Provides information about estimation methods, standard errors,
    controls, and other methodological details needed for replication.
    """

    estimation_method: str | None = Field(
        None, description="Statistical estimation method (OLS, IV, logit, etc.)"
    )
    standard_error_type: str | None = Field(
        None, description="Type of standard errors (robust, clustered, etc.)"
    )
    clustering_variable: str | None = Field(
        None, description="Variable used for clustering if clustered SEs"
    )
    control_variables: list[str] = Field(
        default_factory=list, description="Control variables included in models"
    )
    fixed_effects: list[str] = Field(
        default_factory=list, description="Fixed effects included"
    )
    missing_data_handling: str | None = Field(
        None, description="How missing data was handled"
    )
    weights: str | None = Field(None, description="Weighting scheme if applicable")
    software: str | None = Field(None, description="Statistical software used")
    model_selection_criteria: str | None = Field(
        None, description="Criteria for model selection if applicable"
    )
    source_sections: list[str] = Field(
        default_factory=list, description="Paper sections where info was found"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in extracted context (0-1)"
    )


class OutcomeContext(BaseModel):
    """Detailed information about outcome measurement.

    Critical for understanding how outcomes were measured and
    enabling harmonization across studies with different measures.
    """

    outcome_variable_name: str = Field(description="Name of outcome variable")
    measurement_method: str | None = Field(None, description="How outcome was measured")
    instrument: str | None = Field(
        None, description="Survey instrument or measurement tool used"
    )
    scale: str | None = Field(None, description="Scale or range of outcome measure")
    measurement_timing: str | None = Field(
        None, description="When outcome was measured (baseline, endline, etc.)"
    )
    data_collection_method: str | None = Field(
        None, description="How data was collected (survey, admin records, etc.)"
    )
    higher_is_better: bool | None = Field(
        None, description="Whether higher values indicate better outcomes"
    )
    source_sections: list[str] = Field(
        default_factory=list, description="Paper sections where info was found"
    )
    confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in extracted context (0-1)"
    )


class ValidationResult(BaseModel):
    """Result of cross-validating a parsed value against paper text.

    Documents whether a parsed numerical value matches what's
    extracted via semantic search, with confidence and source info.
    """

    parsed_value: float | str | None = Field(
        None, description="Value extracted by table parser"
    )
    rag_extracted_value: float | str | None = Field(
        None, description="Value extracted via semantic search + LLM"
    )
    matches: bool = Field(description="Whether values match within threshold")
    discrepancy_size: float | None = Field(
        None, description="Size of discrepancy if values differ"
    )
    relative_discrepancy: float | None = Field(
        None, description="Relative discrepancy as percentage"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in validation result"
    )
    source_text: str | None = Field(
        None, description="Text excerpt where value was found"
    )
    source_page: int | None = Field(
        None, description="Page number where value was found"
    )


class HarmonizationMetadata(BaseModel):
    """Structured metadata prepared for downstream harmonization.

    Standardized fields that enable automated matching and
    comparison of variables across multiple studies.
    """

    outcome_measure_category: str | None = Field(
        None,
        description="Standardized outcome category (e.g., child_health, income, education)",
    )
    outcome_operationalization: str | None = Field(
        None,
        description="Specific operationalization (e.g., height_for_age_zscore, test_scores)",
    )
    outcome_scale_type: str | None = Field(
        None,
        description="Scale type (continuous, binary, categorical, count)",
    )
    treatment_type: str | None = Field(
        None,
        description="Standardized treatment type (e.g., cash_transfer, training, subsidies)",
    )
    treatment_amount: float | None = Field(
        None, description="Treatment amount if applicable (standardized units)"
    )
    treatment_duration_months: int | None = Field(
        None, description="Treatment duration in months"
    )
    sample_population_type: str | None = Field(
        None,
        description="Population type (e.g., rural_kenya_children, urban_india_women)",
    )
    study_quality_tier: str | None = Field(
        None, description="Quality tier (high_rct, medium_quasi, low_observational)"
    )
    comparable_to_studies: list[str] = Field(
        default_factory=list,
        description="IDs of studies with comparable methods/populations",
    )
    harmonization_notes: dict[str, Any] = Field(
        default_factory=dict, description="Additional notes for harmonization"
    )


class TableContext(BaseModel):
    """Comprehensive semantic context for an entire table.

    Combines all context types to provide full understanding
    of what a table contains and how to interpret it.
    """

    table_id: str = Field(description="Table identifier")
    table_description: str | None = Field(
        None, description="High-level description of table content and purpose"
    )
    study_context: StudyContext | None = Field(
        None, description="Study-level context (shared across tables)"
    )
    treatment_contexts: list[TreatmentContext] = Field(
        default_factory=list, description="Treatment arm descriptions"
    )
    variable_contexts: dict[str, VariableContext] = Field(
        default_factory=dict, description="Context for each variable (keyed by name)"
    )
    outcome_contexts: dict[str, OutcomeContext] = Field(
        default_factory=dict, description="Outcome measurement details"
    )
    methods_context: MethodsContext | None = Field(
        None, description="Statistical methods for this table"
    )
    harmonization_metadata: HarmonizationMetadata | None = Field(
        None, description="Metadata prepared for harmonization"
    )
    overall_confidence: float | None = Field(
        None, ge=0.0, le=1.0, description="Overall confidence in table augmentation"
    )
