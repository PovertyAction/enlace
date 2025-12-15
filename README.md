# enlace

**Extract, validate, and summarize research papers to prepare for data harmonization and meta-analysis**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

enlace is a Python package for extracting structured data from social science research papers. It automatically extracts tables (regression results, summary statistics, balance tables), figures, and metadata from PDF/DOCX papers, with optional semantic augmentation for enhanced context and error detection.

### Key Features

- **Automated Table Extraction** - Regression tables, summary statistics, balance tables
- **Form-Based Data Extraction** - Extract structured data using custom Excel form definitions (project-agnostic)
- **Figure Extraction** - Extract and save figures with vision model annotations
- **Vision Model Annotations** - Local AI-powered image descriptions
- **Metadata Extraction** - Title, authors, institution, journal, year, DOI, citations, methodology
- **OCR Support** - Hybrid OCR with Tesseract + EasyOCR fallback
- **Semantic Augmentation** - RAG-based context extraction using LLMs
- **Data Validation** - Comprehensive quality checks with configurable validation levels
- **Batch Processing** - Parallel processing of multiple papers
- **CLI + Python API** - Use from command line or integrate into your code

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Quick Install

```bash
# Clone repository
git clone https://github.com/yourusername/enlace.git
cd enlace

# Install with uv (recommended)
uv pip install -e .

# Or use just (installs uv and creates virtual environment)
just get-started
```

### Verify Installation

```bash
enlace --help
```

## Quick Start

### Extract from a Single Paper

Given a path to a file, `paper.pdf`, enlace converts the file to markdown using docling, generates an `extraction.json` with identified tables and metadata, and stores images from the paper. Optionally, you can output tables to csv and use vision models to annotate images.

```bash
# Basic extraction
enlace extract paper.pdf

# With OCR for scanned documents
enlace extract scanned_paper.pdf --ocr auto

# With semantic augmentation (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your_api_key
enlace extract paper.pdf --augment

# Save as both JSON and CSV
enlace extract paper.pdf --format both -o results/
```

### Validate Extraction Quality

following the extract step, it's often helpful to validate that the table contents are sensible.

```bash
# Standard validation
enlace validate output/paper/extraction.json

# Comprehensive validation with all checks
enlace validate output/paper/extraction.json --level comprehensive

# Fail on validation issues
enlace validate output/paper/extraction.json --fail-on-issues
```

### Generate Research Summaries

Using the outputs of the extract step, you can create AI-generated summaries of research papers.

```bash
# Set up API key (first time only - see .env.example)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Basic summary
enlace summarize output/paper/extraction.json

# Generate markdown summary
enlace summarize output/paper --format markdown

# Use custom output directory
enlace summarize output/paper -o summaries/

# Enhanced summary with web search
enlace summarize output/paper --web-search
```

### Form-Based Data Extraction (Project-Agnostic)

Extract structured data from papers according to custom form definitions. Perfect for systematic reviews, meta-analysis, and data harmonization projects.

```bash
# Set up API key (first time only)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Place your Excel form definitions in data/forms/
# Place your papers in papers/
# Run extraction - automatically discovers all forms
uv run python scripts/extract_from_form_improved.py

# Results saved to output/form_extractions/{form_id}/
# - Individual JSON files per paper
# - Combined Excel file per form
# - Detailed completion statistics
```

**Key Features:**

- **Auto-discovery** - Automatically finds all Excel forms in `data/forms/`
- **Flexible schemas** - Adapts to different column names (`rando`, `deliver`, `type`)
- **Multiple forms** - Process multiple forms in one run, separate outputs per form
- **Type validation** - Automatic type coercion (text, integer, date, select_one, select_multiple)
- **Incremental processing** - Skips already-extracted papers to save API costs
- **Error recovery** - Continues processing even if individual papers fail
- **Comprehensive reporting** - Field completion rates, validation warnings, statistics

See [Form Extraction Guide](docs/FORM_EXTRACTION_SUMMARY.md) for detailed documentation.

### Batch Processing

```bash
# Process all papers in directory
enlace batch papers/ -o batch_output/

# High-performance batch with validation
enlace batch papers/ --workers 8 --validate --validation-level comprehensive
```

### Python API

```python
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig

# Configure extraction
config = ExtractionConfig(
    enable_ocr=True,
    enable_augmentation=False,
    output_format="json"
)

# Extract from paper
extractor = PaperExtractor(config)
result = extractor.extract(Path("paper.pdf"))

# Access results
print(f"Extracted {len(result.tables)} tables")
for table in result.tables:
    print(f"  - {table.title} ({table.table_type})")

# Save results
result.save(Path("output"))
```

