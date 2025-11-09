# Ground Truth Annotation Instructions

**Purpose**: Create accurate ground truth annotations for benchmark testing of the extraction pipeline.

**Time Estimate**: 1.5-2 hours per paper (8-10 tables)

---

## Overview

Ground truth annotations serve as the "gold standard" for measuring extraction accuracy. These annotations are manually verified values from research papers that we compare against automated extraction results to calculate precision, recall, and field-level accuracy metrics.

---

## Quick Start

### 1. Generate Annotation Template

```bash
# Create initial template from automated extraction
python scripts/create_annotation.py papers/BHKM_Liberia.pdf --annotator "Your Name"

# Output: tests/fixtures/benchmark_data/BHKM_Liberia_ground_truth.json
```

### 2. Manual Review Process

**Setup**:

- Open the PDF: `papers/BHKM_Liberia.pdf`
- Open the JSON: `tests/fixtures/benchmark_data/BHKM_Liberia_ground_truth.json`
- Use split-screen or dual monitors for efficiency

**Tools**:

- PDF viewer: Any reader with zoom and search
- JSON editor: VS Code, Sublime, or any text editor with JSON syntax highlighting

### 3. Validate Completed Annotation

```bash
# Check annotation passes schema validation
python scripts/create_annotation.py papers/BHKM_Liberia.pdf --validate-only
```

---

## Annotation Workflow

### Step 1: Metadata (5-10 minutes)

**Fields to verify/update**:

```json
{
  "metadata": {
    "title": "Exact title from paper first page",
    "authors": ["First Author", "Second Author", "Third Author"],
    "year": 2018,
    "doi": "10.1234/journal.2018.123456",
    "journal": "Journal of Development Economics",
    "abstract": "Optional: full abstract text"
  }
}
```

**Sources**:

- Title: First page of PDF
- Authors: First page (list all authors in order)
- Year: Publication year from first page or citation
- DOI: Look for DOI on first page or in footer
- Journal: Journal name from first page

**Tips**:

- Copy-paste title exactly (preserve capitalization)
- Watch for special characters (é, ñ, etc.)
- Year = publication year, not study year

---

### Step 2: Table Identification (10-15 minutes)

**For each table in the paper**:

1. **Find table in PDF** - Note page number
2. **Update table metadata**:

```json
{
  "table_id": "table_3",
  "table_number": "Table 3",
  "title": "Impact of Program on Welfare Indicators",
  "page_number": 25,
  "table_type": "regression",
  "notes": "Standard errors in parentheses. * p<0.10, ** p<0.05, *** p<0.01"
}
```

3. **Table type classification**:
   - `regression` - Regression coefficients with dependent variable
   - `summary_statistics` - Descriptive statistics (mean, median, SD)
   - `balance` - Treatment vs control comparison (baseline characteristics)
   - `other` - Other table types

**Tips**:

- `table_id` should be lowercase with underscores: `table_3`
- `table_number` matches PDF exactly: `"Table 3"` or `"Table A.1"`
- Page numbers are critical for validation
- Copy notes verbatim (footnotes under table)

---

### Step 3: Regression Tables (30-60 minutes per table)

**For each regression table**:

#### Model Structure

```json
{
  "models": [
    {
      "model_number": 1,
      "dependent_variable": "Welfare today (standardized)",
      "coefficients": [...],
      "n_observations": 1523,
      "r_squared": 0.234,
      "adjusted_r_squared": 0.228,
      "f_statistic": null,
      "se_type": "Robust",
      "fixed_effects": ["Village FE", "Year FE"],
      "clustering": "Household"
    }
  ]
}
```

#### Coefficient Values

**Critical fields** (verify against PDF):

```json
{
  "variable_name": "Treatment",
  "coefficient": 0.068,
  "std_error": 0.021,
  "t_statistic": 3.24,
  "p_value": 0.001,
  "significance": "***",
  "ci_lower": 0.027,
  "ci_upper": 0.109
}
```

**Verification checklist**:

