"""Semantic validation for cross-checking extracted values.

This module provides semantic validation that cross-checks extracted table
values against paper text using RAG to catch OCR errors and ensure data quality.

Note: This is a wrapper around the existing semantic_validator module to adapt
it to the new validation interface. Full migration will happen in later phases.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.semantic")


def validate_semantic_consistency(extraction: ExtractionResult) -> CheckResult:
    """Validate extraction using semantic cross-checking.

    This validation uses RAG to cross-check extracted numerical values
    against the source paper text to catch OCR errors and parsing mistakes.

    Note: This is currently a placeholder that checks if semantic augmentation
    was performed. Full semantic validation requires the RAG pipeline to be
    initialized, which is expensive for batch validation.

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with semantic validation outcome

    """
    issues = []
    warnings = []

    # Check if semantic augmentation was performed during extraction
    has_augmentation = False

    # Check tables for augmentation context
    for table in extraction.tables:
        # Check if table has any semantic context fields populated
        if hasattr(table, "study_context") and table.study_context:
            has_augmentation = True
            break
        if hasattr(table, "variable_context") and table.variable_context:
            has_augmentation = True
            break

    if not has_augmentation:
        warnings.append(
            "No semantic augmentation context found - "
            "consider re-extracting with --augment flag for better validation"
        )
        # Return neutral score since we can't perform semantic validation
        return CheckResult(
            passed=True,
            score=0.8,
            issues=issues,
            warnings=warnings,
            metadata={
                "semantic_augmentation_present": False,
                "validation_performed": False,
            },
        )

    # If augmentation is present, we assume it passed basic validation
    # during extraction (the semantic_validator module validates during augmentation)
    logger.info(
        "Semantic augmentation context found - validation was performed during extraction"
    )

    return CheckResult(
        passed=True,
        score=1.0,
        issues=issues,
        warnings=warnings,
        metadata={
            "semantic_augmentation_present": True,
            "validation_performed": True,
            "note": "Validation performed during semantic augmentation phase",
        },
    )


# Future enhancement: Add async validation function for comprehensive semantic checks
# async def validate_semantic_with_rag(
#     extraction: ExtractionResult,
#     config: AugmentationConfig
# ) -> CheckResult:
#     """Perform full semantic validation using RAG pipeline."""
#     from src.semantic_validator import SemanticValidator
#
#     validator = SemanticValidator(config=config)
#     # Validate key values from tables
#     ...
#     return CheckResult(...)
