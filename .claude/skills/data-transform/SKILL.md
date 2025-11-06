---
name: data-transform
description: Transform, analyze, and harmonize research data using xan (CSV), duckdb (SQL), or polars (Python). Automatically routes to the best tool based on task complexity. Use for data cleaning, merging studies, statistical file conversion, and preparing data for analysis.
---

# Data Transformation for Research

Unified skill for transforming, cleaning, and harmonizing research data. This skill intelligently routes between three complementary tools based on your specific needs.

## When to Use This Skill

Use this skill when you need to:

- Clean and transform extracted research data
- Merge and harmonize data across multiple studies
- Convert between data formats (CSV, Parquet, Stata, SPSS, SAS)
- Filter, aggregate, and reshape datasets
- Join datasets from different sources
- Validate and quality-check research data
- Prepare data for econometric analysis
- Perform exploratory data analysis

## Tool Selection - Decision Tree

```text
What kind of task?
        │
        ├─→ Quick CLI exploration, single CSV
        │   → Use XAN
        │   Examples:
        │   - Preview first 100 rows
        │   - Get column statistics
        │   - Filter rows by condition
        │   - Create histogram
        │
        ├─→ SQL queries, joins, format conversion
        │   → Use DuckDB
        │   Examples:
        │   - Join multiple datasets
        │   - Complex aggregations
        │   - Convert .dta to .parquet
        │   - Window functions
        │
        └─→ Python pipeline, large data, integration with analysis
            → Use polars (via pyfixest)
            Examples:
            - Multi-step transformation pipeline
            - Integration with statistical analysis
            - Memory-efficient large file processing
            - Complex data validation
```

## Quick Start

### xan (Command-Line CSV Swiss Army Knife)

**Best for:** Quick exploration, filtering, basic transformations

```bash
# Preview data
xan view data.csv

# Get statistics
xan stats data.csv

# Filter rows
xan filter 'age > 25' data.csv > filtered.csv

# Select specific columns
xan select name,age,outcome data.csv

# Create frequency table
xan frequency -s treatment_group data.csv
```

### DuckDB (SQL for Data Analysis)

**Best for:** SQL queries, joins, format conversion

```bash
# Query CSV file
duckdb -c "SELECT treatment, AVG(outcome) FROM 'data.csv' GROUP BY treatment"

# Join datasets
duckdb -c "SELECT * FROM 'study1.csv' a JOIN 'study2.csv' b ON a.id = b.id"

# Convert formats
duckdb -c "COPY (FROM 'data.dta') TO 'data.parquet'"

# Complex aggregation
duckdb -c "
    SELECT
        treatment_group,
        COUNT(*) as n,
        AVG(outcome) as mean_outcome,
        STDDEV(outcome) as sd_outcome
    FROM 'rct_data.csv'
    GROUP BY treatment_group
"
```

### polars (Python DataFrame Processing)

**Best for:** Python pipelines, integration with analysis

```python
import polars as pl

# Read and transform data
df = (
    pl.read_csv("data.csv")
    .filter(pl.col("age") > 25)
    .with_columns([
        (pl.col("price") * pl.col("quantity")).alias("total")
    ])
    .group_by("treatment")
    .agg([
        pl.len().alias("n"),
        pl.mean("outcome").alias("mean_outcome")
    ])
)

# Write to parquet
df.write_parquet("processed.parquet")
```

## Common Research Workflows

### Workflow 1: Harmonize Variables Across Studies

**Scenario:** You have datasets from 5 different RCTs with different variable names for the same concepts.

**Tool:** DuckDB (SQL best for consistent renaming/joining)

```bash
# Create harmonized dataset
duckdb -c "
CREATE TABLE harmonized AS
SELECT
    'study1' as study_id,
    participant_id as id,
    treatment_arm as treatment,
    primary_outcome as outcome,
    baseline_age as age
FROM 'study1.csv'

UNION ALL

SELECT
    'study2' as study_id,
    subject_id as id,
    group as treatment,
    endpoint_value as outcome,
    age_baseline as age
FROM 'study2.csv'

UNION ALL

SELECT
    'study3' as study_id,
    id as id,
    arm as treatment,
    y as outcome,
    age as age
FROM 'study3.csv';

COPY harmonized TO 'harmonized_data.csv' (HEADER, DELIMITER ',');
"
```

### Workflow 2: Quick Data Quality Check

**Scenario:** Just extracted tables from a paper, want to quickly check data quality.

**Tool:** xan (fast CLI exploration)

```bash
# Check basic stats
xan stats extracted_table.csv

# Check for missing values
xan frequency -s outcome extracted_table.csv

# Get row count by treatment group
xan frequency -s treatment extracted_table.csv

# Visualize distribution
xan hist -s outcome extracted_table.csv

# Check for duplicates
xan count extracted_table.csv
xan dedup extracted_table.csv | xan count
```

### Workflow 3: Convert Statistical Files

