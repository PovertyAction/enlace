# Marker vs Docling: Comparison for Research Paper Processing

This document compares marker-pdf and docling for research paper processing to help
you choose the right tool for your needs.

## Quick Comparison

| Feature | Marker-PDF | Docling |
|---------|-----------|---------|
| **Speed** | Up to 25 pages/sec (GPU) | Moderate speed |
| **Accuracy** | Benchmark-leading on papers | High accuracy |
| **Installation** | Via pip (in pyproject.toml) | Via pip (in pyproject.toml) |
| **CLI** | `uv run marker_single` / `uv run marker` | `uv run docling` |
| **Python API** | Simple, converter-based | Simple, converter-based |
| **License** | GPL-3.0 (code), Modified Open Rail-M (models) | MIT (code and models) |
| **Table Extraction** | Excellent, specialized converter | Excellent, ACCURATE mode |
| **Figure Extraction** | Automatic, built-in | Requires configuration |
| **LLM Enhancement** | Optional (Gemini) | Optional (multiple VLMs) |
| **Output Formats** | MD, JSON, HTML, chunks | MD, JSON, HTML, DocTags |
| **OCR** | Surya-based | EasyOCR, Tesseract, RapidOCR |
| **GPU Support** | CUDA, CPU, MPS | CUDA, CPU, MPS |
| **Best For** | Speed, research papers, books | Complex layouts, multi-format |

## When to Use Marker-PDF

**Choose marker-pdf when you need:**

- **Maximum speed**: 25 pages/second on GPU hardware
- **Benchmark-leading accuracy**: Optimized for research papers and books
- **Simple table extraction**: Specialized TableConverter
- **Automatic image extraction**: No configuration needed
- **Chunks format**: Pre-formatted output for RAG systems
- **Quick batch processing**: Efficient parallel processing
- **Research papers**: Specifically optimized for academic documents

**Best use cases:**

- Converting large collections of research papers
- Extracting regression tables from economics papers
- Building RAG systems with academic content
- Processing books and long-form documents
- High-throughput document conversion pipelines

## When to Use Docling

**Choose docling when you need:**

- **Multiple input formats**: DOCX, PPTX, XLSX, HTML, EPUB, audio
- **MIT license**: More permissive for commercial use
- **Flexible OCR**: Multiple OCR engine options
- **IBM ecosystem**: Integration with IBM tools
- **Fine-grained control**: Extensive configuration options
- **Multi-format support**: Beyond just PDFs

**Best use cases:**

- Converting mixed document types (PDF, DOCX, PPTX)
- Projects requiring MIT licensing
- Integration with IBM AI tools
- Documents requiring specific OCR engines
- Multi-format document processing workflows

## Performance Comparison

### Speed

**Marker-PDF:**

- GPU: ~25 pages/second (H100)
- CPU: Moderate speed
- Optimized model usage (only where necessary)

**Docling:**

- GPU: Good speed with Heron layout model
- CPU: Moderate speed
- More comprehensive per-page processing

### Accuracy

Both tools achieve high accuracy on research papers:

- **Marker**: Benchmark-leading on test sets
- **Docling**: Advanced PDF understanding with table structure recognition

## Feature Comparison

### Table Extraction

**Marker-PDF:**

```python
# Specialized table converter
from marker.converters.table import TableConverter
converter = TableConverter(artifact_dict=create_model_dict())
rendered = converter("paper.pdf")
```

```bash
uv run marker_single paper.pdf \
  --converter_cls marker.converters.table.TableConverter
```

**Docling:**

```python
# Accurate mode for complex tables
from docling.datamodel.pipeline_options import TableFormerMode
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
```

```bash
# Built into standard pipeline
docling paper.pdf
```

**Winner:** Tie - both excellent, different approaches

### Figure Extraction

**Marker-PDF:**

```python
# Automatic - images extracted by default
rendered = converter("paper.pdf")
text, metadata, images = text_from_rendered(rendered)
# images is a dict of PIL Images
```

**Docling:**

```python
# Requires configuration
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2.0
```

**Winner:** Marker (automatic, simpler)

### Output Formats

**Marker-PDF:**

- Markdown (default)
- JSON (structured tree)
- HTML
- Chunks (RAG-optimized)

**Docling:**

- Markdown
- JSON
- HTML
- DocTags

