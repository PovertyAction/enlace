"""Utility functions for benchmark testing.

This module provides comparison functions to measure extraction accuracy
against ground truth annotations.
"""

from dataclasses import dataclass
from pathlib import Path

from enlace.models.extraction import ExtractionResult
from tests.fixtures.annotation_validator import Annotation


@dataclass
class DetectionMetrics:
    """Metrics for table/figure detection accuracy."""

    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


@dataclass
class FieldAccuracy:
    """Accuracy metrics for a specific field type."""

    field_name: str
    total_values: int
    exact_matches: int
    close_matches: int  # Within tolerance
    mismatches: int
    missing: int  # In ground truth but not extracted
    exact_match_rate: float
    close_match_rate: float


@dataclass
class TableAccuracy:
    """Accuracy metrics for a single table."""

    table_id: str
    table_number: str
    table_type: str
    detected: bool
    field_accuracies: dict[str, FieldAccuracy]
    overall_accuracy: float


@dataclass
class PaperAccuracy:
    """Complete accuracy metrics for a paper."""

    paper_id: str
    detection_metrics: DetectionMetrics
    table_accuracies: list[TableAccuracy]
    metadata_accuracy: dict[str, bool]
    overall_accuracy: float


def calculate_detection_metrics(
    extracted_ids: set[str], ground_truth_ids: set[str]
) -> DetectionMetrics:
    """Calculate precision, recall, and F1 for detection.

    Args:
        extracted_ids: Set of extracted table/figure IDs
        ground_truth_ids: Set of ground truth table/figure IDs

    Returns:
        DetectionMetrics with calculated values

    """
    tp = len(extracted_ids & ground_truth_ids)
    fp = len(extracted_ids - ground_truth_ids)
    fn = len(ground_truth_ids - extracted_ids)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return DetectionMetrics(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
    )


def compare_numeric(
    extracted: float | None, expected: float | None, tolerance: float = 0.001
) -> tuple[bool, bool]:
    """Compare two numeric values with tolerance.

    Args:
        extracted: Extracted value
        expected: Ground truth value
        tolerance: Absolute tolerance for "close match"

    Returns:
        Tuple of (exact_match, close_match)

    """
    if extracted is None and expected is None:
        return (True, True)
    if extracted is None or expected is None:
        return (False, False)

    exact = abs(extracted - expected) < 1e-10
    close = abs(extracted - expected) <= tolerance

    return (exact, close)


def compare_string(
    extracted: str | None, expected: str | None, case_sensitive: bool = False
) -> bool:
    """Compare two string values.

    Args:
        extracted: Extracted value
        expected: Ground truth value
        case_sensitive: Whether to perform case-sensitive comparison

    Returns:
        True if strings match

    """
    if extracted is None and expected is None:
        return True
    if extracted is None or expected is None:
        return False

    if not case_sensitive:
        extracted = extracted.lower().strip()
        expected = expected.lower().strip()

    return extracted == expected


def normalize_variable_name(name: str) -> str:
    """Normalize variable name for comparison.

    Args:
        name: Variable name to normalize

    Returns:
        Normalized name (lowercase, trimmed, standardized spacing)

    """
    return " ".join(name.lower().strip().split())


def compare_coefficients(
    extracted_coefficients: list, ground_truth_coefficients: list
) -> FieldAccuracy:
    """Compare regression coefficients.

    Args:
        extracted_coefficients: List of extracted coefficients
        ground_truth_coefficients: List of ground truth coefficients

    Returns:
        FieldAccuracy for coefficient values

    """
    total = len(ground_truth_coefficients)
    exact_matches = 0
    close_matches = 0
    missing = 0

    # Create lookup by variable name
    extracted_dict = {
        normalize_variable_name(c.variable_name): c for c in extracted_coefficients
    }

    for gt_coef in ground_truth_coefficients:
        gt_var_name = normalize_variable_name(gt_coef.variable_name)

        if gt_var_name not in extracted_dict:
            missing += 1
            continue

        ex_coef = extracted_dict[gt_var_name]

        # Compare coefficient value
        if gt_coef.coefficient is not None:
            exact, close = compare_numeric(ex_coef.coefficient, gt_coef.coefficient)
            if exact:
                exact_matches += 1
            if close:
                close_matches += 1

    mismatches = total - exact_matches - missing

    return FieldAccuracy(
        field_name="coefficient",
        total_values=total,
        exact_matches=exact_matches,
        close_matches=close_matches,
        mismatches=mismatches,
        missing=missing,
        exact_match_rate=exact_matches / total if total > 0 else 0.0,
        close_match_rate=close_matches / total if total > 0 else 0.0,
    )


def compare_standard_errors(
    extracted_coefficients: list, ground_truth_coefficients: list
) -> FieldAccuracy:
    """Compare standard errors.

    Args:
        extracted_coefficients: List of extracted coefficients
        ground_truth_coefficients: List of ground truth coefficients

    Returns:
        FieldAccuracy for standard error values

    """
    total = 0
    exact_matches = 0
    close_matches = 0
    missing = 0

    extracted_dict = {
        normalize_variable_name(c.variable_name): c for c in extracted_coefficients
    }

    for gt_coef in ground_truth_coefficients:
        if gt_coef.std_error is None:
            continue  # Skip if no SE in ground truth

        total += 1
        gt_var_name = normalize_variable_name(gt_coef.variable_name)

        if gt_var_name not in extracted_dict:
            missing += 1
            continue

        ex_coef = extracted_dict[gt_var_name]

        exact, close = compare_numeric(ex_coef.std_error, gt_coef.std_error)
        if exact:
            exact_matches += 1
        if close:
            close_matches += 1

    mismatches = total - exact_matches - missing

    return FieldAccuracy(
        field_name="std_error",
        total_values=total,
        exact_matches=exact_matches,
        close_matches=close_matches,
        mismatches=mismatches,
        missing=missing,
        exact_match_rate=exact_matches / total if total > 0 else 0.0,
        close_match_rate=close_matches / total if total > 0 else 0.0,
    )


