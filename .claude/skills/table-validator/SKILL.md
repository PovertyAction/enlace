---
name: table-validator
description: Validate extracted tables against source PDFs, check regression table accuracy, verify statistical results, and identify extraction errors. Use after pdf-processor to ensure data quality.
---

# Table Validation for Research Data Extraction

Validate that tables extracted from PDFs match the source documents and contain accurate data.

## When to Use This Skill

Use this skill when you need to:

- Verify extracted regression tables against source PDF
- Check that coefficients and standard errors match
- Validate summary statistics tables
- Identify extraction errors or inconsistencies
- Quality-check automated extraction workflows
- Compare multiple extraction attempts

## Quick Validation Workflow

### Step 1: Extract Table from PDF

```python
# Using pdf-processor (docling)
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("paper.pdf")

# Save first table
if result.document.tables:
    first_table = result.document.tables[0]
    table_html = first_table.export_to_html()
    with open("extracted_table.html", "w") as f:
        f.write(table_html)
```

### Step 2: Visual Comparison

```python
from pathlib import Path
import pandas as pd
from IPython.display import display, HTML

# Load extracted table
table_html = Path("extracted_table.html").read_text()

# Display side-by-side with source page image
print("Extracted Table:")
display(HTML(table_html))

print("\nSource PDF (check manually)")
# Note: Page information available from table metadata if needed
if result.document.tables:
    print(f"Table found in document")
```

### Step 3: Statistical Validation

```python
def validate_regression_table(df, expected_stats):
    """Validate extracted regression table."""
    errors = []

    # Check row count
    if len(df) != expected_stats.get("rows"):
        errors.append(f"Row count mismatch: {len(df)} vs {expected_stats['rows']}")

    # Check column count
    if len(df.columns) != expected_stats.get("columns"):
        errors.append(f"Column count mismatch: {len(df.columns)} vs {expected_stats['columns']}")

    # Check for null values in key columns
    key_cols = ["coefficient", "std_error"]
    for col in key_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > expected_stats.get(f"{col}_nulls", 0):
                errors.append(f"{col} has {null_count} null values")

    # Check value ranges
    if "coefficient" in df.columns:
        coef_range = df["coefficient"].abs().max()
        if coef_range > 1000:  # Suspiciously large
            errors.append(f"Coefficient values seem too large: max={coef_range}")

    return errors

# Example usage
expected = {
    "rows": 15,
    "columns": 4,
    "coefficient_nulls": 0,
    "std_error_nulls": 0
}

errors = validate_regression_table(extracted_df, expected)
if errors:
    print("Validation errors found:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✓ Table validation passed")
```

## Advanced Validation

### Compare Extracted Numbers to Source

```python
import re
from difflib import SequenceMatcher

def extract_numbers_from_html(html):
    """Extract all numbers from HTML table."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Find all numbers
    numbers = re.findall(r'[-+]?\d*\.?\d+', text)
    return [float(n) for n in numbers]

def compare_tables(extracted_html, reference_html, tolerance=0.01):
    """Compare extracted table to reference."""
    extracted_nums = extract_numbers_from_html(extracted_html)
    reference_nums = extract_numbers_from_html(reference_html)

    if len(extracted_nums) != len(reference_nums):
        return {
            "match": False,
            "reason": f"Number count mismatch: {len(extracted_nums)} vs {len(reference_nums)}"
        }

    # Compare each number
    mismatches = []
    for i, (ext, ref) in enumerate(zip(extracted_nums, reference_nums)):
        if abs(ext - ref) > tolerance:
            mismatches.append({
                "position": i,
                "extracted": ext,
                "reference": ref,
                "difference": ext - ref
            })

    if mismatches:
        return {
            "match": False,
            "mismatches": mismatches,
            "accuracy": 1 - (len(mismatches) / len(extracted_nums))
        }

    return {"match": True, "accuracy": 1.0}
```

### Regression Table Specific Checks

```python
def validate_regression_coefficients(df):
    """Validate regression table structure and values."""
    checks = {}

    # Check 1: t-statistics match coefficients/SE
    if all(col in df.columns for col in ["coefficient", "std_error", "t_statistic"]):
        df["computed_t"] = df["coefficient"] / df["std_error"]
        t_diff = (df["t_statistic"] - df["computed_t"]).abs()
        checks["t_statistic_valid"] = (t_diff < 0.1).all()
    checks["observations"] = len(df)
    checks["models"] = len([c for c in df.columns if c.startswith("Model")])

    # Check 3: Significance stars match p-values
    if "significance" in df.columns and "p_value" in df.columns:
        def check_sig(row):
            if pd.isna(row["p_value"]):
                return True
            stars = row["significance"].count("*") if isinstance(row["significance"], str) else 0
            if row["p_value"] < 0.01:
                return stars == 3
            elif row["p_value"] < 0.05:
                return stars == 2
            elif row["p_value"] < 0.10:
                return stars == 1
            return stars == 0

        checks["significance_valid"] = df.apply(check_sig, axis=1).all()

    return checks

# Run validation
validation = validate_regression_coefficients(regression_df)
for check, result in validation.items():
    status = "✓" if result else "✗"
    print(f"{status} {check}: {result}")
```

## Integration with Research Workflow

```text
PDF Paper
    │
    ▼
pdf-processor
    │
    ▼
Extracted Table (HTML/DataFrame)
    │
    ▼
table-validator
    │
    ├─→ Structure validation
    ├─→ Number comparison
    ├─→ Statistical checks
    └─→ Generate validation report
    │
    ▼
Validated Data ✓
    │
    ▼
research-analyst / pyfixest
```

## Best Practices

1. **Always validate critical tables** - Regression results, primary outcomes
2. **Check manually for first few papers** - Build confidence in extraction
3. **Set up automated checks** - Run validation in pipeline
4. **Document validation failures** - Track which papers need manual review

## See Also

- **pdf-processor** - Extract tables from PDFs
- **data-validator** - Validate data quality and completeness
- **research-analyst** - Systematic data extraction workflow
