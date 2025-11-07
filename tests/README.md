# Tests

This directory contains comprehensive tests for the **enlace** semantic table augmentation system.

## Test Structure

```text
tests/
├── test_semantic_search.py  # Tests for semantic search pipeline (31 tests)
├── test_semantic_validator.py  # Tests for semantic validation (37 tests)
└── test_semantic_augmentation_integration.py  # Integration tests (10 tests)
```

## Running Tests

### Run All Semantic Augmentation Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_semantic_search.py -v

# Run specific test class
uv run pytest tests/test_semantic_validator.py::TestSemanticValidator

# Run tests matching a pattern
uv run pytest -k "validate_coefficient"
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests with mocked dependencies
- `@pytest.mark.integration` - Integration tests that test multiple components together
- `@pytest.mark.slow` - Tests that take longer to run (require actual models, etc.)

### Run tests by marker

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Exclude slow tests
uv run pytest -m "not slow"
```

## Test Coverage

### Generate Coverage Report

```bash
# Generate coverage report in terminal
uv run pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html

# Open HTML report (generated in htmlcov/)
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Test Fixtures

Tests use pytest's built-in mocking and async capabilities. No custom fixtures are currently defined, but you can add them to a `conftest.py` file if needed for shared test data.

## Writing Tests

### Test Organization

Each test module follows this structure:

1. **Unit tests** - Test individual functions/methods in isolation
   - Use mocks for external dependencies
   - Fast execution
   - Mark with `@pytest.mark.unit`

2. **Integration tests** - Test multiple components working together
   - May use some mocks for slow operations
   - Test realistic workflows
   - Mark with `@pytest.mark.integration`

### Example Test

```python
import pytest
from unittest.mock import MagicMock, patch

@pytest.mark.unit
class TestMyComponent:
    """Tests for MyComponent class."""

    def test_initialization(self):
        """Test component initialization."""
        component = MyComponent()
        assert component is not None

    @patch("module.external_dependency")
    def test_with_mock(self, mock_dependency):
        """Test using mocked dependencies."""
        mock_dependency.return_value = "mocked value"
        result = my_function()
        assert result == "expected result"
```

## Test Coverage Report

### Semantic Augmentation System Tests

- **Semantic Search**: 31 tests - coverage TBD
  - Pipeline initialization (default and custom config)
  - PDF processing (text extraction, chunking, error handling)
  - Document processing (vectorstore creation, caching)
  - Semantic search (similarity search, threshold filtering)
  - Question answering (QA with LLM, confidence estimation)
  - Batch operations (concurrent and sequential processing)
  - Error handling (missing documents, LLM failures, empty results)

- **Semantic Validator**: 37 tests - coverage TBD
  - Coefficient validation (exact match, close match, mismatch detection)
  - Summary statistics (mean, std, min, max validation)
  - Sample size (N validation with group context)
  - Batch validation (multiple coefficients efficiently)
  - Value comparison (relative/absolute discrepancy calculation)
  - Confidence adjustment (based on match quality)
  - Number extraction (decimal, integer, scientific notation, negative)
  - Table summaries (full table validation reports)

- **Semantic Augmentation Integration**: 10 tests
  - Complete workflows (document → search → validation)
  - Multi-table handling (multiple tables from same document)
  - OCR error detection (catches parsing mistakes via validation)
  - Batch validation (efficient multi-coefficient validation)
  - Table summaries (full table validation reports)
  - Missing data (graceful handling of incomplete information)
  - Pipeline reset (document switching and reprocessing)
  - Realistic workflows (end-to-end research paper processing)

### Total: 78 tests

### Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| **semantic_search.py** | TBD | **31** |
| **semantic_validator.py** | TBD | **37** |
| **semantic_augmentation** (integration) | - | **10** |

**Coverage Goal**: >90% for semantic augmentation modules

## Running Tests Before Commits

It's recommended to run tests before committing changes:

```bash
# Quick test run (unit tests only)
uv run pytest -m unit

# Full test suite
uv run pytest -v

# With coverage
uv run pytest --cov=src --cov-report=term-missing
```

