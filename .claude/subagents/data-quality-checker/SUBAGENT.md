# Data Quality Checker Subagent

**Version:** 1.0
**Status:** ✅ Production Ready
**Phase:** Validation (Phase 1)

## Overview

The **data-quality-checker** subagent performs comprehensive validation of extracted research paper data, ensuring quality and consistency before data harmonization and analysis.

## Purpose

Validate extraction outputs from the [content-extractor](../content-extractor/) subagent through multiple validation levels:

1. **Structure Validation** - Required fields and data types
2. **Completeness Analysis** - Coverage of metadata and content
3. **Accuracy Checking** - Quality scores and internal consistency
4. **Statistical Consistency** - Regression statistics validation
5. **Missing Data Detection** - Systematic gaps and patterns

## Skills Used

- `table-validator` - Table accuracy validation
- `data-validator` - Data quality checks
- `research-analyst` - Quality criteria

## Input/Output

### Input

**Single Paper Validation:**

```json
{
  "extraction_path": "extracted/paper_id/extraction.json",
  "source_pdf": "papers/paper_id.pdf",  // Optional
  "validation_level": "standard"  // quick, standard, comprehensive
}
```

**Batch Validation:**

```json
{
  "extraction_dir": "extracted/",
  "validation_level": "standard"
}
```

### Output

**Validation Report:**

```json
{
  "paper_id": "smith2020",
  "validation_date": "2025-11-06T10:30:00",
  "passed": true,
  "score": 0.85,
  "issues": [],
  "warnings": [
    "Table table_3: Low quality score (0.65)"
  ],
  "checks": {
    "structure": {"passed": true, "score": 1.0},
    "completeness": {"passed": true, "score": 0.8},
    "accuracy": {"passed": true, "score": 0.9},
    "statistical_consistency": {"passed": true, "score": 0.95},
    "missing_data": {"passed": true, "score": 0.7}
  },
  "table_validations": [
    {
      "table_id": "table_1",
      "passed": true,
      "quality_score": 0.95,
      "issues": [],
      "warnings": []
    }
  ],
  "recommendations": [
    "Consider manual review of table_3 due to low quality score"
  ]
}
```

## Validation Levels

### Quick (2-5 seconds)

- Structure validation
- Completeness checks
- **Use for:** Fast screening, CI/CD pipelines

### Standard (5-10 seconds) ⭐ Default

- Structure + Completeness
- Accuracy checks
- Missing data detection
- **Use for:** Normal validation workflow

### Comprehensive (10-20 seconds)

- All standard checks
- Statistical consistency validation
- Cross-validation with source PDF (if provided)
- **Use for:** High-stakes papers, final QA

## Validation Checks

### 1. Structure Validation

**Purpose:** Ensure extraction output format is correct

**Checks:**

- Required fields present (`paper_id`, `metadata`, `tables`, etc.)
- Correct data types (lists, dicts)
- No malformed JSON

**Failure Criteria:** Missing required fields

### 2. Completeness Analysis

**Purpose:** Assess coverage of extracted content

**Metrics:**

- Metadata completeness (title, authors, year, DOI)
- Tables extracted (count)
- Citations found (typical: 20+)

**Warning Thresholds:**

- Metadata < 50% complete
- No tables extracted
- < 5 citations found

### 3. Accuracy Checking

**Purpose:** Validate extraction quality

**Checks:**

- Table quality scores (target: > 0.7)
- Empty or malformed tables
- Data vs. metadata consistency (row/col counts)

**Failure Criteria:**

- Empty tables
- Severe row/column mismatches

### 4. Statistical Consistency

**Purpose:** Validate regression statistics

**Checks:**

- T-statistics = coefficient / std_error (±10% tolerance)
- P-values consistent with t-stats (|t| > 1.96 → p < 0.05)
- Standard errors positive
- Reasonable coefficient magnitudes

**Example:**

```text
Coefficient: 0.500
Std Error:   (0.250)
Expected t:  2.00
Actual t:    1.95  ✓ Within 10% tolerance

|t| = 1.95 < 1.96 → p should be ≥ 0.05
Actual p:    0.052  ✓ Consistent
```

**Warning Criteria:**

- Statistical inconsistencies found
- < 80% of checks pass

### 5. Missing Data Detection

**Purpose:** Identify systematic data gaps

**Checks:**

- Cell fill rate (warning if < 50% filled)
- Completely empty rows/columns
- Systematic missing patterns

**Warning Thresholds:**
>
- > 50% empty cells
- Multiple empty rows/columns

## Quality Scoring

### Overall Score Calculation

Weighted average of check scores:

```text
Score = 0.30 × structure
      + 0.20 × completeness
      + 0.30 × accuracy
      + 0.10 × statistical_consistency
      + 0.10 × missing_data
```

### Pass/Fail Determination

- **PASSED:** No issues AND score ≥ 0.70
- **FAILED:** Any issues OR score < 0.70

## Usage

### CLI Usage

**Single Paper:**

```bash
uv run python validator.py validate extracted/smith2020/extraction.json \
  --level standard \
  --source-pdf papers/smith2020.pdf \
  --output-dir validation_reports
```

**Batch Processing:**

```bash
uv run python validator.py batch extracted/ \
  --level comprehensive \
  --output-dir validation_reports
```

### Python API

