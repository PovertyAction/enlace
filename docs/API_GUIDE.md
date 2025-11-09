# API Guide

Python API documentation for **enlace** - Programmatic access to paper extraction and validation.

## Installation

```bash
# Install enlace
uv pip install -e .

# Or with pip
pip install -e .
```

## Quick Start

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

# Save to file
result.save(Path("output"))
```

## Core Classes

### `PaperExtractor`

Main entry point for extracting structured data from research papers.

**Location:** `enlace.core.extractor`

**Constructor:**

```python
PaperExtractor(config: ExtractionConfig)
```

**Parameters:**

- `config` - `ExtractionConfig` instance with extraction settings

**Methods:**

#### `extract(paper_path: Path) -> ExtractionResult`

Extract tables, figures, and metadata from a paper.

**Parameters:**

- `paper_path` - Path to PDF or DOCX file

**Returns:**

- `ExtractionResult` with extracted content

**Raises:**

- `PaperNotFoundError` - If paper file does not exist
- `UnsupportedFormatError` - If file format is not supported (must be .pdf or .docx)
- `ExtractionError` - If extraction fails

**Example:**

```python
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig

config = ExtractionConfig(enable_ocr=True)
extractor = PaperExtractor(config)

try:
    result = extractor.extract(Path("paper.pdf"))
    print(f"Success! Extracted {result.tables_extracted} tables")
except PaperNotFoundError as e:
    print(f"Paper not found: {e.path}")
except UnsupportedFormatError as e:
    print(f"Unsupported format. Supported: {e.supported_formats}")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
```

#### `augment(extraction: ExtractionResult) -> ExtractionResult`

Augment extraction with semantic context using RAG.

**Parameters:**

- `extraction` - `ExtractionResult` from `extract()` method

**Returns:**

- Enhanced `ExtractionResult` with semantic context fields populated

**Raises:**

- `AugmentationError` - If augmentation fails
- `ModelNotFoundError` - If embedding/LLM model is not available

**Example:**

```python
config = ExtractionConfig(
    enable_augmentation=True,
    llm_model="claude-4-5-haiku"
)
extractor = PaperExtractor(config)

# Extract and augment
result = extractor.extract(Path("paper.pdf"))
augmented = extractor.augment(result)

# Access semantic context
for table in augmented.tables:
    if hasattr(table, "study_context"):
        print(f"Study context: {table.study_context}")
```

### `ExtractionValidator`

Validate extracted research data quality with configurable validation levels.

**Location:** `enlace.core.validator`

**Constructor:**

```python
ExtractionValidator(config: ValidationConfig)
```

**Parameters:**

- `config` - `ValidationConfig` instance with validation settings

**Methods:**

#### `validate(extraction: ExtractionResult | Path, level: str | None = None) -> ValidationResult`

Validate extraction result with configurable checks.

**Parameters:**

- `extraction` - `ExtractionResult` object or path to extraction.json
- `level` - Override validation level from config (quick, standard, comprehensive)

**Returns:**

- `ValidationResult` with check results and recommendations

**Raises:**

- `ValidationError` - If validation cannot be performed
- `FileNotFoundError` - If extraction path does not exist

**Example:**

```python
from enlace.core.validator import ExtractionValidator
from enlace.core.config import ValidationConfig

# Standard validation
config = ValidationConfig(level="standard")
validator = ExtractionValidator(config)
result = validator.validate(extraction)

if not result.passed:
    print(f"Validation failed (score: {result.score:.2f})")
    for issue in result.issues:
        print(f"  - {issue.message}")

# Comprehensive validation
result = validator.validate(extraction, level="comprehensive")
result.save(Path("validation_reports"))
```

#### `validate_batch(extractions: list[ExtractionResult] | Path, level: str | None = None) -> BatchValidationResult`

Validate multiple extractions in batch.

**Parameters:**

- `extractions` - List of `ExtractionResult` objects or directory containing extractions
- `level` - Validation level override

**Returns:**

- `BatchValidationResult` with aggregated statistics

**Raises:**

- `ValidationError` - If batch validation fails

**Example:**

```python
from pathlib import Path
from enlace.core.validator import ExtractionValidator
from enlace.core.config import ValidationConfig

config = ValidationConfig(level="comprehensive")
validator = ExtractionValidator(config)

# Validate all extractions in directory
batch_result = validator.validate_batch(Path("output"))

