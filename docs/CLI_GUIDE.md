# CLI Guide

Command-line interface guide for **enlace** - Extract and validate research paper data.

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) for package management (recommended)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/enlace.git
cd enlace

# Install with uv (recommended)
uv pip install -e .

# Or install with pip
pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

### Verify Installation

```bash
enlace --help
```

You should see the main help message with available commands.

## Quick Start

### Extract from a Single Paper

```bash
# Basic extraction (no OCR, no augmentation)
enlace extract paper.pdf

# With output directory
enlace extract paper.pdf --output output/

# Enable OCR for scanned documents
enlace extract paper.pdf --ocr auto

# Enable semantic augmentation
enlace extract paper.pdf --augment
```

### Validate Extraction Results

```bash
# Validate with standard checks
enlace validate output/paper/extraction.json

# Use comprehensive validation
enlace validate output/paper/extraction.json --level comprehensive

# Fail on validation issues (exit code 1)
enlace validate output/paper/extraction.json --fail-on-issues
```

### Batch Processing

```bash
# Process all papers in a directory
enlace batch papers/ --output batch_output/

# With 8 parallel workers
enlace batch papers/ --workers 8

# With augmentation and validation
enlace batch papers/ --augment --validate --validation-level comprehensive
```

## Commands

### `enlace extract`

Extract tables, figures, and metadata from research papers.

**Usage:**

```bash
enlace extract [OPTIONS] INPUT_PATH
```

**Arguments:**

- `INPUT_PATH` - Path to PDF or DOCX file (required)

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `output` | Output directory for results |
| `--augment` | | `False` | Enable semantic augmentation with RAG |
| `--ocr` | | `None` | Enable OCR (auto, tesseract, easyocr) |
| `--ocr-confidence` | | `0.8` | OCR confidence threshold (0.0-1.0) |
| `--no-hybrid-ocr` | | `False` | Disable hybrid OCR fallback |
| `--format` | `-f` | `json` | Output format (json, csv, both) |
| `--config` | `-c` | `None` | Path to configuration file |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Examples:**

```bash
# Basic extraction
enlace extract paper.pdf

# With OCR (auto mode = Tesseract + EasyOCR fallback)
enlace extract scanned_paper.pdf --ocr auto

# Specify OCR backend explicitly
enlace extract paper.pdf --ocr tesseract
enlace extract paper.pdf --ocr easyocr

# Customize OCR confidence threshold
enlace extract paper.pdf --ocr auto --ocr-confidence 0.9

# Disable hybrid fallback (use only primary backend)
enlace extract paper.pdf --ocr tesseract --no-hybrid-ocr

# Full pipeline with augmentation and CSV output
enlace extract paper.pdf --augment --ocr auto --format both -o results/

# Using configuration file
enlace extract paper.pdf --config .enlace.toml
```

**Output:**

The command creates a directory structure:

```text
output/
└── paper_id/
    ├── extraction.json          # Main extraction result
    ├── extraction.csv           # CSV format (if --format csv or both)
    ├── tables/                  # Individual table files
    │   ├── table_1.json
    │   ├── table_2.json
    │   └── ...
    └── figures/                 # Extracted figures
        ├── figure_1.png
        ├── figure_2.png
        └── ...
```

**Exit Codes:**

- `0` - Success
- `1` - Error (paper not found, unsupported format, extraction failed)

### `enlace validate`

Validate extracted research data quality.

**Usage:**

```bash
enlace validate [OPTIONS] EXTRACTION_PATH
```

**Arguments:**

- `EXTRACTION_PATH` - Path to extraction.json or directory (required)

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--level` | `-l` | `standard` | Validation level (quick, standard, comprehensive) |
| `--output` | `-o` | `validation_reports` | Output directory for reports |
| `--config` | `-c` | `None` | Path to configuration file |
| `--fail-on-issues` | | `False` | Exit with error if issues found |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Validation Levels:**

1. **quick** - Fast checks (structure, completeness)
   - Schema validation
   - Required fields
   - Data completeness

2. **standard** (default) - Recommended for most uses
   - All quick checks
   - Accuracy validation
   - Missing data analysis

3. **comprehensive** - Thorough validation
   - All standard checks
   - Statistical consistency
   - OCR quality validation
   - Semantic validation (if augmentation enabled)

**Examples:**

```bash
# Validate with standard level
enlace validate output/paper/extraction.json