**Scenario:** Have .dta, .sas7bdat files that need to be CSV/Parquet for analysis.

**Tool:** DuckDB with read_stat extension

```bash
# Convert Stata to CSV
duckdb -c "LOAD read_stat; COPY (FROM read_stat('data.dta')) TO 'data.csv'"

# Convert to Parquet (faster, smaller)
duckdb -c "LOAD read_stat; COPY (FROM read_stat('data.dta')) TO 'data.parquet'"

# Preview before converting
duckdb -c "LOAD read_stat; FROM read_stat('data.dta') LIMIT 10" -markdown

# Or use the stat-convert skill
just convert input.dta output.csv
```

### Workflow 4: Merge Treatment Effects from Multiple Papers

**Scenario:** Extracted regression coefficients from 10 papers, need to prepare for meta-analysis.

**Tool:** DuckDB (SQL for joining and aggregating)

```bash
# Combine all extracted coefficients
duckdb -c "
SELECT
    source_file,
    model_number,
    variable,
    coefficient,
    std_error,
    CASE
        WHEN significance = '***' THEN 0.001
        WHEN significance = '**' THEN 0.01
        WHEN significance = '*' THEN 0.05
        ELSE 0.10
    END as p_value
FROM 'paper1_regression_*.csv'
WHERE variable IN ('treatment', 'treatment_effect', 'intervention')
" > meta_analysis_data.csv
```

### Workflow 5: Complex Multi-Step Pipeline

**Scenario:** Need to clean, transform, and validate data before analysis.

**Tool:** polars (Python for complex pipelines)

```python
import polars as pl

# Multi-step data pipeline
def prepare_for_analysis(file_path):
    df = (
        pl.read_csv(file_path)
        # Remove rows with missing outcome
        .filter(pl.col("outcome").is_not_null())
        # Create age categories
        .with_columns([
            pl.when(pl.col("age") < 30)
              .then(pl.lit("young"))
              .when(pl.col("age") < 50)
              .then(pl.lit("middle"))
              .otherwise(pl.lit("old"))
              .alias("age_group")
        ])
        # Standardize treatment variable
        .with_columns([
            pl.col("treatment").cast(pl.Int32),
        ])
        # Calculate additional variables
        .with_columns([
            (pl.col("outcome") - pl.col("outcome").mean()).alias("outcome_centered"),
            (pl.col("outcome") / pl.col("outcome").std()).alias("outcome_standardized")
        ])
        # Remove outliers (3 SD from mean)
        .filter(
            (pl.col("outcome") > pl.col("outcome").mean() - 3 * pl.col("outcome").std()) &
            (pl.col("outcome") < pl.col("outcome").mean() + 3 * pl.col("outcome").std())
        )
    )

    # Validation checks
    assert df.height > 0, "No data remaining after filtering"
    assert df["treatment"].n_unique() >= 2, "Need at least 2 treatment groups"

    return df

# Process multiple files
processed_data = []
for paper in ["study1.csv", "study2.csv", "study3.csv"]:
    df = prepare_for_analysis(paper)
    df = df.with_columns(pl.lit(paper).alias("source"))
    processed_data.append(df)

# Combine
final_df = pl.concat(processed_data)
final_df.write_parquet("ready_for_analysis.parquet")
```

## Tool Comparison

| Task | xan | DuckDB | polars |
|------|-----|--------|--------|
| **Speed (small files)** | ⚡⚡⚡ Instant | ⚡⚡ Fast | ⚡⚡ Fast |
| **Speed (large files)** | ⚡⚡⚡ Fast | ⚡⚡⚡ Fast | ⚡⚡⚡ Fastest |
| **Learning curve** | ⭐ Easy | ⭐⭐ SQL knowledge | ⭐⭐ Python knowledge |
| **Quick exploration** | ⭐⭐⭐ Best | ⭐⭐ Good | ⭐ OK |
| **Complex queries** | ⭐ Limited | ⭐⭐⭐ Excellent | ⭐⭐⭐ Excellent |
| **Joins** | ⭐⭐ Basic | ⭐⭐⭐ Full SQL | ⭐⭐⭐ Full support |
| **Format conversion** | ⭐⭐ JSON/CSV | ⭐⭐⭐ All formats | ⭐⭐⭐ All formats |
| **Statistical files** | ✗ | ⭐⭐⭐ Via read_stat | ⭐⭐ Limited |
| **Visualization** | ⭐⭐⭐ Terminal plots | ✗ | ⭐⭐ Via matplotlib |
| **Scripting** | ⭐⭐ Bash | ⭐⭐⭐ SQL scripts | ⭐⭐⭐ Python |

## Format Conversion Quick Reference

### Convert from Stata/SPSS/SAS

```bash
# DuckDB (recommended)
duckdb -c "LOAD read_stat; COPY (FROM read_stat('data.dta')) TO 'data.csv'"
duckdb -c "LOAD read_stat; COPY (FROM read_stat('data.sas7bdat')) TO 'data.parquet'"

# Or use Justfile helper
just convert input.dta output.csv
just preview-csv input.dta
```

