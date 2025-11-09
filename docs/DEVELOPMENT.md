# Development Guide

Guide for contributing to **enlace** and setting up a development environment.

## Prerequisites

- **Python 3.12+** - Required for modern type hints and features
- **uv** - Fast Python package manager (recommended)
- **just** - Task runner for common commands
- **Git** - Version control

### Install Prerequisites

```bash
# Install uv (package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install just (task runner)
# macOS
brew install just

# Linux
cargo install just

# Windows
scoop install just
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/enlace.git
cd enlace
```

### 2. Setup Development Environment

```bash
# Using just (recommended)
just get-started

# Or manually
just venv           # Create virtual environment and install dependencies
just install-readstat  # Install DuckDB read_stat extension
```

### 3. Activate Virtual Environment

```bash
# Bash
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\activate.ps1

# Windows (Git Bash)
source .venv/Scripts/activate
```

### 4. Verify Installation

```bash
# Test CLI
enlace --help

# Run tests
uv run pytest

# Check code quality
just lint-python
```

## Development Workflow

### Making Changes

1. **Create a branch** for your changes:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** to the codebase

3. **Format and lint** (REQUIRED):

   ```bash
   just fmt-python    # Auto-format Python code
   just lint-python   # Lint and auto-fix issues
   ```

4. **Run tests**:

   ```bash
   uv run pytest
   ```

5. **Run pre-commit checks**:

   ```bash
   just pre-commit-run
   ```

6. **Commit changes**:

   ```bash
   git add .
   git commit -m "Description of changes"
   ```

7. **Push and create pull request**:

   ```bash
   git push origin feature/your-feature-name
   ```

### Code Quality (CRITICAL)

**All Python code MUST be formatted and linted before committing.**

```bash
# Format all Python files
just fmt-python

# Lint and auto-fix issues
just lint-python

# Format single file
just fmt-py src/enlace/core/extractor.py

# Run all pre-commit hooks
just pre-commit-run
```

Pre-commit hooks automatically run on commit, but it's faster to fix issues beforehand.

## Project Structure

```text
enlace/
├── src/enlace/              # Main package
│   ├── core/                # Core extraction and validation
│   │   ├── extractor.py     # PaperExtractor
│   │   ├── parser.py        # TableParser
│   │   ├── validator.py     # ExtractionValidator
│   │   ├── metadata.py      # Metadata extraction
│   │   ├── config.py        # Configuration management
│   │   └── batch.py         # Batch processing
│   ├── models/              # Pydantic data models
│   │   ├── tables.py        # Table models
│   │   ├── figures.py       # Figure models
│   │   ├── extraction.py    # ExtractionResult
│   │   └── validation.py    # ValidationResult
│   ├── validators/          # Validation check modules
│   │   ├── structure.py     # Schema validation
│   │   ├── completeness.py  # Completeness checks
│   │   ├── accuracy.py      # Accuracy validation
│   │   ├── statistical.py   # Statistical consistency
│   │   ├── missing_data.py  # Missing data analysis
│   │   └── ocr_quality.py   # OCR quality checks
│   ├── semantic/            # Semantic augmentation (RAG)
│   │   ├── search.py        # Semantic search
│   │   ├── augmenter.py     # Table augmentation
│   │   ├── models.py        # Context models
│   │   └── extractors.py   # Context extractors
│   ├── cli/                 # Command-line interface
│   │   └── main.py          # CLI commands
│   ├── utils/               # Utility modules
│   │   ├── docling_utils.py # Document conversion
│   │   ├── ocr_backends.py  # OCR backend management
│   │   ├── ocr_options.py   # OCR configuration
│   │   └── logging.py       # Logging setup
│   └── exceptions.py        # Custom exceptions
├── tests/                   # Test suite
│   ├── core/                # Core module tests
│   ├── validators/          # Validator tests
│   ├── semantic/            # Semantic augmentation tests
│   ├── benchmark/           # Benchmark tests
│   │   ├── test_table_detection.py
│   │   ├── test_field_accuracy.py
│   │   └── test_ocr_comparison.py
│   └── fixtures/            # Test data and annotations
├── docs/                    # Documentation
│   ├── CLI_GUIDE.md
│   ├── API_GUIDE.md
│   ├── CONFIGURATION.md
│   ├── DEVELOPMENT.md (this file)
│   ├── MIGRATION_PLAN.md
│   └── BENCHMARK_README.md
├── examples/                # Example scripts
├── scripts/                 # Utility scripts
│   ├── create_annotation.py
│   └── generate_benchmark_report.py
├── pyproject.toml           # Project metadata and dependencies
├── justfile                 # Task automation
└── .pre-commit-config.yaml  # Pre-commit hooks
```

