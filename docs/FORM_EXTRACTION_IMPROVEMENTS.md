# Form Extraction Improvements

This document describes the enhancements made to the form-based paper extraction system.

## Overview of Improvements

The improved `extract_from_form_improved.py` script provides significant enhancements over the original:

### 1. **Structured Field Parsing (`FormField` class)**

- **What**: Object-oriented representation of form fields with all metadata
- **Why**: Makes it easier to work with field properties like constraints, hints, and choices
- **Benefit**: Better validation, clearer code, extensible for future features

```python
class FormField:
    def __init__(self, row: pd.Series):
        self.name = row['name']
        self.label = row['label']
        self.field_type = str(row['rando'])
        self.hint = row.get('hint', '')
        self.required = str(row.get('required', '')).lower() == 'yes'
        self.choices = self._parse_choices(row)
        self.constraint = row.get('constraint', '')
```

### 2. **Data Validation (`ExtractionValidator` class)**

- **What**: Validates extracted data against form schema with type coercion
- **Why**: LLMs may return data in inconsistent formats
- **Features**:
  - Type conversion (string to int, parsing dates)
  - Required field validation
  - Choice validation for select fields
  - Warning collection for problematic extractions

**Example**:

```python
validator = ExtractionValidator(form_fields)
cleaned_data, warnings = validator.validate(raw_extraction)
# Automatically converts "2023" to 2023 for integer fields
# Converts "value1; value2" to ["value1", "value2"] for multi-select
```

### 3. **Retry Logic with Exponential Backoff**

- **What**: Automatic retry on API errors or JSON parsing failures
- **Why**: API calls can fail due to rate limits, network issues, or malformed JSON
- **Implementation**:

```python
def extract_with_llm(prompt: str, api_key: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            # ... API call
        except APIError as e:
            wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
            time.sleep(wait_time)
```

### 4. **Incremental Processing**

- **What**: Skip already-extracted papers unless force flag is set
- **Why**: Save time and API costs when re-running after failures
- **Usage**:

```python
# Skips papers that already have extraction JSON files
process_paper(..., force_reextract=False)
```

### 5. **Enhanced Prompting**

- **What**: More structured prompt with field metadata
- **Improvements**:
  - Field type specifications (integer, date, select_one, etc.)
  - Hints from form definition
  - Required field indicators
  - Choice options for select fields
  - Clear output format examples

**Before**:

```text
**authNum**: Number of authors
Type: integer
```

**After**:

```text
**authNum**: Number of authors
   Hint: Count all authors listed in the paper
   Type: integer (REQUIRED)
   Constraint: must be >= 1
```

### 6. **Better Field Categorization**

- **What**: Organized fields into 9 logical sections instead of 7
- **New categories**: Data Collection, expanded matching patterns
- **Benefit**: Better prompt organization, easier for LLM to process related fields together

Categories:

- Publication Details
- Study Design
- Interventions/Treatments
- Credit/Loan Details
- Outcomes
- Geographic Information
- Sample Information
- Data Collection (NEW)
- Other (fallback)

### 7. **Comprehensive Reporting**

- **What**: Detailed statistics and diagnostics after extraction
- **Features**:
  - Overall completion statistics
  - Field-by-field completion rates
  - Top 10 most/least complete fields
  - Warning summaries per paper
  - Failed paper tracking

**Example Output**:

```text
╭───────────────────────────────────────╮
│    Overall Statistics                 │
├─────────────────────────┬─────────────┤
│ Metric                  │ Value       │
├─────────────────────────┼─────────────┤
│ Total Papers            │ 6           │
│ Total Fields            │ 89          │
│ Papers with Warnings    │ 2           │
╰─────────────────────────┴─────────────╯

Field Completion Rates:
╭────────────────────────────────────────╮
│  Top 10 Most Complete Fields           │
├──────────────────────┬─────────────────┤
│ Field                │ Completion %    │
├──────────────────────┼─────────────────┤
│ studyID              │ 100.0%          │
│ IPA_studyName        │ 100.0%          │
│ pubYear              │ 100.0%          │
│ authNum              │ 100.0%          │
╰──────────────────────┴─────────────────╯
```

