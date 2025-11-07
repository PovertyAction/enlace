# Phase 8 Testing Plan: Semantic Table Augmentation

**Status**: 🔄 In Progress
**Started**: 2025-11-06
**Dependencies**: Phases 1-7 complete

## Overview

Phase 8 focuses on comprehensive testing and validation of the semantic table augmentation system. The goal is to ensure the RAG-based context extraction and validation systems work correctly with real research papers and produce high-quality augmented table data.

## Existing Test Infrastructure

The project has a robust test suite (318 tests, 71% overall coverage) from the Evidence Summaries Streamlit app:

### Current Test Coverage

| Module | Coverage | Tests | Notes |
|--------|----------|-------|-------|
| rag_pipeline.py | 100% 🎯 | 32 | RAG, vectorstore, embeddings |
| web_search.py | 100% 🎯 | 50 | Web search integration |
| guidelines_loader.py | 100% 🎯 | 70 | Guidelines management |
| logging_config.py | 100% 🎯 | 23 | Logging configuration |
| config.py | 100% 🎯 | 54 | Configuration validation |
| summary_generator.py | 96% ⭐ | 33 | Summary generation |
| examples_loader.py | 90% ⭐ | 33 | Example management |
| document_processor.py | 89% | 14 | PDF processing |

### Available Test Fixtures

From `tests/conftest.py`:

- `temp_dir` - Temporary directory (auto-cleaned)
- `sample_pdf` - Minimal PDF with text
- `sample_pdf_with_text` - Multi-page research paper PDF
- `sample_text_chunks` - Pre-chunked text for RAG
- `mock_config` - Mock configuration
- `mock_section_content` - Sample section content

### Test Organization

- **Unit tests** (`@pytest.mark.unit`) - Fast, mocked dependencies
- **Integration tests** (`@pytest.mark.integration`) - Multi-component workflows
- **Slow tests** (`@pytest.mark.slow`) - Require actual models

## New Modules Requiring Tests

### 1. augmentation_config.py

**Purpose**: Configuration for semantic augmentation
**Priority**: High
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] Configuration initialization with defaults
- [ ] Custom configuration values
- [ ] Validation of ranges (thresholds, k values)
- [ ] Environment variable overrides
- [ ] Model name validation
- [ ] Concurrency limits
- [ ] Default flag behavior

**Test Structure**:

```python
@pytest.mark.unit
class TestAugmentationConfig:
    """Tests for AugmentationConfig class."""

    def test_init_with_defaults()
    def test_custom_model_name()
    def test_validation_thresholds()
    def test_concurrent_limit()
    def test_enable_flags()
```

### 2. context_models.py

**Purpose**: Pydantic models for context data
**Priority**: High
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] StudyContext creation and validation
- [ ] InterventionContext creation and validation
- [ ] OutcomeContext creation and validation
- [ ] MethodologyContext creation and validation
- [ ] ValidationResult creation and validation
- [ ] Optional field handling
- [ ] Data type validation
- [ ] Model serialization (dict, JSON)

**Test Structure**:

```python
@pytest.mark.unit
class TestContextModels:
    """Tests for context Pydantic models."""

    def test_study_context_valid()
    def test_study_context_optional_fields()
    def test_intervention_context_valid()
    def test_outcome_context_valid()
    def test_methodology_context_valid()
    def test_validation_result()
    def test_model_serialization()
```

### 3. semantic_search.py

**Purpose**: RAG-based semantic QA pipeline
**Priority**: Critical
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] SemanticSearchPipeline initialization
- [ ] Vector store creation from markdown
- [ ] Semantic QA with retrieved context
- [ ] Source chunk extraction
- [ ] Confidence scoring
- [ ] Empty/invalid markdown handling
- [ ] Multiple concurrent queries
- [ ] Reset functionality

**Test Structure**:

```python
@pytest.mark.unit
class TestSemanticSearchPipeline:
    """Unit tests for semantic search pipeline."""

    @patch("semantic_search.DocumentConverter")
    @patch("semantic_search.Chroma")
    def test_init_success()

    @patch("semantic_search.DocumentConverter")
    def test_load_paper_from_markdown()

    @patch("semantic_search.Chroma")
    def test_semantic_qa_success()

    def test_extract_source_chunks()
    def test_confidence_calculation()
    def test_reset()

@pytest.mark.integration
class TestSemanticSearchIntegration:
    """Integration tests with actual markdown conversion."""

    def test_complete_search_workflow()
    def test_concurrent_queries()
```

### 4. semantic_validator.py

**Purpose**: Cross-check parsed values with paper text
**Priority**: Critical
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] SemanticValidator initialization
- [ ] Coefficient validation (match/mismatch)
- [ ] Summary statistic validation
- [ ] Sample size validation
- [ ] Batch coefficient validation
- [ ] Number extraction from text
- [ ] Value comparison (relative/absolute)
- [ ] Confidence adjustment logic
- [ ] Table summary validation
- [ ] Source info extraction

