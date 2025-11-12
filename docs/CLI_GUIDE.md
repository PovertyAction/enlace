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
# Basic extraction (Camelot-only, no OCR, no augmentation)
uv run enlace extract paper.pdf

# With output directory and CSV format
uv run enlace extract paper.pdf --output output/ --format csv

# Enable OCR for scanned documents
uv run enlace extract paper.pdf --ocr auto

# Enable docling extraction with reconciliation (dual extraction mode)
uv run enlace extract paper.pdf --use-docling

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
| `--use-camelot / --no-camelot` | | `True` | Enable Camelot table extraction |
| `--use-docling` | | `False` | Enable docling table extraction and reconciliation with Camelot |
| `--camelot-fallback-only / --camelot-always` | | `True` | Only use Camelot when docling quality is low (only applies with --use-docling) |
| `--reconciliation-strategy` | | `camelot_primary` | Table reconciliation strategy (camelot_primary, confidence_based, prefer_camelot, prefer_docling) |
| `--augment` | | `False` | Enable semantic augmentation with RAG (works with any extraction mode) |
| `--vlm` | | `False` | Enable VLM fallback for low-quality tables (requires --use-docling) |
| `--vlm-framework` | | `auto` | VLM framework (auto, transformers, mlx) |
| `--claude-cleanup` | | `False` | Enable Claude cleanup pass (requires API key) |
| `--ocr` | | `None` | Enable OCR (auto, tesseract, easyocr) - enhances PDF quality for all extraction modes |
| `--ocr-confidence` | | `0.8` | OCR confidence threshold (0.0-1.0) |
| `--no-hybrid-ocr` | | `False` | Disable hybrid OCR fallback |
| `--format` | `-f` | `json` | Output format (json, csv, both) |
| `--config` | `-c` | `None` | Path to configuration file |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Examples:**

```bash
# Basic extraction (Camelot-only by default)
uv run enlace extract paper.pdf

# With OCR (auto mode = Tesseract + EasyOCR fallback)
uv run enlace extract scanned_paper.pdf --ocr auto

# CSV output format (Camelot-only)
uv run enlace extract paper.pdf --format csv -o results/

# Disable Camelot, docling-only extraction
uv run enlace extract paper.pdf --no-camelot --use-docling

# Enable docling extraction with reconciliation (dual extraction mode)
uv run enlace extract paper.pdf --use-docling

# Dual extraction with camelot_primary reconciliation (default strategy)
uv run enlace extract paper.pdf --use-docling --reconciliation-strategy camelot_primary

# Specify OCR backend explicitly
uv run enlace extract paper.pdf --ocr tesseract
uv run enlace extract paper.pdf --ocr easyocr

# Customize OCR confidence threshold
uv run enlace extract paper.pdf --ocr auto --ocr-confidence 0.9

# Disable hybrid fallback (use only primary backend)
uv run enlace extract paper.pdf --ocr tesseract --no-hybrid-ocr

# Full pipeline with augmentation and CSV output (Camelot-only)
uv run enlace extract paper.pdf --augment --ocr auto --format both -o results/

# Enable VLM fallback for complex tables (requires --use-docling)
uv run enlace extract paper.pdf --use-docling --vlm --ocr auto

# VLM with specific framework (faster on macOS)
uv run enlace extract paper.pdf --use-docling --vlm --vlm-framework mlx

# Two-pass VLM: Granite + Claude cleanup (highest accuracy, requires --use-docling)
uv run enlace extract paper.pdf --use-docling --vlm --claude-cleanup --ocr auto

# Using configuration file
uv run enlace extract paper.pdf --config .enlace.toml
```

**Output:**

The command creates a directory structure depending on the extraction mode:

**Camelot-only mode (default):**

```text
output/
└── paper_id/
    ├── extraction.json          # Main extraction result with figure annotations
    ├── extraction.csv           # CSV format (if --format csv or both)
    ├── paper_id.md              # Markdown with vision model annotations
    ├── tables/
    │   └── camelot/             # Camelot-extracted tables
    │       ├── table_1.csv      # or .json depending on --format
    │       ├── table_2.csv
    │       └── ...
    └── figures/                 # Extracted figures (referenced in markdown)
        ├── figure_1.png
        ├── figure_2.png
        └── ...
```

**Dual extraction mode (with --use-docling):**