## Common Development Tasks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/enlace --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/core/test_extractor.py -v

# Run specific test
uv run pytest tests/core/test_extractor.py::test_extract_success -v

# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run benchmark tests
uv run pytest tests/benchmark/ -v

# Stop on first failure
uv run pytest -x

# Show print statements
uv run pytest -s
```

### Code Formatting and Linting

```bash
# Format all Python code
just fmt-python

# Lint Python code (with auto-fix)
just lint-python

# Format single file
just fmt-py src/enlace/core/extractor.py

# Format all markdown
just fmt-markdown

# Format single markdown file
just fmt-md docs/CLI_GUIDE.md

# Format everything
just fmt-all

# Run pre-commit hooks manually
just pre-commit-run

# Update pre-commit hooks
uv run pre-commit autoupdate
```

### Building and Installing

```bash
# Install in editable mode (development)
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Build distribution
uv build

# Test built wheel
uv pip install dist/enlace-0.1.0-py3-none-any.whl
```

### Dependency Management

```bash
# Add dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Update dependencies
just update-reqs

# Show dependency tree
uv pip tree
```

### Documentation

```bash
# Launch Jupyter Lab (for notebooks)
just lab

# Preview markdown locally
# (Use VS Code with Markdown Preview or grip)
pip install grip
grip docs/CLI_GUIDE.md
```

## Code Style Guidelines

### Python Style

enlace follows these Python conventions:

- **Line length**: 88 characters (Ruff default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Type hints**: Use modern syntax (e.g., `list[str]` instead of `List[str]`)
- **Docstrings**: Google-style format

### Docstring Format

```python
def extract(self, paper_path: Path) -> ExtractionResult:
    """Extract tables, figures, and metadata from a paper.

    Args:
        paper_path: Path to PDF or DOCX file.

    Returns:
        ExtractionResult with extracted content.

    Raises:
        PaperNotFoundError: If paper file does not exist.
        UnsupportedFormatError: If file format is not supported.
        ExtractionError: If extraction fails.

    Example:
        >>> extractor = PaperExtractor(config)
        >>> result = extractor.extract(Path("paper.pdf"))
        >>> print(f"Extracted {result.tables_extracted} tables")
    """
```

### Import Organization

Ruff automatically sorts imports:

1. Standard library imports
2. Third-party imports
3. Local imports

```python
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel

from enlace.core.config import ExtractionConfig
from enlace.exceptions import ExtractionError
```

### Type Hints

Use modern type hint syntax (Python 3.12+):

```python
# Good
def process(items: list[str]) -> dict[str, int]:
    ...

def get_value(x: int | None = None) -> str | None:
    ...

# Avoid (old syntax)
from typing import List, Dict, Optional, Union

def process(items: List[str]) -> Dict[str, int]:
    ...

def get_value(x: Optional[int] = None) -> Optional[str]:
    ...
