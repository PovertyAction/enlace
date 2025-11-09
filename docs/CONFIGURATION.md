# Configuration Guide

Complete configuration reference for **enlace** - research paper extraction and validation.

## Configuration Methods

enlace supports multiple configuration methods with clear priority ordering.

### Priority Order

Configuration is loaded in this order (later overrides earlier):

1. **Default values** - Built-in defaults in Pydantic models
2. **Configuration file** - `.enlace.toml` or `[tool.enlace]` in `pyproject.toml`
3. **Environment variables** - Prefixed with `ENLACE_`
4. **Command-line arguments** - CLI flags (highest priority)

### Example Priority Resolution

```bash
# Config file sets: enable_ocr = false
# Environment sets: ENLACE_ENABLE_OCR=true
# CLI sets: --ocr auto

# Result: enable_ocr = true, ocr_backend = "auto" (CLI wins)
```

## Configuration Files

### `.enlace.toml`

Create `.enlace.toml` in your project directory:

```toml
[tool.enlace]
# Document processing
enable_ocr = true
ocr_backend = "auto"
ocr_confidence_threshold = 0.85
hybrid_ocr_enabled = true
extract_figures = true
extract_tables = true
extract_metadata = true

# Semantic augmentation
enable_augmentation = true
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
llm_model = "claude-4-5-haiku"

# Output
output_format = "both"
output_dir = "extracted_data"

# Performance
batch_size = 10
max_workers = 8

# Logging
verbose = false
log_file = "enlace.log"

# Validation configuration
[tool.enlace.validation]
level = "comprehensive"
output_dir = "validation_reports"
fail_on_issues = true

# Custom validation levels
[tool.enlace.validation.levels]
quick = ["structure", "completeness"]
standard = ["structure", "completeness", "accuracy", "missing_data"]
comprehensive = [
    "structure",
    "completeness",
    "accuracy",
    "statistical_consistency",
    "missing_data",
    "ocr_quality",
    "semantic_validation"
]
custom = ["structure", "accuracy", "statistical_consistency"]
```

### `pyproject.toml`

Alternatively, add configuration to `pyproject.toml`:

```toml
[tool.enlace]
enable_ocr = true
enable_augmentation = false
output_format = "json"
max_workers = 4

[tool.enlace.validation]
level = "standard"
fail_on_issues = false
```

### Using Configuration Files

```bash
# Automatically detected in current directory
enlace extract paper.pdf

# Specify custom config file
enlace extract paper.pdf --config custom.toml

# Override config file settings with CLI args
enlace extract paper.pdf --config .enlace.toml --ocr easyocr
```

## Environment Variables

All configuration options can be set via environment variables with `ENLACE_` prefix.

### Extraction Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_ENABLE_OCR` | bool | `false` | Enable OCR for scanned documents |
| `ENLACE_OCR_BACKEND` | str | `"auto"` | OCR backend (auto, tesseract, easyocr) |
| `ENLACE_OCR_CONFIDENCE_THRESHOLD` | float | `0.8` | OCR confidence threshold (0.0-1.0) |
| `ENLACE_HYBRID_OCR_ENABLED` | bool | `true` | Enable hybrid OCR fallback |
| `ENLACE_OCR_LANGUAGES` | str | `"eng"` | OCR languages (comma-separated) |
| `ENLACE_OCR_USE_GPU` | bool | `false` | Use GPU for OCR (EasyOCR only) |
| `ENLACE_ENABLE_AUGMENTATION` | bool | `false` | Enable semantic augmentation |
| `ENLACE_EXTRACT_FIGURES` | bool | `true` | Extract figures from papers |
| `ENLACE_EXTRACT_TABLES` | bool | `true` | Extract tables from papers |
| `ENLACE_EXTRACT_METADATA` | bool | `true` | Extract metadata from papers |

### Model Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_EMBEDDING_MODEL` | str | `"sentence-transformers/all-MiniLM-L6-v2"` | HuggingFace embedding model |
| `ENLACE_LLM_MODEL` | str | `"claude-4-5-haiku"` | LLM model for semantic extraction |
| `ANTHROPIC_API_KEY` | str | - | Anthropic API key (required for augmentation) |

