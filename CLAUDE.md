# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**enlace** is a research tool for parsing academic papers in development economics and extracting structured data for meta-analysis and data harmonization. The project focuses on automating extraction of study characteristics, outcome measures, and statistical results from research papers (PDF/DOCX), and linking them to microdata sources.

## Development Setup

This project uses:

- **uv** for Python installation and virtual environment management
- **just** for task automation
- **DuckDB** for data processing with the `read_stat` extension for Stata/SAS/SPSS files
- **pre-commit** for code quality enforcement

### Initial Setup

```bash
# Install required software and create virtual environment
just get-started

# Or manually:
just venv  # Create venv, install dependencies, setup pre-commit
just install-readstat  # Install DuckDB read_stat extension (run once)
```

### Activate Virtual Environment

```bash
# Bash
.venv/Scripts/activate

# Powershell
.venv/Scripts/activate.ps1

# Nushell
overlay use .venv/Scripts/activate.nu
```

## Common Development Commands

### Code Quality

```bash
# Lint Python code
just lint-py

# Format Python code
just fmt-python

# Format a single Python file
just fmt-py <file>

# Format markdown files
just fmt-markdown

# Format single markdown file
just fmt-md <file>

# Format everything
just fmt-all

# Run pre-commit hooks
just pre-commit-run
```

### Data Conversion (DuckDB)

```bash
# Convert Stata/SAS/SPSS file to CSV
just convert input.dta output.csv

# Preview first 10 rows of a data file
just preview-csv input.dta
```

### Jupyter

```bash
# Launch Jupyter Lab
just lab
```

### Dependency Management

```bash
# Update dependencies and pre-commit hooks
just update-reqs
```

## Code Architecture

### Main Module: `src/parse.py`

This is the core module containing all paper parsing and table extraction logic:

**Pydantic Data Models:**

- `RegressionCoefficient`, `RegressionModel`, `RegressionTable` - For regression results
- `SummaryStatistic`, `SummaryStatisticsTable` - For descriptive statistics
- `BalanceStatistic`, `BalanceTable` - For treatment/control balance tables

**Main Class: `AcademicTableExtractor`**

This class handles document conversion and structured table extraction from academic papers:

- **Document Processing:** Uses `docling` library for PDF/DOCX conversion with table structure detection
- **Table Classification:** Automatically identifies table types (regression, summary stats, balance tables)
- **Parsing Logic:** Converts raw table data into structured Pydantic models with proper field validation
- **Output Methods:**
  - Exports to JSON (structured Pydantic models)
  - Converts to pandas DataFrames for analysis
  - Batch processing for multiple papers

**Key Methods:**

- `extract_structured_tables(file_path)` - Main entry point for single file processing
- `batch_extract(input_dir)` - Process multiple papers in a directory
- `parse_regression_table()`, `parse_summary_stats_table()`, `parse_balance_table()` - Specialized parsers
- `regression_to_dataframe()`, `summary_stats_to_dataframe()`, `balance_to_dataframe()` - Convert to pandas

**CLI Usage:**

```bash
# Single file
python src/parse.py paper.pdf -o output_dir

# Batch processing
python src/parse.py papers/ --batch -o output_dir

# Enable OCR for scanned documents
python src/parse.py paper.pdf --ocr
```

## Code Style and Standards

### Python Standards

- Target Python 3.12+
- Line length: 88 characters (Ruff formatter)
- Type hints encouraged where appropriate
- Pydantic models for structured data
- Docstrings use Google-style format

### Automated Code Quality (IMPORTANT)

**Claude Code MUST automatically format and lint Python code after writing or modifying files.**

Use the **py-format-lint** subagent or the **ruff** skill after ANY Python code changes:

```bash
# Use project's just commands
just fmt-python    # Format all Python code
just lint-python   # Lint and auto-fix issues
```

Or invoke the py-format-lint subagent to do both automatically.

### Linting Configuration (Ruff)

Selected rule sets:

- F (Pyflakes) - Errors, undefined names, unused imports
- E/W (pycodestyle) - PEP 8 violations
- I (isort) - Import sorting
- D (flake8-docstrings) - Docstring validation
- UP (pyupgrade) - Python syntax modernization
- SIM (flake8-simplify) - Code simplification

Note: Some docstring rules are disabled (D105, D100, D104, D203, D213) - check `pyproject.toml` for full list.

**Common linting issues and fixes:**

- **D400/D415**: Docstrings must end with period (`.`)
- **D401**: Use imperative mood ("Validate data" not "Validates data")
- **D103**: Add docstrings to public functions
- **F841**: Remove or use unused variables

### Pre-commit Hooks

Pre-commit automatically runs:

- YAML/JSON/TOML validation
- Merge conflict detection
- Pyproject.toml validation
- Codespell for typo detection
- Markdown linting
- Ruff linting and formatting

Always run `just pre-commit-run` before committing, or install hooks with `uv run pre-commit install`.

## Key Dependencies

- **docling** - PDF/DOCX document conversion and table extraction
- **pydantic** - Data validation and structured models
- **pandas** - Data manipulation and export
- **duckdb** - Data processing and file format conversion
- **marker-pdf** - Alternative PDF processing
- **altair** - Data visualization (for analysis notebooks)
- **pyfixest**, **nbstata** - Statistical analysis tools (for Jupyter notebooks)

## Directory Structure

- `src/` - Source code (currently contains `parse.py`)
- `data/` - Data files (ignored: .dta, .csv, .parquet, .xlsx, .sav, etc.)
- `do_files/` - Stata scripts
- `papers/` - Research papers for processing
- `.venv/` - Virtual environment (auto-created by uv)

## Development Workflow

**IMPORTANT: Claude Code must follow this workflow when writing Python code:**

1. Write or modify Python code in `src/` or skill/subagent scripts
2. **AUTOMATICALLY run formatting and linting** using one of:
   - The **py-format-lint** subagent (recommended - does both)
   - Or run `just fmt-python` and `just lint-python` directly
3. Fix any remaining linting issues that can't be auto-fixed
4. Run `just pre-commit-run` to validate all checks pass
5. Test the changes (e.g., `python src/parse.py path/to/paper.pdf`)
6. Commit changes (pre-commit hooks will run automatically)

**Key point**: Step 2 (formatting and linting) is NOT optional - it must happen after every Python code change.

## Notes

- Data files in `data/` directory are gitignored
- The project uses DuckDB's `read_stat` extension for reading statistical data formats
- When adding new Python files, ensure they follow the Ruff configuration in `pyproject.toml`
- For Jupyter notebooks, use `just lab` to launch Jupyter Lab with the project environment
