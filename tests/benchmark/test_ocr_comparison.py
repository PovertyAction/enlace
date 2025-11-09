"""Benchmark tests comparing OCR backends.

This module specifically tests and compares the performance of different
OCR backends (tesseract, easyocr, auto/hybrid) for scanned documents.
"""

from pathlib import Path

import pytest

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor
from tests.benchmark.utils import compare_paper, load_annotation


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


class TestOCRBackendQuality:
    """Test quality differences between OCR backends."""

    def test_tesseract_vs_easyocr_coefficient_accuracy(
        self, paper_path, ground_truth, tmp_path
    ):
        """Compare coefficient extraction accuracy between Tesseract and EasyOCR."""
        # Extract with Tesseract
        config_tess = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="tesseract",
            enable_augmentation=False,
            output_dir=tmp_path / "tesseract",
            verbose=False,
        )
        extractor_tess = PaperExtractor(config_tess)
        result_tess = extractor_tess.extract(paper_path)
        accuracy_tess = compare_paper(result_tess, ground_truth)

        # Extract with EasyOCR
        config_easy = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="easyocr",
            enable_augmentation=False,
            output_dir=tmp_path / "easyocr",
            verbose=False,
        )
        extractor_easy = PaperExtractor(config_easy)
        result_easy = extractor_easy.extract(paper_path)
        accuracy_easy = compare_paper(result_easy, ground_truth)

        # Collect coefficient accuracies
        tess_coef_acc = []
        easy_coef_acc = []

        for table_acc in accuracy_tess.table_accuracies:
            if "coefficient" in table_acc.field_accuracies:
                tess_coef_acc.append(
                    table_acc.field_accuracies["coefficient"].exact_match_rate
                )

        for table_acc in accuracy_easy.table_accuracies:
            if "coefficient" in table_acc.field_accuracies:
                easy_coef_acc.append(
                    table_acc.field_accuracies["coefficient"].exact_match_rate
                )

        if not tess_coef_acc or not easy_coef_acc:
            pytest.skip("No regression tables in ground truth")

        avg_tess = sum(tess_coef_acc) / len(tess_coef_acc)
        avg_easy = sum(easy_coef_acc) / len(easy_coef_acc)

        # Print comparison
        print(f"\n{'=' * 70}")
        print("Tesseract vs EasyOCR - Coefficient Accuracy")
        print(f"{'=' * 70}")
        print(f"Tesseract: {avg_tess:.2%}")
        print(f"EasyOCR:   {avg_easy:.2%}")
        print(f"Difference: {avg_easy - avg_tess:+.2%}")

        # Both should achieve minimum threshold
        assert avg_tess >= 0.6, f"Tesseract accuracy too low: {avg_tess:.2%}"
        assert avg_easy >= 0.6, f"EasyOCR accuracy too low: {avg_easy:.2%}"

    def test_auto_ocr_fallback_behavior(self, paper_path, ground_truth, tmp_path):
        """Test that auto OCR backend makes intelligent fallback decisions."""
        # Extract with auto OCR
        config = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="auto",
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=True,  # Enable verbose to see fallback decisions
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Auto should achieve similar or better accuracy than individual backends
        # since it can choose the best one dynamically
        assert accuracy.overall_accuracy >= 0.6, (
            f"Auto OCR accuracy too low: {accuracy.overall_accuracy:.2%}"
        )

        print(f"\nAuto OCR overall accuracy: {accuracy.overall_accuracy:.2%}")


class TestOCRBackendPerformance:
    """Test performance characteristics of OCR backends."""

    def test_ocr_backend_extraction_time(self, paper_path, tmp_path):
        """Compare extraction time across OCR backends."""
        import time

        backends = ["tesseract", "easyocr", "auto"]
        timings = {}

        for backend in backends:
            config = ExtractionConfig(
                enable_ocr=True,
                ocr_backend=backend,
                enable_augmentation=False,
                output_dir=tmp_path / backend,
                verbose=False,
            )
            extractor = PaperExtractor(config)

            start = time.time()
            extractor.extract(paper_path)
            elapsed = time.time() - start

            timings[backend] = elapsed

        # Print timing comparison
        print(f"\n{'=' * 70}")
        print("OCR Backend Extraction Time Comparison")
        print(f"{'=' * 70}")
        for backend, elapsed in timings.items():
            print(f"{backend:>10}: {elapsed:>6.2f}s")

        # Ensure no backend is unreasonably slow (> 5 minutes for typical paper)
        for backend, elapsed in timings.items():
            assert elapsed < 300, (
                f"{backend} took too long: {elapsed:.1f}s (> 5 minutes)"
            )

    def test_no_ocr_vs_ocr_performance(self, paper_path, tmp_path):
        """Compare extraction time with and without OCR."""
        import time

        # No OCR baseline
        config_no_ocr = ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=tmp_path / "no_ocr",
            verbose=False,
        )
        extractor_no_ocr = PaperExtractor(config_no_ocr)

        start = time.time()
        extractor_no_ocr.extract(paper_path)
        time_no_ocr = time.time() - start

        # With OCR (auto backend)
        config_ocr = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="auto",
            enable_augmentation=False,
            output_dir=tmp_path / "ocr",
            verbose=False,
        )
        extractor_ocr = PaperExtractor(config_ocr)

        start = time.time()
        extractor_ocr.extract(paper_path)
        time_ocr = time.time() - start

        # Print comparison
        print(f"\n{'=' * 70}")
        print("OCR vs No-OCR Performance Comparison")
        print(f"{'=' * 70}")
        print(f"No OCR: {time_no_ocr:>6.2f}s")
        print(f"OCR:    {time_ocr:>6.2f}s")
        print(
            f"Overhead: {time_ocr - time_no_ocr:>6.2f}s ({(time_ocr / time_no_ocr - 1) * 100:+.1f}%)"
        )


