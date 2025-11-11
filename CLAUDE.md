# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**enlace** is a research tool for parsing academic papers in development economics and extracting structured data for meta-analysis and data harmonization. The project focuses on automating extraction of study characteristics, outcome measures, and statistical results from research papers (PDF/DOCX), and linking them to microdata sources.

**Core capabilities:**

- **Table Extraction** - Parse regression tables, summary statistics, and balance tables from PDFs/DOCX
- **OCR Enhancement** - Hybrid OCR system combining Tesseract and EasyOCR for scanned documents
- **VLM Integration** - Vision-Language Model support with Granite-Docling for complex layouts
- **Semantic Augmentation** - RAG-based context extraction to enrich parsed data
- **Research Summarization** - LLM-powered generation of structured research summaries
- **Validation** - Automated validation of extracted data against source documents

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
just lint-python

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

### Testing

```bash
# Run all tests
just test

# Run tests with coverage
just test-cov

# Run specific test file
uv run pytest tests/test_semantic_search.py -v
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

### CLI Commands: `src/enlace/cli.py`

The main CLI interface provides four core commands:

1. **`enlace extract`** - Extract tables from research papers
2. **`enlace validate`** - Validate extracted tables against source documents
3. **`enlace summarize`** - Generate structured research summaries
4. **`enlace batch`** - Process multiple papers in batch mode

**CLI Usage:**

```bash
# Extract tables from a single paper
enlace extract paper.pdf -o output_dir

# With OCR for scanned documents
enlace extract paper.pdf --ocr

# With semantic augmentation (adds context from paper text)
enlace extract paper.pdf --augment

# Validate extracted tables
enlace validate paper.pdf extracted_tables.json

# Generate research summary
enlace summarize paper.pdf -o summary.json

# Batch processing
enlace batch papers/ -o output_dir --workers 4
```

### Core Parsing: `src/enlace/parse.py`

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
- **OCR Enhancement:** Hybrid system using Tesseract and EasyOCR with confidence-based selection
- **VLM Support:** Vision-Language Model integration for complex layouts and visual elements
- **Output Methods:** JSON export, pandas DataFrames, batch processing

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

### VLM Integration: `src/enlace/vlm_processor.py`

**Purpose:** Vision-Language Model support for processing complex document layouts, visual elements, and scanned documents where traditional OCR struggles.

**Key Features:**

- **Granite-Docling Integration** - Uses IBM's Granite-Docling VLM for document understanding
- **Fallback Support** - Gracefully falls back to standard OCR if VLM is unavailable
- **Image Processing** - Handles tables, figures, charts, and mixed text-visual content
- **Document Context** - Leverages visual layout understanding for better extraction

**Configuration:**

```bash
# Enable VLM processing
export DOCLING_VLM_MODEL=granite-docling
export DOCLING_VLM_ENABLED=true

# Use with extract command
enlace extract paper.pdf --vlm
```

### OCR Enhancement: `src/enlace/ocr.py`

**Purpose:** Hybrid OCR system that combines Tesseract and EasyOCR for improved accuracy on scanned documents.

**How It Works:**

1. **Dual OCR Engines** - Runs both Tesseract and EasyOCR in parallel
2. **Confidence-Based Selection** - Chooses results with higher confidence scores
3. **Word-Level Optimization** - Selects best result for each word independently
4. **Fallback Strategy** - Uses single engine if the other fails

**Configuration:**

```bash
# Enable hybrid OCR
export OCR_ENGINE=hybrid  # Options: tesseract, easyocr, hybrid

# Use with extract command
enlace extract paper.pdf --ocr --ocr-engine hybrid
```

### Research Summarization: `src/enlace/summarize.py`

**Purpose:** Generate structured summaries of research papers using LLMs, with customizable detail levels and output formats.

**Key Features:**

- **LLM-Powered** - Uses Claude (default) or OpenAI for intelligent summarization
- **Detail Levels** - Choose from brief, standard, or detailed summaries
- **Multiple Formats** - Output as JSON, Markdown, or plain text
- **Structured Data** - Extracts metadata, methods, results, and key findings
- **Batch Processing** - Process multiple papers efficiently

**Configuration:**

```toml
# pyproject.toml or enlace.toml
[tool.enlace.summary]
llm_provider = "anthropic"  # or "openai"
model = "claude-3-5-sonnet-20241022"
detail_level = "standard"  # brief, standard, detailed
output_format = "json"  # json, markdown, text
temperature = 0.3
max_tokens = 4000
```

**CLI Usage:**

```bash
# Generate summary with defaults
enlace summarize paper.pdf

# Detailed summary as markdown
enlace summarize paper.pdf --detail detailed --format markdown -o summary.md

# Brief summary with custom model
enlace summarize paper.pdf --detail brief --model gpt-4

