"""Accuracy validation for extracted data.

This module validates extraction accuracy based on internal consistency
and quality metrics.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.tables import RegressionTable
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.accuracy")


def validate_accuracy(extraction: ExtractionResult) -> CheckResult:
    """Check extraction accuracy based on internal consistency.

    Checks:
    - Table quality scores
    - Regression table completeness
    - Empty or malformed tables
    - Coefficient data quality

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with accuracy assessment

    """
    issues = []
    warnings = []

    tables = extraction.tables
    if not tables:
        # No tables to validate
        return CheckResult(
            passed=True,
            score=1.0,
            issues=issues,
            warnings=["No tables to validate"],
            metadata={"tables_validated": 0},
        )

    # Track quality metrics
    low_quality_tables = []
    empty_tables = []
    quality_scores = []

    # Validate each table
    for table in tables:
        table_id = getattr(table, "table_id", "unknown")

        # Check for quality score
        if hasattr(table, "quality_score"):
            quality = table.quality_score
            if quality is not None:
                quality_scores.append(quality)
                if quality < 0.5:
                    low_quality_tables.append(table_id)
                    warnings.append(f"{table_id}: Low quality score ({quality:.2f})")

        # Check regression tables specifically
        if isinstance(table, RegressionTable):
            if not table.models or len(table.models) == 0:
                empty_tables.append(table_id)
                issues.append(f"{table_id}: Regression table has no models")
            else:
                # Check each model
                for i, model in enumerate(table.models):
                    if not model.coefficients or len(model.coefficients) == 0:
                        warnings.append(
                            f"{table_id}, model {i + 1}: No coefficients extracted"
                        )
                    else:
                        # Check coefficient quality
                        null_coefs = sum(
                            1 for c in model.coefficients if c.coefficient is None
                        )
                        if null_coefs > 0:
                            warnings.append(
                                f"{table_id}, model {i + 1}: "
                                f"{null_coefs}/{len(model.coefficients)} coefficients are null"
                            )

    # Report findings
    if low_quality_tables:
        warnings.append(
            f"Tables with low quality scores: {', '.join(low_quality_tables)}"
        )

    if empty_tables:
        issues.append(f"Empty or malformed tables: {', '.join(empty_tables)}")

    # Calculate accuracy score
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        accuracy_score = avg_quality
    else:
        # No quality scores available, use heuristic
        if len(issues) > 0:
            accuracy_score = 0.3
        elif len(warnings) > 0:
            accuracy_score = 0.7
        else:
            accuracy_score = 1.0

    return CheckResult(
        passed=len(issues) == 0,
        score=round(accuracy_score, 2),
        issues=issues,
        warnings=warnings,
        metadata={
            "tables_validated": len(tables),
            "low_quality_tables": low_quality_tables,
            "empty_tables": empty_tables,
            "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 2)
            if quality_scores
            else None,
        },
    )
