---
name: stat-convert
description: This skill should be used when users need to convert statistical software data files (Stata .dta, SAS .sas7bdat/.xpt, SPSS .sav/.zsav/.por) to CSV or other formats using DuckDB's read_stat extension. Use this skill for data format conversion, preparing statistical datasets for analysis with other tools, or batch converting multiple files.
---

# Statistical Data Format Conversion Skill

This skill provides guidance for converting proprietary statistical software data formats (Stata, SAS, SPSS) to open formats like CSV using DuckDB's `read_stat` community extension. This enables seamless integration with data analysis tools like xan, pandas, R, and other CSV-based workflows.

## About Statistical Data Formats

Statistical software packages use proprietary binary formats that preserve metadata like variable labels, value labels, and data types. While these formats are excellent for their native software, they create barriers for data sharing and analysis with other tools. This skill helps bridge that gap.

### Supported Formats

- **Stata**: `.dta` files (all versions)
- **SAS**: `.sas7bdat` (SAS7BDAT format), `.xpt` (SAS Transport files)
- **SPSS**: `.sav` (SPSS format), `.zsav` (compressed SPSS), `.por` (portable format)

## When to Use This Skill

Use this skill when users:

- Need to convert Stata, SAS, or SPSS files to CSV for analysis
- Want to prepare statistical datasets for use with xan, pandas, or other tools
- Need to batch convert multiple statistical data files
- Want to query statistical data files using SQL without conversion
- Need to handle character encoding issues in statistical datasets
- Want to inspect the contents of proprietary format files
- Need to integrate statistical software data into data pipelines
- Want to share data in open, accessible formats

## Prerequisites

### Installing DuckDB CLI

DuckDB must be installed on your system. See the duckdb skill (`@.claude/skills/duckdb/SKILL.md`) for installation instructions.

Quick install options:

```bash
# Homebrew (macOS/Linux)
brew install duckdb

# Chocolatey (Windows)
choco install duckdb

# Scoop (Windows)
scoop install duckdb
```

### Installing the read_stat Extension

The `read_stat` extension must be installed once per DuckDB installation:

```bash
# Install from community repository
duckdb -c "INSTALL read_stat FROM community"
```

Or using the project Justfile:

```bash
just install-readstat
```

This only needs to be run once. The extension persists across DuckDB sessions.

## Basic Usage

### Simple Conversion with Justfile

The project includes Just recipes for common conversion tasks:

**Convert any statistical format to CSV:**

```bash
just convert input.dta output.csv
just convert data.sas7bdat data.csv
just convert survey.sav survey.csv
```

**Quick conversion (uses replacement scan):**

```bash
just convert-csv input.dta output.csv
```

**Preview data before converting:**

```bash
just preview-csv input.dta
```

### Direct DuckDB Commands

**Basic conversion pattern:**

```bash
duckdb -c "LOAD read_stat; COPY (FROM read_stat('input.dta')) TO 'output.csv'"
```

**Using replacement scan (automatic format detection):**

```bash
# After extension is installed, DuckDB automatically recognizes file types
duckdb -c "COPY (FROM 'input.dta') TO 'output.csv'"
```

**Convert to other formats:**

```bash
# Convert to Parquet
duckdb -c "COPY (FROM 'data.dta') TO 'data.parquet' (FORMAT PARQUET)"

# Convert to JSON
duckdb -c "COPY (FROM 'data.dta') TO 'data.json'"
```

## Advanced Usage

### Preview Before Converting

Always preview data to understand structure before full conversion:

```bash
# Preview first 10 rows in table format
duckdb -c "LOAD read_stat; FROM read_stat('data.dta') LIMIT 10"

# Preview in markdown format
duckdb -c "FROM 'data.dta' LIMIT 10" -markdown

# Preview with specific columns
duckdb -c "SELECT name, age, income FROM 'data.dta' LIMIT 20"

# Count total rows
duckdb -c "SELECT COUNT(*) FROM 'data.dta'"

# Show column information
duckdb -c "DESCRIBE SELECT * FROM 'data.dta'"
```

### Handling Character Encoding

Statistical software files often contain non-UTF-8 encoded text (especially older files or files from non-English regions):

```bash
# Specify encoding explicitly
duckdb -c "LOAD read_stat;
  COPY (FROM read_stat('data.dta', encoding='iso-8859-1'))
  TO 'output.csv'"

# Common encodings
# - 'utf-8' (default)
# - 'iso-8859-1' (Latin-1, Western European)
# - 'windows-1252' (Windows Western European)
# - 'iso-8859-2' (Latin-2, Central European)
# - 'shift-jis' (Japanese)
# - 'gbk' (Chinese)
```