# Batch summarization
enlace batch papers/ --summarize --detail standard
```

### Validation: `src/enlace/validate.py`

**Purpose:** Validate extracted tables against source documents to detect OCR errors, missing data, and extraction issues.

**Key Features:**

- **Cross-Validation** - Checks parsed values against original paper text
- **Error Detection** - Identifies OCR errors, type mismatches, missing values
- **Confidence Scores** - Quantifies validation quality
- **Detailed Reports** - Generates validation reports with suggested fixes

**CLI Usage:**

```bash
# Validate extracted tables
enlace validate paper.pdf extracted_tables.json

# Generate detailed validation report
enlace validate paper.pdf extracted_tables.json --report validation_report.json
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

- **docling** - PDF/DOCX document conversion and table extraction with VLM support
- **pydantic** - Data validation and structured models
- **pandas** - Data manipulation and export
- **duckdb** - Data processing and file format conversion
- **anthropic** / **openai** - LLM providers for summarization and semantic augmentation
- **chromadb** - Vector database for semantic search
- **sentence-transformers** - Embedding models for RAG pipeline
- **pytesseract** / **easyocr** - OCR engines for scanned documents
- **altair** - Data visualization (for analysis notebooks)
- **pyfixest**, **nbstata** - Statistical analysis tools (for Jupyter notebooks)

## Directory Structure

- `src/enlace/` - Source code
  - `cli.py` - CLI interface (extract, validate, summarize, batch commands)
  - `parse.py` - Core table extraction module
  - `summarize.py` - Research paper summarization
  - `validate.py` - Validation engine
  - `ocr.py` - Hybrid OCR system (Tesseract + EasyOCR)
  - `vlm_processor.py` - Vision-Language Model integration
  - `augmentation_config.py` - Semantic augmentation configuration
  - `semantic_search.py` - RAG pipeline for context extraction
  - `context_models.py` - Pydantic models for context data
  - `context_extractors.py` - Specialized context extractors
  - `semantic_validator.py` - Cross-validation engine
  - `table_augmenter.py` - Table augmentation orchestration
- `tests/` - Test suite (75 passing tests)
  - `test_semantic_search.py` - Semantic search tests (31 tests)
  - `test_semantic_validator.py` - Validation tests (37 tests)
  - `test_table_augmenter.py` - Table augmentation tests
  - `test_semantic_augmentation_integration.py` - Integration tests (10 tests)
  - `benchmark/` - Benchmark tests (23 skipped - ground truth incomplete)
  - `fixtures/` - Test fixtures and ground truth data
- `docs/` - Documentation
  - `SUBAGENT_ARCHITECTURE.md` - Semantic augmentation architecture
  - `PHASE8_TESTING_PLAN.md` - Testing strategy
  - `CLI_GUIDE.md` - Complete CLI documentation
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

The project includes comprehensive tests covering all major functionality:

```bash
# Run all tests (75 passing, 23 skipped)
just test

# Run with coverage
just test-cov

# Run only semantic augmentation tests
uv run pytest tests/test_semantic*.py -v

# Run only unit tests (fast)
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run specific test file
uv run pytest tests/test_semantic_search.py -v
```

**Test Suite:**

- **75 passing tests** - Core functionality fully tested
- **23 skipped tests** - Benchmark tests (ground truth incomplete)
- **Coverage areas:**
  - Semantic search and RAG pipeline (31 tests)
  - Semantic validation (37 tests)
  - Table augmentation (multiple tests)
  - Integration tests (10 tests)

**Benchmark Tests:**

The benchmark tests in `tests/benchmark/` are currently skipped because ground truth data is incomplete. These tests validate extraction accuracy against manually annotated papers:

- `test_field_accuracy.py` - Field-level accuracy metrics
- `test_ocr_comparison.py` - OCR engine comparison
- `test_table_detection.py` - Table detection accuracy

To run benchmark tests, complete the ground truth annotations in `tests/fixtures/benchmark_data/` and remove the `@pytest.mark.skip` decorators.

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Recent Updates (Updated: 2025-11-10)

### Research Paper Summarization (NEW)

Added comprehensive LLM-powered summarization capabilities:

- **`enlace summarize`** command for generating structured research summaries
- **Multiple detail levels** - Brief, standard, and detailed summaries
- **Multiple output formats** - JSON, Markdown, and plain text
- **Configurable LLM providers** - Claude (default) and OpenAI support
- **Batch processing** - Efficiently summarize multiple papers
- **Structured extraction** - Metadata, methods, results, and key findings

**Usage:**

```bash
# Generate summary
enlace summarize paper.pdf

# Detailed summary as markdown
enlace summarize paper.pdf --detail detailed --format markdown -o summary.md

# Batch summarization
enlace batch papers/ --summarize
```

See [CLI_GUIDE.md](docs/CLI_GUIDE.md) for complete documentation.

### VLM Integration (NEW)

Added Vision-Language Model support for complex document layouts:

- **Granite-Docling VLM** integration for document understanding
- **Visual layout processing** - Better handling of tables, figures, and charts
- **Fallback support** - Gracefully falls back to standard OCR
- **`--vlm` flag** - Easy activation via CLI

