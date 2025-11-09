# Benchmark Testing Guide

This document provides a comprehensive guide to the benchmark testing infrastructure for evaluating extraction accuracy across different configurations.

## Overview

The benchmark system evaluates extraction accuracy by comparing automated extraction results against manually annotated ground truth data. It supports testing across multiple configurations:

- **OCR Backends**: None (baseline), Tesseract, EasyOCR, Auto/Hybrid
- **Semantic Augmentation**: Enabled/Disabled
- **Metrics**: Detection accuracy, field-level accuracy, performance timing

## Quick Start

### 1. Create Ground Truth Annotation

```bash
# Generate annotation template from automated extraction
python scripts/create_annotation.py papers/BHKM_Liberia.pdf --annotator "Your Name"

# This creates: tests/fixtures/benchmark_data/BHKM_Liberia_ground_truth.json
```

### 2. Manual Review and Correction

Follow the detailed instructions in [docs/VALIDATION_INSTRUCTIONS.md](VALIDATION_INSTRUCTIONS.md):

1. Open the PDF and annotation JSON side-by-side
2. Verify and correct all values (coefficients, standard errors, metadata)
3. Estimated time: 1.5-2 hours per paper

### 3. Validate Annotation

```bash
# Check that annotation passes schema validation
python scripts/create_annotation.py papers/BHKM_Liberia.pdf --validate-only
```

### 4. Run Benchmark Tests

```bash
# Run all benchmark tests
uv run pytest tests/benchmark/ -v

# Run specific test suites
uv run pytest tests/benchmark/test_table_detection.py -v
uv run pytest tests/benchmark/test_field_accuracy.py -v
uv run pytest tests/benchmark/test_ocr_comparison.py -v

# Run with detailed output
uv run pytest tests/benchmark/ -v -s
```

### 5. Generate Benchmark Report

```bash
# Generate comprehensive markdown report
python scripts/generate_benchmark_report.py

# Customize papers and configurations
python scripts/generate_benchmark_report.py \
  --papers BHKM_Liberia Karlan-etal-GhanaDigitalCredit \
  --configs baseline tesseract easyocr auto augmented \
  --output reports/benchmark_$(date +%Y%m%d).md \
  --json reports/benchmark_$(date +%Y%m%d).json
```

## Directory Structure

```text
tests/
├── benchmark/
│   ├── __init__.py
│   ├── utils.py                      # Comparison functions, metrics
│   ├── test_table_detection.py       # Detection accuracy tests
│   ├── test_field_accuracy.py        # Field-level accuracy tests
│   └── test_ocr_comparison.py        # OCR backend comparison tests
└── fixtures/
    ├── benchmark_data/
    │   ├── BHKM_Liberia_ground_truth.json
    │   ├── Karlan-etal-GhanaDigitalCredit_ground_truth.json
    │   └── BKM_recruitment_feb2013_ground_truth.json
    ├── annotation_schema.json        # JSON schema for annotations
    └── annotation_validator.py       # Pydantic models for validation

scripts/
├── create_annotation.py              # Create/validate annotations
└── generate_benchmark_report.py     # Generate benchmark reports

docs/
├── VALIDATION_INSTRUCTIONS.md        # Detailed annotation guide
└── BENCHMARK_README.md              # This file
```

## Ground Truth Annotation

### Annotation Schema

Ground truth annotations are JSON files that contain:

1. **Metadata**: Paper title, authors, year, DOI, journal
2. **Tables**: Regression, summary statistics, and balance tables with:
   - Table identification (number, title, page, type)
   - Regression models with coefficients, standard errors, significance
   - Summary statistics (means, medians, standard deviations)
   - Balance comparisons (treatment/control groups)
3. **Figures**: Figure numbers, captions, page numbers, types
4. **Semantic Context** (optional): Variable definitions, treatment descriptions

### Pydantic Models

The annotation validator provides type-safe Pydantic models:

- `Annotation`: Top-level annotation structure
- `GroundTruth`: Complete ground truth data
- `PaperMetadata`: Title, authors, year, DOI, journal
- `GroundTruthTable`: Table with type-specific content
- `GroundTruthModel`: Regression model with coefficients
- `GroundTruthCoefficient`: Individual coefficient with SE, p-value, CI
- `GroundTruthStatistic`: Summary statistic with mean, median, SD
- `GroundTruthComparison`: Balance table comparison
- `GroundTruthFigure`: Figure metadata

### Loading and Validation

```python
from pathlib import Path
from tests.fixtures.annotation_validator import Annotation

# Load and validate annotation
annotation = Annotation.load(Path("tests/fixtures/benchmark_data/BHKM_Liberia_ground_truth.json"))

# Access ground truth data
print(annotation.ground_truth.metadata.title)
print(f"Tables: {len(annotation.ground_truth.tables)}")
print(f"Figures: {len(annotation.ground_truth.figures)}")

# Iterate through tables
for table in annotation.ground_truth.tables:
    print(f"{table.table_number}: {table.title} ({table.table_type})")
```

## Benchmark Tests

### Test Suites