### Format Override

For files with non-standard extensions or when you need explicit format control:

```bash
# Explicitly specify format
duckdb -c "LOAD read_stat;
  COPY (FROM read_stat('renamed_file.dat', format='dta'))
  TO 'output.csv'"

# Available format values:
# - 'dta' (Stata)
# - 'sas7bdat' (SAS)
# - 'xpt' (SAS Transport)
# - 'sav' (SPSS)
# - 'zsav' (compressed SPSS)
# - 'por' (SPSS portable)
```

### Filtering and Transforming During Conversion

Use SQL to filter, transform, or select specific data during conversion:

```bash
# Select specific columns
duckdb -c "COPY (
  SELECT respondent_id, age, income, survey_date
  FROM 'survey.dta'
) TO 'selected_vars.csv'"

# Filter rows
duckdb -c "COPY (
  SELECT * FROM 'data.dta'
  WHERE age >= 18 AND income > 0
) TO 'filtered.csv'"

# Create derived variables
duckdb -c "COPY (
  SELECT
    *,
    income / 12 AS monthly_income,
    CASE
      WHEN age < 18 THEN 'Minor'
      WHEN age < 65 THEN 'Adult'
      ELSE 'Senior'
    END AS age_group
  FROM 'data.dta'
) TO 'enhanced.csv'"

# Aggregate data
duckdb -c "COPY (
  SELECT
    region,
    COUNT(*) AS n_respondents,
    AVG(income) AS avg_income,
    MEDIAN(age) AS median_age
  FROM 'survey.dta'
  GROUP BY region
) TO 'regional_summary.csv'"
```

### Batch Conversion

Convert multiple files efficiently:

**Using shell loops (Bash/Linux/macOS):**

```bash
# Convert all Stata files in directory
for file in *.dta; do
  output="${file%.dta}.csv"
  duckdb -c "COPY (FROM '$file') TO '$output'"
  echo "Converted: $file -> $output"
done

# Convert all SAS files
for file in *.sas7bdat; do
  output="${file%.sas7bdat}.csv"
  duckdb -c "COPY (FROM '$file') TO '$output'"
  echo "Converted: $file -> $output"
done

# Convert files matching pattern in subdirectories
find . -name "*.dta" -type f | while read file; do
  output="${file%.dta}.csv"
  duckdb -c "COPY (FROM '$file') TO '$output'"
  echo "Converted: $file -> $output"
done
```

**Using PowerShell (Windows):**

```powershell
# Convert all Stata files
Get-ChildItem -Filter *.dta | ForEach-Object {
  $output = $_.BaseName + ".csv"
  duckdb -c "COPY (FROM '$($_.Name)') TO '$output'"
  Write-Host "Converted: $($_.Name) -> $output"
}

# Convert with progress
$files = Get-ChildItem -Filter *.dta
$total = $files.Count
$current = 0

foreach ($file in $files) {
  $current++
  $output = $file.BaseName + ".csv"
  Write-Progress -Activity "Converting files" -Status "$current of $total" -PercentComplete ($current/$total*100)
  duckdb -c "COPY (FROM '$($file.Name)') TO '$output'"
}
```

### Combining Multiple Files

Merge multiple statistical datasets during conversion:

```bash
# Union multiple files (same structure)
duckdb -c "COPY (
  SELECT * FROM 'wave1.dta'
  UNION ALL
  SELECT * FROM 'wave2.dta'
  UNION ALL
  SELECT * FROM 'wave3.dta'
) TO 'combined_waves.csv'"

# Join files from different sources
duckdb -c "COPY (
  SELECT
    s.*,
    d.demographic_info
  FROM 'survey_responses.dta' s
  LEFT JOIN 'demographics.sas7bdat' d
    ON s.respondent_id = d.id
) TO 'merged_data.csv'"
```

## Integration with Analysis Tools

### Piping to xan

After conversion, use xan for further processing:

```bash
# Convert and immediately analyze with xan
duckdb -c "COPY (FROM 'data.dta') TO 'temp.csv'"
xan stats temp.csv
xan frequency -s category temp.csv

# Or use xan directly on converted file
just convert data.dta data.csv
xan view data.csv
xan filter 'age > 25' data.csv | xan select name,age,income
```

See the xan skill (`@.claude/skills/xan/SKILL.md`) for extensive CSV processing capabilities.

### Using with Python/Pandas

```python
import duckdb

# Direct query (no intermediate CSV)
con = duckdb.connect()
con.execute("INSTALL read_stat FROM community")
con.execute("LOAD read_stat")
df = con.execute("SELECT * FROM 'data.dta'").df()

# Now use pandas for analysis
df.describe()
df.groupby('category').mean()
```

