"""Generate comprehensive benchmark report from test results.

This script runs benchmark tests and generates a formatted report comparing
extraction accuracy across different configurations (OCR backends, augmentation).

Usage:
    python scripts/generate_benchmark_report.py
    python scripts/generate_benchmark_report.py --papers BHKM_Liberia Karlan-etal-GhanaDigitalCredit
    python scripts/generate_benchmark_report.py --output reports/benchmark_$(date +%Y%m%d).md
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor

# Add tests to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from benchmark.utils import compare_paper, load_annotation


def run_extraction(paper_path: Path, config: ExtractionConfig) -> tuple[dict, float]:
    """Run extraction and return results with timing.

    Args:
        paper_path: Path to PDF file
        config: Extraction configuration

    Returns:
        Tuple of (extraction_result, elapsed_time)

    """
    extractor = PaperExtractor(config)

    start = time.time()
    result = extractor.extract(paper_path)
    elapsed = time.time() - start

    return result, elapsed


def calculate_metrics(result, ground_truth) -> dict:
    """Calculate all accuracy metrics.

    Args:
        result: ExtractionResult
        ground_truth: Annotation

    Returns:
        Dictionary of metrics

    """
    accuracy = compare_paper(result, ground_truth)

    # Collect field-level metrics
    coef_accuracies = []
    se_accuracies = []
    close_coef_accuracies = []
    close_se_accuracies = []

    for table_acc in accuracy.table_accuracies:
        if "coefficient" in table_acc.field_accuracies:
            coef_acc = table_acc.field_accuracies["coefficient"]
            coef_accuracies.append(coef_acc.exact_match_rate)
            close_coef_accuracies.append(coef_acc.close_match_rate)

        if "std_error" in table_acc.field_accuracies:
            se_acc = table_acc.field_accuracies["std_error"]
            se_accuracies.append(se_acc.exact_match_rate)
            close_se_accuracies.append(se_acc.close_match_rate)

    return {
        "overall_accuracy": accuracy.overall_accuracy,
        "detection_precision": accuracy.detection_metrics.precision,
        "detection_recall": accuracy.detection_metrics.recall,
        "detection_f1": accuracy.detection_metrics.f1_score,
        "coefficient_exact": (
            sum(coef_accuracies) / len(coef_accuracies) if coef_accuracies else 0.0
        ),
        "coefficient_close": (
            sum(close_coef_accuracies) / len(close_coef_accuracies)
            if close_coef_accuracies
            else 0.0
        ),
        "std_error_exact": (
            sum(se_accuracies) / len(se_accuracies) if se_accuracies else 0.0
        ),
        "std_error_close": (
            sum(close_se_accuracies) / len(close_se_accuracies)
            if close_se_accuracies
            else 0.0
        ),
        "tables_detected": len([ta for ta in accuracy.table_accuracies if ta.detected]),
        "tables_total": len(accuracy.table_accuracies),
        "metadata_title": accuracy.metadata_accuracy["title"],
        "metadata_year": accuracy.metadata_accuracy["year"],
    }


def generate_markdown_report(results: dict, output_path: Path) -> None:
    """Generate markdown benchmark report.

    Args:
        results: Dictionary of benchmark results
        output_path: Path to save markdown report

    """
    lines = []

    # Header
    lines.append("# Extraction Benchmark Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Papers tested:** {len(results['papers'])}")
    lines.append(
        f"- **Configurations:** {len(results['papers'][next(iter(results['papers']))]['configurations'])}"
    )
    lines.append("")

    # Per-paper results
    for paper_id, paper_results in results["papers"].items():
        lines.append(f"## {paper_id}")
        lines.append("")

        # Configuration comparison table
        lines.append("### Configuration Comparison")
        lines.append("")
        lines.append(
            "| Configuration | Overall | Coef (exact) | Coef (close) | SE (exact) | SE (close) | Detection F1 | Time |"
        )
        lines.append(
            "|---------------|---------|--------------|--------------|------------|------------|--------------|------|"
        )

        for config_name, config_results in paper_results["configurations"].items():
            metrics = config_results["metrics"]
            lines.append(
                f"| {config_name} | {metrics['overall_accuracy']:.2%} | "
                f"{metrics['coefficient_exact']:.2%} | {metrics['coefficient_close']:.2%} | "
                f"{metrics['std_error_exact']:.2%} | {metrics['std_error_close']:.2%} | "
                f"{metrics['detection_f1']:.2%} | {config_results['time']:.1f}s |"
            )

        lines.append("")

        # Detection metrics
        lines.append("### Detection Metrics")
        lines.append("")
        lines.append("| Configuration | Precision | Recall | F1 | Tables Detected |")
        lines.append("|---------------|-----------|--------|----|--------------------|")

        for config_name, config_results in paper_results["configurations"].items():
            metrics = config_results["metrics"]
            lines.append(
                f"| {config_name} | {metrics['detection_precision']:.2%} | "
                f"{metrics['detection_recall']:.2%} | {metrics['detection_f1']:.2%} | "
                f"{metrics['tables_detected']}/{metrics['tables_total']} |"
            )

        lines.append("")

        # Metadata accuracy
        lines.append("### Metadata Extraction")
        lines.append("")
        lines.append("| Configuration | Title Match | Year Match |")
        lines.append("|---------------|-------------|------------|")

        for config_name, config_results in paper_results["configurations"].items():
            metrics = config_results["metrics"]
            title_icon = "✓" if metrics["metadata_title"] else "✗"
            year_icon = "✓" if metrics["metadata_year"] else "✗"
            lines.append(f"| {config_name} | {title_icon} | {year_icon} |")

        lines.append("")
        lines.append("---")
        lines.append("")

    # Cross-paper summary
    lines.append("## Cross-Paper Summary")
    lines.append("")

    # Aggregate metrics by configuration
    config_aggregates = {}
    for paper_results in results["papers"].values():
        for config_name, config_results in paper_results["configurations"].items():
            if config_name not in config_aggregates:
                config_aggregates[config_name] = {
                    "overall_accuracy": [],
                    "coefficient_exact": [],
                    "detection_f1": [],
                    "time": [],
                }

            metrics = config_results["metrics"]
            config_aggregates[config_name]["overall_accuracy"].append(
                metrics["overall_accuracy"]
            )
            config_aggregates[config_name]["coefficient_exact"].append(
                metrics["coefficient_exact"]
            )
            config_aggregates[config_name]["detection_f1"].append(
                metrics["detection_f1"]
            )
            config_aggregates[config_name]["time"].append(config_results["time"])

    lines.append("### Average Performance Across Papers")
    lines.append("")
    lines.append("| Configuration | Avg Overall | Avg Coef | Avg F1 | Avg Time |")
    lines.append("|---------------|-------------|----------|--------|----------|")

    for config_name, aggregates in config_aggregates.items():
        avg_overall = sum(aggregates["overall_accuracy"]) / len(
            aggregates["overall_accuracy"]
        )
        avg_coef = sum(aggregates["coefficient_exact"]) / len(
            aggregates["coefficient_exact"]
        )
        avg_f1 = sum(aggregates["detection_f1"]) / len(aggregates["detection_f1"])
        avg_time = sum(aggregates["time"]) / len(aggregates["time"])

        lines.append(
            f"| {config_name} | {avg_overall:.2%} | {avg_coef:.2%} | {avg_f1:.2%} | {avg_time:.1f}s |"
        )

    lines.append("")

    # Best configurations
    lines.append("### Best Configurations")
    lines.append("")

    best_overall = max(
        config_aggregates.items(),
        key=lambda x: sum(x[1]["overall_accuracy"]) / len(x[1]["overall_accuracy"]),
    )
    best_coef = max(
        config_aggregates.items(),
        key=lambda x: sum(x[1]["coefficient_exact"]) / len(x[1]["coefficient_exact"]),
    )
    best_f1 = max(
        config_aggregates.items(),
        key=lambda x: sum(x[1]["detection_f1"]) / len(x[1]["detection_f1"]),
    )
    best_time = min(
        config_aggregates.items(),
        key=lambda x: sum(x[1]["time"]) / len(x[1]["time"]),
    )

    lines.append(f"- **Overall Accuracy:** {best_overall[0]}")
    lines.append(f"- **Coefficient Accuracy:** {best_coef[0]}")
    lines.append(f"- **Detection F1:** {best_f1[0]}")
    lines.append(f"- **Fastest:** {best_time[0]}")
    lines.append("")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✓ Report saved to: {output_path}")


def main():
    """Run benchmark tests and generate report."""
    parser = argparse.ArgumentParser(description="Generate extraction benchmark report")
    parser.add_argument(
        "--papers",
        nargs="+",
        default=["BHKM_Liberia"],
        help="Paper IDs to benchmark",
    )
    parser.add_argument(
        "--configs",
        nargs="+",
        default=["baseline", "tesseract", "easyocr", "auto", "augmented"],
        help="Configurations to test",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/benchmark_report.md"),
        help="Output path for report",
    )
    parser.add_argument(
        "--json",
        type=Path,
        help="Also save results as JSON",
    )

    args = parser.parse_args()

    # Setup paths
    papers_dir = Path("papers")
    annotation_dir = Path("tests/fixtures/benchmark_data")
    output_dir = Path("temp_benchmark")

    # Define configurations
    config_definitions = {
        "baseline": ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=False,
            output_dir=output_dir / "baseline",
        ),
        "tesseract": ExtractionConfig(
            enable_ocr=True,
            ocr_backend="tesseract",
            enable_augmentation=False,
            output_dir=output_dir / "tesseract",
        ),
        "easyocr": ExtractionConfig(
            enable_ocr=True,
            ocr_backend="easyocr",
            enable_augmentation=False,
            output_dir=output_dir / "easyocr",
        ),
        "auto": ExtractionConfig(
            enable_ocr=True,
            ocr_backend="auto",
            enable_augmentation=False,
            output_dir=output_dir / "auto",
        ),
        "augmented": ExtractionConfig(
            enable_ocr=False,
            enable_augmentation=True,
            output_dir=output_dir / "augmented",
        ),
    }

    # Filter to requested configs
    configs = {k: v for k, v in config_definitions.items() if k in args.configs}

    print("=" * 70)
    print("EXTRACTION BENCHMARK")
    print("=" * 70)
    print(f"\nPapers: {', '.join(args.papers)}")
    print(f"Configurations: {', '.join(configs.keys())}")
    print("")

    results = {"papers": {}}

    # Run benchmarks
    for paper_id in args.papers:
        print(f"\n{'─' * 70}")
        print(f"Paper: {paper_id}")
        print(f"{'─' * 70}")

        # Load ground truth
        annotation_path = annotation_dir / f"{paper_id}_ground_truth.json"
        if not annotation_path.exists():
            print(f"⚠️  Ground truth not found: {annotation_path}")
            continue

        ground_truth = load_annotation(annotation_path)

        # Get paper path
        paper_path = papers_dir / f"{paper_id}.pdf"
        if not paper_path.exists():
            print(f"⚠️  Paper not found: {paper_path}")
            continue

        results["papers"][paper_id] = {"configurations": {}}

        # Test each configuration
        for config_name, config in configs.items():
            print(f"\n  Testing {config_name}...", end=" ", flush=True)

            config.verbose = False
            result, elapsed = run_extraction(paper_path, config)
            metrics = calculate_metrics(result, ground_truth)

            results["papers"][paper_id]["configurations"][config_name] = {
                "time": elapsed,
                "metrics": metrics,
            }

            print(f"✓ ({elapsed:.1f}s, {metrics['overall_accuracy']:.2%} accuracy)")

    # Generate reports
    print(f"\n{'=' * 70}")
    print("Generating reports...")
    print(f"{'=' * 70}")

    # Markdown report
    generate_markdown_report(results, args.output)

    # JSON report (optional)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        with args.json.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"✓ JSON saved to: {args.json}")

    print("\n✅ Benchmark complete!")


if __name__ == "__main__":
    main()
