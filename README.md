# enlace

**Extract and validate research paper data for meta-analysis and data harmonization**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

enlace is a Python package for extracting structured data from development economics research papers. It automatically extracts tables (regression results, summary statistics, balance tables), figures, and metadata from PDF/DOCX papers, with optional semantic augmentation for enhanced context and error detection.

### Key Features

- **Automated Table Extraction** - Regression tables, summary statistics, balance tables
- **Figure Extraction** - Extract and save figures with vision model annotations
- **Vision Model Annotations** - Local AI-powered image descriptions using Granite Vision
- **Metadata Extraction** - Title, authors, year, DOI, citations, methodology
- **OCR Support** - Hybrid OCR with Tesseract + EasyOCR fallback for scanned documents
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

```bash
# Standard validation
enlace validate output/paper/extraction.json

# Comprehensive validation with all checks
enlace validate output/paper/extraction.json --level comprehensive

# Fail on validation issues (useful for CI/CD)
enlace validate output/paper/extraction.json --fail-on-issues
```

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
- **Privacy-Preserving** - All processing happens locally, no external API calls
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

### Semantic Augmentation

Enhance extractions with context from paper text using RAG:

- **Variable Context** - Definitions, units, data sources
- **Treatment Context** - Intervention details, implementation
- **Sample Context** - Population characteristics, selection criteria
- **Methods Context** - Estimation techniques, standard error types
- **Cross-Validation** - Detects OCR errors by comparing to paper text
- **Confidence Scores** - Quality metrics for extracted information

**Requirement:** Semantic augmentation requires `ANTHROPIC_API_KEY` environment variable.

```bash
# Set API key
export ANTHROPIC_API_KEY=your_api_key

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
```

### Environment Variables

All options can be set via environment variables with `ENLACE_` prefix:

```bash
export ENLACE_ENABLE_OCR=true
export ENLACE_OCR_BACKEND=auto
export ENLACE_ENABLE_AUGMENTATION=true
export ENLACE_EXTRACT_FIGURES=true
export ENLACE_DESCRIBE_PICTURES=true  # Enable vision model annotations
export ENLACE_OUTPUT_FORMAT=both
export ENLACE_MAX_WORKERS=8
export ANTHROPIC_API_KEY=your_api_key  # Required for augmentation
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

# 3. Export to CSV for analysis
# (CSV files are in extractions/*/tables/)
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