```text
output/
└── paper_id/
    ├── extraction.json          # Main extraction result
    ├── paper_id.md              # Markdown
    ├── tables/
    │   ├── docling/             # Original docling extractions
    │   │   ├── table_1.json
    │   │   └── ...
    │   ├── camelot/             # Original Camelot extractions
    │   │   ├── table_1.csv
    │   │   └── ...
    │   └── reconciled/          # Final reconciled tables
    │       ├── table_1.json     # Best-of-both merged results
    │       └── ...
    ├── reconciliation_report.json  # Metadata about merging
    └── figures/
        └── ...
```

**Note:** Figure annotations can optionally be generated using Granite Vision (local AI model) by setting `ENLACE_DESCRIBE_PICTURES=true`. When enabled, annotations are saved in both:

- **Markdown**: Below each image reference as `VISION MODEL ANNOTATION: [description]`
- **JSON**: In `extraction.json` under each figure's `annotation` field

**Flag Compatibility:**

The following table shows which enhancement flags work with each extraction mode:

| Flag | Camelot-only | Dual Extraction (--use-docling) | Purpose |
|------|--------------|--------------------------------|---------|
| `--augment` | ✅ Yes | ✅ Yes | Adds semantic context to any extracted tables using RAG |
| `--ocr auto` | ✅ Yes | ✅ Yes | Improves PDF text quality before table extraction |
| `--vlm` | ❌ No | ✅ Yes | Vision-language model for complex table layouts (docling-specific) |

**Recommended Combinations:**

```bash
# Best quality Camelot-only extraction
uv run enlace extract paper.pdf --ocr auto --augment --format csv

# Maximum quality with all enhancements (dual extraction)
uv run enlace extract paper.pdf --use-docling --vlm --ocr auto --augment --format both
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
| `--output` | `-o` | Auto-detected | Output directory (defaults to extraction parent directory) |
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
output/
└── paper_id/
    ├── extraction.json         # Original extraction
    └── validation.json         # Validation report with issues and recommendations
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

### `enlace summarize`

Generate LLM-based research summaries from extraction results.

**Usage:**

```bash
uv run enlace summarize [OPTIONS] EXTRACTION_PATH
```

**Arguments:**

- `EXTRACTION_PATH` - Path to extraction.json or directory containing it (required)

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | Same as extraction | Output directory for summary files |
| `--validation` | | Auto-detected | Path to validation.json (optional) |
| `--pdf` | | `None` | Path to original PDF for enhanced analysis |
| `--model` | | `claude-3-5-haiku-20241022` | LLM model for summarization |
| `--level` | | `standard` | Detail level (brief, standard, detailed) |
| `--format` | | `json` | Output format (json, markdown, both) |
| `--web-search` | | `False` | Enhance summary with web search |
| `--config` | `-c` | `None` | Path to configuration file |
| `--verbose` | `-v` | `False` | Enable verbose output |

**Summary Detail Levels:**

1. **brief** - Concise summary
   - Title and overview only
   - Key findings (top 3)
   - Basic metadata

2. **standard** (default) - Balanced detail
   - All brief content
   - Research question and methodology
   - Treatment and sample information
   - Policy implications
   - Quality assessment

3. **detailed** - Comprehensive summary
   - All standard content
   - Table-by-table summaries
   - Detailed validation issues
   - Statistical methods
   - Data source information

**Examples:**

```bash
# Basic usage (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=your_api_key
uv run enlace summarize output/paper/extraction.json

# With auto-detected validation
uv run enlace summarize output/paper/

# Custom model and detail level
uv run enlace summarize output/paper/ \
    --model claude-3-5-sonnet-20241022 \
    --level detailed

# Generate markdown format
uv run enlace summarize output/paper/ --format markdown

# Both JSON and markdown
uv run enlace summarize output/paper/ --format both -o summaries/

# Enhanced with web search (slower, requires internet)
uv run enlace summarize output/paper/ --web-search

# With validation and PDF for comprehensive analysis
uv run enlace summarize output/paper/ \
    --validation output/paper/validation.json \
    --pdf papers/paper.pdf \
    --level detailed \
    --format both
```

**Output:**

```text
output/
└── paper_id/
    ├── extraction.json         # Original extraction
    ├── validation.json         # Validation report (if exists)
    ├── summary.json            # Generated summary (JSON)
    └── summary.md              # Generated summary (Markdown, if --format markdown/both)