**Test Structure**:

```python
@pytest.mark.unit
class TestSemanticValidator:
    """Unit tests for semantic validator."""

    @pytest.mark.asyncio
    async def test_validate_coefficient_match()

    @pytest.mark.asyncio
    async def test_validate_coefficient_mismatch()

    @pytest.mark.asyncio
    async def test_validate_summary_statistic()

    @pytest.mark.asyncio
    async def test_batch_validate_coefficients()

    def test_extract_number_from_text()
    def test_compare_values()
    def test_adjust_confidence()

@pytest.mark.integration
class TestSemanticValidatorIntegration:
    """Integration tests with real paper data."""

    @pytest.mark.asyncio
    async def test_validate_real_regression_table()
```

### 5. context_extractors.py

**Purpose**: Extract rich context for tables using RAG
**Priority**: Critical
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] StudyContextExtractor initialization
- [ ] Study context extraction (location, sample, timeline)
- [ ] InterventionContextExtractor initialization
- [ ] Intervention context extraction
- [ ] OutcomeContextExtractor initialization
- [ ] Outcome context extraction
- [ ] MethodologyContextExtractor initialization
- [ ] Methodology context extraction
- [ ] Confidence scoring
- [ ] Source attribution
- [ ] Missing context handling
- [ ] Concurrent extraction

**Test Structure**:

```python
@pytest.mark.unit
class TestStudyContextExtractor:
    """Tests for study context extraction."""

    @pytest.mark.asyncio
    async def test_extract_study_context_complete()

    @pytest.mark.asyncio
    async def test_extract_study_context_partial()

    def test_confidence_calculation()

@pytest.mark.unit
class TestInterventionContextExtractor:
    """Tests for intervention context extraction."""

    @pytest.mark.asyncio
    async def test_extract_intervention_context()

@pytest.mark.unit
class TestOutcomeContextExtractor:
    """Tests for outcome context extraction."""

    @pytest.mark.asyncio
    async def test_extract_outcome_context()

@pytest.mark.unit
class TestMethodologyContextExtractor:
    """Tests for methodology context extraction."""

    @pytest.mark.asyncio
    async def test_extract_methodology_context()

@pytest.mark.integration
class TestContextExtractorsIntegration:
    """Integration tests for all extractors."""

    @pytest.mark.asyncio
    async def test_extract_all_contexts_for_table()
```

### 6. table_augmenter.py

**Purpose**: Main orchestrator for augmentation
**Priority**: Critical
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] TableAugmenter initialization
- [ ] Load paper from markdown/PDF
- [ ] Augment single table with all contexts
- [ ] Augment regression table (coefficients + contexts)
- [ ] Augment summary stats table
- [ ] Augment balance table
- [ ] Validate table values
- [ ] Batch augmentation (multiple tables)
- [ ] Error handling (missing paper, invalid table)
- [ ] Progress tracking
- [ ] Reset functionality

**Test Structure**:

```python
@pytest.mark.unit
class TestTableAugmenter:
    """Unit tests for table augmenter."""

    @patch("table_augmenter.SemanticSearchPipeline")
    def test_init_success()

    @patch("table_augmenter.DocumentConverter")
    @pytest.mark.asyncio
    async def test_load_paper_from_markdown()

    @patch("table_augmenter.SemanticSearchPipeline")
    @pytest.mark.asyncio
    async def test_augment_table_regression()

    @pytest.mark.asyncio
    async def test_validate_table_values()

    @pytest.mark.asyncio
    async def test_batch_augment_tables()

@pytest.mark.integration
class TestTableAugmenterIntegration:
    """Integration tests with real data."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_augmentation_workflow()
```

### 7. Integration with parse.py

**Purpose**: End-to-end extraction with augmentation
**Priority**: High
**Status**: ⏸️ Not started

**Required Tests**:

- [ ] Extract tables with augmentation enabled
- [ ] Extract tables without augmentation (baseline)
- [ ] Compare augmented vs non-augmented output
- [ ] Verify context fields populated
- [ ] Verify validation results attached
- [ ] Performance benchmarking

**Test Structure**:

```python
@pytest.mark.integration
class TestAugmentedExtraction:
    """Integration tests for augmented table extraction."""

    @pytest.mark.slow
    def test_extract_with_augmentation()

    def test_extract_without_augmentation()

    def test_compare_augmented_output()

    @pytest.mark.slow
    def test_end_to_end_real_paper()
```

## Test Data Requirements

### Sample Papers

Need representative test papers covering:

- ✅ Simple RCT with regression tables (conftest.py fixture)
- ⏸️ Complex paper with multiple table types
- ⏸️ Paper with summary statistics
- ⏸️ Paper with balance tables
- ⏸️ Paper with appendix tables

### Expected Outputs

For each test paper, create:

- ⏸️ Ground truth table structures
- ⏸️ Expected context values
- ⏸️ Expected validation results
- ⏸️ Performance baselines

## Testing Strategy

### Phase 1: Unit Tests (Week 1)