```

## Testing Guidelines

### Test Structure

```python
# tests/core/test_extractor.py
"""Tests for PaperExtractor."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig
from enlace.exceptions import PaperNotFoundError


@pytest.fixture
def config():
    """Extraction configuration for tests."""
    return ExtractionConfig(
        enable_ocr=False,
        enable_augmentation=False
    )


@pytest.fixture
def extractor(config):
    """PaperExtractor instance."""
    return PaperExtractor(config)


class TestPaperExtractor:
    """Tests for PaperExtractor class."""

    def test_init(self, extractor, config):
        """Test extractor initialization."""
        assert extractor.config == config
        assert extractor.parser is not None

    def test_extract_nonexistent_paper_raises_error(self, extractor):
        """Test that extracting nonexistent paper raises error."""
        with pytest.raises(PaperNotFoundError):
            extractor.extract(Path("nonexistent.pdf"))

    @patch("enlace.utils.docling_utils.convert_pdf_to_markdown")
    def test_extract_success(self, mock_convert, extractor, tmp_path):
        """Test successful extraction."""
        pdf_file = tmp_path / "paper.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf")

        mock_convert.return_value = tmp_path / "paper.md"

        result = extractor.extract(pdf_file)

        assert result.paper_id == "paper"
        assert result.extraction_quality >= 0.0
        mock_convert.assert_called_once()
```

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_fast_function():
    """Fast unit test with mocks."""
    ...

@pytest.mark.integration
def test_full_pipeline():
    """Integration test with real components."""
    ...

@pytest.mark.slow
def test_expensive_operation():
    """Test that takes long time."""
    ...
```

Run specific markers:

```bash
uv run pytest -m unit        # Only unit tests
uv run pytest -m integration # Only integration tests
uv run pytest -m "not slow"  # Skip slow tests
```

### Fixtures

Use fixtures for shared test data:

```python
# tests/conftest.py
"""Shared test fixtures."""
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_paper(fixtures_dir):
    """Path to sample PDF paper."""
    return fixtures_dir / "papers" / "sample_rct.pdf"


@pytest.fixture
def temp_output(tmp_path):
    """Temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
```

### Mocking

Use `unittest.mock` or `pytest-mock` for mocking:

```python
from unittest.mock import Mock, patch, MagicMock

@patch("enlace.core.extractor.TableParser")
def test_with_mock(mock_parser_class):
    """Test using mock."""
    mock_parser = Mock()
    mock_parser.parse_tables.return_value = []
    mock_parser_class.return_value = mock_parser

    # Test code that uses TableParser
    ...

    mock_parser.parse_tables.assert_called_once()
```

## Creating Benchmark Tests

Benchmark tests validate extraction accuracy against ground truth annotations.

### 1. Create Ground Truth Annotation

```bash
# Generate annotation template
uv run python scripts/create_annotation.py papers/sample.pdf

# Manually review and correct the annotation
# Edit temp_extraction/sample/annotation.json

# Validate annotation
uv run python scripts/create_annotation.py --validate temp_extraction/sample/annotation.json
```

### 2. Add Test Fixture

```bash
# Move validated annotation to fixtures
mv temp_extraction/sample/annotation.json tests/fixtures/annotations/
cp papers/sample.pdf tests/fixtures/papers/
```

### 3. Write Benchmark Test

```python
# tests/benchmark/test_field_accuracy.py
import pytest
from pathlib import Path
from enlace.core.extractor import PaperExtractor
from enlace.core.config import ExtractionConfig
from tests.benchmark.utils import load_annotation, compare_paper


class TestFieldAccuracy:
    """Test field-level extraction accuracy."""

    def test_sample_accuracy(self):
        """Test accuracy for sample paper."""
        # Load ground truth
        annotation = load_annotation(
            Path("tests/fixtures/annotations/sample.json")
        )

        # Extract
        config = ExtractionConfig()
        extractor = PaperExtractor(config)
        result = extractor.extract(
            Path("tests/fixtures/papers/sample.pdf")
        )

        # Compare
        comparison = compare_paper(result, annotation)

        # Assertions
        assert comparison["overall_accuracy"] >= 0.7
        assert comparison["coefficient_accuracy"] >= 0.7
```

See [BENCHMARK_README.md](BENCHMARK_README.md) for complete benchmarking guide.

## Adding New Features

### 1. Add Configuration Option

```python
# src/enlace/core/config.py
class ExtractionConfig(BaseSettings):
    ...
    new_feature_enabled: bool = Field(
        default=False,
        description="Enable new feature"
    )
```

### 2. Implement Feature

```python
# src/enlace/core/new_feature.py
"""New feature implementation."""
from enlace.exceptions import EnlaceError