```

**Example JSON Output:**

```json
{
  "paper_id": "smith_2020_rct",
  "title": "Job Referral Networks Disadvantage Women in Labor Markets",
  "overview": "Field experiment in Malawi examining how job referral networks systematically disadvantage qualified women through gender-biased referral patterns.",
  "research_question": "Do job referral networks inherently disadvantage women in the labor market?",
  "methodology": "Randomized field experiment with 767 job applicants. Participants randomly assigned to refer women, men, or anyone, with cross-randomized payment structures.",
  "sample_size": "767 job applicants",
  "treatment_info": "Applicants randomly assigned to referral treatments: must refer a woman, must refer a man, or can refer anyone",
  "key_findings": [
    "Only 30% of referrals were women (vs 38% of original applicants)",
    "Men systematically refer other men (77% of men's referrals)",
    "Women refer less qualified candidates across both genders"
  ],
  "implications": "Job referral networks can perpetuate gender wage gaps. Employers may need quota systems or carefully designed referral contracts to mitigate these effects.",
  "authors": ["Lori Beaman", "Niall Keleher", "Jeremy Magruder"],
  "institutions": ["Northwestern University", "UC Berkeley"],
  "timeline": "2013",
  "study_type": "RCT",
  "extraction_quality": 0.72,
  "validation_score": 0.56,
  "llm_model": "claude-3-5-haiku-20241022"
}
```

**Example Markdown Output:**

```markdown
# Job Networks Disadvantage Women in Labor Market

## Study Details
**Authors:** Lori Beaman, Niall Keleher, Jeremy Magruder
**Institutions:** Northwestern University, UC Berkeley
**Timeline:** 2013
**Study Type:** RCT
**Sample Size:** 767 job applicants

## Overview
Field experiment in Malawi examining how job referral networks systematically disadvantage qualified women through gender-biased referral patterns.

## Research Question
Do job referral networks inherently disadvantage women in the labor market?

## Methodology
Randomized field experiment with job applicants in Malawi, varying referral gender requirements and payment incentives.