### Output Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_OUTPUT_FORMAT` | str | `"json"` | Output format (json, csv, both) |
| `ENLACE_OUTPUT_DIR` | str | `"output"` | Output directory path |

### Performance Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_BATCH_SIZE` | int | `10` | Batch size for processing |
| `ENLACE_MAX_WORKERS` | int | `4` | Maximum parallel workers |

### Logging Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_VERBOSE` | bool | `false` | Enable verbose logging |
| `ENLACE_LOG_FILE` | str | - | Optional log file path |

### Validation Settings

Validation environment variables use `ENLACE_VALIDATION_` prefix:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENLACE_VALIDATION_LEVEL` | str | `"standard"` | Validation level name |
| `ENLACE_VALIDATION_OUTPUT_DIR` | str | `"validation_reports"` | Validation output directory |
| `ENLACE_VALIDATION_FAIL_ON_ISSUES` | bool | `false` | Exit with error if issues found |
| `ENLACE_VALIDATION_VERBOSE` | bool | `false` | Enable verbose validation logging |

### Example Usage

```bash
# Set environment variables
export ENLACE_ENABLE_OCR=true
export ENLACE_OCR_BACKEND=auto
export ENLACE_ENABLE_AUGMENTATION=true
export ENLACE_LLM_MODEL=claude-4-5-haiku
export ANTHROPIC_API_KEY=your_api_key
export ENLACE_OUTPUT_FORMAT=both
export ENLACE_MAX_WORKERS=8
export ENLACE_VALIDATION_LEVEL=comprehensive

# Run extraction (uses environment variables)
enlace extract paper.pdf

# Override environment variable with CLI
enlace extract paper.pdf --ocr easyocr
```

## Configuration Options Reference

### Extraction Configuration

#### Document Processing

**`enable_ocr`** (bool, default: `false`)

- Enable OCR for scanned documents
- Required for papers with image-based text
- Increases processing time significantly

**`ocr_backend`** (str, default: `"auto"`)

- OCR backend selection
- Options: `"auto"`, `"tesseract"`, `"easyocr"`
- `"auto"` uses Tesseract with EasyOCR fallback

**`ocr_confidence_threshold`** (float, default: `0.8`)

- Minimum OCR confidence threshold (0.0-1.0)
- Cells below threshold trigger hybrid fallback
- Higher values = stricter quality requirements

**`hybrid_ocr_enabled`** (bool, default: `true`)

- Enable automatic OCR backend fallback
- Switches to EasyOCR for low-confidence extractions
- Disabled when using specific backend

**`ocr_languages`** (str, default: `"eng"`)

- OCR language codes (comma-separated)
- Examples: `"eng"`, `"eng,fra"`, `"eng,spa,por"`
- See Tesseract/EasyOCR docs for language codes

**`ocr_use_gpu`** (bool, default: `false`)

- Use GPU acceleration for OCR
- Only applies to EasyOCR backend
- Requires CUDA-compatible GPU and PyTorch with CUDA

**`extract_figures`** (bool, default: `true`)

- Extract figures and images from papers
- Saves figures to output directory

**`extract_tables`** (bool, default: `true`)

- Extract tables from papers
- Includes regression, summary stats, and balance tables

**`extract_metadata`** (bool, default: `true`)

- Extract metadata from papers
- Includes title, authors, year, DOI, citations

#### Semantic Augmentation

**`enable_augmentation`** (bool, default: `false`)

- Enable semantic augmentation with RAG
- Adds context from paper text to tables
- Requires `ANTHROPIC_API_KEY` environment variable

**`embedding_model`** (str, default: `"sentence-transformers/all-MiniLM-L6-v2"`)

- HuggingFace embedding model for semantic search
- Alternative: `"minishlab/potion-base-8M"` (faster, smaller)
- Must be compatible with sentence-transformers

**`llm_model`** (str, default: `"claude-4-5-haiku"`)

- LLM model for context extraction
- Supported: Claude models from Anthropic
- Use stable names without version dates

#### Output

**`output_format`** (str, default: `"json"`)

- Output file format
- Options: `"json"`, `"csv"`, `"both"`
- JSON preserves full structure, CSV is tabular

**`output_dir`** (Path, default: `Path("output")`)

- Directory for output files
- Created automatically if doesn't exist
- Each paper gets subdirectory with paper_id

#### Performance

**`batch_size`** (int, default: `10`)

- Batch size for processing operations
- Affects memory usage
- Higher values = faster but more memory

**`max_workers`** (int, default: `4`)

- Maximum parallel workers for batch processing
- Set based on CPU cores and memory
- Too high can cause out-of-memory errors

#### Logging

**`verbose`** (bool, default: `false`)

- Enable verbose logging output
- Shows DEBUG-level messages
- Useful for troubleshooting

**`log_file`** (Path | None, default: `None`)

- Optional log file path
- Logs written to both console and file
- Useful for debugging batch processing

### Validation Configuration

#### Validation Levels

**`level`** (str, default: `"standard"`)

- Validation level name
- Built-in levels: `"quick"`, `"standard"`, `"comprehensive"`
- Can define custom levels in config file

**`output_dir`** (Path, default: `Path("validation_reports")`)

- Directory for validation reports
- Reports saved as JSON files
- One report per validated extraction

**`fail_on_issues`** (bool, default: `false`)

- Exit with error code 1 if validation fails
- Useful for CI/CD pipelines
- Only affects CLI, not programmatic usage

**`verbose`** (bool, default: `false`)

- Enable verbose validation logging
- Shows detailed check progress
- Useful for debugging validation failures

#### Custom Validation Levels

Define custom validation levels in configuration file:

```toml
[tool.enlace.validation.levels]
# Minimal checks (fastest)
minimal = ["structure"]

