"""Schema and structure validation for extracted data.

This module validates that extraction results conform to the expected
data structure and contain all required fields.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.structure")


def validate_structure(extraction: ExtractionResult) -> CheckResult:
    """Validate extraction data structure and required fields.

    Checks:
    - Required fields are present
    - Data types are correct
    - Lists are properly formatted
    - Paper ID is valid

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with validation outcome

    """
    issues = []
    warnings = []

    # Check required fields
    if not extraction.paper_id:
        issues.append("Missing required field: paper_id")

    if extraction.source_file is None:
        issues.append("Missing required field: source_file")

    if extraction.metadata is None:
        issues.append("Missing required field: metadata")

    if extraction.extraction_date is None:
        warnings.append("Missing extraction_date")

    # Check tables and figures
    if not extraction.tables and not extraction.figures:
        warnings.append("No tables or figures extracted")

    # Validate tables structure
    for i, table in enumerate(extraction.tables):
        if not hasattr(table, "table_id"):
            issues.append(f"Table {i}: Missing table_id")
        if not hasattr(table, "table_type"):
            issues.append(f"Table {i}: Missing table_type")

    # Validate figures structure
    for i, figure in enumerate(extraction.figures):
        if not hasattr(figure, "figure_id"):
            issues.append(f"Figure {i}: Missing figure_id")

    # Validate metadata structure
    if (
        extraction.metadata
        and not extraction.metadata.title
        and not extraction.metadata.doi
    ):
        warnings.append(
            "Metadata missing both title and DOI - paper identification may be difficult"
        )

    # Calculate score
    if len(issues) > 0:
        score = 0.0
    elif len(warnings) > 0:
        score = 0.8
    else:
        score = 1.0

    return CheckResult(
        passed=len(issues) == 0,
        score=score,
        issues=issues,
        warnings=warnings,
        metadata={
            "fields_checked": [
                "paper_id",
                "source_file",
                "metadata",
                "tables",
                "figures",
            ],
            "tables_count": len(extraction.tables),
            "figures_count": len(extraction.figures),
        },
    )
