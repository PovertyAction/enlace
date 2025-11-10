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
```

### Verify Installation

```bash
uv run enlace --help
```

You should see the main help message with available commands.

## Quick Start

### Extract from a Single Paper

```bash
# Basic extraction (no OCR, no augmentation)
uv run enlace extract paper.pdf

# With output directory
uv run enlace extract paper.pdf --output output/

# Enable OCR for scanned documents
uv run enlace extract paper.pdf --ocr auto

# Enable semantic augmentation
uv run enlace extract paper.pdf --augment
```

### Validate Extraction Results

```bash
# Validate with standard checks
uv run enlace validate output/paper/extraction.json

# Use comprehensive validation
uv run enlace validate output/paper/extraction.json --level comprehensive

# Fail on validation issues (exit code 1)
uv run enlace validate output/paper/extraction.json --fail-on-issues
```

### Batch Processing

```bash
# Process all papers in a directory
uv run enlace batch papers/ --output batch_output/

# With 8 parallel workers
uv run enlace batch papers/ --workers 8

# With augmentation and validation
uv run enlace batch papers/ --augment --validate --validation-level comprehensive
```

## Commands

### `enlace extract`

Extract tables, figures, and metadata from research papers.

**Usage:**

```bash
uv run enlace extract [OPTIONS] INPUT_PATH
```

**Arguments:**

- `INPUT_PATH` - Path to PDF or DOCX file (required)

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `output` | Output directory for results |
| `--augment` | | `False` | Enable semantic augmentation with RAG |
| `--vlm` | | `False` | Enable VLM fallback for low-quality tables |
| `--vlm-framework` | | `auto` | VLM framework (auto, transformers, mlx) |
| `--claude-cleanup` | | `False` | Enable Claude cleanup pass (requires API key) |
| `--ocr` | | `None` | Enable OCR (auto, tesseract, easyocr) |
| `--ocr-confidence` | | `0.8` | OCR confidence threshold (0.0-1.0) |
| `--no-hybrid-ocr` | | `False` | Disable hybrid OCR fallback |
| `--format` | `-f` | `json` | Output format (json, csv, both) |
| `--config` | `-c` | `None` | Path to configuration file |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Examples:**

```bash
# Basic extraction
uv run enlace extract paper.pdf

# With OCR (auto mode = Tesseract + EasyOCR fallback)
uv run enlace extract scanned_paper.pdf --ocr auto

# Specify OCR backend explicitly
uv run enlace extract paper.pdf --ocr tesseract
uv run enlace extract paper.pdf --ocr easyocr

# Customize OCR confidence threshold
uv run enlace extract paper.pdf --ocr auto --ocr-confidence 0.9

# Disable hybrid fallback (use only primary backend)
uv run enlace extract paper.pdf --ocr tesseract --no-hybrid-ocr

# Full pipeline with augmentation and CSV output
uv run enlace extract paper.pdf --augment --ocr auto --format both -o results/

# Enable VLM fallback for complex tables (Granite-Docling)
uv run enlace extract paper.pdf --vlm --ocr auto

# VLM with specific framework (faster on macOS)
uv run enlace extract paper.pdf --vlm --vlm-framework mlx

# Two-pass VLM: Granite + Claude cleanup (highest accuracy)
uv run enlace extract paper.pdf --vlm --claude-cleanup --ocr auto

# Using configuration file
uv run enlace extract paper.pdf --config .enlace.toml
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
uv run enlace validate [OPTIONS] EXTRACTION_PATH
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
uv run enlace validate output/paper/extraction.json

# Quick validation
uv run enlace validate output/paper/extraction.json --level quick

# Comprehensive validation with custom output
uv run enlace validate output/paper/extraction.json \
    --level comprehensive \
    --output validation/ \
    --fail-on-issues

# Validate entire directory
uv run enlace validate output/

# Using configuration file
uv run enlace validate output/paper/extraction.json --config .enlace.toml
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
uv run enlace batch [OPTIONS] INPUT_DIR
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
uv run enlace batch papers/

# High-performance batch processing
uv run enlace batch papers/ --workers 8 --output results/

# Full pipeline with augmentation and validation
uv run enlace batch papers/ \
    --augment \
    --ocr auto \
    --validate \
    --validation-level comprehensive \
    --workers 4