**Configuration:**

```bash
export DOCLING_VLM_MODEL=granite-docling
export DOCLING_VLM_ENABLED=true
enlace extract paper.pdf --vlm
```

### OCR Enhancements (NEW)

Improved OCR accuracy with hybrid engine system:

- **Dual OCR engines** - Tesseract and EasyOCR running in parallel
- **Confidence-based selection** - Automatically chooses best results
- **Word-level optimization** - Selects best result for each word independently
- **Fallback strategy** - Uses single engine if the other fails

**Configuration:**

```bash
export OCR_ENGINE=hybrid
enlace extract paper.pdf --ocr --ocr-engine hybrid
```

### Test Suite Fixes

Fixed all test failures and improved test organization:

- **75 passing tests** - All core functionality fully tested
- **23 skipped tests** - Benchmark tests marked as skipped (ground truth incomplete)
- **Fixed import errors** - Updated all module paths to use `enlace.` prefix
- **Fixed validation schemas** - Updated Pydantic models to handle null values
- **Clear skip reasons** - All skipped tests have explicit reasons

### Semantic Table Augmentation System (Complete)

**All 8 phases complete** - The semantic augmentation system enhances table extraction with RAG-based context:

1. **Phase 1-2: Foundation** - Configuration and semantic search pipeline
2. **Phase 3: Context Extraction** - 5 specialized extractors for different context types
3. **Phase 4: Validation** - Cross-validation engine to catch OCR errors
4. **Phase 5: Integration** - Added to content-extractor subagent with `--augment` flag
5. **Phase 6: Data Models** - Added optional context fields to Pydantic models in `parse.py`
6. **Phase 7: Dependencies** - Updated `pyproject.toml` with required packages
7. **Phase 8: Testing** - 75 comprehensive tests (31 unit + 37 unit + 10 integration)

**Key Benefits:**

- **Richer Context**: Adds variable definitions, treatment details, sample descriptions
- **Error Detection**: Cross-validates parsed values against paper text
- **Data Harmonization**: Structured metadata enables cross-study variable mapping
- **Quality Scores**: Confidence metrics help identify low-quality extractions

**Usage:**

```bash
# Enable semantic augmentation when extracting tables
enlace extract paper.pdf --augment

# Or use environment variables
export AUGMENTATION_ENABLED=true
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Documentation Updates

- Added comprehensive summarization docs to [README.md](README.md)
- Added complete CLI reference to [CLI_GUIDE.md](docs/CLI_GUIDE.md)
- Updated [CLAUDE.md](CLAUDE.md) with all recent changes
- Added `docs/SUBAGENT_ARCHITECTURE.md` with complete semantic augmentation architecture
- Added `docs/PHASE8_TESTING_PLAN.md` with testing strategy
- Updated `tests/README.md` to document test suite

## Configuration

### Environment Variables

Key environment variables for configuring enlace:

**LLM Providers:**

```bash
# Anthropic (default)
export ANTHROPIC_API_KEY=your_api_key
export ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# OpenAI
export OPENAI_API_KEY=your_api_key
export OPENAI_MODEL=gpt-4
```

**OCR Configuration:**

```bash
export OCR_ENGINE=hybrid  # Options: tesseract, easyocr, hybrid
export TESSERACT_CMD=/usr/bin/tesseract  # Path to tesseract binary
```

**VLM Configuration:**

```bash
export DOCLING_VLM_ENABLED=true
export DOCLING_VLM_MODEL=granite-docling
```

**Semantic Augmentation:**

```bash
export AUGMENTATION_ENABLED=true
export EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
export CHROMA_PERSIST_DIR=.chroma_db
```

**Summarization:**

```bash
export SUMMARY_LLM_PROVIDER=anthropic  # or openai
export SUMMARY_DETAIL_LEVEL=standard  # brief, standard, detailed
export SUMMARY_OUTPUT_FORMAT=json  # json, markdown, text
export SUMMARY_TEMPERATURE=0.3
export SUMMARY_MAX_TOKENS=4000
```

### Configuration Files

You can also configure enlace using `pyproject.toml` or a dedicated `enlace.toml`:

```toml
[tool.enlace.summary]
llm_provider = "anthropic"
model = "claude-3-5-sonnet-20241022"
detail_level = "standard"
output_format = "json"
temperature = 0.3
max_tokens = 4000

[tool.enlace.ocr]
engine = "hybrid"
tesseract_cmd = "/usr/bin/tesseract"

[tool.enlace.augmentation]
enabled = true
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
```

## Notes

- Data files in `data/` directory are gitignored
- The project uses DuckDB's `read_stat` extension for reading statistical data formats
- When adding new Python files, ensure they follow the Ruff configuration in `pyproject.toml`
- For Jupyter notebooks, use `just lab` to launch Jupyter Lab with the project environment
- Semantic augmentation is optional - use `--augment` flag to enable
- OCR and VLM features require additional dependencies - see installation docs