# Quick validation
enlace validate output/paper/extraction.json --level quick

# Comprehensive validation with custom output
enlace validate output/paper/extraction.json \
    --level comprehensive \
    --output validation/ \
    --fail-on-issues

# Validate entire directory
enlace validate output/

# Using configuration file
enlace validate output/paper/extraction.json --config .enlace.toml
```

**Output:**

```text
validation_reports/
└── paper_id_validation.json    # Validation report with issues and recommendations
```

**Console Output Example:**

```text
✓ PASSED: paper_id
  Score: 0.85
  Issues: 0
  Warnings: 2

Warnings:
  - Low OCR confidence for table 3 (0.72)
  - Missing methodology description

Recommendations:
  - Consider re-extracting table 3 with EasyOCR backend
  - Verify p-values in table 2 (possible OCR artifacts)
```

**Exit Codes:**

- `0` - Validation passed (or issues found but --fail-on-issues not set)
- `1` - Validation failed and --fail-on-issues set, or validation error

### `enlace batch`

Process multiple papers in batch with parallel processing.

**Usage:**

```bash
enlace batch [OPTIONS] INPUT_DIR
```

**Arguments:**

- `INPUT_DIR` - Directory containing PDF/DOCX papers (required)

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `batch_output` | Output directory |
| `--workers` | `-w` | `4` | Number of parallel workers |
| `--augment` | | `False` | Enable semantic augmentation |
| `--ocr` | | `None` | Enable OCR (auto, tesseract, easyocr) |
| `--validate` / `--no-validate` | | `True` | Run validation after extraction |
| `--validation-level` | | `standard` | Validation level |
| `--config` | `-c` | `None` | Path to configuration file |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Examples:**

```bash
# Process all papers with default settings
enlace batch papers/

# High-performance batch processing
enlace batch papers/ --workers 8 --output results/

# Full pipeline with augmentation and validation
enlace batch papers/ \
    --augment \
    --ocr auto \
    --validate \
    --validation-level comprehensive \
    --workers 4

# Process without validation
enlace batch papers/ --no-validate

# Using configuration file
enlace batch papers/ --config .enlace.toml
```

**Output:**

```text
batch_output/
├── paper_1/
│   ├── extraction.json
│   ├── tables/
│   └── figures/
├── paper_2/
│   ├── extraction.json
│   ├── tables/
│   └── figures/
├── ...
├── batch_summary.json          # Batch statistics
└── validation_reports/         # If --validate enabled
    ├── paper_1_validation.json
    ├── paper_2_validation.json
    └── ...
```

**Batch Summary Example:**

```json
{
  "papers_processed": 25,
  "papers_successful": 23,
  "papers_failed": 2,
  "total_tables": 147,
  "total_figures": 58,
  "avg_quality": 0.82,
  "processing_time_seconds": 324.5,
  "failed_papers": ["paper_15.pdf", "paper_22.pdf"]
}
```

**Exit Codes:**

- `0` - Success (even if some papers failed)
- `1` - Batch processing error

## Configuration

### Configuration Files

enlace supports configuration files in TOML format:

- `.enlace.toml` in current directory
- `[tool.enlace]` section in `pyproject.toml`
- Custom file via `--config` option

**Example `.enlace.toml`:**

```toml
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
ocr_confidence_threshold = 0.85
enable_augmentation = true
output_format = "both"
output_dir = "extracted_data"
max_workers = 8

# LLM configuration
llm_model = "claude-4-5-haiku"
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

[tool.enlace.validation]
level = "comprehensive"
output_dir = "validation_reports"
fail_on_issues = true
```

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

### Environment Variables

All configuration options can be set via environment variables with `ENLACE_` prefix:

```bash
export ENLACE_ENABLE_OCR=true
export ENLACE_OCR_BACKEND=auto
export ENLACE_ENABLE_AUGMENTATION=true
export ENLACE_OUTPUT_FORMAT=json
export ENLACE_LLM_MODEL=claude-4-5-haiku
export ENLACE_VALIDATION_LEVEL=comprehensive
```

### Configuration Priority

Configuration is loaded in this order (later overrides earlier):

1. **Default values** - Built-in defaults
2. **Configuration file** - `.enlace.toml` or `pyproject.toml`
3. **Environment variables** - `ENLACE_*` variables
4. **Command-line arguments** - CLI flags (highest priority)

**Example:**

```bash
# Config file sets: enable_ocr = false
# Environment sets: ENLACE_ENABLE_OCR=true
# CLI sets: --ocr auto