# Regression-focused
regression_only = [
    "structure",
    "accuracy",
    "statistical_consistency"
]

# OCR quality checks
ocr_focused = [
    "structure",
    "ocr_quality",
    "accuracy"
]

# Full validation (slowest, most thorough)
full = [
    "structure",
    "completeness",
    "accuracy",
    "statistical_consistency",
    "missing_data",
    "ocr_quality",
    "semantic_validation"
]
```

Available validation checks:

- **`structure`** - Schema and required fields validation
- **`completeness`** - Data completeness checks (metadata, content)
- **`accuracy`** - Table quality and coefficient data accuracy
- **`statistical_consistency`** - T-stats, p-values, confidence intervals
- **`missing_data`** - Missing data patterns in tables
- **`ocr_quality`** - OCR confidence and numeric validation
- **`semantic_validation`** - Cross-validation with paper text (requires augmentation)

## Complete Configuration Examples

### Minimal Configuration

```toml
# .enlace.toml - Minimal setup for digital PDFs
[tool.enlace]
output_dir = "results"
max_workers = 4

[tool.enlace.validation]
level = "quick"
```

### Standard Research Workflow

```toml
# .enlace.toml - Balanced performance and quality
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
output_format = "both"
output_dir = "extracted_data"
max_workers = 8

[tool.enlace.validation]
level = "standard"
output_dir = "validation_reports"
fail_on_issues = true
```

### High-Quality Meta-Analysis

```toml
# .enlace.toml - Maximum quality for meta-analysis
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
ocr_confidence_threshold = 0.9
hybrid_ocr_enabled = true
enable_augmentation = true
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
llm_model = "claude-4-5-haiku"
output_format = "both"
output_dir = "meta_analysis_data"
max_workers = 4
verbose = true
log_file = "enlace.log"

[tool.enlace.validation]
level = "comprehensive"
output_dir = "validation_reports"
fail_on_issues = true
verbose = true
```

### Fast Batch Processing

```toml
# .enlace.toml - Speed-optimized for large batches
[tool.enlace]
enable_ocr = false  # Disable OCR for digital PDFs
enable_augmentation = false
extract_figures = false
output_format = "json"
output_dir = "batch_output"
batch_size = 20
max_workers = 16

