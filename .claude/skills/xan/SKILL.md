---
name: xan
description: This skill should be used when users need to process, analyze, transform, or visualize CSV files using the xan command-line tool. Use this skill for tasks involving CSV data manipulation, filtering, aggregation, joining, format conversion, or statistical analysis at the command line.
---

# Xan CSV Processing Skill

This skill provides expertise in using xan, a high-performance Rust-based command-line tool for processing CSV files at scale.

## About Xan

Xan is designed to handle large CSV files (Gigabytes) efficiently using minimal memory. It leverages SIMD technology for rapid parsing and supports multithreading for parallel computation. Beyond standard CSV files, xan can handle CSV-adjacent formats from various disciplines including web archival (`.cdx`) and bioinformatics (`.vcf`, `.gtf`, `.sam`, `.bed`).

### Key Capabilities

- **Data Exploration**: Preview, view, and inspect CSV files
- **Data Transformation**: Filter, map, select, sort, and deduplicate
- **Data Analysis**: Compute statistics, frequencies, histograms, and correlations
- **Data Visualization**: Terminal-based plots, histograms, heatmaps, and scatterplots
- **Data Combination**: Join, merge, and concatenate multiple CSV files
- **Format Conversion**: Convert between CSV, JSON, Excel, NumPy, and other formats
- **Expression Language**: Built-in language for complex transformations

## When to Use This Skill

Use this skill when users:

- Need to process CSV files from the command line
- Want to filter, transform, or analyze CSV data
- Need to join or combine multiple CSV files
- Want to visualize CSV data in the terminal
- Need to convert CSV to/from other formats (JSON, Excel, etc.)
- Ask about CSV statistics, frequencies, or aggregations
- Need to handle large CSV files efficiently
- Work with bioinformatics or web archival CSV-like formats

## How to Use This Skill

### Basic Xan Workflow

Xan commands follow a pipeline pattern where data flows through multiple operations:

```bash
xan [command] [options] input.csv | xan [next_command]
```

### Common Operations

#### Data Exploration

Preview a CSV file:

```bash
xan view data.csv
xan headers data.csv  # Show column names with indices
xan count data.csv    # Count rows
xan flatten data.csv  # Show flattened row display
```

#### Filtering and Selection

Select specific columns:

```bash
xan select column1,column3 data.csv
xan drop column2 data.csv  # Remove specific columns
```

Filter rows based on conditions:

```bash
xan filter 'age > 25' data.csv
xan search 'pattern' data.csv
xan head -n 100 data.csv    # First 100 rows
xan tail -n 50 data.csv     # Last 50 rows
xan slice --start 10 --end 20 data.csv
```

#### Transformation

Create new columns with expressions:

```bash
xan map 'price * quantity as total' data.csv
xan transform 'upper(name)' -c name data.csv
xan enum data.csv  # Add sequential index column
```

Sort and deduplicate:

```bash
xan sort -s column data.csv
xan dedup data.csv
xan shuffle data.csv  # Randomize order
```

#### Analysis and Statistics

Compute statistics:

```bash
xan stats data.csv
xan stats -s column data.csv
xan frequency -s category data.csv
xan hist -s column data.csv  # Show histogram
```

Aggregations:

```bash
xan groupby category data.csv
xan agg 'sum(sales) as total_sales' data.csv
xan bins -s age --bins 10 data.csv
```

#### Combining Files

Join files:

```bash
xan join column file1.csv column file2.csv
xan cat rows file1.csv file2.csv  # Concatenate by rows
xan cat cols file1.csv file2.csv  # Concatenate by columns
```

#### Visualization

Create terminal visualizations:

```bash
xan hist -s column data.csv
xan plot -x column1 -y column2 data.csv
xan heatmap matrix.csv
```

#### Format Conversion

Convert to other formats:

```bash
xan to json data.csv
xan to xlsx data.csv
xan from json data.json
```

#### Working with Special Formats

Xan automatically detects formats like:

- `.tsv` (tab-separated)
- `.psv` (pipe-separated)
- `.vcf`, `.gtf`, `.sam`, `.bed` (bioinformatics)
- `.cdx` (web archival)

For compressed files:

```bash
xan view data.csv.gz  # Automatically handles gzip
xan view data.csv.zst # Automatically handles Zstandard
```

### Expression Language

Xan includes a powerful expression language for transformations. Access the cheatsheet and function documentation:

Reference `references/xan-expressions.md` for detailed expression syntax, operators, and built-in functions.

Common expression patterns:

- String operations: `upper(name)`, `lower(text)`, `concat(first, " ", last)`
- Math operations: `price * quantity`, `round(value, 2)`
- Conditional logic: `if(age > 18, "adult", "minor")`
- Aggregations: `sum(column)`, `mean(column)`, `count(column)`
- Date handling: Date parsing and formatting functions

### Advanced Features

#### Parallel Processing

For map-reduce style operations on large files:

```bash
xan parallel [options] data.csv
```

#### Custom Delimiters

Process files with custom separators:

```bash
xan -d ';' view data.csv  # Semicolon-separated
xan fmt -t '|' data.csv   # Output as pipe-separated
```

#### Headless CSV

Work with files without headers:

```bash
xan -n count data.csv
```

#### Pipeline Input

Read from stdin:

```bash
cat data.csv | xan filter 'age > 25' | xan select name,age
```

### Best Practices

1. **Start with exploration**: Use `xan view` and `xan headers` to understand the data structure
2. **Chain operations**: Combine multiple xan commands in pipelines for complex workflows
3. **Test expressions**: Use `xan eval` to test single expressions before incorporating them
4. **Use appropriate output modes**: Redirect output with `-o` flag when saving results
5. **Leverage compression**: Xan handles `.gz` and `.zst` files transparently
6. **Check performance**: For very large files, consider using `xan parallel` for distributed processing

## Reference Documentation

For detailed command documentation and expression language syntax, refer to:

- `references/xan-commands.md` - Complete command reference with all options
- `references/xan-expressions.md` - Expression language syntax and functions
- `references/xan-examples.md` - Practical examples and real-world workflows

## Installation

Xan can be installed via:

- **Cargo**: `cargo install xan --locked`
- **Homebrew** (macOS): `brew install xan`
- **Scoop** (Windows): `scoop bucket add extras && scoop install xan`
- **Arch Linux**: `sudo pacman -S xan`
- **NetBSD**: `pkgin install xan`
- **Nix**: `nix-shell -p xan`
- **Pixi**: `pixi global install xan`

Pre-built binaries are available for multiple platforms on the GitHub releases page.