### 8. **Progress Tracking**

- **What**: Rich progress bar showing current paper being processed
- **Why**: Better user experience for long-running extractions
- **Includes**: Spinner, progress bar, task counter

### 9. **Error Recovery**

- **What**: Continues processing remaining papers even if some fail
- **Why**: One bad PDF shouldn't stop the entire batch
- **Tracking**: Collects all failures with error messages for review

### 10. **Logging Infrastructure**

- **What**: Proper Python logging setup
- **Why**: Easier debugging and audit trail
- **Output**: Timestamps, module names, log levels

## Usage

### Basic Usage

```bash
# Run improved extraction
uv run python scripts/extract_from_form_improved.py
```

### Force Re-extraction

To re-extract already processed papers, modify the script:

```python
extracted_data, warnings = process_paper(
    paper, form_fields, validator, api_key, output_dir,
    force_reextract=True  # Set to True
)
```

### Custom Form Path

```python
form_path = Path("data/forms/DEV_stage2_ipaMC_v1.xlsx")  # Use different form
```

## Validation Features

### Type Coercion

Automatically converts extracted values to correct types:

```python
# Integer fields
"3" → 3
"2,500" → 2500
"2.0" → 2

# Date fields
Validates format and stores as string

# Select multiple
"income; consumption; savings" → ["income", "consumption", "savings"]
```

### Required Field Checking

```python
if field.required and (value is None or value == "NOT FOUND"):
    warnings.append(f"Missing required field: {field_name}")
```

### Constraint Validation

The validator checks field constraints defined in the form:

- Numeric ranges
- Date ranges
- Pattern matching
- Custom validation rules

## Output Files

### Individual JSON Files

```text
output/form_extractions/
├── Paper_ID10008_extraction.json
├── Paper_ID10005_extraction.json
└── ...
```

Each file contains:

- All extracted fields
- `null` for NOT FOUND values
- Properly typed values (integers as numbers, lists as arrays)

### Combined Excel File

**`output/form_extractions/all_extractions.xlsx`**

- One row per paper
- One column per form field
- `paper_id` column for identification
- Empty cells for NOT FOUND values

## Best Practices

### 1. Form Design

**Clear Labels**: Make questions specific and unambiguous

```text
❌ "What is the sample?"
✅ "Total number of households in the study sample"
```

**Use Hints**: Provide clarification in the hint field

```text
Field: authNum
Label: Number of authors
Hint: Count all authors listed in the paper header, including those in footnotes
```

**Specify Constraints**: Add validation rules

```text
Field: pubYear
Constraint: >= 1900 AND <= 2025
```

### 2. Paper Preparation

- Ensure PDFs are text-based (not scanned images)
- Run `enlace extract` first to verify markdown quality
- Check that tables and figures are properly extracted

### 3. Extraction Quality

**Review Warnings**: Check papers with validation warnings

```bash
# Papers with warnings are highlighted in yellow during extraction
⚠ Paper_ID10008.pdf: 3 warnings
```

**Check Completion Rates**: Focus on fields with low completion

```text
Fields with <50% completion:
  • loan_eligibility_criteria: 33.3%
  • baseline_survey_date: 16.7%
```

**Validate Critical Fields**: Manually verify important extractions

- Study ID
- Sample sizes
- Treatment descriptions
- Key outcomes

### 4. Iterative Refinement

1. Run initial extraction
2. Review completion rates and warnings
3. Refine form labels/hints for low-completion fields
4. Re-extract problematic papers with `force_reextract=True`
5. Repeat until satisfactory

## Comparison with Original Script

| Feature | Original | Improved |
|---------|----------|----------|
| Field parsing | Basic dict | Structured FormField objects |
| Validation | None | Comprehensive with type coercion |
| Error handling | Stop on error | Continue with retry logic |
| Progress tracking | Spinner only | Full progress bar |
| Reporting | Minimal | Detailed statistics |
| Incremental processing | No | Yes (skip completed) |
| Prompting | Basic | Enhanced with metadata |
| Field categorization | 7 sections | 9 sections + better matching |
| Logging | Print statements | Proper logging |
| Type coercion | Manual in LLM | Automatic validation |