- [ ] `coefficient` - Exact value from table (check decimal places)
- [ ] `std_error` - Usually in parentheses below coefficient
- [ ] `t_statistic` - May be in separate column or calculated
- [ ] `p_value` - Explicit p-value if shown
- [ ] `significance` - Count stars: `*` (p<0.10), `**` (p<0.05), `***` (p<0.01)
- [ ] `ci_lower` / `ci_upper` - Confidence interval bounds if shown

**Common patterns**:

| PDF Format | JSON Values |
|------------|-------------|
| `0.068***`<br>`(0.021)` | `coefficient: 0.068`<br>`std_error: 0.021`<br>`significance: "***"` |
| `0.045**`<br>`[0.012, 0.078]` | `coefficient: 0.045`<br>`ci_lower: 0.012`<br>`ci_upper: 0.078`<br>`significance: "**"` |
| `0.023 (0.015)` | `coefficient: 0.023`<br>`std_error: 0.015`<br>`significance: null` |

**Tips**:

- Use search (Ctrl+F) in PDF to find specific values
- Watch for negative signs: `-0.045` vs `0.045`
- Decimal precision matters: `0.12` ≠ `0.120`
- If value not shown, use `null` (not `0` or empty string)
- Variable names should match PDF (preserve case)
- Check table notes for SE type (robust, clustered, bootstrapped)

---

### Step 4: Summary Statistics Tables (20-40 minutes per table)

**For each summary statistics table**:

```json
{
  "statistics": [
    {
      "variable_name": "Age",
      "n_obs": 1523,
      "mean": 34.5,
      "median": 32.0,
      "std_dev": 12.3,
      "min_value": 18.0,
      "max_value": 75.0,
      "p10": 22.0,
      "p25": 27.0,
      "p50": 32.0,
      "p75": 41.0,
      "p90": 52.0
    }
  ]
}
```

**Verification checklist**:

- [ ] `variable_name` - Exact name from table
- [ ] `n_obs` - Sample size (often in first column)
- [ ] `mean` - Average value
- [ ] `std_dev` - Standard deviation (often in parentheses or "SD" column)
- [ ] Percentiles - If shown (p10, p25, p50/median, p75, p90)
- [ ] `min_value` / `max_value` - If shown

**Tips**:

- SD often shown as `34.5 (12.3)` - second number is `std_dev`
- `p50` = `median` (if both shown, verify they match)
- Some tables show only mean/SD - leave other fields as `null`

---

### Step 5: Balance Tables (20-40 minutes per table)

**For each balance table**:

```json
{
  "comparisons": [
    {
      "variable_name": "Age",
      "control_mean": 33.2,
      "control_sd": 11.8,
      "control_n": 762,
      "treatment_mean": 34.1,
      "treatment_sd": 12.5,
      "treatment_n": 761,
      "difference": 0.9,
      "p_value": 0.234,
      "normalized_difference": 0.073
    }
  ]
}
```

**Verification checklist**:

- [ ] `control_mean` / `treatment_mean` - Group means
- [ ] `control_sd` / `treatment_sd` - Group standard deviations
- [ ] `control_n` / `treatment_n` - Group sample sizes
- [ ] `difference` - Usually treatment minus control
- [ ] `p_value` - Significance of difference
- [ ] `normalized_difference` - Standardized difference (if shown)

**Common formats**:

| Column Headers | Field Mapping |
|----------------|---------------|
| Control, Treatment, Diff, p-value | `control_mean`, `treatment_mean`, `difference`, `p_value` |
| (1), (2), (3)-(1), p | `control_mean`, `treatment_mean`, `difference`, `p_value` |

**Tips**:

- SDs often in parentheses below means
- N may be at table bottom or in column header
- Check table notes for which group is control/treatment
- Difference direction matters: verify sign (+ or -)

---

### Step 6: Figures (5-10 minutes)

**For each figure**:

```json
{
  "figures": [
    {
      "figure_id": "figure_1",
      "figure_number": "Figure 1",
      "caption": "Study Timeline and Sample Flow",
      "page_number": 12,
      "figure_type": "diagram"
    }
  ]
}
```

**Figure types**:

