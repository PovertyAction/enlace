# VLM Integration Guide

**Status**: Phase 9.2.1-9.2.2 Complete
**Last Updated**: 2025-11-09
**Implementation**: Two-pass VLM strategy (Granite-Docling → Claude)

---

## Overview

The enlace VLM integration improves table extraction accuracy by using Vision-Language Models as a fallback when traditional parsing fails. This addresses the critical **6.4% standard error extraction rate** identified in Phase 8.

### Two-Pass Strategy

1. **Pass 1: Granite-Docling-258M** (Local, Fast)
   - IBM's compact 258M parameter VLM
   - Excellent table structure recognition (97% TEDS score)
   - Runs locally (no API costs)
   - Inference: 6-100 seconds depending on framework

2. **Pass 2: Claude 3.5 Sonnet** (Optional, Validation)
   - Final validation and cleanup
   - PDF vision + text cross-validation
   - Only for low-quality Granite extractions
   - Cost: ~$0.01-0.05 per table

---

## Architecture

### Core Components

#### 1. Configuration ([src/enlace/core/config.py](../src/enlace/core/config.py:67-136))

```python
class ExtractionConfig(BaseSettings):
    # VLM Enhancement (Granite-Docling + Claude)
    enable_vlm: bool = False
    vlm_backend: str = "granite"  # granite, claude, or both
    vlm_model: str = "granite-docling"
    vlm_framework: str = "auto"  # auto, transformers, or mlx (macOS)

    # Quality Triggers
    vlm_null_se_threshold: float = 0.30  # Trigger if >30% SEs missing
    vlm_null_coef_threshold: float = 0.20  # Trigger if >20% coefficients missing
    vlm_confidence_threshold: float = 0.70  # Trigger if OCR conf <70%

    # Claude Cleanup Pass (Pass 2)
    enable_claude_cleanup: bool = False
    claude_model: str = "claude-3-5-sonnet-20241022"
    claude_api_key: str | None = None
    claude_null_se_threshold: float = 0.15  # Trigger if >15% SEs still missing
    claude_max_cost_per_table: float = 0.05  # Budget limit per table
```

#### 2. Granite VLM Extractor ([src/enlace/core/vlm_extractor.py](../src/enlace/core/vlm_extractor.py:1-309))

```python
class GraniteVLMExtractor:
    """Extract tables using Granite-Docling VLM."""

    def extract_from_pdf(self, pdf_path: Path) -> dict[str, Any]:
        """Extract tables from PDF using Granite-Docling VLM.

        Returns:
            Dictionary with:
                - markdown: Full document markdown
                - tables: List of structured table data
                - metadata: VLM backend info
        """
```

**Key Features:**

- **Auto-framework detection**: Uses MLX on macOS (fast), Transformers elsewhere
- **Lazy loading**: Only imports docling VLM when needed
- **DocTags parsing**: Extracts structured table data from VLM output
- **Error handling**: Graceful fallback if VLM dependencies missing

#### 3. Quality Triggers ([src/enlace/core/parser.py](../src/enlace/core/parser.py:401-489))

```python
class TableParser:
    def _calculate_table_quality(self, table) -> dict[str, Any]:
        """Calculate quality metrics for parsed table.

        Returns:
            - null_se_rate: Proportion of missing standard errors
            - null_coef_rate: Proportion of missing coefficients
            - avg_ocr_confidence: Average OCR confidence
            - needs_vlm: Boolean indicating if VLM fallback recommended
        """
```

**Trigger Conditions:**

VLM fallback is triggered when **any** of these conditions are met:

1. **Missing Standard Errors**: `null_se_rate > 30%` (default)
2. **Missing Coefficients**: `null_coef_rate > 20%` (default)
3. **Low OCR Confidence**: `avg_ocr_confidence < 70%` (default)

#### 4. Claude Cleanup Extractor ([src/enlace/core/vlm_extractor.py](../src/enlace/core/vlm_extractor.py:194-309))

```python
class ClaudeCleanupExtractor:
    """Validate and clean VLM extractions using Claude 3.5 Sonnet."""

    async def cleanup_extraction(
        self,
        granite_extraction: dict[str, Any],
        pdf_path: Path,
        paper_text: str,
    ) -> dict[str, Any]:
        """Validate and clean Granite extraction using Claude."""
```

**Status**: Implementation pending (Phase 9.2.3)

---

## Usage

### Environment Variables

```bash
# Enable VLM fallback
export ENLACE_ENABLE_VLM=true
export ENLACE_VLM_FRAMEWORK=auto  # auto, transformers, or mlx

# Configure quality triggers
export ENLACE_VLM_NULL_SE_THRESHOLD=0.30
export ENLACE_VLM_NULL_COEF_THRESHOLD=0.20
export ENLACE_VLM_CONFIDENCE_THRESHOLD=0.70

# Enable Claude cleanup (optional)
export ENLACE_ENABLE_CLAUDE_CLEANUP=true
export ENLACE_CLAUDE_API_KEY=sk-ant-...
export ENLACE_CLAUDE_NULL_SE_THRESHOLD=0.15
```

### Python API

```python
from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor

# Create config with VLM enabled
config = ExtractionConfig(
    enable_vlm=True,
    vlm_framework="auto",
    vlm_null_se_threshold=0.30,
    enable_claude_cleanup=False,  # Optional second pass
)

# Extract paper
extractor = PaperExtractor(config)
result = extractor.extract(Path("paper.pdf"))

# Quality metrics available in result
for table in result.tables:
    quality = parser._calculate_table_quality(table)
    print(f"Table: {table.title}")
    print(f"  Null SE rate: {quality['null_se_rate']:.1%}")
    print(f"  VLM needed: {quality['needs_vlm']}")
```

