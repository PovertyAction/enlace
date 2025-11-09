"""Benchmark tests for field-level extraction accuracy.

This module tests the accuracy of specific field extraction (coefficients,
standard errors, etc.) across different extraction configurations.
"""

from pathlib import Path

import pytest

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor
from tests.benchmark.utils import (
    compare_paper,
    generate_accuracy_report,
    load_annotation,
)


@pytest.fixture
def annotation_dir():
    """Return path to benchmark annotation directory."""
    return Path(__file__).parent.parent / "fixtures" / "benchmark_data"


@pytest.fixture
def papers_dir():
    """Return path to papers directory."""
    return Path(__file__).parent.parent.parent / "papers"


@pytest.fixture(params=["BHKM_Liberia"])
def paper_id(request):
    """Parametrize tests across annotated papers."""
    return request.param


@pytest.fixture
def ground_truth(annotation_dir, paper_id):
    """Load ground truth annotation."""
    annotation_path = annotation_dir / f"{paper_id}_ground_truth.json"
    if not annotation_path.exists():
        pytest.skip(f"Ground truth annotation not found: {annotation_path}")
    return load_annotation(annotation_path)


@pytest.fixture
def paper_path(papers_dir, paper_id):
    """Get path to paper PDF."""
    path = papers_dir / f"{paper_id}.pdf"
    if not path.exists():
        pytest.skip(f"Paper not found: {path}")
    return path


class TestFieldAccuracyBaseline:
    """Test field extraction accuracy without OCR (baseline)."""

    def test_coefficient_accuracy_no_ocr(self, paper_path, ground_truth, tmp_path):
        """Test coefficient extraction accuracy without OCR."""
        # Extract with no OCR
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Check coefficient accuracy across all regression tables
        coefficient_accuracies = []
        for table_acc in accuracy.table_accuracies:
            if "coefficient" in table_acc.field_accuracies:
                coef_acc = table_acc.field_accuracies["coefficient"]
                coefficient_accuracies.append(coef_acc.exact_match_rate)

        if not coefficient_accuracies:
            pytest.skip("No regression tables in ground truth")

        avg_coef_accuracy = sum(coefficient_accuracies) / len(coefficient_accuracies)

        # Assert minimum threshold
        assert avg_coef_accuracy >= 0.7, (
            f"Coefficient accuracy too low: {avg_coef_accuracy:.2%}"
        )

        # Print report
        print(generate_accuracy_report(accuracy))

    def test_standard_error_accuracy_no_ocr(self, paper_path, ground_truth, tmp_path):
        """Test standard error extraction accuracy without OCR."""
        # Extract with no OCR
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Check SE accuracy across all regression tables
        se_accuracies = []
        for table_acc in accuracy.table_accuracies:
            if "std_error" in table_acc.field_accuracies:
                se_acc = table_acc.field_accuracies["std_error"]
                se_accuracies.append(se_acc.exact_match_rate)

        if not se_accuracies:
            pytest.skip("No standard errors in ground truth")

        avg_se_accuracy = sum(se_accuracies) / len(se_accuracies)

        # Assert minimum threshold
        assert avg_se_accuracy >= 0.7, (
            f"Standard error accuracy too low: {avg_se_accuracy:.2%}"
        )

    def test_metadata_extraction_no_ocr(self, paper_path, ground_truth, tmp_path):
        """Test metadata extraction accuracy without OCR."""
        # Extract with no OCR
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Check metadata accuracy
        assert accuracy.metadata_accuracy["title"], "Title does not match ground truth"

        # Year can be off by 1 due to publication vs study year
        if not accuracy.metadata_accuracy["year"]:
            year_diff = abs(
                result.metadata.year - ground_truth.ground_truth.metadata.year
            )
            assert year_diff <= 1, f"Year too far off: {year_diff} years"