- `chart` - Bar chart, line chart, scatter plot
- `diagram` - Flow diagram, timeline, conceptual diagram
- `map` - Geographic map
- `photo` - Photograph
- `plot` - Statistical plot (distribution, regression plot)
- `other` - Other types

**Tips**:

- Copy caption exactly from PDF
- Page number = where figure appears
- Count figures in order of appearance

---

## Quality Control Checklist

### Before Validation

**Metadata**:

- [ ] Title matches first page exactly
- [ ] All authors listed in order
- [ ] Year is publication year (not study year)
- [ ] DOI format correct (if available)

**Tables**:

- [ ] All tables from PDF are annotated
- [ ] Table numbers match PDF (`"Table 3"` not `"table 3"`)
- [ ] Page numbers added for all tables
- [ ] Table types correct (regression/summary_statistics/balance)

**Regression Tables**:

- [ ] All coefficient values match PDF
- [ ] Standard errors verified (check parentheses)
- [ ] Significance stars counted correctly
- [ ] N observations correct
- [ ] R² values verified
- [ ] Variable names preserve case/spelling from PDF

**Summary Statistics**:

- [ ] Means match PDF
- [ ] Standard deviations match PDF
- [ ] N values correct

**Balance Tables**:

- [ ] Control and treatment groups identified correctly
- [ ] All group means verified
- [ ] Difference values and signs correct

**Figures**:

- [ ] All figures counted
- [ ] Captions copied exactly
- [ ] Page numbers correct

---

## Common Issues and Solutions

### Issue: Coefficient not extracting correctly

**Diagnosis**: OCR may misread digits (O→0, l→1, S→5)

**Solution**: Manually verify and correct each value against PDF

**Example**:

- PDF shows: `0.068`
- Extraction shows: `O.O68` (letter O instead of zero)
- Correction: Change to `0.068`

### Issue: Variable names inconsistent

**Problem**: Extraction may truncate or reformat names

**Solution**: Copy exact text from PDF table

**Example**:

- PDF: `Treatment (Cash Transfer)`
- Extraction: `Treatment`
- Correction: Change to `"Treatment (Cash Transfer)"`

### Issue: Table not detected

**Problem**: Template missing a table from PDF

**Solution**: Manually add table to JSON

```json
{
  "table_id": "table_4",
  "table_number": "Table 4",
  "title": "Robustness Checks",
  "page_number": 28,
  "table_type": "regression",
  "notes": null,
  "models": []
}
```

Then fill in models/coefficients.

### Issue: Standard errors vs confidence intervals

**Problem**: PDF shows both, unclear which to use

**Solution**: Prioritize standard errors, add CIs if shown

```json
{
  "coefficient": 0.068,
  "std_error": 0.021,
  "ci_lower": 0.027,
  "ci_upper": 0.109
}
```

### Issue: Missing values in PDF

**Problem**: Some cells blank or show "-"

**Solution**: Use `null` in JSON (not `0`, not `"-"`)

```json
{
  "coefficient": 0.045,
  "std_error": null,
  "p_value": null
}
```

---

## Validation

### Run Validation Check

```bash
python scripts/create_annotation.py papers/BHKM_Liberia.pdf --validate-only
```

### Expected Output (Success)

```text
✅ Annotation is valid!
   Paper: Impact of Agriculture Programs on Welfare in Liberia
   Tables: 6
   Figures: 2
```

### Expected Output (Errors)

```text
❌ Validation failed:
  - Table table_3: Regression tables must have at least one model
  - Field 'year' must be between 1900 and 2026
```

**Fix errors and re-validate** until successful.

---

## Tips for Efficiency

### Keyboard Shortcuts

**PDF Navigation**:

- `Ctrl/Cmd + F` - Find text
- `Ctrl/Cmd + G` - Find next
- `Page Up/Down` - Navigate pages
- `Ctrl/Cmd + +/-` - Zoom in/out

**JSON Editing** (VS Code):

- `Ctrl/Cmd + D` - Select next occurrence
- `Ctrl/Cmd + Shift + L` - Select all occurrences
- `Alt + Up/Down` - Move line up/down
- `Ctrl/Cmd + /` - Comment/uncomment

### Workflow Optimization

