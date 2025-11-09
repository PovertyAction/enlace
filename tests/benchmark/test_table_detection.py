"""Benchmark tests for table detection accuracy.

This module tests the accuracy of table detection across different extraction
configurations (OCR backends, augmentation settings).
"""

from pathlib import Path

import pytest

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor
from tests.benchmark.utils import calculate_detection_metrics, load_annotation


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


class TestTableDetectionBaseline:
    """Test table detection without OCR (baseline)."""

    def test_table_detection_no_ocr(self, paper_path, ground_truth, tmp_path):
        """Test table detection accuracy without OCR."""
        # Extract with no OCR
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Get table IDs
        extracted_ids = {t.table_number for t in result.tables}
        expected_ids = {t.table_number for t in ground_truth.ground_truth.tables}

        # Calculate metrics
        metrics = calculate_detection_metrics(extracted_ids, expected_ids)

        # Assert minimum thresholds (adjust based on actual performance)
        assert metrics.recall >= 0.8, f"Table recall too low: {metrics.recall:.2%}"
        assert metrics.precision >= 0.8, (
            f"Table precision too low: {metrics.precision:.2%}"
        )
        assert metrics.f1_score >= 0.8, f"Table F1 too low: {metrics.f1_score:.2%}"

        # Log results for reporting
        print(f"\nTable Detection (No OCR) - {paper_path.stem}:")
        print(f"  Precision: {metrics.precision:.2%}")
        print(f"  Recall: {metrics.recall:.2%}")
        print(f"  F1 Score: {metrics.f1_score:.2%}")

    def test_figure_detection_no_ocr(self, paper_path, ground_truth, tmp_path):
        """Test figure detection accuracy without OCR."""
        # Extract with no OCR
        config = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Get figure IDs
        extracted_ids = {f.figure_number for f in result.figures}
        expected_ids = {
            f.figure_number
            for f in ground_truth.ground_truth.figures
            if f.figure_number
        }

        if not expected_ids:
            pytest.skip("No figures in ground truth")

        # Calculate metrics
        metrics = calculate_detection_metrics(extracted_ids, expected_ids)

        # Assert minimum thresholds
        assert metrics.recall >= 0.7, f"Figure recall too low: {metrics.recall:.2%}"
        assert metrics.precision >= 0.7, (
            f"Figure precision too low: {metrics.precision:.2%}"
        )

        # Log results
        print(f"\nFigure Detection (No OCR) - {paper_path.stem}:")
        print(f"  Precision: {metrics.precision:.2%}")
        print(f"  Recall: {metrics.recall:.2%}")
        print(f"  F1 Score: {metrics.f1_score:.2%}")


class TestTableDetectionOCR:
    """Test table detection with OCR backends."""

    @pytest.mark.parametrize("ocr_backend", ["tesseract", "easyocr"])
    def test_table_detection_with_ocr(
        self, paper_path, ground_truth, ocr_backend, tmp_path
    ):
        """Test table detection accuracy with different OCR backends."""
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

        # Get table IDs
        extracted_ids = {t.table_number for t in result.tables}
        expected_ids = {t.table_number for t in ground_truth.ground_truth.tables}

        # Calculate metrics
        metrics = calculate_detection_metrics(extracted_ids, expected_ids)

        # Assert minimum thresholds (should be same or better than baseline)
        assert metrics.recall >= 0.8, f"Table recall too low: {metrics.recall:.2%}"
        assert metrics.precision >= 0.8, (
            f"Table precision too low: {metrics.precision:.2%}"
        )

        # Log results
        print(f"\nTable Detection ({ocr_backend.upper()}) - {paper_path.stem}:")
        print(f"  Precision: {metrics.precision:.2%}")
        print(f"  Recall: {metrics.recall:.2%}")
        print(f"  F1 Score: {metrics.f1_score:.2%}")

    def test_table_detection_auto_ocr(self, paper_path, ground_truth, tmp_path):
        """Test table detection with auto OCR backend (hybrid mode)."""
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

        # Get table IDs
        extracted_ids = {t.table_number for t in result.tables}
        expected_ids = {t.table_number for t in ground_truth.ground_truth.tables}

        # Calculate metrics
        metrics = calculate_detection_metrics(extracted_ids, expected_ids)

        # Assert minimum thresholds
        assert metrics.recall >= 0.8, f"Table recall too low: {metrics.recall:.2%}"
        assert metrics.precision >= 0.8, (
            f"Table precision too low: {metrics.precision:.2%}"
        )

        # Log results
        print(f"\nTable Detection (AUTO/HYBRID) - {paper_path.stem}:")
        print(f"  Precision: {metrics.precision:.2%}")
        print(f"  Recall: {metrics.recall:.2%}")
        print(f"  F1 Score: {metrics.f1_score:.2%}")


class TestDetectionComparison:
    """Compare detection performance across configurations."""

    def test_detection_comparison(self, paper_path, ground_truth, tmp_path):
        """Compare table detection across all configurations."""
        configs = {
            "no_ocr": ExtractionConfig(
                enable_ocr=False, enable_augmentation=False, output_dir=tmp_path
            ),
            "tesseract": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="tesseract",
                enable_augmentation=False,
                output_dir=tmp_path,
            ),
            "easyocr": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="easyocr",
                enable_augmentation=False,
                output_dir=tmp_path,
            ),
            "auto": ExtractionConfig(
                enable_ocr=True,
                ocr_backend="auto",
                enable_augmentation=False,
                output_dir=tmp_path,
            ),
        }

        results = {}
        expected_ids = {t.table_number for t in ground_truth.ground_truth.tables}

        for config_name, config in configs.items():
            config.verbose = False
            extractor = PaperExtractor(config)
            result = extractor.extract(paper_path)

            extracted_ids = {t.table_number for t in result.tables}
            metrics = calculate_detection_metrics(extracted_ids, expected_ids)

            results[config_name] = {
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1_score,
                "tp": metrics.true_positives,
                "fp": metrics.false_positives,
                "fn": metrics.false_negatives,
            }

        # Print comparison report
        print(f"\n{'=' * 70}")
        print(f"Table Detection Comparison - {paper_path.stem}")
        print(f"{'=' * 70}")
        print(
            f"{'Configuration':<15} {'Precision':>10} {'Recall':>10} {'F1':>10} {'TP':>5} {'FP':>5} {'FN':>5}"
        )
        print("-" * 70)
        for config_name, metrics in results.items():
            print(
                f"{config_name:<15} {metrics['precision']:>9.2%} {metrics['recall']:>9.2%} "
                f"{metrics['f1']:>9.2%} {metrics['tp']:>5} {metrics['fp']:>5} {metrics['fn']:>5}"
            )

        # Assert that at least one configuration achieves good performance
        best_f1 = max(r["f1"] for r in results.values())
        assert best_f1 >= 0.8, (
            f"No configuration achieved F1 >= 0.8 (best: {best_f1:.2%})"
        )