### Convert CSV to Parquet

```bash
# DuckDB (fastest)
duckdb -c "COPY (FROM 'data.csv') TO 'data.parquet'"

# xan (includes compression)
xan to npy data.csv  # NumPy format
```

### Convert JSON to CSV

```bash
# xan
xan from json data.json > data.csv

# DuckDB
duckdb -c "COPY (FROM 'data.json') TO 'data.csv'"
```

## Integration with Research Workflow

```text
Extracted Tables (PDF → parse.py)
        │
        ▼
CSV/JSON structured data
        │
        ▼
data-transform skill
        │
        ├─→ xan: Quick validation
        │   - Check row counts
        │   - View statistics
        │   - Identify issues
        │
        ├─→ DuckDB: Format conversion
        │   - Convert .dta to .parquet
        │   - Harmonize variables
        │   - Join datasets
        │
        └─→ polars: Complex cleaning
            - Multi-step pipeline
            - Remove outliers
            - Create derived variables
        │
        ▼
Clean, harmonized data
        │
        ▼
pyfixest / stata (Analysis)
        │
        ▼
quarto (Reports)
```

## Best Practices

### 1. Start with xan for exploration

```bash
# Always start by looking at your data
xan headers data.csv
xan stats data.csv
xan view data.csv | head -20
```

### 2. Use DuckDB for SQL-heavy tasks

```bash
# Joins, aggregations, format conversion
duckdb -c "
    SELECT study, AVG(effect_size) as mean_effect
    FROM 'meta_data.csv'
    GROUP BY study
"
```

### 3. Use polars for complex pipelines

```python
# Multi-step transformations with validation
df = (
    pl.read_csv("raw.csv")
    .pipe(clean_missing_values)
    .pipe(remove_outliers)
    .pipe(harmonize_variables)
    .pipe(validate_schema)
)
```

### 4. Combine tools in workflows

```bash
# xan for quick filter, DuckDB for complex query
xan filter 'year == 2020' studies.csv | \
  duckdb -c "SELECT treatment, AVG(outcome) FROM read_csv_auto('/dev/stdin') GROUP BY treatment"
```

## Common Patterns

### Pattern 1: Preview → Transform → Save

```bash
# xan pipeline
xan view data.csv | head  # Preview
xan filter 'age > 18' data.csv | \
  xan select id,treatment,outcome | \
  xan sort -s id > clean_data.csv
```

### Pattern 2: SQL Analysis

```bash
# DuckDB for statistical summaries
duckdb -c "
    SELECT
        treatment,
        COUNT(*) as n,
        AVG(outcome) as mean,
        STDDEV(outcome) as sd,
        MIN(outcome) as min,
        MAX(outcome) as max
    FROM 'data.csv'
    GROUP BY treatment
" -markdown
```

### Pattern 3: Python Data Validation

```python
import polars as pl

def validate_rct_data(df: pl.DataFrame) -> pl.DataFrame:
    """Validate RCT data structure and content."""

    # Required columns
    required = ["id", "treatment", "outcome"]
    assert all(col in df.columns for col in required)

    # No missing in key variables
    assert df["id"].null_count() == 0
    assert df["treatment"].null_count() == 0

    # Treatment is binary or categorical
    assert df["treatment"].n_unique() >= 2

    # Outcome is numeric
    assert df["outcome"].dtype in [pl.Float64, pl.Int64]

    return df

# Use in pipeline
df = pl.read_csv("study_data.csv").pipe(validate_rct_data)
```

## Troubleshooting

### Large File Performance

```bash
# xan handles large files well (streaming)
xan stats large_file.csv

# DuckDB can handle files larger than RAM
duckdb -c "SELECT * FROM 'huge_file.csv' LIMIT 10"

# polars - use lazy evaluation
df = pl.scan_csv("large_file.csv").filter(...).collect()
```

### Memory Issues

```bash
# DuckDB streaming
duckdb -c "COPY (SELECT * FROM 'input.csv' WHERE condition) TO 'output.csv'"

# polars lazy mode
df = pl.scan_csv("file.csv").filter(...).write_parquet("output.parquet")
```

### Encoding Issues

```bash
# xan auto-detects encoding
xan view data.csv

# DuckDB specify encoding
duckdb -c "COPY (FROM read_csv('data.csv', encoding='latin1')) TO 'output.csv'"
```

## Reference

For detailed documentation:

- `references/xan_details.md` - Complete xan reference
- `references/duckdb_details.md` - Complete DuckDB reference
- `references/polars_guide.md` - polars usage guide

## See Also

- **stat-convert** skill - Specialized Stata/SAS/SPSS conversion
- **pyfixest** skill - Uses polars for econometric analysis
- **research-analyst** skill - Structured data extraction
