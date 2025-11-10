# Enlace Development Roadmap

**Last Updated:** 2025-11-09

## Project Status

Enlace is a research tool for extracting structured data from development economics papers. The core extraction pipeline is **functional** with ~6,500 lines of production code. Current focus: improving extraction quality and preparing for distribution.

---

## Completed Work (Phases 1-8)

### ✅ Core Infrastructure (Phases 1-5)

- **Architecture:** src-layout package structure with proper separation of concerns
- **Extraction Pipeline:** PDF/DOCX → tables/figures/metadata with docling
- **Data Models:** 13 Pydantic models for tables, validation, extraction results
- **Validation System:** 6 validation checks (structure, completeness, accuracy, statistical, missing data, semantic)
- **CLI:** 3 commands (extract, validate, batch) with typer framework
- **Configuration:** Priority loading (defaults < file < env < CLI args)
- **Error Handling:** Custom exception hierarchy with proper logging
- **Code Quality:** All code formatted/linted with ruff (0 errors)

### ✅ OCR Enhancement (Phase 4.5)

- Hybrid OCR with Tesseract (fast) + EasyOCR (accurate fallback)
- Per-cell confidence tracking and automatic fallback triggering
- Numeric validation for common OCR errors (p-values, character substitutions)

### ✅ Semantic Augmentation (Phases 1-8, Subagent Work)

- RAG-based context extraction (ChromaDB + HuggingFace embeddings)
- 5 context extractors (variable, treatment, sample, methods, data validation)
- Cross-validation with paper text for error detection
- 78 comprehensive tests covering semantic augmentation system

### ✅ Documentation & Benchmarking (Phases 6-7)

- Complete CLI guide, API guide, configuration reference, development guide
- 4 working examples (basic, batch, validation, augmentation)
- Benchmark infrastructure with ground truth annotations
- Professional README with features and quick start

### ✅ Phase 8: Core Parsing Quality

- Enhanced coefficient extraction (88% vs 55% before)
- Improved table title extraction (67% vs 0%)
- Better dependent variable detection (73% vs 0%)
- Fixed semantic augmentation crashes
- **Critical Finding:** Standard error extraction remains poor (6.4%) due to complex table layouts

---

## Current Challenge: Standard Error Extraction

### Phase 9.1 Investigation (COMPLETED)

**Problem:** Only 6.4% of standard errors successfully extracted from economics papers.

**Root Cause:** Complex multi-row table patterns that regex cannot handle:

```text
Row 0: Variable Name     | -0.004  | -0.055      (coefficients)
Row 1:                   | (0.038) | (0.054)     (SEs - empty first cell) ✓
Row 2: Another Variable  | 0.014 (0.040) | ...   (inline SEs) ✓
Row 3: Interaction 1     | -0.148  | ***-0.113   (coefficients)
Row 4: Interaction 2     | 0.004   | -0.013      (coefficients)
Row 5: Perf Pay * Either | (0.076) | (0.111)     (SEs for rows 3-4, BUT has var name!) ✗
Row 6:                   | 0.152   | *0.086      (more coefficients!)
Row 7:                   | (0.079) | (0.110)     (SEs for row 6) ✓
```

**Issue:** Row 5 contains SEs but has a variable name in the first cell, breaking the `first_cell.strip() == ""` detection logic. Traditional regex-based parsing cannot understand that this row semantically belongs with rows 3-4.

**Attempted Solutions:**

1. Enhanced SE row detection by parentheses ratio → worse (lost coefficients)
2. Standalone SE row skipping → worse (skipped legitimate data)

**Conclusion:** Regex-based improvements have **diminishing returns**. The 6.4% → 80%+ jump requires understanding table semantics, which needs Vision-Language Models (VLMs).

---

## Remaining Work

### Phase 9.2: VLM Integration (PRIORITY)

**Goal:** Use VLM as fallback for complex tables where traditional parsing fails.

**Approach:**

```python
def parse_table(table_data):
    # 1. Try traditional parsing first
    result = traditional_parse(table_data)

    # 2. Assess quality
    if result.null_se_rate > 30% or result.low_confidence:
        # 3. Use VLM for low-quality extractions
        vlm_result = vlm_extract(table_image, paper_text)
        result = merge_results(result, vlm_result)

    return result
```