## Features

### Table Extraction

Automatically detects and extracts three types of tables:

1. **Regression Tables** - Coefficients, standard errors, p-values, significance stars
2. **Summary Statistics** - Mean, SD, min, max, N for multiple variables
3. **Balance Tables** - Treatment vs. control group comparisons

### Figure Extraction with Vision Model Annotations

Automatically extract figures and generate AI-powered descriptions:

- **Local Vision Model** - Uses Granite Vision (IBM's 258M parameter model) by default
- **Dual Output** - Annotations saved in both markdown and JSON
- **Searchable** - Text descriptions make figures discoverable
- **Accessible** - Provides alt-text-like descriptions for all images

**Output Examples:**

*Markdown:*

```markdown
![Image](figures/figure_1.png)
VISION MODEL ANNOTATION: The image shows a bar chart comparing treatment and control groups across three outcome variables...
```

*JSON:*

```json
{
  "figure_id": "figure_1",
  "caption": "Figure 1: Treatment Effects",
  "annotation": "The image shows a bar chart comparing treatment and control groups...",
  "image_path": "figures/figure_1.png"
}
```

**Configuration:**

```bash
# Figure annotation is disabled by default
# The following will not generate annotations
enlace extract paper.pdf

# Enable via environment variable
export ENLACE_DESCRIBE_PICTURES=true
enlace extract paper.pdf
```

### OCR Support

Hybrid OCR system for scanned documents:

- **Auto mode** (default) - Tesseract primary + EasyOCR fallback
- **Per-cell confidence** - Tracks OCR quality for each extracted value
- **Automatic fallback** - Switches to EasyOCR when Tesseract confidence is low
- **Numeric validation** - Detects common OCR errors (O↔0, l↔1, S↔5)

```bash
# Use auto mode (Tesseract + EasyOCR fallback)
enlace extract paper.pdf --ocr auto

# Use specific backend
enlace extract paper.pdf --ocr easyocr

# Customize confidence threshold
enlace extract paper.pdf --ocr auto --ocr-confidence 0.9
```

### Form-Based Structured Data Extraction

**Project-Agnostic System** for extracting structured data from papers according to custom form definitions. Ideal for systematic reviews, meta-analysis projects, and data harmonization across studies.

#### How It Works

1. **Define your data schema** - Create Excel forms with field definitions (supports ODK/KoBoToolbox format)
2. **Place forms in `data/forms/`** - Script automatically discovers all Excel files
3. **Add papers to `papers/`** - PDF research papers to extract from
4. **Run extraction** - Processes all papers against all forms automatically
5. **Get structured output** - JSON + Excel files with completion statistics

#### Form Structure

Forms are Excel files with columns defining your data fields:

| Column | Description | Values |
|--------|-------------|--------|
| `type` / `rando` / `deliver` | Field type | `text`, `integer`, `date`, `select_one`, `select_multiple` |
| `name` | Field identifier | `study_id`, `sample_size`, `treatment_effect` |
| `label` | Human-readable label | "Study Identifier", "Total Sample Size" |
| `hint` | Extraction guidance (optional) | "Look in methods section" |
| `required` | Required field (optional) | `yes` / `no` |
| `constraint` | Validation rule (optional) | Pattern or value constraints |

**Example form row:**

```
type: integer
name: sample_size
label: Total number of participants in study
hint: Check Table 1 or methods section
required: yes
```

#### Running Extraction

```bash
# Set up API key (first time only)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run extraction (auto-discovers forms)
uv run python scripts/extract_from_form_improved.py
```

#### Output Structure

```
output/form_extractions/
├── stage1/                          # First form (e.g., basic study info)
│   ├── Paper_001_extraction.json   # Individual extractions
│   ├── Paper_002_extraction.json
│   ├── ...
│   └── stage1_all_extractions.xlsx # Combined data
├── stage2/                          # Second form (e.g., detailed outcomes)
│   ├── Paper_001_extraction.json
│   ├── Paper_002_extraction.json
│   ├── ...
│   └── stage2_all_extractions.xlsx
└── ...
```

#### Features

- **Auto-discovery** - Finds all forms automatically, no configuration needed
- **Flexible column mapping** - Adapts to different form formats (`rando`, `deliver`, `type` columns)
- **Multiple forms support** - Process multiple schemas in one run
- **Type validation & coercion** - Automatic conversion to integers, dates, lists
- **Incremental processing** - Skip already-extracted papers (saves API costs)
- **Retry logic** - Automatic retry with exponential backoff for API failures
- **Field categorization** - Intelligent grouping for better LLM prompting
- **Completion tracking** - Per-field completion rates and statistics
- **Validation warnings** - Missing required fields, type mismatches
- **Error recovery** - Continues processing if individual papers fail

#### Customization

The extraction system is designed to work out-of-the-box, but can be customized:

```python
# Modify field categorization in scripts/extract_from_form_improved.py
def categorize_fields(fields: list[FormField]) -> dict[str, list[FormField]]:
    # Add custom categories or modify existing patterns
    ...

# Adjust validation rules
class ExtractionValidator:
    def validate(self, data: dict) -> tuple[dict, list[str]]:
        # Add custom validation logic
        ...
```

See [Form Extraction Documentation](docs/FORM_EXTRACTION_SUMMARY.md) for complete guide.

### Semantic Augmentation

Enhance extractions with context from paper text using RAG:

- **Variable Context** - Definitions, units, data sources
- **Treatment Context** - Intervention details, implementation
- **Sample Context** - Population characteristics, selection criteria
- **Methods Context** - Estimation techniques, standard error types
- **Cross-Validation** - Detects OCR errors by comparing to paper text
- **Confidence Scores** - Quality metrics for extracted information

**Requirement:** Semantic augmentation requires `ANTHROPIC_API_KEY` in `.env` file. (Other remote models as well as local models are on the roadmap).

```bash
# Set up API key (first time only)
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Extract with augmentation
enlace extract paper.pdf --augment
```

### Data Validation

Configurable validation with three built-in levels:

1. **Quick** - Structure and completeness checks (fastest)
2. **Standard** - Quick + accuracy + missing data checks (recommended)
3. **Comprehensive** - All checks including statistical consistency and OCR quality

Custom validation levels can be defined in configuration files.

```bash
# Quick validation
enlace validate output/paper/extraction.json --level quick

# Custom validation with specific checks
enlace validate output/paper/extraction.json --config .enlace.toml
```

### Research Paper Summarization

Generate structured, LLM-based summaries of research papers from extraction results:

**Features:**

- **Structured Output** - JSON and Markdown formats with standardized sections
- **Multi-Source Integration** - Combines extraction data, validation results, and optional PDF analysis
- **Anti-Hallucination** - Strict prompting minimizes fabrication of data
- **Customizable Detail Levels** - Brief, standard, or detailed summaries
- **Web Search Enhancement** - Optional web search for additional context (not yet implemented)
- **Quality Assessment** - Includes extraction quality scores and validation issues

**Summary Sections:**

- Title (50-60 character jargon-free)
- Research question and methodology
- Sample information and treatment details
- Key findings with specific metrics
- Policy implications
- Data quality assessment

**Usage:**

```bash
# Set up API key first (see .env.example)
# cp .env.example .env and add your ANTHROPIC_API_KEY

# Basic usage
enlace summarize output/paper/extraction.json

# With validation results (auto-detected)
enlace summarize output/paper/

# Custom model and detail level
enlace summarize output/paper/ --model claude-3-5-sonnet-20241022 --level detailed

# Generate markdown format
enlace summarize output/paper/ --format markdown

# Both JSON and markdown
enlace summarize output/paper/ --format both -o summaries/

# Enhanced with web search
enlace summarize output/paper/ --web-search
```

**Example Output (Markdown):**

```markdown
# Study Title
## Study Details
**Authors:** Smith J, Jones A
**Timeline:** 2015-2017
**Study Type:** RCT
**Sample Size:** 1,200 households

## Overview
Brief description of the research question and significance...

## Key Findings
- Treatment increased school attendance by 15% (SE: 0.03, p<0.001)
- Effects strongest for girls (+20% vs +10% for boys)

## Data Quality Assessment
**Extraction Quality:** 0.85
**Validation Score:** 0.78
```

**Customizing the Summarizer:**

The summarizer can be customized via Python API or configuration:

```python
from pathlib import Path
from enlace.core.summarizer import PaperSummarizer
from enlace.core.config import SummaryConfig

# Custom configuration
config = SummaryConfig(
    llm_model="claude-4-5-sonnet-20250929",  # Use more powerful model
    temperature=0.3,  # Lower = more conservative
    max_tokens=4096,  # Longer summaries
    detail_level="detailed",  # brief, standard, or detailed
    use_web_search=True,  # Enable web search
)

# Initialize summarizer
summarizer = PaperSummarizer(config)

# Generate summary
extraction_path = Path("output/paper/extraction.json")
result = summarizer.summarize(extraction_path)

# Save in both formats
result.save_json(Path("summaries/paper_summary.json"))
result.save_markdown(Path("summaries/paper_summary.md"))
```

**Custom Summary Prompts:**

To modify the summary structure or focus, edit the prompts in `src/enlace/core/summarizer.py`:

- `SYSTEM_PROMPT` - Controls the LLM's role and anti-hallucination rules
- `SUMMARY_TEMPLATE` - Defines the output structure and JSON schema

**Environment Configuration:**

```bash
# Set default model
export ENLACE_SUMMARY_MODEL=claude-4-5-sonnet

# Set temperature (0.0-1.0, lower = more conservative)
export ENLACE_SUMMARY_TEMPERATURE=0.2

# Enable web search by default
export ENLACE_SUMMARY_WEB_SEARCH=true
```

### Batch Processing

Process multiple papers in parallel with automatic validation:

```bash
# Process directory with 8 workers
enlace batch papers/ --workers 8 --output batch_results/

# Full pipeline with augmentation and validation
enlace batch papers/ \
    --augment \
    --ocr auto \
    --validate \
    --validation-level comprehensive \
    --workers 4
```

## Output Structure

Extraction creates organized output directories:

```text
output/
└── paper_id/
    ├── extraction.json          # Complete extraction results
    ├── extraction.csv           # CSV format (if --format csv or both)
    ├── tables/                  # Individual table files
    │   ├── table_1.json
    │   ├── table_2.json
    │   └── ...
    ├── figures/                 # Extracted figures
    │   ├── figure_1.png
    │   └── figure_2.png
    └── logs/                    # Extraction logs
        └── extraction.log
```

## Configuration

### Configuration File

Create `.enlace.toml` in your project:

```toml
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
ocr_confidence_threshold = 0.85
enable_augmentation = true
extract_figures = true
# describe_pictures = true  # Optional: Enable vision model annotations (slow)
output_format = "both"
max_workers = 8

# LLM configuration
llm_model = "claude-4-5-haiku"
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

[tool.enlace.validation]
level = "comprehensive"
fail_on_issues = true

[tool.enlace.summary]
llm_model = "claude-4-5-sonnet"
temperature = 0.3
max_tokens = 4096
detail_level = "standard"
use_web_search = false
output_format = "both"
```

### Environment Variables

All options can be set via environment variables with `ENLACE_` prefix:

```bash
# Extraction settings
export ENLACE_ENABLE_OCR=true
export ENLACE_OCR_BACKEND=auto
export ENLACE_ENABLE_AUGMENTATION=true
export ENLACE_EXTRACT_FIGURES=true
export ENLACE_DESCRIBE_PICTURES=true  # Enable vision model annotations
export ENLACE_OUTPUT_FORMAT=both
export ENLACE_MAX_WORKERS=8

# Summary settings
export ENLACE_SUMMARY_MODEL=claude-4-5-sonnet
export ENLACE_SUMMARY_TEMPERATURE=0.3
export ENLACE_SUMMARY_DETAIL_LEVEL=detailed
export ENLACE_SUMMARY_WEB_SEARCH=true

# API key (required for augmentation and summarization)
export ANTHROPIC_API_KEY=your_api_key
```

### Configuration Priority

Later sources override earlier ones:

1. Default values (built-in)
2. Configuration file (`.enlace.toml` or `pyproject.toml`)
3. Environment variables (`ENLACE_*`)
4. Command-line arguments (highest priority)

## Documentation

- **[CLI Guide](docs/CLI_GUIDE.md)** - Complete command-line reference
- **[API Guide](docs/API_GUIDE.md)** - Python API documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** - All configuration options
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and development setup
- **[Benchmark Guide](docs/BENCHMARK_README.md)** - Benchmark testing system
- **[Migration Plan](docs/MIGRATION_PLAN.md)** - Package architecture details

### Examples

See the [examples/](examples/) directory for complete working examples:

- [basic_extraction.py](examples/basic_extraction.py) - Simple extraction example
- [batch_processing.py](examples/batch_processing.py) - Batch processing workflows
- [custom_validation.py](examples/custom_validation.py) - Custom validation levels
- [semantic_augmentation.py](examples/semantic_augmentation.py) - Semantic context extraction

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/enlace.git
cd enlace

# Install with just (recommended)
just get-started

# Or manually
uv pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/enlace --cov-report=term-missing --cov-report=html

# Run only unit tests (fast)
uv run pytest -m unit

# Run benchmark tests
uv run pytest tests/benchmark/ -v
```

### Code Quality

```bash
# Format and lint (REQUIRED before committing)
just fmt-python
just lint-python

# Run all pre-commit hooks
just pre-commit-run
```

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete development guide.

## Common Use Cases

### Meta-Analysis Workflow

```bash
# 1. Extract from all papers
enlace batch papers/ --ocr auto --augment -o extractions/

# 2. Validate extractions
for file in extractions/*/extraction.json; do
    enlace validate "$file" --level comprehensive --fail-on-issues
done

# 3. Generate summaries for all papers
for dir in extractions/*/; do
    enlace summarize "$dir" --format both -o summaries/
done

# 4. Export to CSV for analysis
# (CSV files are in extractions/*/tables/)
```

### Complete Research Paper Processing Workflow

```bash
# Single paper: extract → validate → summarize
enlace extract paper.pdf --ocr auto --augment -o output/
enlace validate output/paper/ --level comprehensive
enlace summarize output/paper/ --format both

# Batch processing with summaries
enlace batch papers/ \
    --ocr auto \
    --augment \
    --validate \
    --validation-level comprehensive \
    -o batch_output/

# Generate summaries for all
for dir in batch_output/*/; do
    enlace summarize "$dir" --format markdown -o summaries/
done
```

### OCR Quality Comparison

```bash
# Extract with different OCR backends
enlace extract scanned.pdf --ocr tesseract -o results_tesseract/
enlace extract scanned.pdf --ocr easyocr -o results_easyocr/
enlace extract scanned.pdf --ocr auto -o results_auto/

# Compare validation results
enlace validate results_tesseract/scanned/extraction.json -v
enlace validate results_easyocr/scanned/extraction.json -v
enlace validate results_auto/scanned/extraction.json -v
```

### Semantic Context for Data Harmonization

```python
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig

# Extract with semantic context
config = ExtractionConfig(enable_augmentation=True)
extractor = PaperExtractor(config)

result = extractor.extract(Path("paper.pdf"))
augmented = extractor.augment(result)

# Access variable context for harmonization
for table in augmented.tables:
    if table.table_type == "regression":
        for model in table.models:
            for coef in model.coefficients:
                if coef.variable_context:
                    print(f"{coef.variable_name}:")
                    print(f"  Definition: {coef.variable_context['definition']}")
                    print(f"  Units: {coef.variable_context['units']}")
                    print(f"  Source: {coef.variable_context['data_source']}")
```

## Troubleshooting

### OCR Not Working

1. Ensure OCR is enabled: `--ocr auto`
2. Install OCR backends: `uv pip install docling[easyocr,tesseract]`
3. For EasyOCR GPU support: `uv pip install torch torchvision`

### Semantic Augmentation Fails

1. Check API key: `echo $ANTHROPIC_API_KEY`
2. Set API key: `export ANTHROPIC_API_KEY=your_key`
3. Verify model: `export ENLACE_LLM_MODEL=claude-4-5-haiku`

### Low Extraction Quality

1. Try different OCR backend: `--ocr easyocr`
2. Enable augmentation for validation: `--augment`
3. Check validation report: `enlace validate output/paper/extraction.json --level comprehensive -v`

See [CLI Guide](docs/CLI_GUIDE.md#troubleshooting) for more troubleshooting tips.

## Contributing

We welcome contributions! Please see [DEVELOPMENT.md](docs/DEVELOPMENT.md) for:

- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Citation

If you use enlace in your research, please cite:

```bibtex
@software{enlace2025,
  title = {enlace: Research Paper Data Extraction for Meta-Analysis},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/enlace}
}
```

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Report bugs at <https://github.com/yourusername/enlace/issues>
- **Discussions**: Ask questions at <https://github.com/yourusername/enlace/discussions>

## Acknowledgments

enlace is built on excellent open-source tools:

- [docling](https://github.com/DS4SD/docling) - Document conversion and table extraction
- [pydantic](https://github.com/pydantic/pydantic) - Data validation
- [typer](https://github.com/tiangolo/typer) - CLI framework
- [langchain](https://github.com/langchain-ai/langchain) - LLM integration
- [chromadb](https://github.com/chroma-core/chroma) - Vector database for RAG