```python
from validator import DataQualityChecker

# Initialize
checker = DataQualityChecker(output_dir="validation_reports")

# Validate single extraction
result = checker.validate(
    extraction_path="extracted/smith2020/extraction.json",
    source_pdf="papers/smith2020.pdf",
    validation_level="comprehensive"
)

if result["passed"]:
    print(f"✓ Validation passed: score={result['score']:.2f}")
else:
    print(f"✗ Validation failed: {len(result['issues'])} issues")
    for issue in result["issues"]:
        print(f"  - {issue}")

# Batch validation
batch_result = checker.validate_batch(
    extraction_dir="extracted/",
    validation_level="standard"
)

print(f"Validated: {batch_result['papers_validated']}")
print(f"Passed: {batch_result['papers_passed']}")
print(f"Failed: {batch_result['papers_failed']}")
```

## Integration with Workflow

### Sequential Pipeline

```text
content-extractor → data-quality-checker → data-harmonizer
     (Phase 2)            (Phase 3)             (Phase 4)
```

**Workflow:**

1. Content-extractor produces `extraction.json`
2. Data-quality-checker validates output
3. If validation passes → proceed to harmonization
4. If validation fails → flag for manual review

### Recommended Usage Patterns

**Pattern 1: Quick Batch Screen**

```bash
# Fast validation of all extractions
uv run python validator.py batch extracted/ --level quick
# Review failures, re-extract if needed
```

**Pattern 2: Standard Validation**

```bash
# Normal workflow validation
uv run python validator.py batch extracted/ --level standard
# Papers that pass → ready for harmonization
# Papers with warnings → review manually
```

**Pattern 3: High-Confidence Papers**

```bash
# Comprehensive validation for key papers
uv run python validator.py validate extracted/important_paper/extraction.json \
  --level comprehensive \
  --source-pdf papers/important_paper.pdf
```

## Output Files

### Individual Validation Reports

**Location:** `validation_reports/{paper_id}_validation.json`

**Contents:**

- Pass/fail status
- Overall quality score
- Detailed check results
- Per-table validations
- Issues and warnings
- Actionable recommendations

### Batch Validation Summary

**Location:** `validation_reports/batch_validation_summary.json`

**Contents:**

- Aggregate statistics
- Papers passed/failed counts
- Average quality scores
- Links to individual reports

## Recommendations Engine

The validator generates actionable recommendations based on validation results:

| Issue | Recommendation |
|-------|----------------|
| Low metadata completeness | Use bibliography skill for better extraction |
| No tables extracted | Verify PDF quality, try OCR for scanned docs |
| Low accuracy scores | Review extraction settings, try docling VLM |
| Statistical inconsistencies | Manual review of regression tables |
| High missing data rates | Check table formatting, may need custom rules |
| Score < 0.5 | Re-extract with different settings |

## Performance

- **Quick validation:** ~2-5 seconds/paper
- **Standard validation:** ~5-10 seconds/paper
- **Comprehensive validation:** ~10-20 seconds/paper
- **Batch processing:** ~100 papers in 5-10 minutes (standard)

## Known Limitations

1. **Source PDF comparison not implemented:** Currently validates internal consistency only. Full accuracy checking requires PDF comparison (future enhancement).

2. **Table type detection:** Relies on content-extractor's classification. May not detect all regression tables.

3. **Statistical checks basic:** Assumes standard regression format. May miss alternative specifications.

4. **No cross-paper validation:** Validates papers independently. No checks for consistency across studies (handled by data-harmonizer).

## Future Enhancements

### Priority 1: Source PDF Comparison

- Direct number matching against PDF
- OCR fallback for scanned documents
- Pixel-level table comparison

### Priority 2: Enhanced Statistical Validation

- Detect standard error formats (heteroskedasticity-robust, clustered)
- Validate F-statistics, R²
- Check coefficient bounds (e.g., probabilities in [0,1])

### Priority 3: Machine Learning Quality Prediction

- Train model to predict extraction quality
- Automated flagging of problematic extractions
- Active learning from user feedback

### Priority 4: Integration with table-validator Skill

- Use existing table-validator for deeper checks
- Leverage validation templates
- Cross-reference with paper structure

## Testing

### Test with Existing Extractions

The validator has been designed to work with the existing extraction outputs in `extracted_test_v2/`:

```bash
# Test single paper
uv run python validator.py validate \
  extracted_test_v2/BHKM_Liberia/extraction.json \
  --level comprehensive

# Test all papers
uv run python validator.py batch extracted_test_v2/ --level standard
```

### Expected Results

Based on the architecture document's test results:

- **5 papers processed**
- **59 tables extracted**
- **Average quality score:** 0.61
- **Expected validation pass rate:** 80-90%

### Validation Metrics

- Structure: 100% pass expected (well-formed JSON)
- Completeness: 60-80% (metadata extraction limited)
- Accuracy: 70-90% (depends on table quality)
- Statistical: 90%+ (few regression tables in test set)
- Missing data: 70-85% (some empty cells expected)

## Dependencies

**Python packages:**

- `numpy` - Statistical calculations
- Standard library only (no external API calls)

**Skills (future integration):**

- `table-validator` - Enhanced table validation
- `data-validator` - Advanced quality checks

## Version History

### Version 1.0 (2025-11-06)

- Initial implementation
- All 5 validation checks implemented
- CLI and Python API
- Batch processing support
- Recommendations engine
- Comprehensive documentation

## Related Documentation

- [Content Extractor](../content-extractor/SUBAGENT.md) - Upstream subagent
- [Subagent Architecture](../../../docs/SUBAGENT_ARCHITECTURE.md) - Overall system design
- [CLAUDE.md](../../../CLAUDE.md) - Project overview

## Support

For issues or questions:

1. Check [docs/SUBAGENT_ARCHITECTURE.md](../../../docs/SUBAGENT_ARCHITECTURE.md) for workflow context
2. Review test outputs in `validation_reports/`
3. Examine individual validation reports for detailed diagnostics