### Using with R

```r
library(DBI)

# Connect and query
con <- dbConnect(duckdb::duckdb())
dbExecute(con, "INSTALL read_stat FROM community")
dbExecute(con, "LOAD read_stat")
data <- dbGetQuery(con, "SELECT * FROM 'data.dta'")

# Use R for analysis
summary(data)
```

## Data Quality Checks

Always verify conversion results:

```bash
# Compare row counts
echo "Original rows:"
duckdb -c "SELECT COUNT(*) FROM 'original.dta'"
echo "Converted rows:"
duckdb -c "SELECT COUNT(*) FROM 'converted.csv'"

# Check for missing values
duckdb -c "
  SELECT
    COUNT(*) AS total_rows,
    COUNT(var1) AS var1_present,
    COUNT(*) - COUNT(var1) AS var1_missing,
    COUNT(var2) AS var2_present,
    COUNT(*) - COUNT(var2) AS var2_missing
  FROM 'data.dta'
"

# Preview both formats
echo "Original (Stata):"
duckdb -c "FROM 'data.dta' LIMIT 5"
echo "Converted (CSV):"
duckdb -c "FROM 'data.csv' LIMIT 5"

# Compare value distributions
duckdb -c "
  SELECT 'Original' AS source, category, COUNT(*) AS n
  FROM 'data.dta'
  GROUP BY category
  UNION ALL
  SELECT 'Converted' AS source, category, COUNT(*) AS n
  FROM 'data.csv'
  GROUP BY category
  ORDER BY source, category
"
```

## Common Workflows

### Workflow 1: Convert for Analysis

```bash
# 1. Preview the data
just preview-csv survey.dta

# 2. Convert to CSV
just convert survey.dta survey.csv

# 3. Analyze with xan
xan stats survey.csv
xan frequency -s region survey.csv
xan hist -s age survey.csv
```

### Workflow 2: Clean and Convert

```bash
# Filter, clean, and convert in one step
duckdb -c "COPY (
  SELECT
    respondent_id,
    TRIM(LOWER(email)) AS email,
    age,
    COALESCE(income, 0) AS income,
    region
  FROM 'raw_survey.dta'
  WHERE age >= 18
    AND email IS NOT NULL
    AND income >= 0
) TO 'clean_survey.csv'"
```

### Workflow 3: Multi-Format Pipeline

```bash
# Convert various formats and combine
duckdb -c "COPY (
  SELECT *, 'stata' AS source FROM 'data1.dta'
  UNION ALL
  SELECT *, 'sas' AS source FROM 'data2.sas7bdat'
  UNION ALL
  SELECT *, 'spss' AS source FROM 'data3.sav'
) TO 'combined_analysis.csv'"
```

### Workflow 4: Batch Convert Project Data

```bash
# Create output directory
mkdir -p converted

# Convert all statistical files
for file in data/*.dta; do
  basename=$(basename "$file" .dta)
  duckdb -c "COPY (FROM '$file') TO 'converted/${basename}.csv'"
done

for file in data/*.sas7bdat; do
  basename=$(basename "$file" .sas7bdat)
  duckdb -c "COPY (FROM '$file') TO 'converted/${basename}.csv'"
done

# Generate conversion report
echo "Conversion Report" > report.txt
echo "=================" >> report.txt
for csv in converted/*.csv; do
  rows=$(duckdb -c "SELECT COUNT(*) FROM '$csv'" -noheader)
  echo "$(basename $csv): $rows rows" >> report.txt
done
```

## Troubleshooting

### Extension Not Loaded

**Problem:** Error about `read_stat` function not found

**Solution:**

```bash
# Ensure extension is installed
duckdb -c "INSTALL read_stat FROM community"

# Then load it in your query
duckdb -c "LOAD read_stat; FROM read_stat('data.dta')"
```

Or use replacement scan (automatic loading):

```bash
duckdb -c "FROM 'data.dta'"  # Extension loads automatically
```

### Character Encoding Issues

**Problem:** Garbled text, special characters appear as question marks or boxes

**Solution:** Specify the correct encoding:

```bash
# Try common encodings
duckdb -c "LOAD read_stat;
  FROM read_stat('data.dta', encoding='iso-8859-1') LIMIT 5"

# For Latin American data
duckdb -c "LOAD read_stat;
  FROM read_stat('data.dta', encoding='iso-8859-1')"

# For Eastern European data
duckdb -c "LOAD read_stat;
  FROM read_stat('data.dta', encoding='iso-8859-2')"
```

### File Not Found Errors

**Problem:** Cannot find the input file

**Solution:**

