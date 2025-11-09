"""OCR quality validation for numeric data extraction.

This module validates extracted numeric data for common OCR errors including
truncated decimals, p-value range issues, and character substitution artifacts.
"""

import logging
import re

from enlace.models.extraction import ExtractionResult
from enlace.models.validation import CheckResult, ValidationIssue

logger = logging.getLogger("enlace.validators.ocr_quality")


class NumericValidator:
    """Validates extracted numeric data for common OCR errors."""

    @staticmethod
    def extract_numbers(text: str) -> list[str]:
        """Extract all numeric values from text.

        Args:
            text: Text to extract numbers from

        Returns:
            List of numeric strings found in text

        """
        # Pattern matches: integers, decimals, scientific notation, percentages
        pattern = r"-?\d+\.?\d*(?:[eE][+-]?\d+)?%?"
        return re.findall(pattern, text)

    @staticmethod
    def validate_pvalue(value: str) -> dict:
        """Validate p-value extraction.

        Args:
            value: P-value string to validate

        Returns:
            Dict with 'valid' (bool) and 'issues' (list of strings)

        """
        issues = []

        try:
            # Remove percentage sign for parsing
            num_val = float(value.replace("%", ""))

            # P-values should be between 0 and 1 (or 0-100 if percentage)
            if "%" in value:
                if not (0 <= num_val <= 100):
                    issues.append(f"P-value percentage {value} out of range [0, 100]")
            else:
                if not (0 <= num_val <= 1):
                    issues.append(f"P-value {value} out of range [0, 1]")

            # Common OCR error: missing leading zero
            if value.startswith("."):
                issues.append(f"P-value {value} missing leading zero")

        except ValueError:
            issues.append(f"Could not parse {value} as numeric value")

        return {"valid": len(issues) == 0, "issues": issues, "value": value}

    @staticmethod
    def detect_truncated_decimals(numbers: list[str]) -> list[dict]:
        """Detect potential truncated decimals (common Tesseract error).

        Args:
            numbers: List of numeric strings

        Returns:
            List of suspicious numbers with diagnostics

        """
        suspicious = []

        for num in numbers:
            # Check for numbers that might be missing decimal places
            # e.g., "2997" when it should be "2997.23"
            if "." not in num and len(num) >= 4:
                suspicious.append(
                    {
                        "value": num,
                        "issue": "Possible truncated decimal - no decimal point in 4+ digit number",
                    }
                )

            # Check for suspiciously round numbers
            if num.endswith(".0") or num.endswith(".00"):
                suspicious.append(
                    {
                        "value": num,
                        "issue": "Suspiciously round number - possible decimal truncation",
                    }
                )

        return suspicious

    @staticmethod
    def detect_ocr_artifacts(text: str) -> list[dict]:
        """Detect common OCR character substitution errors.

        Args:
            text: Text to check for OCR artifacts

        Returns:
            List of detected artifacts with descriptions

        """
        artifacts = []

        # Common OCR errors in numeric context
        patterns = [
            (r"\bO\b", "0", "Letter O instead of zero"),
            (r"\bl\b", "1", "Letter l instead of one"),
            (r"\bS\b", "5", "Letter S instead of five"),
            (r"\bZ\b", "2", "Letter Z instead of two"),
        ]

        for pattern, replacement, description in patterns:
            if re.search(pattern, text):
                artifacts.append(
                    {
                        "pattern": pattern,
                        "description": description,
                        "suggestion": f"Replace with {replacement}",
                    }
                )

        return artifacts


def validate_ocr_quality(extraction: ExtractionResult) -> CheckResult:
    """Validate OCR quality of extracted tables.

    Checks for:
    - Low OCR confidence scores
    - Common OCR error patterns
    - Invalid numeric ranges (p-values, etc.)
    - Truncated decimals

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with validation outcome

    """
    issues = []
    warnings = []
    metadata = {
        "low_confidence_values": 0,
        "ocr_artifacts_detected": 0,
        "pvalue_issues": 0,
        "truncated_decimal_warnings": 0,
    }

    validator = NumericValidator()

    # Check regression tables
    for table in extraction.tables:
        if not hasattr(table, "models"):
            continue

        table_id = getattr(table, "table_id", "unknown")

        for model_idx, model in enumerate(table.models):
            if not hasattr(model, "coefficients"):
                continue

            for coef in model.coefficients:
                var_name = coef.variable_name

                # Check OCR confidence
                if (
                    hasattr(coef, "ocr_confidence")
                    and coef.ocr_confidence is not None
                    and coef.ocr_confidence < 0.8
                ):
                    metadata["low_confidence_values"] += 1
                    warnings.append(
                        f"{table_id}, model {model_idx + 1}, {var_name}: "
                        f"Low OCR confidence ({coef.ocr_confidence:.2f})"
                    )

                # Validate p-values
                if coef.p_value is not None:
                    pval_check = validator.validate_pvalue(str(coef.p_value))
                    if not pval_check["valid"]:
                        metadata["pvalue_issues"] += 1
                        for issue_msg in pval_check["issues"]:
                            issues.append(
                                ValidationIssue(
                                    check_name="ocr_quality",
                                    severity="warning",
                                    message=issue_msg,
                                    location=f"{table_id}, model {model_idx + 1}, {var_name}",
                                ).message
                            )

                # Check for OCR artifacts in variable names
                if var_name:
                    artifacts = validator.detect_ocr_artifacts(var_name)
                    if artifacts:
                        metadata["ocr_artifacts_detected"] += len(artifacts)
                        for artifact in artifacts:
                            warnings.append(
                                f"{table_id}, {var_name}: {artifact['description']} - {artifact['suggestion']}"
                            )

                # Check for truncated decimals in coefficient values
                if coef.coefficient is not None:
                    coef_str = str(coef.coefficient)
                    truncated = validator.detect_truncated_decimals([coef_str])
                    if truncated:
                        metadata["truncated_decimal_warnings"] += 1
                        warnings.append(
                            f"{table_id}, {var_name}: {truncated[0]['issue']}"
                        )

    # Calculate score
    # Subtract points for issues and warnings
    total_issues = len(issues) + metadata["low_confidence_values"]
    score = max(0.0, 1.0 - (total_issues * 0.1))  # -0.1 per issue

    # Log summary
    if metadata["low_confidence_values"] > 0:
        logger.info(
            f"OCR Quality: {metadata['low_confidence_values']} values with low confidence"
        )
    if metadata["pvalue_issues"] > 0:
        logger.warning(
            f"OCR Quality: {metadata['pvalue_issues']} p-value issues detected"
        )
    if metadata["ocr_artifacts_detected"] > 0:
        logger.warning(
            f"OCR Quality: {metadata['ocr_artifacts_detected']} potential OCR artifacts detected"
        )

    return CheckResult(
        passed=len(issues) == 0,
        score=score,
        issues=issues,
        warnings=warnings,
        metadata=metadata,
    )