**Implementation Plan:**

1. **VLM Infrastructure (3-5 days)**
   - Add VLMConfig to ExtractionConfig
   - Create VLMTableExtractor class
   - Integrate with Claude 3.5 Sonnet API (or GPT-4o as fallback)
   - Add image cropping for table regions from PDF

2. **Hybrid Parsing Strategy (2-3 days)**
   - Modify TableParser to try traditional first
   - Trigger VLM when:
     - >30% null SEs or coefficients
     - OCR confidence <70% on >20% cells
     - Validation discrepancies >15%
   - Merge VLM + traditional results with weighted scoring

3. **Text-Based Cross-Validation (2 days)**
   - Extract value mentions from paper text via semantic search
   - Compare VLM values against text-reported values
   - Flag discrepancies for manual review
   - Boost confidence when VLM + text agree

4. **Cost Optimization (1-2 days)**
   - Cache VLM results per table
   - Use haiku for simple tables, sonnet for complex
   - Track token usage and costs
   - Implement budget limits per paper

**Expected Improvement:**

- SE extraction: 6.4% → 85%+ (VLM handles complex layouts)
- Coefficient extraction: 88% → 95%+ (VLM corrects OCR errors)
- Dependent variable: 73% → 90%+ (VLM reads from notes/captions)

**Cost:** ~$0.01-0.05 per table (mitigated by using VLM only as fallback)

**Timeline:** 8-12 days

---

### Phase 10: Packaging & Distribution (2-3 days)

**Goal:** Make enlace installable and distributable.

**Tasks:**

- [ ] Update pyproject.toml metadata (description, keywords, classifiers)
- [ ] Add author/license information
- [ ] Configure hatchling build backend
- [ ] Test installation: `uv pip install -e .`
- [ ] Test CLI: `enlace --help`, `enlace extract --help`
- [ ] Build distribution: `uv build`
- [ ] Test wheel installation: `uv pip install dist/enlace-*.whl`
- [ ] Create GitHub release workflow (optional)
- [ ] Publish to PyPI (optional)

**Deliverables:**

- Installable package via pip/uv
- Working CLI commands
- Importable Python API

---

### Phase 11: Testing (Deferred from Phase 6)

**Goal:** Comprehensive test coverage for production readiness.

**Unit Tests (Fast, Mocked):**

- `tests/core/test_extractor.py` - PaperExtractor
- `tests/core/test_parser.py` - TableParser
- `tests/core/test_validator.py` - ExtractionValidator
- `tests/core/test_config.py` - Configuration loading
- `tests/semantic/test_search.py` - Semantic search
- `tests/validators/test_*.py` - Each validation check
- `tests/cli/test_cli.py` - CLI commands

**Integration Tests (Real Components):**

- `tests/integration/test_end_to_end.py` - Full pipeline
- `tests/integration/test_batch.py` - Batch processing
- `tests/integration/test_vlm.py` - VLM integration

**Coverage Goals:**

- Overall: >80%
- Core modules: >90%
- Validators: >85%
- CLI: >70%

**Timeline:** 5-7 days

---

## Priority Order

1. **Phase 9.2 (VLM Integration)** - Biggest quality improvement, addresses critical SE extraction issue
2. **Phase 10 (Packaging)** - Make tool usable outside development environment
3. **Phase 11 (Testing)** - Production readiness and regression prevention

---

## Notes

- **Semantic augmentation** is functional but optional (requires API keys)
- **OCR** works well for scanned documents (hybrid mode recommended)
- **Benchmark suite** ready for testing once VLM integration is complete
- **Documentation** is comprehensive and up-to-date

---

## Quick Start for Contributors

```bash
# Setup
git clone <repo>
cd enlace
just get-started  # Creates venv, installs deps, sets up pre-commit

# Development
just fmt-python   # Format code
just lint-python  # Lint and auto-fix

# Testing (after Phase 11)
just test         # Run all tests
just test-cov     # Run with coverage

# CLI Usage
enlace extract paper.pdf --ocr auto
enlace validate output/paper/extraction.json
enlace batch papers/ -o batch_output --workers 4
```

---

**For detailed implementation history, see:** [docs/MIGRATION_PLAN.md](MIGRATION_PLAN.md) (archived reference)
