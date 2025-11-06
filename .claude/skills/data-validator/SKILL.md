---
name: data-validator
description: Validate research data quality, check completeness, identify outliers, verify data types, and ensure consistency across datasets. Use before analysis to catch data issues early.
---

# Data Quality Validation

Ensure research data quality through comprehensive validation checks.

## When to Use This Skill

Use this skill when you need to:

- Validate extracted data quality
- Check for missing values
- Identify outliers
- Verify data types and schemas
- Ensure data consistency
- Prepare data quality reports
- Validate data before analysis

## Quick Start

### Basic Validation

```python
import pandas as pd
import numpy as np

def basic_validation(df):
    """Run basic data quality checks."""
    report = {}

    # Dimensions
    report["rows"] = len(df)
    report["columns"] = len(df.columns)

    # Missing values
    report["missing"] = df.isnull().sum().to_dict()
    report["missing_pct"] = (df.isnull().sum() / len(df) * 100).to_dict()

    # Duplicates
    report["duplicates"] = df.duplicated().sum()

    # Data types
    report["dtypes"] = df.dtypes.astype(str).to_dict()

    return report

# Example
df = pd.read_csv("extracted_data.csv")
report = basic_validation(df)

print(f"Rows: {report['rows']}, Columns: {report['columns']}")
print(f"Duplicates: {report['duplicates']}")
print("\nMissing Values:")
for col, pct in report["missing_pct"].items():
    if pct > 0:
        print(f"  {col}: {pct:.1f}%")
```

### Schema Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class RCTDataSchema(BaseModel):
    """Schema for RCT data."""
    id: int = Field(..., description="Participant ID")
    treatment: int = Field(..., ge=0, le=1, description="Treatment indicator (0/1)")
    outcome: float = Field(..., description="Primary outcome")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    baseline_outcome: Optional[float] = Field(None, description="Baseline outcome")

    @validator("outcome")
    def outcome_reasonable(cls, v):
        """Check outcome is in reasonable range."""
        if abs(v) > 1000:
            raise ValueError(f"Outcome seems unreasonable: {v}")
        return v

def validate_schema(df, schema_class):
    """Validate DataFrame against Pydantic schema."""
    errors = []

    for idx, row in df.iterrows():
        try:
            schema_class(**row.to_dict())
        except Exception as e:
            errors.append({
                "row": idx,
                "error": str(e)
            })

    return errors

# Validate
df = pd.read_csv("rct_data.csv")
errors = validate_schema(df, RCTDataSchema)

if errors:
    print(f"Found {len(errors)} validation errors:")
    for err in errors[:5]:  # Show first 5
        print(f"  Row {err['row']}: {err['error']}")
else:
    print("✓ Schema validation passed")
```

### Outlier Detection

```python
def detect_outliers(df, column, method="iqr", threshold=3):
    """Detect outliers in a column."""

    if method == "iqr":
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = (df[column] < lower) | (df[column] > upper)

    elif method == "zscore":
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        outliers = z_scores > threshold

    return {
        "n_outliers": outliers.sum(),
        "pct_outliers": (outliers.sum() / len(df)) * 100,
        "outlier_indices": df[outliers].index.tolist(),
        "outlier_values": df.loc[outliers, column].tolist()
    }

# Check for outliers
result = detect_outliers(df, "outcome", method="iqr")
print(f"Outliers detected: {result['n_outliers']} ({result['pct_outliers']:.1f}%)")
if result["n_outliers"] > 0:
    print(f"Values: {result['outlier_values'][:5]}")  # Show first 5
```

### Consistency Checks

```python
def check_consistency(df):
    """Check for logical consistency issues."""
    issues = []

    # Check 1: Baseline should be before endline
    if "baseline_outcome" in df.columns and "outcome" in df.columns:
        inconsistent = df[df["outcome"] < df["baseline_outcome"]]
        if len(inconsistent) > 0:
            issues.append({
                "check": "baseline_endline_order",
                "n_issues": len(inconsistent),
                "description": "Endline value less than baseline"
            })

    # Check 2: Age should be reasonable
    if "age" in df.columns:
        unreasonable = df[(df["age"] < 0) | (df["age"] > 120)]
        if len(unreasonable) > 0:
            issues.append({
                "check": "age_range",
                "n_issues": len(unreasonable),
                "description": "Age outside reasonable range (0-120)"
            })

    # Check 3: Treatment should be binary
    if "treatment" in df.columns:
        invalid = df[~df["treatment"].isin([0, 1])]
        if len(invalid) > 0:
            issues.append({
                "check": "treatment_binary",
                "n_issues": len(invalid),
                "description": "Treatment not binary (0/1)"
            })

    return issues

# Run consistency checks
issues = check_consistency(df)
if issues:
    print("Consistency issues found:")
    for issue in issues:
        print(f"  {issue['check']}: {issue['n_issues']} rows - {issue['description']}")
else:
    print("✓ All consistency checks passed")
```

## Comprehensive Data Quality Report

```python
def generate_quality_report(df):
    """Generate comprehensive data quality report."""

    print("=" * 70)
    print("DATA QUALITY REPORT")
    print("=" * 70)

    # 1. Basic info
    print("\n1. DATASET OVERVIEW")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Memory: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    # 2. Missing values
    print("\n2. MISSING VALUES")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    for col in df.columns:
        if missing[col] > 0:
            print(f"   {col}: {missing[col]:,} ({missing_pct[col]:.1f}%)")
        else:
            print(f"   {col}: ✓ No missing values")

    # 3. Duplicates
    print("\n3. DUPLICATES")
    n_dupes = df.duplicated().sum()
    if n_dupes > 0:
        print(f"   ⚠ {n_dupes:,} duplicate rows found")
    else:
        print("   ✓ No duplicates")

    # 4. Data types
    print("\n4. DATA TYPES")
    for col, dtype in df.dtypes.items():
        print(f"   {col}: {dtype}")

    # 5. Numeric columns - outliers
    print("\n5. OUTLIER DETECTION (Numeric Columns)")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        outliers = detect_outliers(df, col)
        if outliers["n_outliers"] > 0:
            print(f"   {col}: {outliers['n_outliers']} outliers ({outliers['pct_outliers']:.1f}%)")
        else:
            print(f"   {col}: ✓ No outliers")

    # 6. Consistency checks
    print("\n6. CONSISTENCY CHECKS")
    issues = check_consistency(df)
    if issues:
        for issue in issues:
            print(f"   ⚠ {issue['check']}: {issue['n_issues']} issues")
    else:
        print("   ✓ All checks passed")

    # 7. Summary statistics
    print("\n7. NUMERIC SUMMARY")
    print(df.describe().to_string())

    print("\n" + "=" * 70)

# Generate report
generate_quality_report(df)
```

## Integration with Research Workflow

```text
Extracted Data
    │
    ▼
data-validator
    │
    ├─→ Schema validation
    ├─→ Missing value check
    ├─→ Outlier detection
    ├─→ Consistency checks
    └─→ Generate report
    │
    ▼
Quality Report
    │
    ├─→ If issues: Fix data
    └─→ If clean: Proceed to analysis
    │
    ▼
pyfixest / stata (Analysis)
```

## Best Practices

1. **Validate early** - Check data before analysis
2. **Document issues** - Track all data quality problems
3. **Automate checks** - Run validation in pipeline
4. **Use schemas** - Define expected data structure
5. **Report all findings** - Transparency in data quality

## See Also

- **table-validator** - Validate extracted tables
- **data-transform** - Clean and transform data
- **research-analyst** - Systematic data extraction