def compare_table(extracted_table, ground_truth_table) -> TableAccuracy:
    """Compare a single extracted table against ground truth.

    Args:
        extracted_table: Extracted table object
        ground_truth_table: Ground truth table dict

    Returns:
        TableAccuracy with detailed metrics

    """
    field_accuracies = {}

    # For regression tables, compare coefficients and SEs
    if ground_truth_table.table_type == "regression":
        all_gt_coefficients = []
        all_ex_coefficients = []

        # Collect all coefficients across models
        for gt_model in ground_truth_table.models:
            all_gt_coefficients.extend(gt_model.coefficients)

        if hasattr(extracted_table, "models"):
            for ex_model in extracted_table.models:
                all_ex_coefficients.extend(ex_model.coefficients)

        field_accuracies["coefficient"] = compare_coefficients(
            all_ex_coefficients, all_gt_coefficients
        )
        field_accuracies["std_error"] = compare_standard_errors(
            all_ex_coefficients, all_gt_coefficients
        )

    # Calculate overall accuracy as average of field accuracies
    if field_accuracies:
        overall = sum(fa.exact_match_rate for fa in field_accuracies.values()) / len(
            field_accuracies
        )
    else:
        overall = 0.0

    return TableAccuracy(
        table_id=ground_truth_table.table_id,
        table_number=ground_truth_table.table_number,
        table_type=ground_truth_table.table_type,
        detected=extracted_table is not None,
        field_accuracies=field_accuracies,
        overall_accuracy=overall,
    )


def compare_paper(
    extraction_result: ExtractionResult, annotation: Annotation
) -> PaperAccuracy:
    """Compare complete paper extraction against ground truth.

    Args:
        extraction_result: ExtractionResult from extraction
        annotation: Ground truth annotation

    Returns:
        PaperAccuracy with comprehensive metrics

    """
    # Calculate table detection metrics
    extracted_table_numbers = {t.table_number for t in extraction_result.tables}
    ground_truth_table_numbers = {
        t.table_number for t in annotation.ground_truth.tables
    }

    detection_metrics = calculate_detection_metrics(
        extracted_table_numbers, ground_truth_table_numbers
    )

    # Compare each table
    table_accuracies = []
    extracted_table_dict = {t.table_number: t for t in extraction_result.tables}

    for gt_table in annotation.ground_truth.tables:
        ex_table = extracted_table_dict.get(gt_table.table_number)
        table_accuracy = compare_table(ex_table, gt_table)
        table_accuracies.append(table_accuracy)

    # Compare metadata
    metadata_accuracy = {
        "title": compare_string(
            extraction_result.metadata.title,
            annotation.ground_truth.metadata.title,
            case_sensitive=False,
        ),
        "year": extraction_result.metadata.year
        == annotation.ground_truth.metadata.year,
    }

    # Calculate overall accuracy
    if table_accuracies:
        overall = sum(ta.overall_accuracy for ta in table_accuracies) / len(
            table_accuracies
        )
    else:
        overall = 0.0

    return PaperAccuracy(
        paper_id=annotation.paper_id,
        detection_metrics=detection_metrics,
        table_accuracies=table_accuracies,
        metadata_accuracy=metadata_accuracy,
        overall_accuracy=overall,
    )


def generate_accuracy_report(accuracy: PaperAccuracy) -> str:
    """Generate formatted accuracy report.

    Args:
        accuracy: PaperAccuracy to format

    Returns:
        Formatted report string

    """
    lines = []
    lines.append(f"\n{'=' * 70}")
    lines.append(f"ACCURACY REPORT: {accuracy.paper_id}")
    lines.append(f"{'=' * 70}\n")

    # Detection metrics
    lines.append("TABLE DETECTION:")
    dm = accuracy.detection_metrics
    lines.append(f"  Precision: {dm.precision:.2%}")
    lines.append(f"  Recall: {dm.recall:.2%}")
    lines.append(f"  F1 Score: {dm.f1_score:.2%}")
    lines.append(f"  True Positives: {dm.true_positives}")
    lines.append(f"  False Positives: {dm.false_positives}")
    lines.append(f"  False Negatives: {dm.false_negatives}\n")

    # Per-table accuracy
    lines.append("PER-TABLE ACCURACY:")
    for ta in accuracy.table_accuracies:
        status = "✓" if ta.detected else "✗"
        lines.append(
            f"  {status} {ta.table_number} ({ta.table_type}): {ta.overall_accuracy:.2%}"
        )
        for field_name, fa in ta.field_accuracies.items():
            lines.append(f"      {field_name}: {fa.exact_match_rate:.2%} exact")

    # Overall accuracy
    lines.append(f"\nOVERALL ACCURACY: {accuracy.overall_accuracy:.2%}\n")

    return "\n".join(lines)


def load_annotation(annotation_path: Path) -> Annotation:
    """Load and validate annotation file.

    Args:
        annotation_path: Path to annotation JSON

    Returns:
        Validated Annotation object

    """
    return Annotation.load(annotation_path)