class TestFieldAccuracyOCR:
    """Test field extraction accuracy with OCR backends."""

    @pytest.mark.parametrize("ocr_backend", ["tesseract", "easyocr"])
    def test_coefficient_accuracy_with_ocr(
        self, paper_path, ground_truth, ocr_backend, tmp_path
    ):
        """Test coefficient extraction accuracy with different OCR backends."""
        # Extract with OCR
        config = ExtractionConfig(
            enable_ocr=True,
            ocr_backend=ocr_backend,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Check coefficient accuracy
        coefficient_accuracies = []
        for table_acc in accuracy.table_accuracies:
            if "coefficient" in table_acc.field_accuracies:
                coef_acc = table_acc.field_accuracies["coefficient"]
                coefficient_accuracies.append(coef_acc.exact_match_rate)

        if not coefficient_accuracies:
            pytest.skip("No regression tables in ground truth")

        avg_coef_accuracy = sum(coefficient_accuracies) / len(coefficient_accuracies)

        # Assert minimum threshold (should be same or better than baseline)
        assert avg_coef_accuracy >= 0.7, (
            f"Coefficient accuracy too low: {avg_coef_accuracy:.2%}"
        )

        # Print report
        print(f"\n{'=' * 70}")
        print(f"Coefficient Accuracy ({ocr_backend.upper()}) - {paper_path.stem}")
        print(f"{'=' * 70}")
        print(f"Average accuracy: {avg_coef_accuracy:.2%}")

    def test_field_accuracy_auto_ocr(self, paper_path, ground_truth, tmp_path):
        """Test field extraction with auto OCR backend (hybrid mode)."""
        # Extract with auto OCR
        config = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="auto",
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Print full report
        print(generate_accuracy_report(accuracy))

        # Assert minimum overall accuracy
        assert accuracy.overall_accuracy >= 0.7, (
            f"Overall accuracy too low: {accuracy.overall_accuracy:.2%}"
        )


class TestFieldAccuracyAugmentation:
    """Test field extraction accuracy with semantic augmentation."""

    def test_field_accuracy_with_augmentation(self, paper_path, ground_truth, tmp_path):
        """Test whether augmentation improves or maintains accuracy."""
        # Extract without augmentation
        config_no_aug = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path / "no_aug",
            verbose=False,
        )
        extractor_no_aug = PaperExtractor(config_no_aug)
        result_no_aug = extractor_no_aug.extract(paper_path)
        accuracy_no_aug = compare_paper(result_no_aug, ground_truth)

        # Extract with augmentation
        config_aug = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=True,
            output_dir=tmp_path / "aug",
            verbose=False,
        )
        extractor_aug = PaperExtractor(config_aug)
        result_aug = extractor_aug.extract(paper_path)
        accuracy_aug = compare_paper(result_aug, ground_truth)

        # Compare results
        print(f"\n{'=' * 70}")
        print(f"Augmentation Impact - {paper_path.stem}")
        print(f"{'=' * 70}")
        print(f"Without augmentation: {accuracy_no_aug.overall_accuracy:.2%}")
        print(f"With augmentation:    {accuracy_aug.overall_accuracy:.2%}")
        print(
            f"Difference:           {accuracy_aug.overall_accuracy - accuracy_no_aug.overall_accuracy:+.2%}"
        )

        # Augmentation should maintain or improve accuracy
        assert (
            accuracy_aug.overall_accuracy >= accuracy_no_aug.overall_accuracy - 0.05
        ), "Augmentation significantly degraded accuracy"