## Troubleshooting

### Common Issues

#### Import errors

Make sure you're in the project root and dependencies are installed:

```bash
cd /home/nkeleher/code/enlace
uv sync
uv run pytest
```

#### Tests fail due to missing dependencies

Install dependencies:

```bash
uv sync
```

#### Slow tests

Skip slow integration tests during development:

```bash
uv run pytest -m "not slow"
# Or run only unit tests
uv run pytest -m unit
```

#### Missing environment variables

Some tests may require environment variables. Check test output for specific requirements.

## Best Practices

1. **Keep tests isolated** - Each test should be independent
2. **Use descriptive names** - Test names should describe what they test
3. **Mock external dependencies** - Use mocks for API calls, file I/O, etc.
4. **Test edge cases** - Test both success and failure scenarios
5. **Keep tests fast** - Use mocks to avoid slow operations
6. **Maintain test coverage** - Aim for high coverage of critical paths

## Semantic Augmentation Tests

The semantic augmentation system has comprehensive test coverage across three test modules:

### test_semantic_search.py (31 tests)

Tests for the `SemanticSearchPipeline` class that provides RAG-based context extraction:

- **Initialization**: Default and custom configuration
- **PDF Processing**: Text extraction, chunking, error handling
- **Document Processing**: Vectorstore creation, caching
- **Semantic Search**: Similarity search, threshold filtering
- **Question Answering**: QA with LLM, confidence estimation
- **Batch Operations**: Concurrent and sequential processing
- **Error Handling**: Missing documents, LLM failures, empty results

Example:

```bash
# Run all semantic search tests
uv run pytest tests/test_semantic_search.py -v

# Run only unit tests
uv run pytest tests/test_semantic_search.py -m unit

# Run integration tests
uv run pytest tests/test_semantic_search.py -m integration
```

### test_semantic_validator.py (37 tests)

Tests for the `SemanticValidator` class that validates parsed values against paper text:

- **Coefficient Validation**: Exact match, close match, mismatch detection
- **Summary Statistics**: Mean, std, min, max validation
- **Sample Size**: N validation with group context
- **Batch Validation**: Multiple coefficients efficiently
- **Value Comparison**: Relative/absolute discrepancy calculation
- **Confidence Adjustment**: Based on match quality
- **Number Extraction**: Decimal, integer, scientific notation, negative
- **Table Summaries**: Full table validation reports

Example:

```bash
# Run all validator tests
uv run pytest tests/test_semantic_validator.py -v

# Test specific validation type
uv run pytest tests/test_semantic_validator.py -k "coefficient"
```

### test_semantic_augmentation_integration.py (10 tests)

Integration tests for the complete semantic augmentation pipeline:

- **Complete Workflows**: Document → Search → Validation
- **Multi-Table Handling**: Multiple tables from same document
- **OCR Error Detection**: Catches parsing mistakes via validation
- **Batch Validation**: Efficient multi-coefficient validation
- **Table Summaries**: Full table validation reports
- **Missing Data**: Graceful handling of incomplete information
- **Pipeline Reset**: Document switching and reprocessing
- **Realistic Workflows**: End-to-end research paper processing

Example:

```bash
# Run all integration tests
uv run pytest tests/test_semantic_augmentation_integration.py -v

# Run realistic workflow test
uv run pytest tests/test_semantic_augmentation_integration.py -k "realistic"
```

### Running All Semantic Augmentation Tests

```bash
# Run all semantic augmentation tests
uv run pytest tests/test_semantic*.py -v

# With coverage
uv run pytest tests/test_semantic*.py --cov=src --cov-report=term-missing

# Only unit tests (fast)
uv run pytest tests/test_semantic*.py -m unit

# Only integration tests
uv run pytest tests/test_semantic*.py -m integration
```

## Adding New Tests

When adding new functionality:

1. Write tests first (TDD approach) or alongside implementation
2. Add unit tests for individual functions
3. Add integration tests for workflows
4. Use appropriate markers (`@pytest.mark.unit`, etc.)
5. Update this README if adding new test categories

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