**Goal**: Test individual components in isolation

1. **Day 1-2**: Test data models and configuration
   - augmentation_config.py
   - context_models.py

2. **Day 3-4**: Test search and validation
   - semantic_search.py
   - semantic_validator.py

3. **Day 5**: Test context extractors
   - context_extractors.py

### Phase 2: Integration Tests (Week 2)

**Goal**: Test component interactions

1. **Day 1-2**: Test augmenter orchestration
   - table_augmenter.py

2. **Day 3-4**: Test end-to-end workflows
   - Integration with parse.py
   - Multi-table augmentation

3. **Day 5**: Performance and edge cases
   - Concurrent processing
   - Error recovery
   - Resource usage

### Phase 3: Validation with Real Papers (Week 3)

**Goal**: Test with actual research papers

1. **Day 1-2**: Simple papers
   - Single regression table
   - Basic RCT structure

2. **Day 3-4**: Complex papers
   - Multiple table types
   - Appendix tables
   - Complex interventions

3. **Day 5**: Edge cases
   - Scanned PDFs
   - Unusual formats
   - Missing information

## Success Criteria

### Code Coverage

- [ ] All new modules: >90% coverage
- [ ] Integration tests: >80% coverage
- [ ] Overall project: >75% coverage

### Test Quality

- [ ] All unit tests pass consistently
- [ ] Integration tests pass with mocked LLMs
- [ ] Slow tests pass with real LLMs (may require API keys)
- [ ] No flaky tests (>95% pass rate)

### Functional Requirements

- [ ] Context extraction accuracy >80%
- [ ] Validation catches OCR errors
- [ ] Performance <5s per table (excluding LLM calls)
- [ ] Handles errors gracefully
- [ ] Progress tracking works correctly

### Documentation

- [ ] All tests have clear docstrings
- [ ] Test README updated
- [ ] Test fixtures documented
- [ ] Performance benchmarks recorded

## Running Tests

### Quick Commands

```bash
# Run all new semantic augmentation tests
uv run pytest tests/test_semantic*.py tests/test_augment*.py tests/test_context*.py -v

# Run only fast unit tests
uv run pytest tests/test_semantic*.py -m "unit and not slow"

# Run integration tests
uv run pytest tests/test_augment*.py -m integration

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing tests/test_semantic*.py
```

### Test Markers

All new tests should use appropriate markers:

```python
@pytest.mark.unit  # Fast unit tests with mocks
@pytest.mark.integration  # Multi-component tests
@pytest.mark.slow  # Tests requiring real LLM calls
@pytest.mark.asyncio  # Async tests
```

## Test File Naming

New test files to create:

- `test_augmentation_config.py` - Configuration tests
- `test_context_models.py` - Pydantic model tests
- `test_semantic_search.py` - Semantic search pipeline tests
- `test_semantic_validator.py` - Validation tests
- `test_context_extractors.py` - Context extraction tests
- `test_table_augmenter.py` - Augmenter orchestration tests
- Update `test_integration.py` - Add augmented extraction tests

## Risk Assessment

### High Risk

- **Async code complexity**: Many concurrent operations
  - *Mitigation*: Thorough async test coverage, use pytest-asyncio
- **LLM API dependencies**: Tests may require API keys
  - *Mitigation*: Mock LLM responses for unit tests, mark slow tests
- **Vector DB state**: ChromaDB state management
  - *Mitigation*: Reset fixtures, isolated test databases

### Medium Risk

- **Test data quality**: Need realistic test papers
  - *Mitigation*: Use existing Evidence Summaries test fixtures
- **Performance variability**: LLM response times vary
  - *Mitigation*: Set generous timeouts for slow tests

### Low Risk

- **Test maintenance**: Many new tests to maintain
  - *Mitigation*: Clear structure, good documentation

## Resources

### Existing Tests to Reference

- `tests/test_rag_pipeline.py` - RAG pipeline patterns (100% coverage)
- `tests/test_integration.py` - Integration test patterns
- `tests/conftest.py` - Fixture patterns

### Tools

- pytest - Test framework
- pytest-asyncio - Async test support
- pytest-mock - Mocking utilities
- pytest-cov - Coverage reporting

### Documentation

- [pytest docs](https://docs.pytest.org/)
- [pytest-asyncio docs](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock docs](https://docs.python.org/3/library/unittest.mock.html)

## Next Steps

1. ✅ Create this testing plan
2. ⏸️ Create test files with skeleton test classes
3. ⏸️ Implement unit tests for augmentation_config.py
4. ⏸️ Implement unit tests for context_models.py
5. ⏸️ Implement unit tests for semantic_search.py
6. ⏸️ Continue with remaining modules
7. ⏸️ Update SUBAGENT_ARCHITECTURE.md with progress

## Change Log

- **2025-11-06**: Created Phase 8 testing plan
- **2025-11-06**: Identified 7 new modules requiring tests
- **2025-11-06**: Defined 3-week testing strategy