- Use absolute paths: `"/full/path/to/data.dta"`
- Check current working directory
- Verify file extension matches actual format
- Use quotes around paths with spaces: `"'data file.dta'"`

### Memory Issues with Large Files

**Problem:** Out of memory errors with very large datasets

**Solution:**

```bash
# Convert in chunks with filtering
duckdb -c "COPY (
  SELECT * FROM 'huge_file.dta'
  WHERE year = 2023
) TO 'filtered_2023.csv'"

# Or convert to Parquet (more memory efficient)
duckdb -c "COPY (FROM 'huge_file.dta')
  TO 'data.parquet' (FORMAT PARQUET)"
```

### Unsupported File Version

**Problem:** Error about unsupported file version

**Solution:**

- Ensure DuckDB and read_stat extension are up to date
- Try opening the file in native software and re-saving in a compatible version
- Check if file is corrupted

## Best Practices

1. **Always preview first**: Use `just preview-csv` or `LIMIT` queries before full conversion
2. **Verify row counts**: Compare original and converted files to ensure no data loss
3. **Check encodings**: For non-English text, test different encodings on a sample
4. **Use appropriate output formats**:
   - CSV for human-readable, xan-compatible files
   - Parquet for large datasets and long-term storage
   - JSON for nested or hierarchical data
5. **Preserve original files**: Never overwrite source statistical data files
6. **Document conversions**: Keep notes on encoding used, filters applied, and transformations
7. **Test SQL transformations**: Preview results with `LIMIT` before full conversion
8. **Organize output**: Use consistent naming conventions and directory structures
9. **Leverage DuckDB's SQL**: Filter and transform during conversion rather than post-processing
10. **Combine with xan**: Use xan for follow-up CSV analysis after conversion

## Performance Tips

1. **Use Parquet for large files**: More efficient storage and faster querying
2. **Filter early**: Apply WHERE clauses during conversion to reduce output size
3. **Select only needed columns**: Reduces I/O and conversion time
4. **Batch conversions in parallel**: Use background jobs for multiple independent files
5. **Use replacement scan**: Simpler syntax and automatic format detection

## Project Integration

This skill is designed to work seamlessly with:

- **DuckDB Skill** (`@.claude/skills/duckdb/SKILL.md`): For SQL-based analysis of converted data
- **Xan Skill** (`@.claude/skills/xan/SKILL.md`): For command-line CSV processing and analysis
- **Justfile**: Pre-configured recipes for common conversion tasks

### Example Integrated Workflow

```bash
# 1. Convert Stata file to CSV
just convert survey_data.dta survey_data.csv

# 2. Quick statistics with xan
xan stats survey_data.csv

# 3. Detailed SQL analysis with DuckDB
duckdb -c "
  SELECT
    region,
    COUNT(*) AS respondents,
    AVG(age) AS avg_age,
    MEDIAN(income) AS median_income
  FROM 'survey_data.csv'
  GROUP BY region
  ORDER BY median_income DESC
"

# 4. Advanced filtering and visualization with xan
xan filter 'region == \"North\"' survey_data.csv \
  | xan hist -s age
```

## Quick Reference

```bash
# Installation (one-time)
duckdb -c "INSTALL read_stat FROM community"
just install-readstat

# Basic conversion
just convert input.dta output.csv
duckdb -c "COPY (FROM 'input.dta') TO 'output.csv'"

# Preview data
just preview-csv input.dta
duckdb -c "FROM 'input.dta' LIMIT 10"

# With encoding
duckdb -c "LOAD read_stat;
  COPY (FROM read_stat('data.dta', encoding='iso-8859-1'))
  TO 'output.csv'"

# Convert to Parquet
duckdb -c "COPY (FROM 'input.dta') TO 'output.parquet' (FORMAT PARQUET)"

# Filter during conversion
duckdb -c "COPY (
  SELECT * FROM 'input.dta' WHERE year >= 2020
) TO 'recent_data.csv'"

# Batch convert all .dta files
for f in *.dta; do
  just convert "$f" "${f%.dta}.csv"
done

# Check row counts
duckdb -c "SELECT COUNT(*) FROM 'data.dta'"
duckdb -c "SELECT COUNT(*) FROM 'data.csv'"
```

## Resources

- [DuckDB read_stat Extension](https://duckdb.org/community_extensions/extensions/read_stat)
- [DuckDB CLI Documentation](https://duckdb.org/docs/clients/cli/overview)
- [ReadStat Library](https://github.com/WizardMac/ReadStat) (underlying C library)
- Project DuckDB Skill: `@.claude/skills/duckdb/SKILL.md`
- Project Xan Skill: `@.claude/skills/xan/SKILL.md`