# Process without validation
uv run enlace batch papers/ --no-validate

# Using configuration file
uv run enlace batch papers/ --config .enlace.toml
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

---

## Vision-Language Model (VLM) Integration

### Overview

enlace supports **two-pass VLM extraction** for improved accuracy on complex tables:

1. **Pass 1: Granite-Docling-258M** (Local, Fast)
   - IBM's 258M parameter VLM optimized for document understanding
   - 97% accuracy on table structure recognition (TEDS benchmark)
   - Runs locally (no API costs)
   - Inference: 6-10s (MLX on macOS) or 80-120s (Transformers)

2. **Pass 2: Claude 3.5 Sonnet** (Optional, Validation)
   - Final validation and cleanup using Claude's vision capabilities
   - Cross-validates with paper text
   - Only triggered for low-quality Granite extractions
   - Cost: ~$0.01-0.05 per table

### When VLM is Triggered

VLM fallback activates automatically when **any** condition is met:

- **>30% missing standard errors** (default threshold)
- **>20% missing coefficients** (default threshold)
- **OCR confidence <70%** (default threshold)

### VLM Usage Examples

```bash
# Enable Granite-Docling VLM fallback
uv run enlace extract paper.pdf --vlm --ocr auto

# Specify VLM framework (auto-detects best option)
uv run enlace extract paper.pdf --vlm --vlm-framework auto

# Use MLX framework on macOS (10-20x faster)
uv run enlace extract paper.pdf --vlm --vlm-framework mlx

# Use Transformers framework (cross-platform)
uv run enlace extract paper.pdf --vlm --vlm-framework transformers

# Two-pass VLM: Granite + Claude cleanup
export ENLACE_CLAUDE_API_KEY=sk-ant-...
uv run enlace extract paper.pdf --vlm --claude-cleanup --ocr auto

# Configure VLM thresholds
export ENLACE_VLM_NULL_SE_THRESHOLD=0.25  # Trigger if >25% SEs missing
export ENLACE_VLM_NULL_COEF_THRESHOLD=0.15  # Trigger if >15% coeffs missing
uv run enlace extract paper.pdf --vlm
```

### VLM Configuration

#### Environment Variables

```bash
# Enable VLM
export ENLACE_ENABLE_VLM=true
export ENLACE_VLM_FRAMEWORK=auto  # auto, transformers, or mlx

# Quality triggers
export ENLACE_VLM_NULL_SE_THRESHOLD=0.30  # Default: 30%
export ENLACE_VLM_NULL_COEF_THRESHOLD=0.20  # Default: 20%
export ENLACE_VLM_CONFIDENCE_THRESHOLD=0.70  # Default: 70%

# Claude cleanup (optional)
export ENLACE_ENABLE_CLAUDE_CLEANUP=true
export ENLACE_CLAUDE_API_KEY=sk-ant-...
export ENLACE_CLAUDE_MODEL=claude-3-5-sonnet-20241022
export ENLACE_CLAUDE_NULL_SE_THRESHOLD=0.15  # Trigger if >15% still missing
export ENLACE_CLAUDE_MAX_COST_PER_TABLE=0.05  # Budget limit ($)
```

#### Configuration File

```toml
[tool.enlace]
# VLM settings
enable_vlm = true
vlm_framework = "auto"
vlm_null_se_threshold = 0.30
vlm_null_coef_threshold = 0.20
vlm_confidence_threshold = 0.70

# Claude cleanup (optional)
enable_claude_cleanup = false
claude_api_key = "sk-ant-..."
claude_null_se_threshold = 0.15
claude_max_cost_per_table = 0.05
```

### VLM Performance

#### Expected Accuracy Improvements

| Metric | Traditional | + Granite | + Claude | Target |
|--------|------------|-----------|----------|--------|
| **Standard Errors** | 6.4% | ~70% | **85-90%** | 85%+ |
| **Coefficients** | 88% | 92% | **95%+** | 95%+ |
| **Dependent Variables** | 73% | 85% | **90%+** | 90%+ |

#### Inference Times