class TestOCRErrorPatterns:
    """Test common OCR error patterns and corrections."""

    def test_numeric_ocr_errors(self, paper_path, ground_truth, tmp_path):
        """Identify common numeric OCR errors (O→0, l→1, S→5)."""
        # Extract with OCR
        config = ExtractionConfig(
            enable_ocr=True,
            ocr_backend="tesseract",  # Tesseract often has these issues
            enable_augmentation=False,
            output_dir=tmp_path,
            verbose=False,
        )
        extractor = PaperExtractor(config)
        result = extractor.extract(paper_path)

        # Compare against ground truth
        accuracy = compare_paper(result, ground_truth)

        # Collect mismatches to analyze error patterns
        mismatches = []

        for table_acc in accuracy.table_accuracies:
            if table_acc.table_type != "regression":
                continue

            # Get extracted and ground truth tables
            extracted_table = next(
                (t for t in result.tables if t.table_number == table_acc.table_number),
                None,
            )
            gt_table = next(
                (
                    t
                    for t in ground_truth.ground_truth.tables
                    if t.table_number == table_acc.table_number
                ),
                None,
            )

            if (
                not extracted_table
                or not gt_table
                or not hasattr(extracted_table, "models")
            ):
                continue

            # Compare coefficients
            for gt_model in gt_table.models:
                for gt_coef in gt_model.coefficients:
                    if gt_coef.coefficient is None:
                        continue

                    # Find matching extracted coefficient
                    for ex_model in extracted_table.models:
                        ex_coef = next(
                            (
                                c
                                for c in ex_model.coefficients
                                if c.variable_name.lower().strip()
                                == gt_coef.variable_name.lower().strip()
                            ),
                            None,
                        )

                        if (
                            ex_coef
                            and ex_coef.coefficient is not None
                            and abs(ex_coef.coefficient - gt_coef.coefficient) > 0.001
                        ):
                            mismatches.append(
                                {
                                    "variable": gt_coef.variable_name,
                                    "expected": gt_coef.coefficient,
                                    "extracted": ex_coef.coefficient,
                                    "error": ex_coef.coefficient - gt_coef.coefficient,
                                }
                            )

        # Print error analysis
        if mismatches:
            print(f"\n{'=' * 70}")
            print("OCR Numeric Error Analysis")
            print(f"{'=' * 70}")
            print(f"Total mismatches: {len(mismatches)}")
            print("\nExamples:")
            for i, mm in enumerate(mismatches[:10]):  # Show first 10
                print(
                    f"  {mm['variable']}: expected {mm['expected']}, got {mm['extracted']} (error: {mm['error']:+.4f})"
                )


class TestOCRComprehensiveComparison:
    """Comprehensive comparison of all OCR configurations."""

    def test_all_ocr_configurations(self, paper_path, ground_truth, tmp_path):
        """Compare all OCR configurations comprehensively."""
        import time

        configs = {
            "no_ocr": {
                "config": ExtractionConfig(
                    enable_ocr=False,
                    enable_augmentation=False,
                    output_dir=tmp_path / "no_ocr",
                    verbose=False,
                ),
                "description": "Baseline (no OCR)",
            },
            "tesseract": {
                "config": ExtractionConfig(
                    enable_ocr=True,
                    ocr_backend="tesseract",
                    enable_augmentation=False,
                    output_dir=tmp_path / "tesseract",
                    verbose=False,
                ),
                "description": "Tesseract OCR",
            },
            "easyocr": {
                "config": ExtractionConfig(
                    enable_ocr=True,
                    ocr_backend="easyocr",
                    enable_augmentation=False,
                    output_dir=tmp_path / "easyocr",
                    verbose=False,
                ),
                "description": "EasyOCR",
            },
            "auto": {
                "config": ExtractionConfig(
                    enable_ocr=True,
                    ocr_backend="auto",
                    enable_augmentation=False,
                    output_dir=tmp_path / "auto",
                    verbose=False,
                ),
                "description": "Auto/Hybrid OCR",
            },
        }

        results = {}

        for config_name, config_info in configs.items():
            extractor = PaperExtractor(config_info["config"])

            start = time.time()
            result = extractor.extract(paper_path)
            elapsed = time.time() - start

            accuracy = compare_paper(result, ground_truth)

            # Collect metrics
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
                "description": config_info["description"],
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
                "time": elapsed,
            }

        # Print comprehensive comparison
        print(f"\n{'=' * 100}")
        print(f"Comprehensive OCR Backend Comparison - {paper_path.stem}")
        print(f"{'=' * 100}")
        print(
            f"{'Configuration':<20} {'Overall':>10} {'Coef':>10} {'SE':>10} {'F1':>10} {'Time':>10}"
        )
        print("-" * 100)

        for config_name, metrics in results.items():
            print(
                f"{metrics['description']:<20} {metrics['overall']:>9.2%} "
                f"{metrics['coefficient']:>9.2%} {metrics['std_error']:>9.2%} "
                f"{metrics['detection_f1']:>9.2%} {metrics['time']:>8.2f}s"
            )

        # Find best configuration by overall accuracy
        best_config = max(results.items(), key=lambda x: x[1]["overall"])
        print(
            f"\nBest configuration: {best_config[1]['description']} ({best_config[1]['overall']:.2%})"
        )

        # Assert reasonable performance
        assert best_config[1]["overall"] >= 0.6, (
            f"Best configuration accuracy too low: {best_config[1]['overall']:.2%}"
        )
