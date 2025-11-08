"""Missing data validation for extracted tables.

This module identifies missing data patterns in extracted tables including
empty cells, systematic missing patterns, and incomplete extractions.
"""

import logging

from enlace.models.extraction import ExtractionResult
from enlace.models.tables import BalanceTable, RegressionTable, SummaryStatisticsTable
from enlace.models.validation import CheckResult

logger = logging.getLogger("enlace.validators.missing_data")


def validate_missing_data(extraction: ExtractionResult) -> CheckResult:
    """Identify missing data patterns in tables.

    Checks:
    - High proportion of missing values in tables
    - Systematic missing patterns
    - Incomplete coefficient data in regression tables
    - Missing statistics in summary tables

    Args:
        extraction: ExtractionResult to validate

    Returns:
        CheckResult with missing data assessment

    """
    issues = []
    warnings = []

    tables = extraction.tables
    if not tables:
        return CheckResult(
            passed=True,
            score=1.0,
            issues=issues,
            warnings=["No tables to check for missing data"],
            metadata={"tables_checked": 0},
        )

    tables_with_issues = 0
    total_missing_rate = 0.0
    tables_checked = 0

    # Check each table type
    for table in tables:
        table_id = getattr(table, "table_id", "unknown")

        if isinstance(table, RegressionTable):
            # Check regression table completeness
            missing_info = _check_regression_table(table, table_id)
            if missing_info["warnings"]:
                warnings.extend(missing_info["warnings"])
                tables_with_issues += 1
            if missing_info["issues"]:
                issues.extend(missing_info["issues"])
                tables_with_issues += 1

            total_missing_rate += missing_info["missing_rate"]
            tables_checked += 1

        elif isinstance(table, SummaryStatisticsTable):
            # Check summary statistics table
            missing_info = _check_summary_table(table, table_id)
            if missing_info["warnings"]:
                warnings.extend(missing_info["warnings"])
                tables_with_issues += 1

            total_missing_rate += missing_info["missing_rate"]
            tables_checked += 1

        elif isinstance(table, BalanceTable):
            # Check balance table
            missing_info = _check_balance_table(table, table_id)
            if missing_info["warnings"]:
                warnings.extend(missing_info["warnings"])
                tables_with_issues += 1

            total_missing_rate += missing_info["missing_rate"]
            tables_checked += 1

    # Calculate overall score
    if tables_checked > 0:
        avg_missing_rate = total_missing_rate / tables_checked
        # Score inversely proportional to missing rate
        # 0% missing = 1.0, 50% missing = 0.5, 100% missing = 0.0
        score = max(0.0, 1.0 - avg_missing_rate)
    else:
        score = 1.0

    # Adjust score based on issues
    if len(issues) > 0:
        score = min(score, 0.3)
    elif tables_with_issues > len(tables) / 2:
        score = min(score, 0.7)

    return CheckResult(
        passed=len(issues) == 0,
        score=round(score, 2),
        issues=issues,
        warnings=warnings,
        metadata={
            "tables_checked": tables_checked,
            "tables_with_issues": tables_with_issues,
            "avg_missing_rate": round(avg_missing_rate, 2)
            if tables_checked > 0
            else 0.0,
        },
    )


def _check_regression_table(table: RegressionTable, table_id: str) -> dict:
    """Check missing data in regression table.

    Args:
        table: Regression table to check
        table_id: Table identifier

    Returns:
        Dictionary with issues, warnings, and missing rate

    """
    issues = []
    warnings = []

    if not table.models:
        issues.append(f"{table_id}: No regression models extracted")
        return {"issues": issues, "warnings": warnings, "missing_rate": 1.0}

    total_fields = 0
    missing_fields = 0

    for model_idx, model in enumerate(table.models):
        if not model.coefficients:
            warnings.append(f"{table_id}, model {model_idx + 1}: No coefficients")
            continue

        for coef in model.coefficients:
            # Count expected fields
            total_fields += 4  # coefficient, std_err, t_stat, p_value

            if coef.coefficient is None:
                missing_fields += 1
            if coef.std_err is None:
                missing_fields += 1
            if coef.t_stat is None:
                missing_fields += 1
            if coef.p_value is None:
                missing_fields += 1

    # Calculate missing rate
    missing_rate = missing_fields / total_fields if total_fields > 0 else 0.0

    if missing_rate > 0.5:
        warnings.append(
            f"{table_id}: High missing data rate ({missing_rate:.1%}) in coefficients"
        )

    # Check for systematic patterns
    if table.models:
        # Check if all p-values are missing (common pattern)
        all_p_missing = all(
            coef.p_value is None
            for model in table.models
            for coef in model.coefficients
        )
        if all_p_missing and total_fields > 0:
            warnings.append(f"{table_id}: All p-values missing (may need calculation)")

    return {"issues": issues, "warnings": warnings, "missing_rate": missing_rate}


def _check_summary_table(table: SummaryStatisticsTable, table_id: str) -> dict:
    """Check missing data in summary statistics table.

    Args:
        table: Summary statistics table to check
        table_id: Table identifier

    Returns:
        Dictionary with warnings and missing rate

    """
    warnings = []

    if not table.statistics:
        warnings.append(f"{table_id}: No summary statistics extracted")
        return {"warnings": warnings, "missing_rate": 1.0}

    total_fields = 0
    missing_fields = 0

    for stat in table.statistics:
        # Count expected fields
        total_fields += 4  # mean, std_dev, min, max

        if stat.mean is None:
            missing_fields += 1
        if stat.std_dev is None:
            missing_fields += 1
        if stat.min is None:
            missing_fields += 1
        if stat.max is None:
            missing_fields += 1

    missing_rate = missing_fields / total_fields if total_fields > 0 else 0.0

    if missing_rate > 0.3:
        warnings.append(f"{table_id}: Moderate missing data rate ({missing_rate:.1%})")

    return {"warnings": warnings, "missing_rate": missing_rate}


def _check_balance_table(table: BalanceTable, table_id: str) -> dict:
    """Check missing data in balance table.

    Args:
        table: Balance table to check
        table_id: Table identifier

    Returns:
        Dictionary with warnings and missing rate

    """
    warnings = []

    if not table.statistics:
        warnings.append(f"{table_id}: No balance statistics extracted")
        return {"warnings": warnings, "missing_rate": 1.0}

    total_fields = 0
    missing_fields = 0

    for stat in table.statistics:
        # Count expected fields
        total_fields += 4  # control_mean, treatment_mean, difference, p_value

        if stat.control_mean is None:
            missing_fields += 1
        if stat.treatment_mean is None:
            missing_fields += 1
        if stat.difference is None:
            missing_fields += 1
        if stat.p_value is None:
            missing_fields += 1

    missing_rate = missing_fields / total_fields if total_fields > 0 else 0.0

    if missing_rate > 0.3:
        warnings.append(f"{table_id}: Moderate missing data rate ({missing_rate:.1%})")

    return {"warnings": warnings, "missing_rate": missing_rate}