#### 1. Table Detection Tests ([test_table_detection.py](../tests/benchmark/test_table_detection.py))

Tests the accuracy of detecting tables and figures in papers.

**Classes:**

- `TestTableDetectionBaseline`: Detection without OCR
- `TestTableDetectionOCR`: Detection with different OCR backends
- `TestDetectionComparison`: Compare detection across all configurations

**Metrics:**

- Precision: TP / (TP + FP)
- Recall: TP / (TP + FN)
- F1 Score: 2 × (Precision × Recall) / (Precision + Recall)

**Thresholds:**

- Table detection: ≥80% precision, recall, F1
- Figure detection: ≥70% precision, recall

#### 2. Field Accuracy Tests ([test_field_accuracy.py](../tests/benchmark/test_field_accuracy.py))

Tests the accuracy of extracting specific field values.

**Classes:**

- `TestFieldAccuracyBaseline`: Field extraction without OCR
- `TestFieldAccuracyOCR`: Field extraction with OCR backends
- `TestFieldAccuracyAugmentation`: Impact of semantic augmentation
- `TestFieldAccuracyComparison`: Comprehensive comparison

**Metrics:**

- Exact match rate: Exact numeric match (<1e-10 difference)
- Close match rate: Within tolerance (default 0.001)
- Missing rate: In ground truth but not extracted
- Mismatch rate: Extracted incorrectly

**Thresholds:**

- Coefficient accuracy: ≥70%
- Standard error accuracy: ≥70%
- Overall accuracy: ≥70%

#### 3. OCR Backend Comparison Tests ([test_ocr_comparison.py](../tests/benchmark/test_ocr_comparison.py))

Compares performance and accuracy across OCR backends.

**Classes:**

- `TestOCRBackendQuality`: Quality comparison (Tesseract vs EasyOCR)
- `TestOCRBackendPerformance`: Speed and performance comparison
- `TestOCRErrorPatterns`: Analyze common OCR errors
- `TestOCRComprehensiveComparison`: Full comparison across all configs

**Metrics:**

- Extraction time (seconds)
- Overall accuracy
- Coefficient accuracy
- Standard error accuracy
- Detection F1 score

**Thresholds:**

- Minimum accuracy: ≥60%
- Maximum extraction time: <5 minutes per paper

## Benchmark Utilities

### Comparison Functions ([tests/benchmark/utils.py](../tests/benchmark/utils.py))

#### Detection Metrics

```python
from tests.benchmark.utils import calculate_detection_metrics

extracted_ids = {"Table 1", "Table 2", "Table 3"}
ground_truth_ids = {"Table 1", "Table 2", "Table 4"}

metrics = calculate_detection_metrics(extracted_ids, ground_truth_ids)
print(f"Precision: {metrics.precision:.2%}")
print(f"Recall: {metrics.recall:.2%}")
print(f"F1: {metrics.f1_score:.2%}")
```

#### Field Comparison

```python
from tests.benchmark.utils import compare_numeric, compare_string

# Numeric comparison with tolerance
exact, close = compare_numeric(0.068, 0.0681, tolerance=0.001)

# String comparison (case-insensitive)
match = compare_string("Treatment Effect", "treatment effect", case_sensitive=False)
```

#### Paper Comparison

```python
from tests.benchmark.utils import compare_paper, generate_accuracy_report

# Compare extraction result against ground truth
accuracy = compare_paper(extraction_result, annotation)

# Generate formatted report
report = generate_accuracy_report(accuracy)
print(report)
```

### Data Classes

- `DetectionMetrics`: TP, FP, FN, precision, recall, F1
- `FieldAccuracy`: Total, exact matches, close matches, mismatches, missing
- `TableAccuracy`: Per-table accuracy with field-level breakdown
- `PaperAccuracy`: Overall paper accuracy with detection and field metrics

## Benchmark Report Generator

### Usage

```bash
python scripts/generate_benchmark_report.py [OPTIONS]
```

### Options

- `--papers`: Paper IDs to benchmark (default: BHKM_Liberia)
- `--configs`: Configurations to test (default: all)
- `--output`: Markdown report path (default: reports/benchmark_report.md)
- `--json`: Also save results as JSON

### Example Report Structure

```markdown
# Extraction Benchmark Report

**Generated:** 2025-11-08 19:30:00

## BHKM_Liberia

### Configuration Comparison

| Configuration | Overall | Coef (exact) | Coef (close) | SE (exact) | SE (close) | Detection F1 | Time |
|---------------|---------|--------------|--------------|------------|------------|--------------|------|
| baseline      | 75.3%   | 72.1%        | 85.4%        | 68.9%      | 79.2%      | 91.7%        | 18.3s |
| tesseract     | 78.2%   | 75.6%        | 87.1%        | 71.3%      | 81.5%      | 91.7%        | 45.2s |
| ...           | ...     | ...          | ...          | ...        | ...        | ...          | ...   |

### Detection Metrics

| Configuration | Precision | Recall | F1    | Tables Detected |
|---------------|-----------|--------|-------|------------------|
| baseline      | 100.0%    | 83.3%  | 91.7% | 5/6             |
| ...           | ...       | ...    | ...   | ...             |

## Cross-Paper Summary

### Average Performance Across Papers

| Configuration | Avg Overall | Avg Coef | Avg F1 | Avg Time |
|---------------|-------------|----------|--------|----------|
| baseline      | 75.3%       | 72.1%    | 91.7%  | 18.3s   |
| ...           | ...         | ...      | ...    | ...     |

### Best Configurations

- **Overall Accuracy:** auto
- **Coefficient Accuracy:** augmented
- **Detection F1:** tesseract
- **Fastest:** baseline
```

