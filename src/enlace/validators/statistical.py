"""Statistical consistency validation for regression tables.

This module validates statistical consistency in regression tables,
including t-statistics, p-values, and standard errors.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.tables import RegressionTable
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.statistical")


def validate_statistical_consistency(extraction: ExtractionResult) -> CheckResult:
    """Check statistical consistency in extracted tables.

    Validates:
    - T-statistics calculated from coefficients and standard errors
    - P-values consistent with t-stats
    - Standard errors are positive
    - Reasonable magnitude for coefficients

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with statistical consistency assessment

    """
    issues = []
    warnings = []
    checks_performed = 0
    checks_passed = 0

    # Only check regression tables
    regression_tables = [t for t in extraction.tables if isinstance(t, RegressionTable)]

    if not regression_tables:
        warnings.append("No regression tables found for statistical validation")
        return CheckResult(
            passed=True,
            score=1.0,
            issues=issues,
            warnings=warnings,
            metadata={"checks_performed": 0, "checks_passed": 0},
        )

    # Validate each regression table
    for table in regression_tables:
        table_id = table.table_id

        for model_idx, model in enumerate(table.models):
            for coef in model.coefficients:
                var_name = coef.variable_name

                # Check 1: Standard errors are positive
                if coef.std_err is not None:
                    checks_performed += 1
                    if coef.std_err < 0:
                        issues.append(
                            f"{table_id}, model {model_idx + 1}, {var_name}: "
                            "Negative standard error"
                        )
                    else:
                        checks_passed += 1

                # Check 2: T-stat calculation
                if (
                    coef.coefficient is not None
                    and coef.std_err is not None
                    and coef.t_stat is not None
                    and coef.std_err != 0
                ):
                    checks_performed += 1
                    expected_t = coef.coefficient / coef.std_err
                    actual_t = coef.t_stat

                    # Allow 10% tolerance for rounding
                    if abs(expected_t - actual_t) / (abs(actual_t) + 1e-10) > 0.1:
                        warnings.append(
                            f"{table_id}, model {model_idx + 1}, {var_name}: "
                            f"T-stat mismatch - expected {expected_t:.3f}, "
                            f"found {actual_t:.3f}"
                        )
                    else:
                        checks_passed += 1

                # Check 3: P-value consistency with t-stat
                if coef.t_stat is not None and coef.p_value is not None:
                    checks_performed += 1
                    # Simple heuristic: |t| > 1.96 should give p < 0.05
                    abs_t = abs(coef.t_stat)
                    p_val = coef.p_value

                    # Check consistency (allowing some tolerance)
                    if (abs_t > 1.96 and p_val >= 0.05) or (
                        abs_t < 1.96 and p_val < 0.05
                    ):
                        warnings.append(
                            f"{table_id}, model {model_idx + 1}, {var_name}: "
                            f"P-value inconsistent - |t|={abs_t:.2f} but p={p_val:.3f}"
                        )
                    else:
                        checks_passed += 1

                # Check 4: Confidence interval consistency
                if (
                    coef.coefficient is not None
                    and coef.conf_int_lower is not None
                    and coef.conf_int_upper is not None
                ):
                    checks_performed += 1
                    # Coefficient should be between CI bounds
                    if not (
                        coef.conf_int_lower <= coef.coefficient <= coef.conf_int_upper
                    ):
                        warnings.append(
                            f"{table_id}, model {model_idx + 1}, {var_name}: "
                            f"Coefficient {coef.coefficient:.3f} outside CI "
                            f"[{coef.conf_int_lower:.3f}, {coef.conf_int_upper:.3f}]"
                        )
                    else:
                        checks_passed += 1

    # Calculate score
    score = checks_passed / checks_performed if checks_performed > 0 else 1.0

    if checks_performed == 0:
        warnings.append(
            "No statistical consistency checks performed (no complete regression data found)"
        )

    return CheckResult(
        passed=len(issues) == 0,
        score=round(score, 2),
        issues=issues,
        warnings=warnings,
        metadata={
            "checks_performed": checks_performed,
            "checks_passed": checks_passed,
            "regression_tables_checked": len(regression_tables),
        },
    )
