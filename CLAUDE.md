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

### Core Parsing: `src/parse.py`

The main module for table extraction from research papers:

**Pydantic Data Models:**

- `RegressionCoefficient`, `RegressionModel`, `RegressionTable` - Regression results with semantic context fields
- `SummaryStatistic`, `SummaryStatisticsTable` - Descriptive statistics
- `BalanceStatistic`, `BalanceTable` - Treatment/control balance tables

**Main Class: `AcademicTableExtractor`**

- **Document Processing:** Uses `docling` for PDF/DOCX conversion with table structure detection
- **Table Classification:** Automatically identifies table types (regression, summary stats, balance tables)
- **Parsing Logic:** Converts raw table data into structured Pydantic models
- **Semantic Augmentation:** Optional enhancement with RAG-based context extraction (see below)
- **Output Methods:** JSON export, pandas DataFrames, batch processing

**CLI Usage:**

```bash
# Single file
python src/parse.py paper.pdf -o output_dir

# Batch processing
python src/parse.py papers/ --batch -o output_dir

# Enable semantic augmentation (adds context from paper text)
python src/parse.py paper.pdf --augment

# Enable OCR for scanned documents
python src/parse.py paper.pdf --ocr
```

### Semantic Augmentation System (NEW)

**Purpose:** Enhances table extraction by adding semantic context from paper text using RAG (Retrieval-Augmented Generation). This helps with data harmonization and catches OCR errors.

**Architecture:** 5 core modules (2,454 lines total)

1. **`src/augmentation_config.py`** (215 lines) - Configuration with environment variables
2. **`src/semantic_search.py`** (393 lines) - RAG pipeline using ChromaDB + HuggingFace embeddings
3. **`src/context_models.py`** (296 lines) - 8 Pydantic models for context data
4. **`src/context_extractors.py`** (583 lines) - 5 specialized extractors for different context types
5. **`src/semantic_validator.py`** (465 lines) - Cross-validation engine for parsed values

**How It Works:**

1. **Document Processing** - Extracts and chunks text from research paper
2. **Vector Store** - Creates embeddings using sentence-transformers or model2vec
3. **Context Extraction** - Uses semantic search to find relevant paper sections
4. **Validation** - Cross-checks parsed values against paper text to catch errors
5. **Augmentation** - Adds semantic context fields to parsed data models

**CLI Usage:**

```bash
# Use content-extractor subagent with semantic augmentation
uv run python .claude/subagents/content-extractor/extractor.py paper.pdf --augment

# Configure via environment variables
export AUGMENTATION_ENABLED=true
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
export LLM_MODEL=claude-3-5-sonnet-20241022
```

**Key Features:**

- **Variable Context** - Adds definitions, measurement units, data sources
- **Treatment Context** - Describes intervention details, implementation
- **Sample Context** - Population characteristics, selection criteria
- **Methods Context** - Estimation techniques, standard error types
- **Data Validation** - Cross-checks parsed values with paper text to detect OCR errors
- **Confidence Scores** - Quality metrics for extracted information

**Integration:**

The semantic augmentation system integrates with `parse.py` through optional context fields in Pydantic models:

```python
class RegressionCoefficient(BaseModel):
    variable_name: str
    coefficient: float | None
    # ... standard fields ...

    # Semantic augmentation fields (optional)
    variable_context: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
```

**Documentation:**

- Architecture details: [`docs/SUBAGENT_ARCHITECTURE.md`](docs/SUBAGENT_ARCHITECTURE.md)
- Testing plan: [`docs/PHASE8_TESTING_PLAN.md`](docs/PHASE8_TESTING_PLAN.md)
- Test suite: [`tests/README.md`](tests/README.md)

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
- **altair** - Data visualization (for analysis notebooks)
- **pyfixest**, **nbstata** - Statistical analysis tools (for Jupyter notebooks)

## Directory Structure

- `src/` - Source code
  - `parse.py` - Core table extraction module
  - `augmentation_config.py` - Semantic augmentation configuration
  - `semantic_search.py` - RAG pipeline for context extraction
  - `context_models.py` - Pydantic models for context data
  - `context_extractors.py` - Specialized context extractors
  - `semantic_validator.py` - Cross-validation engine
- `tests/` - Test suite (78 tests for semantic augmentation)
  - `test_semantic_search.py` - Semantic search tests (31 tests)
  - `test_semantic_validator.py` - Validation tests (37 tests)
  - `test_semantic_augmentation_integration.py` - Integration tests (10 tests)
- `docs/` - Documentation
  - `SUBAGENT_ARCHITECTURE.md` - Semantic augmentation architecture
  - `PHASE8_TESTING_PLAN.md` - Testing strategy
- `data/` - Data files (gitignored)
- `do_files/` - Stata scripts
- `papers/` - Research papers for processing
- `.venv/` - Virtual environment (auto-created by uv)
- `.claude/` - Claude Code configuration
  - `skills/` - Reusable skills for research workflows
  - `subagents/` - Specialized subagents
    - `content-extractor/` - Main extraction subagent with semantic augmentation support

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

## Testing

The project now includes comprehensive tests for the semantic augmentation system:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run only semantic augmentation tests
uv run pytest tests/test_semantic*.py -v

# Run only unit tests (fast)
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration
```

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Recent Updates (Updated: 2025-11-06)

### Semantic Table Augmentation System (Complete)

**All 8 phases complete** - The semantic augmentation system enhances table extraction with RAG-based context:

1. **Phase 1-2: Foundation** - Configuration and semantic search pipeline
2. **Phase 3: Context Extraction** - 5 specialized extractors for different context types
3. **Phase 4: Validation** - Cross-validation engine to catch OCR errors
4. **Phase 5: Integration** - Added to content-extractor subagent with `--augment` flag
5. **Phase 6: Data Models** - Added optional context fields to Pydantic models in `parse.py`
6. **Phase 7: Dependencies** - Updated `pyproject.toml` with required packages
7. **Phase 8: Testing** - 78 comprehensive tests (31 unit + 37 unit + 10 integration)

**Key Benefits:**

- **Richer Context**: Adds variable definitions, treatment details, sample descriptions
- **Error Detection**: Cross-validates parsed values against paper text
- **Data Harmonization**: Structured metadata enables cross-study variable mapping
- **Quality Scores**: Confidence metrics help identify low-quality extractions

**Usage:**

```bash
# Enable semantic augmentation when extracting tables
uv run python .claude/subagents/content-extractor/extractor.py paper.pdf --augment

# Or use environment variables
export AUGMENTATION_ENABLED=true
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Skills & Subagents Cleanup

- Removed unused skills (ripgrep, eza) - replaced by Claude built-in tools
- Archived marker-pdf references - now using docling exclusively
- Streamlined pdf-processor skill documentation

### Documentation Updates

- Added `docs/SUBAGENT_ARCHITECTURE.md` with complete semantic augmentation architecture
- Added `docs/PHASE8_TESTING_PLAN.md` with testing strategy
- Updated `tests/README.md` to document semantic augmentation test suite

## Notes

- Data files in `data/` directory are gitignored
- The project uses DuckDB's `read_stat` extension for reading statistical data formats
- When adding new Python files, ensure they follow the Ruff configuration in `pyproject.toml`
- For Jupyter notebooks, use `just lab` to launch Jupyter Lab with the project environment
- Semantic augmentation is optional - use `--augment` flag to enable