1. **One table at a time** - Complete each table fully before moving to next
2. **Use find/replace** - If same error repeated (e.g., OCR O→0)
3. **Batch similar tasks** - Do all metadata first, then all tables
4. **Take breaks** - Accuracy degrades with fatigue (15 min break/hour)

### Common Patterns

**Coefficient + SE in parentheses**:

```text
PDF: 0.068***
     (0.021)

JSON: {"coefficient": 0.068, "std_error": 0.021, "significance": "***"}
```

**Coefficient + CI in brackets**:

```text
PDF: 0.045**
     [0.012, 0.078]

JSON: {"coefficient": 0.045, "ci_lower": 0.012, "ci_upper": 0.078, "significance": "**"}
```

**Summary stats with SD**:

```text
PDF: 34.5 (12.3)

JSON: {"mean": 34.5, "std_dev": 12.3}
```

---

## Priority Guidelines

### Must Verify (Critical for Benchmarks)

1. **Regression coefficients** - Highest priority
2. **Standard errors** - Second priority
3. **N observations** - Critical for sample size checks
4. **Significance levels** - Important for inference

### Should Verify (Important but Lower Priority)

5. **R² values** - Useful for model quality
6. **Variable names** - Important for matching
7. **Table numbers** - Needed for detection metrics

### Optional (Nice to Have)

8. **Confidence intervals** - If shown in PDF
9. **F-statistics** - Often not reported
10. **Abstract** - Can be added later

---

## Annotation Deliverables

### Files to Create

For each paper:

- `tests/fixtures/benchmark_data/{paper_id}_ground_truth.json`

### Papers to Annotate (Priority Order)

1. **BHKM_Liberia.pdf** (6 tables) - First priority, representative size
2. **Karlan-etal-GhanaDigitalCredit.pdf** (4 tables) - Second priority, smaller
3. **BKM_recruitment_feb2013.pdf** (7 tables) - Third priority, validation

### Success Criteria

**For each annotation**:

- ✅ Passes schema validation
- ✅ All tables from PDF represented
- ✅ All coefficients verified against PDF
- ✅ All standard errors verified
- ✅ Metadata complete and accurate

---

## Next Steps After Annotation

Once annotation is validated:

1. **Run first benchmark**:

   ```bash
   python tests/benchmark/test_field_accuracy.py
   ```

2. **Generate accuracy report**:

   ```python
   from enlace.core.extractor import PaperExtractor
   from tests.benchmark.utils import compare_paper, generate_accuracy_report
   from tests.fixtures.annotation_validator import Annotation

   # Extract
   extractor = PaperExtractor(config)
   result = extractor.extract(Path("papers/BHKM_Liberia.pdf"))

   # Load annotation
   annotation = Annotation.load(Path("tests/fixtures/benchmark_data/BHKM_Liberia_ground_truth.json"))

   # Compare
   accuracy = compare_paper(result, annotation)
   print(generate_accuracy_report(accuracy))
   ```

3. **Iterate and improve** - Use accuracy metrics to identify extraction issues

---

## Support

**Questions?**

- Check `tests/fixtures/annotation_schema.json` for field definitions
- Review `tests/fixtures/annotation_validator.py` for validation rules
- See example annotation (once first one is complete)

**Common errors**:

- Schema validation errors → Check field types (number vs string vs null)
- File not found → Verify file path is relative to project root
- Import errors → Run from project root directory

---

## Appendix: JSON Schema Reference

### Quick Reference

**Metadata**:

```json
{
  "title": "string (required)",
  "authors": ["string", "string"],
  "year": 2018,
  "doi": "string or null",
  "journal": "string or null"
}
```

**Regression Coefficient**:

```json
{
  "variable_name": "string (required)",
  "coefficient": 0.068 or null,
  "std_error": 0.021 or null,
  "significance": "*" or "**" or "***" or null
}
```

**Regression Model**:

```json
{
  "model_number": 1,
  "dependent_variable": "string or null",
  "coefficients": [],
  "n_observations": 1523 or null,
  "r_squared": 0.234 or null
}
```

See `tests/fixtures/annotation_schema.json` for complete schema.
