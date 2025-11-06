# Data Quality Checker Subagent

Comprehensive validation of extracted research paper data.

## Quick Start

**Single paper validation:**

```bash
uv run python validator.py validate extracted/paper_id/extraction.json --level standard
```

**Batch validation:**

```bash
uv run python validator.py batch extracted/ --level standard
```

## Installation

No additional dependencies required beyond the main project environment.

## Validation Levels

- **quick** - Fast screening (structure + completeness)
- **standard** ⭐ - Normal workflow (+ accuracy + missing data)
- **comprehensive** - Full validation (+ statistical consistency)

## Output

Validation reports saved to `validation_reports/`:

- Individual: `{paper_id}_validation.json`
- Batch summary: `batch_validation_summary.json`

## Documentation

See [SUBAGENT.md](SUBAGENT.md) for complete documentation.

## Test Results

Tested on 6 papers from `extracted_test_v2/`:

- **4 passed** (67%)
- **2 failed** (33%)
- **Average score:** 0.75
- **Processing time:** 0.006s (all papers)

**Typical issues found:**

- Empty tables (extraction failures)
- Low metadata completeness
- Missing citations
- Low quality scores

## Integration

Part of the research analysis pipeline:

```text
content-extractor → data-quality-checker → data-harmonizer
```

Validates extraction quality before proceeding to harmonization and analysis.