class TestFieldAccuracyComparison:
    """Compare field accuracy across all configurations."""

    def test_comprehensive_field_accuracy(self, paper_path, ground_truth, tmp_path):
        """Compare field accuracy across all configurations."""
        configs = {
            "baseline": ExtractionConfig(
                enable_ocr=False,
                enable_augmentation=False,
                output_dir=tmp_path / "baseline",
                verbose=False,
            ),
            "tesseract": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="tesseract",
                enable_augmentation=False,
                output_dir=tmp_path / "tesseract",
                verbose=False,
            ),
            "easyocr": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="easyocr",
                enable_augmentation=False,
                output_dir=tmp_path / "easyocr",
                verbose=False,
            ),
            "auto": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="auto",
                enable_augmentation=False,
                output_dir=tmp_path / "auto",
                verbose=False,
            ),
            "augmented": ExtractionConfig(
                enable_ocr=False,
                enable_augmentation=True,
                output_dir=tmp_path / "augmented",
                verbose=False,
            ),
        }

        results = {}

        for config_name, config in configs.items():
            extractor = PaperExtractor(config)
            result = extractor.extract(paper_path)
            accuracy = compare_paper(result, ground_truth)

            # Collect field-level metrics
            coef_accuracies = []
            se_accuracies = []

            for table_acc in accuracy.table_accuracies:
                if "coefficient" in table_acc.field_accuracies:
                    coef_acc = table_acc.field_accuracies["coefficient"]
                    coef_accuracies.append(coef_acc.exact_match_rate)

                if "std_error" in table_acc.field_accuracies:
                    se_acc = table_acc.field_accuracies["std_error"]
                    se_accuracies.append(se_acc.exact_match_rate)

            results[config_name] = {
                "overall": accuracy.overall_accuracy,
                "coefficient": (
                    sum(coef_accuracies) / len(coef_accuracies)
                    if coef_accuracies
                    else 0.0
                ),
                "std_error": (
                    sum(se_accuracies) / len(se_accuracies) if se_accuracies else 0.0
                ),
                "detection_f1": accuracy.detection_metrics.f1_score,
            }

        # Print comparison report
        print(f"\n{'=' * 90}")
        print(f"Comprehensive Field Accuracy Comparison - {paper_path.stem}")
        print(f"{'=' * 90}")
        print(
            f"{'Configuration':<15} {'Overall':>10} {'Coefficient':>12} {'Std Error':>12} {'Detection F1':>14}"
        )
        print("-" * 90)
        for config_name, metrics in results.items():
            print(
                f"{config_name:<15} {metrics['overall']:>9.2%} {metrics['coefficient']:>11.2%} "
                f"{metrics['std_error']:>11.2%} {metrics['detection_f1']:>13.2%}"
            )

        # Assert that at least one configuration achieves good accuracy
        best_overall = max(r["overall"] for r in results.values())
        assert best_overall >= 0.7, (
            f"No configuration achieved overall accuracy >= 70% (best: {best_overall:.2%})"
        )

    def test_per_table_accuracy_breakdown(self, paper_path, ground_truth, tmp_path):
        """Detailed per-table accuracy breakdown for baseline configuration."""
        # Extract with baseline config
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Print detailed per-table report
        print(f"\n{'=' * 90}")
        print(f"Per-Table Accuracy Breakdown - {paper_path.stem}")
        print(f"{'=' * 90}")

        for table_acc in accuracy.table_accuracies:
            print(f"\n{table_acc.table_number} ({table_acc.table_type}):")
            print(f"  Detected: {'✓' if table_acc.detected else '✗'}")
            print(f"  Overall accuracy: {table_acc.overall_accuracy:.2%}")

            for field_name, field_acc in table_acc.field_accuracies.items():
                print(f"\n  {field_name}:")
                print(
                    f"    Exact matches: {field_acc.exact_matches}/{field_acc.total_values} ({field_acc.exact_match_rate:.2%})"
                )
                print(
                    f"    Close matches: {field_acc.close_matches}/{field_acc.total_values} ({field_acc.close_match_rate:.2%})"
                )
                print(f"    Mismatches: {field_acc.mismatches}")
                print(f"    Missing: {field_acc.missing}")

        # All tables should be detected
        all_detected = all(ta.detected for ta in accuracy.table_accuracies)
        assert all_detected, "Not all ground truth tables were detected"