class NewFeatureError(EnlaceError):
    """New feature error."""
    pass


class NewFeature:
    """New feature class."""

    def __init__(self, config):
        self.config = config

    def process(self, data):
        """Process data with new feature."""
        if not self.config.new_feature_enabled:
            return data

        # Implementation
        ...
```

### 3. Integrate Feature

```python
# src/enlace/core/extractor.py
class PaperExtractor:
    def __init__(self, config):
        ...
        if config.new_feature_enabled:
            self.new_feature = NewFeature(config)
```

### 4. Add Tests

```python
# tests/core/test_new_feature.py
"""Tests for new feature."""
import pytest
from enlace.core.new_feature import NewFeature


class TestNewFeature:
    """Tests for NewFeature class."""

    def test_process(self):
        """Test feature processing."""
        ...
```

### 5. Update Documentation

- Add CLI option to [CLI_GUIDE.md](CLI_GUIDE.md)
- Add API usage to [API_GUIDE.md](API_GUIDE.md)
- Add configuration to [CONFIGURATION.md](CONFIGURATION.md)
- Add example script to `examples/`

### 6. Format, Lint, Test

```bash
just fmt-python
just lint-python
uv run pytest
just pre-commit-run
```

## Debugging

### Enable Verbose Logging

```python
from enlace.utils.logging import setup_logging

setup_logging(level="DEBUG", verbose=True)
```

Or use CLI:

```bash
enlace extract paper.pdf --verbose
```

### Use Python Debugger

```python
# Add breakpoint
def extract(self, paper_path):
    breakpoint()  # Python 3.7+
    ...
```

```bash
# Run with debugger
uv run pytest --pdb

# Or use ipdb
uv add --dev ipdb
import ipdb; ipdb.set_trace()
```

### Inspect Intermediate Results

```python
# Save intermediate data
result = extractor.extract(Path("paper.pdf"))

# Save full result for inspection
result.save(Path("debug_output"), format="json")

# Inspect specific tables
for i, table in enumerate(result.tables):
    print(f"Table {i}: {table.title}")
    print(f"  Type: {table.table_type}")
    print(f"  Rows: {len(table.rows)}")
```

## Contributing Guidelines

### Before Submitting PR

- [ ] Code is formatted (`just fmt-python`)
- [ ] Code is linted (`just lint-python`)
- [ ] All tests pass (`uv run pytest`)
- [ ] Pre-commit hooks pass (`just pre-commit-run`)
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Benchmark tests added if applicable

### PR Checklist

- [ ] Clear description of changes
- [ ] Related issue referenced (if applicable)
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Version number updated (if releasing)

### Commit Messages

Follow conventional commit format:

```text
type(scope): description

[optional body]

[optional footer]
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Build/tool changes

Examples:

```text
feat(cli): add --ocr-confidence flag

fix(parser): handle empty table cells correctly

docs(api): update ExtractionResult docstring

test(benchmark): add OCR quality tests
```

## Getting Help

- **Issues**: <https://github.com/yourusername/enlace/issues>
- **Discussions**: <https://github.com/yourusername/enlace/discussions>
- **Documentation**: See `docs/` directory

## Maintainer Notes

### Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release commit:

   ```bash
   git commit -m "chore: release v0.2.0"
   ```

4. Tag release:

   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   ```

5. Push tag:

   ```bash
   git push origin v0.2.0
   ```

6. Build and publish:

   ```bash
   uv build
   uv publish
   ```

### Dependency Updates

```bash
# Update all dependencies
just update-reqs

# Test with updated dependencies
uv run pytest

# Update pre-commit hooks
uv run pre-commit autoupdate
```

## See Also

- [CLI Guide](CLI_GUIDE.md) - Command-line usage
- [API Guide](API_GUIDE.md) - Python API documentation
- [Configuration Guide](CONFIGURATION.md) - Configuration reference
- [Migration Plan](MIGRATION_PLAN.md) - Architecture details
- [Benchmark Guide](BENCHMARK_README.md) - Benchmark testing system