## Advanced Customization

### Custom Validators

Add custom validation logic:

```python
class CustomValidator(ExtractionValidator):
    def validate(self, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        cleaned, warnings = super().validate(data)
        
        # Custom validation
        if cleaned.get('authNum', 0) > 20:
            warnings.append("Unusually high author count (>20)")
        
        if cleaned.get('pubYear'):
            year = int(cleaned['pubYear'])
            if year < 2000:
                warnings.append(f"Old publication ({year})")
        
        return cleaned, warnings
```

### Custom Prompting

Modify the prompt generation:

```python
def create_custom_prompt(fields: list[FormField], paper_text: str) -> str:
    prompt = f"""You are extracting data for a meta-analysis.
    
Focus especially on:
- Sample size and composition
- Treatment details and dosage
- Primary outcome measurements
- Effect sizes and confidence intervals

Paper text:
{paper_text}

Fields to extract:
"""
    # ... add fields
    return prompt
```

### Parallel Processing

For large batches, add multiprocessing:

```python
from concurrent.futures import ThreadPoolExecutor

def process_batch(papers, max_workers=3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_paper, paper, ...)
            for paper in papers
        ]
        results = [f.result() for f in futures]
    return results
```

## Troubleshooting

### High Failure Rate

**Problem**: Many papers failing extraction

**Solutions**:

- Check API key is valid
- Verify papers are properly converted to markdown
- Reduce batch size to avoid rate limits
- Check network connectivity

### Low Completion Rates

**Problem**: Many fields returning "NOT FOUND"

**Solutions**:

- Review form labels for clarity
- Add hints with examples
- Check if information actually exists in papers
- Try more specific keywords in labels

### Type Conversion Errors

**Problem**: Warnings about type conversion failures

**Solutions**:

- Review the raw LLM responses
- Check if LLM is using unexpected formats
- Add custom parsing logic in validator
- Update prompt with clearer format instructions

### Memory Issues

**Problem**: Script crashes on large papers

**Solutions**:

- Reduce `paper_text` truncation limit (currently 50,000 chars)
- Process papers individually rather than batch
- Increase system memory allocation

## Future Enhancements

### Planned Features

1. **Choice Parsing**: Extract valid choices from form definition
2. **Repeat Group Support**: Handle nested/repeated fields
3. **Multi-language Support**: Extract from non-English papers
4. **Confidence Scores**: LLM should indicate certainty
5. **Interactive Review**: Web UI for reviewing extractions
6. **Automated QA**: Cross-reference with paper content
7. **Version Control**: Track extraction history and changes
8. **Batch Validation**: Compare extractions across papers for consistency

### Integration Opportunities

1. **With enlace validation**: Use ExtractionValidator for quality checks
2. **With semantic search**: Verify extractions against paper content
3. **With table extraction**: Pre-populate fields from extracted tables
4. **With VLM**: Extract from figures and images

## Contributing

To add new validation rules or features:

1. Create a new validator class extending `ExtractionValidator`
2. Add custom validation logic in the `validate()` method
3. Document new warnings and error messages
4. Add tests for edge cases

Example:

```python
class OutcomeValidator(ExtractionValidator):
    """Validates outcome-related fields."""
    
    def validate(self, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        cleaned, warnings = super().validate(data)
        
        # Custom logic for outcomes
        outcomes = cleaned.get('outcomes', [])
        if not outcomes:
            warnings.append("No outcomes specified")
        elif len(outcomes) > 10:
            warnings.append(f"Many outcomes specified ({len(outcomes)})")
        
        return cleaned, warnings
```

## Support

For issues or questions:

1. Check the logs in `output/form_extractions/`
2. Review this documentation
3. Consult `FORM_EXTRACTION.md` for basics
4. Check enlace documentation for PDF extraction issues
