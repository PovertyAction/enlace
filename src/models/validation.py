"""Pydantic models for validation results and check outcomes."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from enlace.exceptions import ValidationError
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Critical validation issue."""

    check_name: str
    severity: str = "error"
    message: str
    location: str | None = None


class ValidationWarning(BaseModel):
    """Non-critical validation warning."""

    check_name: str
    message: str
    location: str | None = None


class CheckResult(BaseModel):
    """Result from individual validation check."""

    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableValidationResult(BaseModel):
    """Validation result for single table."""

    table_id: str
    passed: bool
    quality_score: float
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Result from validation operation."""

    paper_id: str
    validation_date: datetime = Field(default_factory=datetime.now)
    extraction_path: Path

    # Status
    passed: bool = Field(description="True if all checks passed")
    score: float = Field(ge=0.0, le=1.0, description="Overall validation score")

    # Issues
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="Critical issues that cause failure"
    )
    warnings: list[ValidationWarning] = Field(
        default_factory=list, description="Non-critical warnings"
    )

    # Check results
    checks: dict[str, CheckResult] = Field(default_factory=dict)
    table_validations: list[TableValidationResult] = Field(default_factory=list)

    # Recommendations
    recommendations: list[str] = Field(default_factory=list)

    def save(self, output_dir: Path) -> None:
        """Save validation report to JSON file.

        Args:
            output_dir: Directory to save validation report

        Raises:
            ValidationError: If save operation fails

        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save validation report
            report_path = output_dir / f"{self.paper_id}_validation.json"
            with open(report_path, "w") as f:
                json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

        except Exception as e:
            raise ValidationError(f"Failed to save validation report: {e}") from e


class BatchValidationResult(BaseModel):
    """Result from batch validation of multiple extractions."""

    total_papers: int
    papers_passed: int
    papers_failed: int
    average_score: float
    validation_results: list[ValidationResult] = Field(default_factory=list)

    # Aggregated statistics
    total_issues: int = 0
    total_warnings: int = 0
    common_issues: dict[str, int] = Field(default_factory=dict)

    def save(self, output_dir: Path) -> None:
        """Save batch validation summary.

        Args:
            output_dir: Directory to save summary

        Raises:
            ValidationError: If save operation fails

        """
        try:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save summary
            summary_path = output_dir / "batch_validation_summary.json"
            with open(summary_path, "w") as f:
                json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

        except Exception as e:
            raise ValidationError(
                f"Failed to save batch validation summary: {e}"
            ) from e