## Running Specific Tests

### Test Individual Papers

```bash
# Test only BHKM_Liberia
uv run pytest tests/benchmark/ -v -k "BHKM_Liberia"
```

### Test Specific Configurations

```bash
# Test only baseline (no OCR)
uv run pytest tests/benchmark/test_field_accuracy.py::TestFieldAccuracyBaseline -v

# Test only OCR backends
uv run pytest tests/benchmark/test_ocr_comparison.py -v
```

### Test Specific Metrics

```bash
# Test only coefficient accuracy
uv run pytest tests/benchmark/ -v -k "coefficient"

# Test only detection
uv run pytest tests/benchmark/test_table_detection.py -v
```

### Show Print Output

```bash
# Show detailed output (reports, comparisons)
uv run pytest tests/benchmark/ -v -s
```

## Current Status

### Completed

- ✅ Annotation infrastructure (schema, validator, script)
- ✅ Benchmark utilities (comparison functions, metrics)
- ✅ Table detection tests (3 test classes, 7 tests)
- ✅ Field accuracy tests (4 test classes, 8 tests)
- ✅ OCR backend comparison tests (4 test classes, 7 tests)
- ✅ Benchmark report generator

### Pending (Manual Work)

- ⏳ Annotate BHKM_Liberia.pdf (template created, needs manual review)
- ⏳ Annotate Karlan-etal-GhanaDigitalCredit.pdf
- ⏳ Annotate BKM_recruitment_feb2013.pdf

### Next Steps

1. **Manual annotation** of BHKM_Liberia.pdf following [VALIDATION_INSTRUCTIONS.md](VALIDATION_INSTRUCTIONS.md)
2. **Validate annotation** using `--validate-only` flag
3. **Run first benchmark** to establish baseline metrics
4. **Iterate on extraction** based on accuracy metrics
5. **Add more papers** to build comprehensive benchmark suite

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Benchmark Tests

on:
  pull_request:
    paths:
      - 'src/enlace/core/**'
      - 'tests/benchmark/**'

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run benchmark tests
        run: |
          uv run pytest tests/benchmark/ -v
      - name: Generate benchmark report
        run: |
          python scripts/generate_benchmark_report.py --output reports/benchmark_latest.md
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-report
          path: reports/benchmark_latest.md
```

## Tips and Best Practices

### Annotation Quality

1. **Verify every value**: Don't trust automated extraction for ground truth
2. **Use split-screen**: PDF viewer + JSON editor side-by-side
3. **Take breaks**: Accuracy degrades with fatigue (15 min break/hour)
4. **Check OCR errors**: Watch for O→0, l→1, S→5 substitutions
5. **Validate early**: Run validation after each table to catch errors

### Testing Strategy

1. **Start with baseline**: Establish baseline (no OCR) performance first
2. **Test incrementally**: Add OCR, then augmentation, measuring impact
3. **Track over time**: Run benchmarks regularly to catch regressions
4. **Use realistic data**: Annotate papers representative of target use cases
5. **Document issues**: Note systematic extraction failures for improvement

### Performance Optimization

1. **Skip slow tests**: Use pytest markers for quick vs comprehensive tests
2. **Cache extractions**: Reuse extraction results across test runs
3. **Parallel testing**: Use pytest-xdist for parallel execution
4. **Profile bottlenecks**: Identify slow OCR backends or configurations

## Troubleshooting

### Annotation Validation Errors

```bash
# Common error: Regression tables must have at least one model
# Fix: Add models array with at least one model

# Common error: Invalid year
# Fix: Ensure year is between 1900 and current year + 1

# Common error: Significance pattern mismatch
# Fix: Use only *, **, or *** (or null)
```

### Test Failures

```bash
# Low accuracy: Check if ground truth is correct
# Missing tables: Verify ground truth has all expected tables
# High variability: Add more papers to benchmark suite
# Timeout errors: Increase pytest timeout or reduce paper size
```

### Performance Issues

```bash
# Slow extraction: Consider disabling OCR for baseline tests
# Memory errors: Process papers individually, not in batch
# GPU errors: Check CUDA availability for EasyOCR
```

## References

- [VALIDATION_INSTRUCTIONS.md](VALIDATION_INSTRUCTIONS.md) - Detailed annotation guide
- [annotation_schema.json](../tests/fixtures/annotation_schema.json) - JSON schema reference
- [annotation_validator.py](../tests/fixtures/annotation_validator.py) - Pydantic models
- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) - Overall project migration plan