print(f"Validated {batch_result.total_papers} papers")
print(f"Passed: {batch_result.passed_papers}")
print(f"Failed: {batch_result.failed_papers}")
print(f"Average score: {batch_result.avg_score:.2f}")
```

### `BatchProcessor`

Process multiple papers in parallel with optional validation.

**Location:** `enlace.core.batch`

**Constructor:**

```python
BatchProcessor(
    output_dir: Path,
    workers: int = 4,
    enable_augmentation: bool = False,
    enable_validation: bool = True,
    validation_level: str = "standard",
    config_file: Path | None = None
)
```

**Parameters:**

- `output_dir` - Directory for output files
- `workers` - Number of parallel workers
- `enable_augmentation` - Enable semantic augmentation
- `enable_validation` - Run validation after extraction
- `validation_level` - Validation level (quick, standard, comprehensive)
- `config_file` - Optional configuration file

**Methods:**

#### `process(input_dir: Path) -> BatchSummary`

Process all papers in a directory.

**Parameters:**

- `input_dir` - Directory containing PDF/DOCX papers

**Returns:**

- `BatchSummary` with processing statistics

**Example:**

```python
from pathlib import Path
from enlace.core.batch import BatchProcessor

processor = BatchProcessor(
    output_dir=Path("batch_output"),
    workers=8,
    enable_augmentation=True,
    enable_validation=True,
    validation_level="comprehensive"
)

summary = processor.process(Path("papers/"))

print(f"Processed: {summary.papers_successful}/{summary.papers_processed}")
print(f"Total tables: {summary.total_tables}")
print(f"Average quality: {summary.avg_quality:.2f}")
print(f"Time: {summary.processing_time_seconds:.1f}s")

# Save summary
summary.save(Path("batch_output"))
```

## Configuration Classes

### `ExtractionConfig`

Configuration for paper extraction with priority loading.

**Location:** `enlace.core.config`

**Constructor:**

```python
ExtractionConfig(
    enable_ocr: bool = False,
    ocr_backend: str = "auto",
    ocr_confidence_threshold: float = 0.8,
    hybrid_ocr_enabled: bool = True,
    enable_augmentation: bool = False,
    extract_figures: bool = True,
    extract_tables: bool = True,
    extract_metadata: bool = True,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    llm_model: str = "claude-4-5-haiku",
    output_format: str = "json",
    output_dir: Path = Path("output"),
    batch_size: int = 10,
    max_workers: int = 4,
    verbose: bool = False,
    log_file: Path | None = None
)
```

**Class Methods:**

#### `load_config(config_file: Path | None = None, **cli_args: Any) -> ExtractionConfig`

Load configuration with priority: defaults < file < env < CLI args.

**Parameters:**

- `config_file` - Optional path to .toml configuration file
- `**cli_args` - Command-line arguments (highest priority)

**Returns:**

- Loaded `ExtractionConfig` instance

**Raises:**

- `ConfigError` - If configuration file is invalid

**Example:**

```python
from pathlib import Path
from enlace.core.config import ExtractionConfig

# Load from config file
config = ExtractionConfig.load_config(
    config_file=Path(".enlace.toml")
)

# Override with CLI args
config = ExtractionConfig.load_config(
    config_file=Path(".enlace.toml"),
    enable_ocr=True,
    ocr_backend="easyocr",
    output_dir=Path("results")
)

# Environment variables automatically loaded (ENLACE_* prefix)
# ENLACE_ENABLE_OCR=true
# ENLACE_LLM_MODEL=claude-4-5-haiku
```

### `ValidationConfig`

Configuration for validation with customizable levels.

**Location:** `enlace.core.config`

**Constructor:**

```python
ValidationConfig(
    level: str = "standard",
    output_dir: Path = Path("validation_reports"),
    fail_on_issues: bool = False,
    levels: dict[str, list[str]] = {...},
    verbose: bool = False
)
```

**Class Methods:**

#### `load_config(config_file: Path | None = None, **cli_args: Any) -> ValidationConfig`

Load validation configuration with priority loading.

**Example:**

```python
from enlace.core.config import ValidationConfig

# Custom validation levels
config = ValidationConfig(
    level="custom",
    levels={
        "custom": ["structure", "accuracy", "semantic_validation"]
    }
)

# Get checks for level
checks = config.get_checks_for_level("comprehensive")
print(f"Running checks: {checks}")
```

#### `get_checks_for_level(level: str | None = None) -> list[str]`

Get list of validation checks for specified level.

**Parameters:**

- `level` - Level name (uses self.level if None)

**Returns:**

- List of check names to run

**Raises:**

- `ConfigError` - If level not found

## Data Models

### `ExtractionResult`

Result from paper extraction operation.

**Location:** `enlace.models.extraction`

**Fields:**

```python
class ExtractionResult(BaseModel):
    paper_id: str
    source_file: Path
    extraction_date: datetime
    tables: list[RegressionTable | SummaryStatisticsTable | BalanceTable]
    figures: list[Figure]
    metadata: PaperMetadata
    extraction_quality: float  # 0.0-1.0
    warnings: list[str]
    processing_time_seconds: float | None
    tables_extracted: int
    figures_extracted: int