[tool.enlace.validation]
level = "quick"
fail_on_issues = false
```

### OCR-Heavy Scanned Documents

```toml
# .enlace.toml - Optimized for scanned papers
[tool.enlace]
enable_ocr = true
ocr_backend = "easyocr"  # More accurate for scanned docs
ocr_confidence_threshold = 0.85
ocr_use_gpu = true  # Faster with GPU
hybrid_ocr_enabled = false  # Already using best backend
output_format = "both"
max_workers = 2  # OCR is memory-intensive

[tool.enlace.validation]
level = "comprehensive"
fail_on_issues = true

[tool.enlace.validation.levels]
ocr_focused = [
    "structure",
    "completeness",
    "accuracy",
    "ocr_quality",
    "missing_data"
]
```

## Programmatic Configuration

### Python API

```python
from pathlib import Path
from enlace.core.config import ExtractionConfig, ValidationConfig

# Create configuration programmatically
extraction_config = ExtractionConfig(
    enable_ocr=True,
    ocr_backend="auto",
    enable_augmentation=True,
    output_dir=Path("results"),
    max_workers=8,
    verbose=True
)

validation_config = ValidationConfig(
    level="comprehensive",
    fail_on_issues=True,
    levels={
        "custom": ["structure", "accuracy", "statistical_consistency"]
    }
)

# Load from file with overrides
config = ExtractionConfig.load_config(
    config_file=Path(".enlace.toml"),
    enable_ocr=True,  # Override file setting
    ocr_backend="easyocr"
)
```

### Environment + File

```python
# Load from file, then override with environment variables
# Environment: ENLACE_ENABLE_OCR=true
# File: enable_ocr = false

config = ExtractionConfig.load_config(
    config_file=Path(".enlace.toml")
)
# Result: enable_ocr = true (environment wins)

# CLI args have highest priority
config = ExtractionConfig.load_config(
    config_file=Path(".enlace.toml"),
    enable_ocr=False  # Overrides both file and environment
)
# Result: enable_ocr = false (CLI wins)
```

## Configuration Validation

enlace validates configuration at load time:

```python
from enlace.core.config import ExtractionConfig
from enlace.exceptions import ConfigError

try:
    config = ExtractionConfig(
        ocr_confidence_threshold=1.5  # Invalid: must be 0.0-1.0
    )
except ConfigError as e:
    print(f"Invalid configuration: {e}")
```

Common validation errors:

- Invalid validation level name
- OCR confidence threshold out of range (0.0-1.0)
- Invalid OCR backend name
- Invalid output format
- Missing required environment variables (e.g., ANTHROPIC_API_KEY for augmentation)

## Best Practices

### 1. Use Configuration Files for Reproducibility

Store project settings in `.enlace.toml` and commit to version control:

```toml
[tool.enlace]
enable_ocr = true
ocr_backend = "auto"
enable_augmentation = true
output_format = "both"

[tool.enlace.validation]
level = "comprehensive"
```

### 2. Use Environment Variables for Secrets

Never commit API keys to config files:

```bash
# .env file (gitignored)
ANTHROPIC_API_KEY=your_api_key_here
```

### 3. Use CLI Args for One-Off Changes

Override config for specific extractions:

```bash
# Project uses Tesseract by default
# Override for specific scanned paper
enlace extract scanned_paper.pdf --ocr easyocr
```

### 4. Validate Configuration Changes

Test configuration changes before batch processing:

```bash
# Test on single paper first
enlace extract test_paper.pdf --config new_config.toml

# If successful, run batch
enlace batch papers/ --config new_config.toml
```

### 5. Document Custom Validation Levels

Add comments to explain custom validation levels:

```toml
[tool.enlace.validation.levels]
# Quick checks for initial screening
screening = ["structure", "completeness"]

# Full checks for meta-analysis inclusion
meta_analysis = [
    "structure",
    "completeness",
    "accuracy",
    "statistical_consistency",
    "missing_data",
    "semantic_validation"
]
```

## See Also

- [CLI Guide](CLI_GUIDE.md) - Command-line usage examples
- [API Guide](API_GUIDE.md) - Python API documentation
- [Development Guide](DEVELOPMENT.md) - Development setup and testing