| Framework | Platform | Time/Table | GPU Required |
|-----------|----------|------------|--------------|
| MLX | macOS M1/M2/M3 | 6-10s | MPS (Apple) |
| Transformers | macOS | 100-120s | Optional (CUDA) |
| Transformers | Linux/Windows | 80-100s | Optional (CUDA) |

#### Cost Analysis

| Strategy | Time | Cost | Use Case |
|----------|------|------|----------|
| Traditional only | 5-10s | $0 | High-quality PDFs |
| + Granite | 15-110s | $0 | Complex tables, scanned docs |
| + Claude cleanup | 17-115s | $0.01-0.05 | Critical extractions |

### VLM Troubleshooting

#### VLM Dependencies Missing

```bash
# VLM dependencies already included in enlace
# Verify installation:
uv pip install "docling[vlm]>=2.60.1"
```

#### MLX Not Available

MLX only works on macOS with Apple Silicon. For other platforms:

```bash
export ENLACE_VLM_FRAMEWORK=transformers
uv run enlace extract paper.pdf --vlm
```

#### Claude API Key Error

```bash
# Set API key
export ENLACE_CLAUDE_API_KEY=sk-ant-api03-...

# Verify it works
uv run enlace extract paper.pdf --vlm --claude-cleanup
```

### VLM Best Practices

1. **Start with Granite only**: Test VLM without Claude cleanup first
2. **Use MLX on macOS**: 10-20x faster than Transformers
3. **Enable for scanned documents**: VLM excels at complex layouts
4. **Monitor costs**: Claude cleanup adds $0.01-0.05 per table
5. **Adjust thresholds**: Lower thresholds = more VLM usage, higher accuracy

For detailed VLM architecture and implementation, see [VLM_INTEGRATION.md](VLM_INTEGRATION.md).

---

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
uv run enlace extract paper.pdf --augment --ocr auto --output results/

# Validate with comprehensive checks
uv run enlace validate results/paper/extraction.json \
    --level comprehensive \
    --fail-on-issues
```

### Batch Processing with Quality Control

```bash
# Process directory with validation
uv run enlace batch papers/ \
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
uv run enlace extract paper.pdf --ocr tesseract -o results_tesseract/

# Validate and find low-confidence tables
uv run enlace validate results_tesseract/paper/extraction.json

# Re-extract with EasyOCR (more accurate)
uv run enlace extract paper.pdf --ocr easyocr -o results_easyocr/

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
uv run enlace extract paper.pdf
uv run enlace batch papers/
```

## Troubleshooting

### OCR Not Working

**Problem:** OCR is not extracting text from scanned documents.

**Solution:**

1. Ensure OCR is enabled: `--ocr auto`
2. Check docling installation includes OCR backends:

   ```bash
   uv add docling[easyocr,tesseract]
   ```

3. For EasyOCR, ensure PyTorch is installed:

   ```bash
   uv add torch torchvision
   ```

### Low Extraction Quality

**Problem:** Validation shows low quality scores or many issues.

**Solution:**

1. Try different OCR backend:

   ```bash
   uv run enlace extract paper.pdf --ocr easyocr
   ```

2. Enable semantic augmentation for validation:

   ```bash
   uv run enlace extract paper.pdf --augment --ocr auto
   ```

3. Check validation report for specific issues:

   ```bash
   uv run enlace validate output/paper/extraction.json --level comprehensive -v
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
   uv add sentence-transformers
   ```

### Batch Processing Hangs

**Problem:** Batch processing stops or hangs.

**Solution:**

1. Reduce number of workers:

   ```bash
   uv run enlace batch papers/ --workers 2
   ```

2. Enable verbose logging to see progress:

   ```bash
   uv run enlace batch papers/ --verbose
   ```

3. Process papers individually to identify problematic files:

   ```bash
   for f in papers/*.pdf; do
       uv run enlace extract "$f" --output batch_output/
   done
   ```

## Getting Help

- **CLI help:** `uv run enlace --help`
- **Command help:** `uv run enlace extract --help`, `uv run enlace validate --help`, etc.
- **API documentation:** See [API_GUIDE.md](API_GUIDE.md)
- **Configuration reference:** See [CONFIGURATION.md](CONFIGURATION.md)
- **Development guide:** See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Issues:** Report bugs at <https://github.com/yourusername/enlace/issues>
