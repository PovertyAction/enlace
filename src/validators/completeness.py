"""Completeness validation for extracted data.

This module checks the completeness of extracted data including metadata
fields, table counts, and expected content.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.completeness")


def validate_completeness(extraction: ExtractionResult) -> CheckResult:
    """Check completeness of extracted data.

    Checks:
    - Metadata fields populated
    - Tables extracted
    - Expected content present
    - Quality metrics available

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with completeness score and warnings

    """
    issues = []
    warnings = []
    completeness_scores = []

    # Metadata completeness
    metadata = extraction.metadata
    if metadata:
        metadata_fields = ["title", "authors", "year", "doi"]
        populated_fields = 0

        if metadata.title:
            populated_fields += 1
        if metadata.authors and len(metadata.authors) > 0:
            populated_fields += 1
        if metadata.year:
            populated_fields += 1
        if metadata.doi:
            populated_fields += 1

        metadata_completeness = populated_fields / len(metadata_fields)
        completeness_scores.append(metadata_completeness)

        if metadata_completeness < 0.5:
            warnings.append(
                f"Low metadata completeness: {metadata_completeness:.1%} "
                f"({populated_fields}/{len(metadata_fields)} fields)"
            )
    else:
        warnings.append("No metadata extracted")
        completeness_scores.append(0.0)

    # Tables extracted
    tables_count = len(extraction.tables)
    if tables_count == 0:
        warnings.append("No tables extracted - verify paper contains tables")
        completeness_scores.append(0.0)
    else:
        # Score based on table count (1-5 tables = full score, 0 = 0, >5 is bonus)
        table_score = min(1.0, tables_count / 3.0)
        completeness_scores.append(table_score)

    # Figures extracted
    figures_count = len(extraction.figures)
    if figures_count == 0:
        # Not a critical issue, many papers focus on tables
        pass
    else:
        figure_score = min(1.0, figures_count / 3.0)
        completeness_scores.append(figure_score)

    # Quality score present
    if extraction.extraction_quality is not None:
        if extraction.extraction_quality < 0.5:
            warnings.append(
                f"Low overall extraction quality: {extraction.extraction_quality:.2f}"
            )
    else:
        warnings.append("No extraction quality score available")

    # Processing info
    if extraction.processing_time_seconds is None:
        # Not critical but useful for monitoring
        pass

    # Calculate overall completeness score
    if completeness_scores:
        overall_score = sum(completeness_scores) / len(completeness_scores)
    else:
        overall_score = 0.0

    return CheckResult(
        passed=True,  # Completeness warnings only, not failures
        score=round(overall_score, 2),
        issues=issues,
        warnings=warnings,
        metadata={
            "metadata_completeness": metadata_completeness if metadata else 0.0,
            "tables_found": tables_count,
            "figures_found": figures_count,
            "extraction_quality": extraction.extraction_quality,
        },
    )
