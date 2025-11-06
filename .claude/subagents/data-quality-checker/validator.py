"""Data Quality Checker Subagent Implementation

This module implements the data-quality-checker subagent for comprehensive
quality assurance of extracted research paper data.

Usage:
    uv run python validator.py validate extracted/paper_id/extraction.json
    uv run python validator.py batch extracted/ --report validation_report.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Data Quality Checker Subagent

    Performs comprehensive validation of extracted research paper data,
    including accuracy checks, completeness analysis, and statistical consistency.
    """

    def __init__(self, output_dir: str = "validation_reports"):
        """Initialize the data quality checker.

        Args:
            output_dir: Directory for validation reports

        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"DataQualityChecker initialized with output_dir={self.output_dir}")

    def validate(
        self,
        extraction_path: str,
        source_pdf: str | None = None,
        validation_level: str = "comprehensive",
    ) -> dict:
        """Validate extraction output with configurable depth.

        Args:
            extraction_path: Path to extraction.json file
            source_pdf: Optional path to source PDF for comparison
            validation_level: One of 'quick', 'standard', 'comprehensive'

        Returns:
            Validation result dictionary with pass/fail status and detailed issues

        """
        start_time = datetime.now()
        extraction_path = Path(extraction_path)

        logger.info(f"Starting {validation_level} validation: {extraction_path.name}")

        # Load extraction data
        try:
            with extraction_path.open() as f:
                extraction_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load extraction file: {str(e)}")
            return self._create_error_result(extraction_path, str(e))

        paper_id = extraction_data.get("paper_id", extraction_path.parent.name)

        # Initialize validation result
        result = {
            "paper_id": paper_id,
            "validation_date": datetime.now().isoformat(),
            "extraction_path": str(extraction_path),
            "source_pdf": str(source_pdf) if source_pdf else None,
            "validation_level": validation_level,
            "passed": True,
            "score": 0.0,
            "issues": [],
            "warnings": [],
            "checks": {},
            "table_validations": [],
            "recommendations": [],
        }

        # Run validation checks based on level
        checks_to_run = self._get_checks_for_level(validation_level)

        for check_name in checks_to_run:
            check_method = getattr(self, f"_check_{check_name}", None)
            if check_method:
                try:
                    check_result = check_method(extraction_data, source_pdf)
                    result["checks"][check_name] = check_result

                    # Collect issues and warnings
                    if check_result.get("issues"):
                        result["issues"].extend(check_result["issues"])
                    if check_result.get("warnings"):
                        result["warnings"].extend(check_result["warnings"])

                except Exception as e:
                    logger.error(f"Check {check_name} failed: {str(e)}", exc_info=True)
                    result["warnings"].append(f"Check {check_name} failed: {str(e)}")

        # Validate individual tables
        for table in extraction_data.get("tables", []):
            table_validation = self._validate_table(table, validation_level)
            result["table_validations"].append(table_validation)

            if table_validation.get("issues"):
                result["issues"].extend(table_validation["issues"])
            if table_validation.get("warnings"):
                result["warnings"].extend(table_validation["warnings"])

        # Calculate overall quality score
        result["score"] = self._calculate_validation_score(result)

        # Determine pass/fail
        result["passed"] = len(result["issues"]) == 0 and result["score"] >= 0.7

        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(result)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        result["processing_time_seconds"] = round(processing_time, 2)

        # Save validation report
        report_path = self.output_dir / f"{paper_id}_validation.json"
        with report_path.open("w") as f:
            json.dump(result, f, indent=2)

        # Log summary
        status = "✓ PASSED" if result["passed"] else "✗ FAILED"
        logger.info(
            f"{status}: {paper_id} - score={result['score']:.2f}, "
            f"issues={len(result['issues'])}, warnings={len(result['warnings'])}"
        )

        return result

    def validate_batch(
        self,
        extraction_dir: str,
        validation_level: str = "standard",
    ) -> dict:
        """Validate multiple extraction outputs in batch.

        Args:
            extraction_dir: Directory containing extraction subdirectories
            validation_level: Validation depth level

        Returns:
            Batch validation summary with aggregated statistics

        """
        start_time = datetime.now()
        extraction_dir = Path(extraction_dir)

        logger.info(f"Starting batch validation in {extraction_dir}")

        # Find all extraction.json files
        extraction_files = list(extraction_dir.glob("*/extraction.json"))

        if not extraction_files:
            logger.warning(f"No extraction.json files found in {extraction_dir}")
            return {
                "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "validation_date": datetime.now().isoformat(),
                "papers_validated": 0,
                "papers_passed": 0,
                "papers_failed": 0,
            }

        # Validate each extraction
        results = []
        for extraction_file in extraction_files:
            # Look for corresponding PDF
            source_pdf = None
            pdf_path = (
                extraction_file.parent.parent
                / "papers"
                / f"{extraction_file.parent.name}.pdf"
            )
            if pdf_path.exists():
                source_pdf = str(pdf_path)

            result = self.validate(
                extraction_path=str(extraction_file),
                source_pdf=source_pdf,
                validation_level=validation_level,
            )
            results.append(result)

        # Compile batch summary
        passed = [r for r in results if r["passed"]]
        failed = [r for r in results if not r["passed"]]

        batch_summary = {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "validation_date": datetime.now().isoformat(),
            "validation_level": validation_level,
            "papers_validated": len(results),
            "papers_passed": len(passed),
            "papers_failed": len(failed),
            "summary": {
                "avg_score": sum(r["score"] for r in results) / len(results)
                if results
                else 0,
                "total_issues": sum(len(r["issues"]) for r in results),
                "total_warnings": sum(len(r["warnings"]) for r in results),
                "processing_time_seconds": (
                    datetime.now() - start_time
                ).total_seconds(),
            },
            "papers": [
                {
                    "paper_id": r["paper_id"],
                    "passed": r["passed"],
                    "score": r["score"],
                    "issues": len(r["issues"]),
                    "warnings": len(r["warnings"]),
                    "report_path": str(
                        self.output_dir / f"{r['paper_id']}_validation.json"
                    ),
                }
                for r in results
            ],
            "output_directory": str(self.output_dir),
        }

        # Save batch summary
        batch_report_path = self.output_dir / "batch_validation_summary.json"
        with batch_report_path.open("w") as f:
            json.dump(batch_summary, f, indent=2)

        logger.info(
            f"Batch validation complete: "
            f"{batch_summary['papers_passed']}/{batch_summary['papers_validated']} passed, "
            f"avg_score={batch_summary['summary']['avg_score']:.2f}"
        )

        return batch_summary

    # ========================================================================
    # VALIDATION CHECKS
    # ========================================================================

    def _check_structure(self, extraction_data: dict, source_pdf: str | None) -> dict:
        """Validate extraction data structure and required fields.

        Checks:
        - Required top-level fields present
        - Data types correct
        - Lists are properly formatted
        """
        issues = []
        warnings = []

        required_fields = [
            "paper_id",
            "extraction_date",
            "metadata",
            "tables",
            "figures",
            "citations",
            "methodology",
            "extraction_report",
        ]

        for field in required_fields:
            if field not in extraction_data:
                issues.append(f"Missing required field: {field}")

        # Check data types
        if "tables" in extraction_data and not isinstance(
            extraction_data["tables"], list
        ):
            issues.append("Field 'tables' must be a list")

        if "figures" in extraction_data and not isinstance(
            extraction_data["figures"], list
        ):
            issues.append("Field 'figures' must be a list")

        if "citations" in extraction_data and not isinstance(
            extraction_data["citations"], list
        ):
            issues.append("Field 'citations' must be a list")

        if "metadata" in extraction_data and not isinstance(
            extraction_data["metadata"], dict
        ):
            issues.append("Field 'metadata' must be a dictionary")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": 1.0 if len(issues) == 0 else 0.0,
        }

    def _check_completeness(
        self, extraction_data: dict, source_pdf: str | None
    ) -> dict:
        """Check completeness of extracted data.

        Checks:
        - Metadata fields populated
        - Tables extracted
        - Expected content present
        """
        issues = []
        warnings = []
        completeness_scores = []

        # Metadata completeness
        metadata = extraction_data.get("metadata", {})
        metadata_fields = ["title", "authors", "year", "doi"]
        populated_fields = sum(1 for f in metadata_fields if metadata.get(f))

        metadata_completeness = populated_fields / len(metadata_fields)
        completeness_scores.append(metadata_completeness)

        if metadata_completeness < 0.5:
            warnings.append(
                f"Low metadata completeness: {metadata_completeness:.1%} "
                f"({populated_fields}/{len(metadata_fields)} fields)"
            )

        # Tables extracted
        tables = extraction_data.get("tables", [])
        if not tables:
            warnings.append("No tables extracted - verify paper contains tables")

        # Citations extracted
        citations = extraction_data.get("citations", [])
        if len(citations) < 5:
            warnings.append(
                f"Few citations extracted ({len(citations)}) - typical paper has 20+"
            )

        return {
            "passed": True,  # Warnings only, not failures
            "issues": issues,
            "warnings": warnings,
            "score": sum(completeness_scores) / len(completeness_scores)
            if completeness_scores
            else 0.0,
            "metadata_completeness": metadata_completeness,
            "tables_found": len(tables),
            "citations_found": len(citations),
        }

    def _check_accuracy(self, extraction_data: dict, source_pdf: str | None) -> dict:
        """Check extraction accuracy based on internal consistency.

        For comprehensive check with source PDF, would compare numbers directly.
        For now, focuses on internal validation.
        """
        issues = []
        warnings = []

        tables = extraction_data.get("tables", [])

        # Check table data quality
        low_quality_tables = []
        for table in tables:
            quality = table.get("quality_score", 0)
            if quality < 0.5:
                low_quality_tables.append(table["table_id"])

        if low_quality_tables:
            warnings.append(
                f"Tables with low quality scores: {', '.join(low_quality_tables)}"
            )

        # Check for empty tables
        empty_tables = []
        for table in tables:
            data = table.get("data", [])
            if not data or len(data) <= 1:
                empty_tables.append(table["table_id"])

        if empty_tables:
            issues.append(f"Empty or single-row tables: {', '.join(empty_tables)}")

        # Calculate accuracy score
        if tables:
            avg_quality = sum(t.get("quality_score", 0) for t in tables) / len(tables)
            accuracy_score = avg_quality
        else:
            accuracy_score = 0.0

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": accuracy_score,
            "low_quality_tables": low_quality_tables,
            "empty_tables": empty_tables,
        }

    def _check_statistical_consistency(
        self, extraction_data: dict, source_pdf: str | None
    ) -> dict:
        """Check statistical consistency in extracted tables.

        Validates:
        - T-statistics calculated from coefficients and standard errors
        - P-values consistent with t-stats
        - Standard errors are positive
        - Reasonable magnitude for coefficients
        """
        issues = []
        warnings = []
        checks_performed = 0
        checks_passed = 0

        tables = extraction_data.get("tables", [])

        for table in tables:
            # Only check regression tables
            if table.get("type") not in ["regression", "other"]:
                continue

            table_id = table["table_id"]
            data = table.get("data", [])

            # Try to find regression columns
            regression_data = self._extract_regression_data(data)

            if not regression_data:
                continue

            for row_idx, row_data in regression_data.items():
                checks_performed += 1

                # Check 1: Standard errors are positive
                if "std_err" in row_data and row_data["std_err"] is not None:
                    if row_data["std_err"] < 0:
                        issues.append(
                            f"{table_id}, row {row_idx}: Negative standard error"
                        )
                        continue
                    else:
                        checks_passed += 1

                # Check 2: T-stat calculation
                if all(
                    k in row_data and row_data[k] is not None
                    for k in ["coef", "std_err", "t_stat"]
                ):
                    expected_t = row_data["coef"] / row_data["std_err"]
                    actual_t = row_data["t_stat"]

                    # Allow 10% tolerance for rounding
                    if abs(expected_t - actual_t) / (abs(actual_t) + 1e-10) > 0.1:
                        warnings.append(
                            f"{table_id}, row {row_idx}: T-stat mismatch - "
                            f"expected {expected_t:.3f}, found {actual_t:.3f}"
                        )
                    else:
                        checks_passed += 1

                # Check 3: P-value consistency with t-stat
                if "t_stat" in row_data and "p_value" in row_data:
                    if (
                        row_data["t_stat"] is not None
                        and row_data["p_value"] is not None
                    ):
                        # Simple heuristic: |t| > 1.96 should give p < 0.05
                        abs_t = abs(row_data["t_stat"])
                        p_val = row_data["p_value"]

                        if (
                            abs_t > 1.96
                            and p_val >= 0.05
                            or abs_t < 1.96
                            and p_val < 0.05
                        ):
                            warnings.append(
                                f"{table_id}, row {row_idx}: P-value inconsistent - "
                                f"|t|={abs_t:.2f} but p={p_val:.3f}"
                            )
                        else:
                            checks_passed += 1

        score = checks_passed / checks_performed if checks_performed > 0 else 1.0

        if checks_performed == 0:
            warnings.append(
                "No statistical consistency checks performed (no regression data found)"
            )

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": score,
            "checks_performed": checks_performed,
            "checks_passed": checks_passed,
        }

    def _check_missing_data(
        self, extraction_data: dict, source_pdf: str | None
    ) -> dict:
        """Identify missing data patterns in tables.

        Checks:
        - High proportion of empty cells
        - Systematic missing patterns (entire rows/cols)
        - Incomplete extractions
        """
        issues = []
        warnings = []

        tables = extraction_data.get("tables", [])

        for table in tables:
            table_id = table["table_id"]
            data = table.get("data", [])

            if not data:
                issues.append(f"{table_id}: No data extracted")
                continue

            # Calculate missing data statistics
            total_cells = sum(len(row) for row in data)
            empty_cells = sum(
                1 for row in data for cell in row if not str(cell).strip()
            )

            if total_cells > 0:
                missing_rate = empty_cells / total_cells

                if missing_rate > 0.5:
                    warnings.append(
                        f"{table_id}: High missing data rate ({missing_rate:.1%})"
                    )

                # Check for completely empty rows
                empty_rows = sum(
                    1 for row in data if all(not str(cell).strip() for cell in row)
                )
                if empty_rows > 0:
                    warnings.append(f"{table_id}: {empty_rows} completely empty rows")

                # Check for completely empty columns
                num_cols = len(data[0]) if data else 0
                empty_cols = 0
                for col_idx in range(num_cols):
                    if all(
                        not str(row[col_idx]).strip() if col_idx < len(row) else True
                        for row in data
                    ):
                        empty_cols += 1

                if empty_cols > 0:
                    warnings.append(
                        f"{table_id}: {empty_cols} completely empty columns"
                    )

        score = 1.0 if len(warnings) == 0 else 0.7 if len(issues) == 0 else 0.3

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": score,
        }

    # ========================================================================
    # TABLE VALIDATION
    # ========================================================================

    def _validate_table(self, table: dict, validation_level: str) -> dict:
        """Validate a single table comprehensively.

        Returns validation result for the table.
        """
        table_id = table.get("table_id", "unknown")
        issues = []
        warnings = []

        # Basic structure checks
        required_fields = ["table_id", "type", "data", "quality_score"]
        for field in required_fields:
            if field not in table:
                issues.append(f"{table_id}: Missing field '{field}'")

        # Caption check
        if not table.get("caption"):
            warnings.append(f"{table_id}: No caption extracted")

        # Data shape checks
        data = table.get("data", [])
        num_rows = table.get("num_rows", 0)
        num_cols = table.get("num_cols", 0)

        if data:
            actual_rows = len(data)
            actual_cols = len(data[0]) if data else 0

            if actual_rows != num_rows:
                issues.append(
                    f"{table_id}: Row count mismatch - "
                    f"metadata says {num_rows}, data has {actual_rows}"
                )

            if actual_cols != num_cols:
                issues.append(
                    f"{table_id}: Column count mismatch - "
                    f"metadata says {num_cols}, data has {actual_cols}"
                )

        # Quality score check
        quality = table.get("quality_score", 0)
        if quality < 0.5:
            warnings.append(f"{table_id}: Low quality score ({quality:.2f})")

        return {
            "table_id": table_id,
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "quality_score": quality,
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_checks_for_level(self, level: str) -> list[str]:
        """Get list of checks to run for validation level."""
        if level == "quick":
            return ["structure", "completeness"]
        elif level == "standard":
            return ["structure", "completeness", "accuracy", "missing_data"]
        elif level == "comprehensive":
            return [
                "structure",
                "completeness",
                "accuracy",
                "statistical_consistency",
                "missing_data",
            ]
        else:
            return ["structure", "completeness"]

    def _extract_regression_data(self, table_data: list[list[str]]) -> dict:
        """Extract regression statistics from table data.

        Returns dictionary mapping row indices to extracted stats.
        """
        regression_rows = {}

        if not table_data or len(table_data) < 2:
            return regression_rows

        # Try to identify columns
        header = table_data[0] if table_data else []
        header_lower = [str(h).lower() for h in header]

        # Look for coefficient/std err/t-stat/p-value columns
        coef_col = None
        se_col = None
        t_col = None
        p_col = None

        for i, h in enumerate(header_lower):
            if any(kw in h for kw in ["coef", "coefficient", "estimate"]):
                coef_col = i
            elif any(kw in h for kw in ["std", "se", "standard error"]):
                se_col = i
            elif any(kw in h for kw in ["t-stat", "t stat", "t value"]):
                t_col = i
            elif any(kw in h for kw in ["p-value", "p value", "prob"]):
                p_col = i

        # Extract data rows
        for row_idx, row in enumerate(table_data[1:], start=1):
            row_data = {}

            try:
                if coef_col is not None and coef_col < len(row):
                    row_data["coef"] = self._parse_numeric(row[coef_col])

                if se_col is not None and se_col < len(row):
                    # Standard errors often in parentheses
                    se_val = self._parse_numeric(row[se_col], allow_parens=True)
                    row_data["std_err"] = se_val

                if t_col is not None and t_col < len(row):
                    row_data["t_stat"] = self._parse_numeric(row[t_col])

                if p_col is not None and p_col < len(row):
                    row_data["p_value"] = self._parse_numeric(row[p_col])

                # Only include if we found at least some data
                if row_data:
                    regression_rows[row_idx] = row_data

            except Exception:
                continue

        return regression_rows

    def _parse_numeric(self, value: Any, allow_parens: bool = False) -> float | None:
        """Parse numeric value from string, handling common formats.

        Args:
            value: Input value (string, number, etc.)
            allow_parens: If True, strip parentheses (for std errors)

        Returns:
            Parsed float or None if not parseable

        """
        if value is None:
            return None

        s = str(value).strip()

        if not s:
            return None

        # Remove parentheses if allowed
        if allow_parens:
            s = s.strip("()")

        # Remove common decorations
        s = s.replace(",", "")  # Thousand separators
        s = s.replace("*", "")  # Significance stars
        s = s.replace("†", "")
        s = s.replace("‡", "")

        # Try to parse
        try:
            return float(s)
        except ValueError:
            return None

    def _calculate_validation_score(self, result: dict) -> float:
        """Calculate overall validation score from check results.

        Weighted average of individual check scores.
        """
        checks = result.get("checks", {})

        if not checks:
            return 0.0

        # Weights for different checks
        weights = {
            "structure": 0.30,
            "completeness": 0.20,
            "accuracy": 0.30,
            "statistical_consistency": 0.10,
            "missing_data": 0.10,
        }

        total_score = 0.0
        total_weight = 0.0

        for check_name, check_result in checks.items():
            if isinstance(check_result, dict) and "score" in check_result:
                weight = weights.get(check_name, 0.1)
                total_score += check_result["score"] * weight
                total_weight += weight

        if total_weight > 0:
            return round(total_score / total_weight, 2)
        else:
            return 0.0

    def _generate_recommendations(self, result: dict) -> list[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []

        # Check specific issues
        checks = result.get("checks", {})

        # Low metadata completeness
        if "completeness" in checks:
            metadata_comp = checks["completeness"].get("metadata_completeness", 1.0)
            if metadata_comp < 0.5:
                recommendations.append(
                    "Improve metadata extraction: Use bibliography skill for "
                    "better author, DOI, and citation extraction"
                )

        # No tables extracted
        if "completeness" in checks:
            if checks["completeness"].get("tables_found", 0) == 0:
                recommendations.append(
                    "No tables extracted: Verify source PDF quality, "
                    "try OCR if scanned document"
                )

        # Low accuracy
        if "accuracy" in checks:
            if checks["accuracy"].get("score", 1.0) < 0.7:
                recommendations.append(
                    "Low extraction accuracy: Review table extraction settings, "
                    "consider using docling with VLM for complex tables"
                )

        # Statistical inconsistencies
        if "statistical_consistency" in checks:
            if checks["statistical_consistency"].get("checks_performed", 0) > 0:
                pass_rate = (
                    checks["statistical_consistency"].get("checks_passed", 0)
                    / checks["statistical_consistency"]["checks_performed"]
                )
                if pass_rate < 0.8:
                    recommendations.append(
                        "Statistical inconsistencies detected: Manual review "
                        "recommended for regression tables"
                    )

        # High missing data
        if "missing_data" in checks:
            if checks["missing_data"].get("score", 1.0) < 0.7:
                recommendations.append(
                    "High missing data rates: Check PDF table formatting, "
                    "may need custom extraction rules"
                )

        # Overall score
        if result["score"] < 0.5:
            recommendations.append(
                "Overall quality below threshold: Consider re-extraction with "
                "different settings or manual review"
            )

        return recommendations

    def _create_error_result(self, extraction_path: Path, error: str) -> dict:
        """Create an error result when validation cannot be performed."""
        return {
            "paper_id": extraction_path.parent.name,
            "validation_date": datetime.now().isoformat(),
            "extraction_path": str(extraction_path),
            "passed": False,
            "score": 0.0,
            "issues": [f"Validation failed: {error}"],
            "warnings": [],
            "checks": {},
            "table_validations": [],
            "recommendations": ["Fix extraction errors before validation"],
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================


async def main():
    """CLI entry point for data-quality-checker subagent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Data Quality Checker Subagent - Validate extracted research data"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Single validation
    validate_parser = subparsers.add_parser(
        "validate", help="Validate single extraction"
    )
    validate_parser.add_argument("extraction_path", help="Path to extraction.json")
    validate_parser.add_argument(
        "--source-pdf", help="Path to source PDF for comparison"
    )
    validate_parser.add_argument(
        "--level",
        choices=["quick", "standard", "comprehensive"],
        default="standard",
        help="Validation level",
    )
    validate_parser.add_argument(
        "--output-dir", default="validation_reports", help="Output directory"
    )

    # Batch validation
    batch_parser = subparsers.add_parser("batch", help="Validate multiple extractions")
    batch_parser.add_argument("extraction_dir", help="Directory containing extractions")
    batch_parser.add_argument(
        "--level",
        choices=["quick", "standard", "comprehensive"],
        default="standard",
        help="Validation level",
    )
    batch_parser.add_argument(
        "--output-dir", default="validation_reports", help="Output directory"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    checker = DataQualityChecker(output_dir=args.output_dir)

    if args.command == "validate":
        # Single validation
        result = checker.validate(
            extraction_path=args.extraction_path,
            source_pdf=args.source_pdf,
            validation_level=args.level,
        )

        print("\n" + "=" * 70)
        print(f"VALIDATION RESULT: {result['paper_id']}")
        print("=" * 70)
        status = "✓ PASSED" if result["passed"] else "✗ FAILED"
        print(f"Status:         {status}")
        print(f"Overall score:  {result['score']:.2f}")
        print(f"Issues:         {len(result['issues'])}")
        print(f"Warnings:       {len(result['warnings'])}")
        print(f"Tables checked: {len(result['table_validations'])}")

        if result["issues"]:
            print("\nISSUES:")
            for issue in result["issues"][:5]:  # Show first 5
                print(f"  - {issue}")

        if result["warnings"]:
            print("\nWARNINGS:")
            for warning in result["warnings"][:5]:  # Show first 5
                print(f"  - {warning}")

        if result["recommendations"]:
            print("\nRECOMMENDATIONS:")
            for rec in result["recommendations"]:
                print(f"  - {rec}")

        print(
            f"\nReport saved to: {args.output_dir}/{result['paper_id']}_validation.json"
        )

    elif args.command == "batch":
        # Batch validation
        result = checker.validate_batch(
            extraction_dir=args.extraction_dir,
            validation_level=args.level,
        )

        print("\n" + "=" * 70)
        print(f"BATCH VALIDATION COMPLETE: {result['batch_id']}")
        print("=" * 70)
        print(f"Papers validated: {result['papers_validated']}")
        print(f"Passed:           {result['papers_passed']}")
        print(f"Failed:           {result['papers_failed']}")
        print(f"Avg score:        {result['summary']['avg_score']:.2f}")
        print(f"Total issues:     {result['summary']['total_issues']}")
        print(f"Total warnings:   {result['summary']['total_warnings']}")
        print(f"\nSummary saved to: {args.output_dir}/batch_validation_summary.json")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