```

**Methods:**

#### `save(output_dir: Path, format: str = "json") -> None`

Save extraction result to file.

**Parameters:**

- `output_dir` - Directory to save output files
- `format` - Output format (json, csv, both)

**Raises:**

- `ExtractionError` - If save operation fails

**Example:**

```python
result = extractor.extract(Path("paper.pdf"))

# Save as JSON
result.save(Path("output"), format="json")

# Save as both JSON and CSV
result.save(Path("output"), format="both")
```

### `ValidationResult`

Result from validation operation.

**Location:** `enlace.models.validation`

**Fields:**

```python
class ValidationResult(BaseModel):
    paper_id: str
    validation_date: datetime
    extraction_path: Path
    passed: bool
    score: float  # 0.0-1.0
    issues: list[ValidationIssue]
    warnings: list[ValidationWarning]
    checks: dict[str, CheckResult]
    table_validations: list[TableValidationResult]
    recommendations: list[str]
```

**Methods:**

#### `save(output_dir: Path) -> None`

Save validation report to JSON file.

**Example:**

```python
result = validator.validate(extraction)
result.save(Path("validation_reports"))

# Check results
if not result.passed:
    for issue in result.issues:
        print(f"[{issue.severity}] {issue.message}")
```

### Table Models

All table models are located in `enlace.models.tables`.

#### `RegressionTable`

Regression analysis results table.

**Key Fields:**

- `title: str` - Table title
- `table_type: str` - "regression"
- `models: list[RegressionModel]` - Regression models
- `dependent_variable: str | None` - Outcome variable
- `study_context: dict | None` - Semantic context (if augmented)

#### `SummaryStatisticsTable`

Descriptive statistics table.

**Key Fields:**

- `title: str` - Table title
- `table_type: str` - "summary_statistics"
- `statistics: list[SummaryStatistic]` - Summary statistics
- `sample_size: int | None` - Number of observations

#### `BalanceTable`

Treatment-control balance table.

**Key Fields:**

- `title: str` - Table title
- `table_type: str` - "balance"
- `variables: list[BalanceStatistic]` - Balance statistics
- `groups: list[str]` - Treatment/control groups

See [models/tables.py](../src/enlace/models/tables.py) for complete schemas.

## Error Handling

### Exception Hierarchy

All enlace exceptions inherit from `EnlaceError`.

**Location:** `enlace.exceptions`

**Exception Classes:**

```python
EnlaceError                # Base exception
├── ConfigError            # Configuration errors
├── PaperNotFoundError     # Paper file not found
├── UnsupportedFormatError # Unsupported file format
├── ExtractionError        # Extraction failed
├── AugmentationError      # Semantic augmentation failed
├── ModelNotFoundError     # LLM/embedding model not found
└── ValidationError        # Validation failed
```

### Error Handling Example

```python
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig
from enlace.exceptions import (
    EnlaceError,
    PaperNotFoundError,
    UnsupportedFormatError,
    ExtractionError,
    AugmentationError
)

config = ExtractionConfig()
extractor = PaperExtractor(config)

try:
    result = extractor.extract(Path("paper.pdf"))

    if config.enable_augmentation:
        result = extractor.augment(result)

    result.save(Path("output"))

except PaperNotFoundError as e:
    print(f"Paper not found: {e.path}")
except UnsupportedFormatError as e:
    print(f"Unsupported format: {e.path}")
    print(f"Supported formats: {e.supported_formats}")