## Key Findings
- Only 30% of referrals were women (vs 38% of original applicants)
- Men systematically refer other men (77% of men's referrals)
- Women refer less qualified candidates across both genders

## Implications
Job referral networks can perpetuate gender wage gaps by systematically disadvantaging qualified women. Employers may need quota systems or carefully designed referral contracts to mitigate these effects.

## Data Quality Assessment
**Extraction Quality:** 0.72
**Validation Score:** 0.56

**Issues:**
- Missing table IDs for 5 tables
- Missing table types for 5 tables
```

**Exit Codes:**

- `0` - Success
- `1` - Error (extraction not found, LLM error, API key missing)

**Requirements:**

- `ANTHROPIC_API_KEY` environment variable must be set
- Valid extraction.json file
- Internet connection (for LLM API calls and optional web search)

---

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
│   ├── figures/
│   └── validation.json         # If --validate enabled
├── paper_2/
│   ├── extraction.json
│   ├── tables/
│   ├── figures/
│   └── validation.json         # If --validate enabled
├── ...
└── batch_summary.json          # Batch statistics
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

enlace supports **two-pass VLM extraction** for improved accuracy on complex tables.

**IMPORTANT:** VLM features require `--use-docling` flag. They do not work with Camelot-only mode.

**Why?** VLM enhancement is part of the docling parsing pipeline, not Camelot's lattice/stream detection.

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

**All VLM examples require `--use-docling` flag:**

```bash
# Enable Granite-Docling VLM fallback (REQUIRES --use-docling)
uv run enlace extract paper.pdf --use-docling --vlm --ocr auto

# Specify VLM framework (auto-detects best option)
uv run enlace extract paper.pdf --use-docling --vlm --vlm-framework auto

# Use MLX framework on macOS (10-20x faster)
uv run enlace extract paper.pdf --use-docling --vlm --vlm-framework mlx

# Use Transformers framework (cross-platform)
uv run enlace extract paper.pdf --use-docling --vlm --vlm-framework transformers

# Two-pass VLM: Granite + Claude cleanup
export ENLACE_CLAUDE_API_KEY=sk-ant-...
uv run enlace extract paper.pdf --use-docling --vlm --claude-cleanup --ocr auto

# Configure VLM thresholds
export ENLACE_VLM_NULL_SE_THRESHOLD=0.25  # Trigger if >25% SEs missing
export ENLACE_VLM_NULL_COEF_THRESHOLD=0.15  # Trigger if >15% coeffs missing
uv run enlace extract paper.pdf --use-docling --vlm
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
uv run enlace extract paper.pdf --use-docling --vlm
```

#### Claude API Key Error

```bash
# Set API key
export ENLACE_CLAUDE_API_KEY=sk-ant-api03-...

# Verify it works
uv run enlace extract paper.pdf --use-docling --vlm --claude-cleanup
```

#### VLM Not Working Without --use-docling

If you get an error or VLM is not being applied, ensure you're using `--use-docling`:

```bash
# ❌ WRONG: VLM doesn't work with Camelot-only
uv run enlace extract paper.pdf --vlm

# ✅ CORRECT: VLM requires --use-docling
uv run enlace extract paper.pdf --use-docling --vlm
```

### VLM Best Practices

1. **Start with Granite only**: Test VLM without Claude cleanup first
2. **Use MLX on macOS**: 10-20x faster than Transformers
3. **Enable for scanned documents**: VLM excels at complex layouts
4. **Monitor costs**: Claude cleanup adds $0.01-0.05 per table
5. **Adjust thresholds**: Lower thresholds = more VLM usage, higher accuracy

For detailed VLM architecture and implementation, see [VLM_INTEGRATION.md](VLM_INTEGRATION.md).

---

## Vision Model Annotations for Figures

### Overview

enlace can generate AI-powered descriptions for all extracted figures using **Granite Vision**, IBM's 258M parameter vision language model. This feature:

- **Runs locally** - No external API calls, privacy-preserving
- **Dual output** - Saves annotations in both markdown and JSON
- **Opt-in** - Disabled by default due to processing time; enable when needed
- **Searchable** - Makes figure content discoverable through text search
- **Accessible** - Provides alt-text-like descriptions

### Output Format

**Markdown Output:**

```markdown
![Image](figures/figure_1.png)
VISION MODEL ANNOTATION: The image shows a bar chart comparing treatment effects across three outcome variables. The treatment group (blue bars) shows higher values than the control group (red bars) for all three variables, with the largest difference observed in variable A.
```

**JSON Output:**

```json
{
  "figures": [
    {
      "figure_id": "figure_1",
      "figure_number": "1",
      "caption": "Figure 1: Treatment Effects by Outcome",
      "annotation": "The image shows a bar chart comparing treatment effects across three outcome variables...",
      "image_path": "figures/figure_1.png",
      "page_number": 15
    }
  ]
}
```

### Configuration

Vision model annotations are **disabled by default** (processing can be slow). To enable:

**Via Environment Variable:**

```bash
export ENLACE_DESCRIBE_PICTURES=true
enlace extract paper.pdf
```

**Via Configuration File:**

```toml
[tool.enlace]
describe_pictures = true
```

### Use Cases

1. **Meta-Analysis** - Search across figure descriptions to find specific chart types
2. **Accessibility** - Provide text descriptions for screen readers
3. **Data Harmonization** - Understand figure content without viewing images
4. **Documentation** - Auto-generate figure summaries for reports

### Performance

- **Processing Time**: 6-10 seconds per figure (MLX on macOS) or 80-120 seconds (Transformers)
- **Cost**: $0 (runs completely locally)
- **Accuracy**: High-quality descriptions suitable for research documentation

### Troubleshooting

**Vision Model Takes Too Long:**

The first run downloads the model (~500MB). Subsequent runs are faster. On macOS with Apple Silicon, enable MLX for 10-20x speedup (automatically detected).

**Disable for Faster Processing:**

```bash
export ENLACE_DESCRIBE_PICTURES=false
enlace batch papers/ --workers 8
```

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
extract_figures = true
describe_pictures = false  # Enable to include vision model annotations for figures
output_format = "both"
output_dir = "extracted_data"
max_workers = 8

# LLM configuration
llm_model = "claude-4-5-haiku"
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

[tool.enlace.validation]
level = "comprehensive"
# output_dir auto-detects from extraction path by default
fail_on_issues = true

[tool.enlace.summary]
llm_model = "claude-3-5-haiku-20241022"
temperature = 0.3
max_tokens = 4096
detail_level = "standard"
use_web_search = false
output_format = "both"
```

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

### Environment Variables

All configuration options can be set via environment variables with `ENLACE_` prefix:

```bash
# Extraction settings
export ENLACE_ENABLE_OCR=true
export ENLACE_OCR_BACKEND=auto
export ENLACE_ENABLE_AUGMENTATION=true
export ENLACE_EXTRACT_FIGURES=true
export ENLACE_DESCRIBE_PICTURES=false  # Enable to include vision model annotations
export ENLACE_OUTPUT_FORMAT=json
export ENLACE_LLM_MODEL=claude-4-5-haiku
export ENLACE_VALIDATION_LEVEL=comprehensive

# Summary settings
export ENLACE_SUMMARY_MODEL=claude-3-5-sonnet-20241022
export ENLACE_SUMMARY_TEMPERATURE=0.3
export ENLACE_SUMMARY_DETAIL_LEVEL=detailed
export ENLACE_SUMMARY_WEB_SEARCH=true

# API key (required for augmentation and summarization)
export ANTHROPIC_API_KEY=your_api_key
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

### Extract, Validate, and Summarize Single Paper

```bash
# Step 1: Extract with comprehensive settings
uv run enlace extract paper.pdf --augment --ocr auto --output results/

# Step 2: Validate with comprehensive checks
uv run enlace validate results/paper/extraction.json \
    --level comprehensive \
    --fail-on-issues

# Step 3: Generate summary
export ANTHROPIC_API_KEY=your_api_key
uv run enlace summarize results/paper/ --format both
```

### Batch Processing with Quality Control and Summaries

```bash
# Step 1: Process directory with validation
uv run enlace batch papers/ \
    --output batch_results/ \
    --workers 8 \
    --augment \
    --ocr auto \
    --validate \
    --validation-level comprehensive

# Step 2: Review batch summary
cat batch_results/batch_summary.json

# Step 3: Generate summaries for all papers
for dir in batch_results/*/; do
    uv run enlace summarize "$dir" --format both -o summaries/
done

# Step 4: Check validation reports for issues
grep -l '"passed": false' batch_results/*/validation.json
```

### Complete Meta-Analysis Pipeline

```bash
# Full workflow: extract → validate → summarize
export ANTHROPIC_API_KEY=your_api_key

# 1. Batch extract with augmentation
uv run enlace batch papers/ --ocr auto --augment -o extractions/

# 2. Validate all extractions
for file in extractions/*/extraction.json; do
    uv run enlace validate "$file" --level comprehensive --fail-on-issues
done

# 3. Generate summaries for all papers
for dir in extractions/*/; do
    uv run enlace summarize "$dir" --format both -o summaries/
done

# 4. Review summaries for screening
ls summaries/*.md
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

### Summarization Fails

**Problem:** `enlace summarize` command fails with API errors.

**Solution:**

1. Ensure Anthropic API key is set:

   ```bash
   export ANTHROPIC_API_KEY=your_api_key
   echo $ANTHROPIC_API_KEY  # Verify it's set
   ```

2. Check model availability and configuration:

   ```bash
   # Use Haiku for faster, cheaper summaries
   uv run enlace summarize output/paper/ --model claude-3-5-haiku-20241022

   # Or Sonnet for higher quality
   uv run enlace summarize output/paper/ --model claude-3-5-sonnet-20241022
   ```

3. Verify extraction file exists and is valid:

   ```bash
   # Check extraction file
   ls -lh output/paper/extraction.json

   # Validate JSON format
   python -m json.tool output/paper/extraction.json > /dev/null
   ```

### Summary Quality Issues

**Problem:** Generated summaries are missing information or inaccurate.

**Solution:**

1. Use more detailed level for comprehensive summaries:

   ```bash
   uv run enlace summarize output/paper/ --level detailed
   ```

2. Enable web search for additional context:

   ```bash
   uv run enlace summarize output/paper/ --web-search
   ```

3. Provide validation results and original PDF:

   ```bash
   uv run enlace summarize output/paper/ \
       --validation output/paper/validation.json \
       --pdf papers/original.pdf \
       --level detailed
   ```

4. Use more powerful model:

   ```bash
   uv run enlace summarize output/paper/ \
       --model claude-3-5-sonnet-20241022 \
       --level detailed
   ```

## Getting Help

- **CLI help:** `uv run enlace --help`
- **Command help:** `uv run enlace extract --help`, `uv run enlace validate --help`, etc.
- **API documentation:** See [API_GUIDE.md](API_GUIDE.md)
- **Configuration reference:** See [CONFIGURATION.md](CONFIGURATION.md)
- **Development guide:** See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Issues:** Report bugs at <https://github.com/yourusername/enlace/issues>