**Winner:** Marker (chunks format specifically designed for RAG)

### Batch Processing

**Marker-PDF:**

```bash
# Multi-threaded batch processing
uv run marker papers_dir/ --workers 4
```

**Docling:**

```bash
# Process multiple files via Python API
# Or use jobkit for distributed processing
```

**Winner:** Marker (better built-in parallel processing via CLI)

### LLM Enhancement

**Marker-PDF:**

```bash
uv run marker_single paper.pdf \
  --llm_service marker.services.gemini.GoogleGeminiService
```

- Cross-page table merging
- Inline math handling
- Table formatting
- Form extraction

**Docling:**

```bash
uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf
```

- Multiple VLM options (GraniteDocling, SmolDocling, etc.)
- Image understanding
- Layout analysis

**Winner:** Tie - different strengths

## Installation and Setup

### Marker-PDF

```bash
# Basic installation
pip install marker-pdf

# Already in your project
# pyproject.toml: marker-pdf>=1.10.1
uv run marker_single --help
```

### Docling

```bash
# Already in your project
# pyproject.toml: docling>=2.60.1
uv run docling --help

# Basic installation (standalone)
pip install docling

# Full features
pip install "docling[all]"
```

**Winner:** Tie - both simple to install and available via uv

## Code Complexity

### Marker-PDF (Simple Conversion)

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

**Lines of code:** 6

### Docling (Simple Conversion)

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("paper.pdf")
text = result.document.export_to_markdown()
```

**Lines of code:** 4

**Winner:** Docling (simpler API)

**Note:** Both are available in your project via `pyproject.toml` and can be used with
`uv run`.

## Licensing Considerations

### Marker-PDF

- **Code:** GPL-3.0 (copyleft - modifications must be open-sourced)
- **Models:** Modified AI Pubs Open Rail-M
  - Free for: research, personal use, startups <$2M
  - Commercial: Requires license from datalab.to
- **Implication:** May require commercial license for production use

### Docling

- **Code:** MIT (permissive - can be used in proprietary software)
- **Models:** Permissive licensing
- **Implication:** More flexible for commercial use

**Winner:** Docling (MIT vs GPL)

## Recommendations

### Use Marker-PDF if

1. **Speed is critical** (large document collections)
2. **Working primarily with PDFs** (especially research papers)
3. **Need chunks format** (for RAG/embedding pipelines)
4. **Want automatic image extraction** (no configuration)
5. **Budget allows** commercial licensing (if needed)
6. **Processing research papers** (benchmark-optimized)

### Use Docling if

1. **Need MIT license** (commercial flexibility)
2. **Working with multiple formats** (DOCX, PPTX, XLSX)
3. **Require specific OCR engines** (Tesseract, EasyOCR)
4. **Need IBM ecosystem integration**
5. **Want extensive configuration options**
6. **Processing mixed document types**

### Use Both if

1. **Test both** on your specific documents
2. **Different documents** have different needs
3. **Want redundancy** (fallback option)
4. **Comparing outputs** for quality assurance

## Practical Examples

### Both installed in your project

Your `pyproject.toml` includes both:

```toml
dependencies = [
    "marker-pdf>=1.10.1",
    "docling>=2.60.1",
]
```

This gives you flexibility to choose the best tool for each task!

### When to switch between them

#### Research paper with complex tables → Marker

```bash
uv run marker_single economics_paper.pdf --output_format json
```

#### Mixed format documents → Docling

```bash
uv run docling presentation.pptx
uv run docling spreadsheet.xlsx
uv run docling document.docx
```

#### Large batch of PDFs → Marker

```bash
uv run marker papers_dir/ --workers 8 --output_format chunks
```

#### Scanned paper requiring specific OCR → Docling

```bash
uv run docling --ocr --ocr-engine tesseract --ocr-lang eng,fra scanned.pdf
```

## Conclusion

Both tools are excellent for research paper processing:

- **Marker-PDF**: Best for speed, research papers, and RAG pipelines
- **Docling**: Best for flexibility, multi-format support, and MIT licensing

**For your use case (research papers with tables/figures):**

Both are excellent choices! Consider:

- Use **Marker** for pure speed and RAG-optimized output
- Use **Docling** for MIT licensing and multi-format needs
- Having both installed gives you the best of both worlds!