### CLI (Future)

```bash
# Extract with VLM fallback
enlace extract paper.pdf --vlm --vlm-framework auto

# Extract with both Granite and Claude
enlace extract paper.pdf --vlm --claude-cleanup
```

---

## Performance Characteristics

### Granite-Docling-258M

| Framework | Platform | Inference Time | GPU Required |
|-----------|----------|----------------|--------------|
| MLX | macOS M1/M2/M3 | 6-10 sec | MPS (Apple GPU) |
| Transformers | macOS | 100-120 sec | Optional (CUDA) |
| Transformers | Linux/Windows | 80-100 sec | Optional (CUDA) |

### Expected Accuracy Improvements

| Metric | Current | + Granite | + Claude | Target |
|--------|---------|-----------|----------|--------|
| **Standard Errors** | 6.4% | ~70% | **85-90%** | 85%+ |
| **Coefficients** | 88% | 92% | **95%+** | 95%+ |
| **Dependent Variables** | 73% | 85% | **90%+** | 90%+ |

### Cost Analysis

| Strategy | Time/Table | Cost/Table | When to Use |
|----------|-----------|------------|-------------|
| Traditional Only | 5-10s | $0 | High-quality PDFs |
| + Granite | 15-110s | $0 | Scanned docs, complex tables |
| + Claude Cleanup | 17-115s | $0.01-0.05 | Critical extractions |

---

## Testing

### Unit Tests ([tests/test_vlm_integration.py](../tests/test_vlm_integration.py))

```bash
# Run VLM integration tests
uv run pytest tests/test_vlm_integration.py -v

# Test coverage:
# ✓ VLM configuration (defaults, env vars)
# ✓ Granite extractor initialization
# ✓ Quality trigger logic (SE, coef, OCR confidence)
# ✓ Pass/fail thresholds
```

**Test Results**: 8 passed, 2 skipped (10 total)

### Integration Tests (Phase 9.2.6)

Benchmark tests with ground truth annotations:

```bash
# Test VLM on benchmark dataset
uv run pytest tests/benchmark/test_vlm_accuracy.py -v

# Compare traditional vs VLM extraction
python scripts/compare_vlm_traditional.py BHKM_Liberia.pdf
```

---

## Implementation Status

### ✅ Phase 9.2.1: VLM Infrastructure (COMPLETE)

- [x] Add `GraniteVLMExtractor` class
- [x] Implement docling VLM pipeline integration
- [x] Auto-framework detection (MLX vs Transformers)
- [x] Lazy loading and error handling
- [x] Configuration options in `ExtractionConfig`

### ✅ Phase 9.2.2: Quality Triggers (COMPLETE)

- [x] Add `_calculate_table_quality()` method
- [x] Implement null SE rate trigger
- [x] Implement null coefficient rate trigger
- [x] Implement OCR confidence trigger
- [x] Unit tests for all trigger conditions

### ⏳ Phase 9.2.3: Claude Cleanup Pass (PENDING)

- [ ] Implement Claude API integration
- [ ] Add PDF vision support
- [ ] Cross-validation with paper text
- [ ] Error correction and cleanup
- [ ] Cost tracking and budget limits

### ⏳ Phase 9.2.4: Result Merging (PENDING)

- [ ] Merge traditional + Granite results
- [ ] Weighted scoring algorithm
- [ ] Conflict resolution strategy
- [ ] Confidence tracking

### ⏳ Phase 9.2.5: Cost Optimization (PENDING)

- [ ] Result caching system
- [ ] Selective Claude invocation
- [ ] Token usage tracking
- [ ] Budget enforcement

### ⏳ Phase 9.2.6: Benchmark Testing (PENDING)

- [ ] Test on BHKM_Liberia.pdf
- [ ] Measure accuracy improvements
- [ ] Compare costs and performance
- [ ] Generate benchmark report

---

## Troubleshooting

### VLM Dependencies Not Found

**Error**: `Failed to import docling VLM components`

**Solution**: docling VLM is already installed via `pyproject.toml`:

```toml
"docling[easyocr,tesserocr,vlm]>=2.60.1"
```

If missing, reinstall:

```bash
uv pip install "docling[vlm]>=2.60.1"
```

### MLX Framework Not Available

**Error**: `MLX not available, falling back to Transformers`

**Solution**: MLX only works on macOS with Apple Silicon. For other platforms, use:

```bash
export ENLACE_VLM_FRAMEWORK=transformers
```

### Claude API Key Missing

**Error**: `Claude API key not found`

**Solution**: Set environment variable:

```bash
export ENLACE_CLAUDE_API_KEY=sk-ant-api03-...
```

Or pass via config:

```python
config = ExtractionConfig(
    enable_claude_cleanup=True,
    claude_api_key="sk-ant-..."
)
```

---

## Next Steps

1. **Phase 9.2.3**: Implement Claude cleanup pass
   - Integrate Anthropic SDK
   - Add PDF vision support
   - Implement cross-validation logic

2. **Phase 9.2.4**: Result merging strategy
   - Design weighted scoring algorithm
   - Handle conflicts between traditional/Granite/Claude
   - Track confidence scores

3. **Phase 9.2.6**: Benchmark testing
   - Test on BHKM_Liberia.pdf ground truth
   - Measure SE extraction: 6.4% → 85%+
   - Generate accuracy report

---

## References

- **Granite-Docling Model**: <https://huggingface.co/ibm-granite/granite-docling-258M>
- **Docling VLM Docs**: <https://docling-project.github.io/docling/usage/vision_models/>
- **Roadmap**: [docs/ROADMAP.md](ROADMAP.md#phase-92-vlm-integration-priority)
- **Test Suite**: [tests/test_vlm_integration.py](../tests/test_vlm_integration.py)
