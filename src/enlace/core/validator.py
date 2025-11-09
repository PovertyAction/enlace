"""Validation orchestrator for extracted research data.

This module provides the main ExtractionValidator class that orchestrates
comprehensive quality assurance checks on extracted paper data.
"""

import logging
from datetime import datetime
from pathlib import Path

from enlace.core.config import ValidationConfig
from enlace.exceptions import ValidationError
from enlace.models.extraction import ExtractionResult
from enlace.models.validation import (
    BatchValidationResult,
    CheckResult,
    ValidationIssue,
    ValidationResult,
    ValidationWarning,
)

logger = logging.getLogger("enlace.validator")


class ExtractionValidator:
    """Validate extracted research data.

    Performs configurable validation checks on extraction results to ensure
    data quality and consistency.

    Example:
        >>> config = ValidationConfig(level="comprehensive")
        >>> validator = ExtractionValidator(config)
        >>> result = validator.validate(extraction_result)
        >>> if not result.passed:
        ...     print(f"Validation failed: {result.issues}")

    """

    def __init__(self, config: ValidationConfig) -> None:
        """Initialize validator with configuration.

        Args:
            config: Validation configuration

        Raises:
            ConfigError: If configuration is invalid

        """
        self.config = config
        # Import validation check modules dynamically
        self._check_modules = self._load_check_modules()

    def _load_check_modules(self) -> dict:
        """Load validation check modules.

        Returns:
            Dictionary mapping check names to validation functions

        """
        from enlace.validators import (
            accuracy,
            completeness,
            missing_data,
            ocr_quality,
            semantic,
            statistical,
            structure,
        )

        return {
            "structure": structure.validate_structure,
            "completeness": completeness.validate_completeness,
            "accuracy": accuracy.validate_accuracy,
            "statistical_consistency": statistical.validate_statistical_consistency,
            "missing_data": missing_data.validate_missing_data,
            "semantic_validation": semantic.validate_semantic_consistency,
            "ocr_quality": ocr_quality.validate_ocr_quality,
        }

    def validate(
        self,
        extraction: ExtractionResult | Path,
        level: str | None = None,
        custom_checks: list[str] | None = None,
    ) -> ValidationResult:
        """Validate extraction result.

        Args:
            extraction: ExtractionResult object or path to extraction.json
            level: Override validation level from config (quick, standard, comprehensive)
            custom_checks: Optional custom list of checks (overrides level)

        Returns:
            ValidationResult with check results and recommendations

        Raises:
            ValidationError: If validation cannot be performed
            FileNotFoundError: If extraction path does not exist

        """
        # Load extraction if path provided
        if isinstance(extraction, Path):
            if not extraction.exists():
                raise FileNotFoundError(f"Extraction file not found: {extraction}")
            extraction = ExtractionResult.parse_file(extraction)

        # Get checks to run (custom_checks override level)
        checks_to_run = self.config.get_checks_for_level(level, custom_checks)
        logger.info(f"Running {len(checks_to_run)} validation checks: {checks_to_run}")

        # Initialize result
        result = ValidationResult(
            paper_id=extraction.paper_id,
            extraction_path=extraction.source_file,
        )

        # Run each check
        for check_name in checks_to_run:
            check_func = self._check_modules.get(check_name)
            if not check_func:
                logger.warning(f"Check not found: {check_name}")
                continue

            try:
                check_result = check_func(extraction)
                result.checks[check_name] = check_result

                # Collect issues and warnings from CheckResult
                for issue_msg in check_result.issues:
                    result.issues.append(
                        ValidationIssue(
                            check_name=check_name,
                            severity="error",
                            message=issue_msg,
                        )
                    )

                for warning_msg in check_result.warnings:
                    result.warnings.append(
                        ValidationWarning(check_name=check_name, message=warning_msg)
                    )

            except Exception as e:
                logger.error(f"Check {check_name} failed: {e}", exc_info=True)
                result.warnings.append(
                    ValidationWarning(
                        check_name=check_name,
                        message=f"Check failed: {str(e)}",
                    )
                )

        # Calculate overall score and pass/fail
        result.score = self._calculate_score(result)
        result.passed = len(result.issues) == 0 and result.score >= 0.7

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def validate_batch(
        self, extractions: list[ExtractionResult] | Path, level: str | None = None
    ) -> BatchValidationResult:
        """Validate multiple extractions in batch.

        Args:
            extractions: List of ExtractionResults or directory containing extractions
            level: Validation level override

        Returns:
            BatchValidationResult with aggregated statistics

        Raises:
            ValidationError: If batch validation fails

        """
        # Load extractions from directory if path provided
        if isinstance(extractions, Path):
            if not extractions.is_dir():
                raise ValidationError(f"Not a directory: {extractions}")

            # Find all extraction.json files
            extraction_files = list(extractions.glob("*/extraction.json"))
            if not extraction_files:
                logger.warning(f"No extraction.json files found in {extractions}")
                return BatchValidationResult(
                    batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    papers_validated=0,
                    papers_passed=0,
                    papers_failed=0,
                )

            # Load each extraction
            extractions = []
            for extract_file in extraction_files:
                try:
                    extractions.append(ExtractionResult.parse_file(extract_file))
                except Exception as e:
                    logger.error(f"Failed to load {extract_file}: {e}")
                    continue

        # Validate each extraction
        results = []
        for extraction in extractions:
            try:
                result = self.validate(extraction, level=level)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Validation failed for {extraction.paper_id}: {e}", exc_info=True
                )
                continue

        # Compile batch summary
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        batch_result = BatchValidationResult(
            batch_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            papers_validated=len(results),
            papers_passed=len(passed),
            papers_failed=len(failed),
            avg_score=sum(r.score for r in results) / len(results) if results else 0.0,
            total_issues=sum(len(r.issues) for r in results),
            total_warnings=sum(len(r.warnings) for r in results),
            results=results,
        )

        logger.info(
            f"Batch validation complete: "
            f"{batch_result.papers_passed}/{batch_result.papers_validated} passed, "
            f"avg_score={batch_result.avg_score:.2f}"
        )

        return batch_result

    def _calculate_score(self, result: ValidationResult) -> float:
        """Calculate weighted validation score from check results.

        Args:
            result: Validation result with check results

        Returns:
            Weighted average score (0.0-1.0)

        """
        checks = result.checks

        if not checks:
            return 0.0

        # Weights for different checks
        weights = {
            "structure": 0.30,
            "completeness": 0.20,
            "accuracy": 0.30,
            "statistical_consistency": 0.10,
            "missing_data": 0.10,
            "semantic_validation": 0.10,
        }

        total_score = 0.0
        total_weight = 0.0

        for check_name, check_result in checks.items():
            if isinstance(check_result, CheckResult):
                weight = weights.get(check_name, 0.1)
                total_score += check_result.score * weight
                total_weight += weight

        if total_weight > 0:
            return round(total_score / total_weight, 2)
        else:
            return 0.0

    def _generate_recommendations(self, result: ValidationResult) -> list[str]:
        """Generate actionable recommendations based on validation results.

        Args:
            result: Validation result to analyze

        Returns:
            List of recommendation strings

        """
        recommendations = []
        checks = result.checks

        # Low metadata completeness
        if "completeness" in checks:
            completeness_result = checks["completeness"]
            if isinstance(completeness_result, CheckResult):
                metadata_comp = completeness_result.metadata.get(
                    "metadata_completeness", 1.0
                )
                if metadata_comp < 0.5:
                    recommendations.append(
                        "Improve metadata extraction: Use bibliography skill for "
                        "better author, DOI, and citation extraction"
                    )

                # No tables extracted
                if completeness_result.metadata.get("tables_found", 0) == 0:
                    recommendations.append(
                        "No tables extracted: Verify source PDF quality, "
                        "try OCR if scanned document"
                    )

        # Low accuracy
        if "accuracy" in checks:
            accuracy_result = checks["accuracy"]
            if isinstance(accuracy_result, CheckResult) and accuracy_result.score < 0.7:
                recommendations.append(
                    "Low extraction accuracy: Review table extraction settings, "
                    "consider using docling with VLM for complex tables"
                )

        # Statistical inconsistencies
        if "statistical_consistency" in checks:
            stat_result = checks["statistical_consistency"]
            if isinstance(stat_result, CheckResult):
                checks_performed = stat_result.metadata.get("checks_performed", 0)
                checks_passed = stat_result.metadata.get("checks_passed", 0)
                if checks_performed > 0:
                    pass_rate = checks_passed / checks_performed
                    if pass_rate < 0.8:
                        recommendations.append(
                            "Statistical inconsistencies detected: Manual review "
                            "recommended for regression tables"
                        )

        # High missing data
        if "missing_data" in checks:
            missing_result = checks["missing_data"]
            if isinstance(missing_result, CheckResult) and missing_result.score < 0.7:
                recommendations.append(
                    "High missing data rates: Check PDF table formatting, "
                    "may need custom extraction rules"
                )

        # Overall score
        if result.score < 0.5:
            recommendations.append(
                "Overall quality below threshold: Consider re-extraction with "
                "different settings or manual review"
            )

        return recommendations