except AugmentationError as e:
    print(f"Augmentation failed: {e}")
    print("Continuing with non-augmented extraction...")
    result.save(Path("output"))
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except EnlaceError as e:
    print(f"Enlace error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Usage

### Custom Validation Checks

Define custom validation levels with specific checks:

```python
from enlace.core.config import ValidationConfig
from enlace.core.validator import ExtractionValidator

config = ValidationConfig(
    level="regression_only",
    levels={
        "regression_only": [
            "structure",
            "accuracy",
            "statistical_consistency"
        ],
        "quick_ocr": [
            "structure",
            "ocr_quality"
        ]
    }
)

validator = ExtractionValidator(config)
result = validator.validate(extraction, level="regression_only")
```

### Programmatic Batch Processing

Build custom batch processing workflows:

```python
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.core.config import ExtractionConfig, ValidationConfig
import concurrent.futures

def process_paper(paper_path: Path, output_dir: Path):
    """Process single paper with extraction and validation."""
    config = ExtractionConfig(
        enable_ocr=True,
        enable_augmentation=True
    )
    extractor = PaperExtractor(config)

    try:
        # Extract
        result = extractor.extract(paper_path)
        result = extractor.augment(result)
        result.save(output_dir / paper_path.stem)

        # Validate
        val_config = ValidationConfig(level="comprehensive")
        validator = ExtractionValidator(val_config)
        val_result = validator.validate(result)
        val_result.save(output_dir / "validation")

        return {
            "paper": paper_path.name,
            "success": True,
            "quality": result.extraction_quality,
            "validation_passed": val_result.passed
        }
    except Exception as e:
        return {
            "paper": paper_path.name,
            "success": False,
            "error": str(e)
        }

# Parallel processing
papers = list(Path("papers").glob("*.pdf"))
results = []

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_paper, paper, Path("output"))
        for paper in papers
    ]
    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

# Summary
successful = sum(1 for r in results if r["success"])
print(f"Processed {successful}/{len(results)} papers successfully")
```

### Access Semantic Context

Extract and use semantic augmentation data:

```python
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig

config = ExtractionConfig(
    enable_augmentation=True,
    llm_model="claude-4-5-haiku"
)
extractor = PaperExtractor(config)

result = extractor.extract(Path("paper.pdf"))
augmented = extractor.augment(result)

# Access regression table context
for table in augmented.tables:
    if table.table_type == "regression":
        print(f"\nTable: {table.title}")

        # Study context
        if table.study_context:
            print(f"Study: {table.study_context.get('description')}")
            print(f"Sample: {table.study_context.get('sample_description')}")

        # Variable context for each coefficient
        for model in table.models:
            for coef in model.coefficients:
                if coef.variable_context:
                    print(f"\n{coef.variable_name}:")
                    print(f"  Definition: {coef.variable_context.get('definition')}")
                    print(f"  Units: {coef.variable_context.get('units')}")
                    print(f"  Source: {coef.variable_context.get('data_source')}")

                # Validation results
                if coef.validation:
                    print(f"  Validation: {coef.validation.get('status')}")
                    if coef.validation.get('discrepancy'):
                        print(f"  Discrepancy: {coef.validation['discrepancy']}")
```

### Export to Pandas DataFrames

Convert extraction results to pandas for analysis:

```python
import pandas as pd
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig

config = ExtractionConfig()
extractor = PaperExtractor(config)
result = extractor.extract(Path("paper.pdf"))

# Extract regression coefficients to DataFrame
regression_data = []
for table in result.tables:
    if table.table_type == "regression":
        for model in table.models:
            for coef in model.coefficients:
                regression_data.append({
                    "table": table.title,
                    "model": model.model_number,
                    "variable": coef.variable_name,
                    "coefficient": coef.coefficient,
                    "se": coef.standard_error,
                    "pvalue": coef.p_value,
                    "sig": coef.significance_stars
                })

df = pd.DataFrame(regression_data)
df.to_csv("regression_results.csv", index=False)
print(df)
```

## Logging

Configure logging for debugging and monitoring:

```python
from enlace.utils.logging import setup_logging
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig
from pathlib import Path

# Setup logging
setup_logging(
    level="DEBUG",
    log_file=Path("enlace.log"),
    verbose=True
)

# Or use config
config = ExtractionConfig(
    verbose=True,
    log_file=Path("enlace.log")
)

extractor = PaperExtractor(config)
result = extractor.extract(Path("paper.pdf"))
```

## Testing

Use enlace in your test suite:

```python
import pytest
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig
from enlace.exceptions import PaperNotFoundError

def test_extract_regression_table():
    """Test extraction of regression tables."""
    config = ExtractionConfig()
    extractor = PaperExtractor(config)

    result = extractor.extract(Path("tests/fixtures/sample_paper.pdf"))

    # Assertions
    assert result.tables_extracted > 0
    assert result.extraction_quality > 0.7

    # Check regression table
    regression_tables = [t for t in result.tables if t.table_type == "regression"]
    assert len(regression_tables) > 0

    table = regression_tables[0]
    assert len(table.models) > 0
    assert len(table.models[0].coefficients) > 0

def test_nonexistent_paper():
    """Test that nonexistent paper raises error."""
    config = ExtractionConfig()
    extractor = PaperExtractor(config)

    with pytest.raises(PaperNotFoundError):
        extractor.extract(Path("nonexistent.pdf"))
```

## See Also

- [CLI Guide](CLI_GUIDE.md) - Command-line interface documentation
- [Configuration Guide](CONFIGURATION.md) - Complete configuration reference
- [Development Guide](DEVELOPMENT.md) - Contributing and development setup
- [Migration Plan](MIGRATION_PLAN.md) - Package architecture details