# Result: OCR enabled with auto backend (CLI wins)
```

## Common Workflows

### Extract and Validate Single Paper

```bash
# Extract with comprehensive settings
enlace extract paper.pdf --augment --ocr auto --output results/

# Validate with comprehensive checks
enlace validate results/paper/extraction.json \
    --level comprehensive \
    --fail-on-issues
```

### Batch Processing with Quality Control

```bash
# Process directory with validation
enlace batch papers/ \
    --output batch_results/ \
    --workers 8 \
    --augment \
    --ocr auto \
    --validate \
    --validation-level comprehensive

# Review batch summary
cat batch_results/batch_summary.json

# Check validation reports for issues
grep -l '"passed": false' batch_results/validation_reports/*.json
```

### Re-extract with Different OCR Backend

```bash
# Initial extraction with Tesseract (fast)
enlace extract paper.pdf --ocr tesseract -o results_tesseract/

# Validate and find low-confidence tables
enlace validate results_tesseract/paper/extraction.json

# Re-extract with EasyOCR (more accurate)
enlace extract paper.pdf --ocr easyocr -o results_easyocr/

# Compare results
diff results_tesseract/paper/extraction.json \
     results_easyocr/paper/extraction.json
```

### Use Configuration File for Reproducibility

```bash
# Create project configuration
cat > .enlace.toml <<EOF
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
ocr_confidence_threshold = 0.85
enable_augmentation = true
output_format = "both"
max_workers = 8
llm_model = "claude-4-5-haiku"

[tool.enlace.validation]
level = "comprehensive"
fail_on_issues = true
EOF

# All extractions will use these settings
enlace extract paper.pdf
enlace batch papers/
```

## Troubleshooting

### OCR Not Working

**Problem:** OCR is not extracting text from scanned documents.

**Solution:**

1. Ensure OCR is enabled: `--ocr auto`
2. Check docling installation includes OCR backends:

   ```bash
   uv pip install docling[easyocr,tesseract]
   ```

3. For EasyOCR, ensure PyTorch is installed:

   ```bash
   uv pip install torch torchvision
   ```

### Low Extraction Quality

**Problem:** Validation shows low quality scores or many issues.

**Solution:**

1. Try different OCR backend:

   ```bash
   enlace extract paper.pdf --ocr easyocr
   ```

2. Enable semantic augmentation for validation:

   ```bash
   enlace extract paper.pdf --augment --ocr auto
   ```

3. Check validation report for specific issues:

   ```bash
   enlace validate output/paper/extraction.json --level comprehensive -v
   ```

### Semantic Augmentation Fails

**Problem:** `--augment` flag causes errors.

**Solution:**

1. Ensure Anthropic API key is set:

   ```bash
   export ANTHROPIC_API_KEY=your_api_key
   ```

2. Check LLM model configuration:

   ```bash
   export ENLACE_LLM_MODEL=claude-4-5-haiku
   ```

3. Verify embedding model is installed:

   ```bash
   uv pip install sentence-transformers
   ```

### Batch Processing Hangs

**Problem:** Batch processing stops or hangs.

**Solution:**

1. Reduce number of workers:

   ```bash
   enlace batch papers/ --workers 2
   ```

2. Enable verbose logging to see progress:

   ```bash
   enlace batch papers/ --verbose
   ```

3. Process papers individually to identify problematic files:

   ```bash
   for f in papers/*.pdf; do
       enlace extract "$f" --output batch_output/
   done
   ```

## Getting Help

- **CLI help:** `enlace --help`
- **Command help:** `enlace extract --help`, `enlace validate --help`, etc.
- **API documentation:** See [API_GUIDE.md](API_GUIDE.md)
- **Configuration reference:** See [CONFIGURATION.md](CONFIGURATION.md)
- **Development guide:** See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Issues:** Report bugs at <https://github.com/yourusername/enlace/issues>
