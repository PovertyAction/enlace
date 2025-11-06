---
name: pdf-processor
description: Convert PDF research papers to Markdown with table/figure extraction. Automatically routes between marker (fast, default) or docling (VLM-enhanced) based on complexity. Use for extracting regression tables, summary statistics, balance tables, and figures from academic papers.
---

# PDF Research Paper Processing

Unified skill for converting PDF research papers to Markdown with high-accuracy table and figure extraction. This skill intelligently routes between two powerful backends based on your needs.

## When to Use This Skill

Use this skill when you need to:

- Convert research papers (PDF/DOCX) to Markdown
- Extract tables: regression results, summary statistics, balance tables, appendix tables
- Extract figures, charts, and diagrams
- Process academic documents with complex layouts
- Batch process multiple papers
- Extract equations and formulas
- Build RAG systems with research paper content
- OCR scanned documents

## Tool Selection

This skill uses **two backends** that can be used interchangeably:

### **marker-pdf** (Default - Recommended)

- ⚡ **Fast**: Up to 25 pages/second on GPU
- 🎯 **Accurate**: Benchmark-leading accuracy on research papers
- 📊 **Excellent table extraction**: Optimized for research paper tables
- 🖼️ **Image extraction**: Automatic figure and chart extraction
- 📐 **LaTeX equations**: $$-fenced equation output
- 🔧 **Formats**: Markdown, JSON, HTML, chunks (for RAG)
- 💻 **Hardware**: GPU/CPU/MPS support

**Use marker when:**

- Speed is important
- Processing many papers in batch
- Standard research papers with typical layouts
- You need JSON/chunks output for RAG systems

### **docling** (VLM-Enhanced Alternative)

- 🤖 **VLM support**: Vision Language Models for complex understanding
- 🏢 **IBM Research**: Production-grade tool
- 📑 **DOCX support**: Better DOCX/DOC processing
- 🎨 **Layout analysis**: Advanced page layout understanding
- 🔄 **Multiple formats**: PDF, DOCX, PPTX, XLSX, HTML

**Use docling when:**

- Very complex layouts or unusual formatting
- Need VLM understanding for better accuracy
- Processing DOCX/DOC files
- Require fine-grained layout analysis

## Quick Start

### Command-Line Usage

```bash
# Process a single paper (uses marker by default)
uv run marker_single research_paper.pdf

# Process with docling instead
uv run docling research_paper.pdf

# Batch process multiple papers
uv run marker papers_directory/ --output_dir ./output

# Extract tables to JSON format
uv run marker_single paper.pdf --output_format json

# High-resolution image extraction
uv run marker_single paper.pdf --highres_image_dpi 300

# Enable VLM for complex papers (docling)
uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf
```

### Python API - Quick Conversion

```python
# Using marker (recommended for speed)
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("research_paper.pdf")
text, metadata, images = text_from_rendered(rendered)

# Save markdown
with open("output.md", "w") as f:
    f.write(text)

# Save extracted images
for img_name, img_data in images.items():
    img_data.save(f"figures/{img_name}")
```

```python
# Using docling (for VLM features)
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("research_paper.pdf")

# Export to markdown
markdown = result.document.export_to_markdown()
with open("output.md", "w") as f:
    f.write(markdown)
```

## Extracting Tables from Research Papers

### Using marker-pdf

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes

converter = PdfConverter(artifact_dict=create_model_dict())
document = converter.build_document("economics_paper.pdf")

# Extract all tables
tables = document.contained_blocks((BlockTypes.Table,))

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    # Save table HTML
    with open(f"table_{i+1}.html", "w") as f:
        f.write(table.html)

    print(f"Table {i+1}: Page {table.page_id}")
```

### Using docling

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

# Configure for accurate table extraction
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("research_paper.pdf")

# Export all tables
for i, table in enumerate(result.document.tables):
    df = table.export_to_dataframe()
    df.to_csv(f"table_{i+1}.csv", index=False)

    print(f"Table {i+1}: {df.shape[0]} rows × {df.shape[1]} columns")
```

## Extracting Figures and Images

### Using marker-pdf

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pathlib import Path

converter = PdfConverter(artifact_dict=create_model_dict())
rendered = converter("research_paper.pdf")
text, metadata, images = text_from_rendered(rendered)

# Save all figures
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

for img_name, img_data in images.items():
    img_data.save(output_dir / img_name)

print(f"Extracted {len(images)} images")
```

### Using docling

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
from docling_core.types.doc import PictureItem
from pathlib import Path

# High-resolution configuration
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0
pipeline_options.generate_picture_images = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result = converter.convert("research_paper.pdf")

# Extract figures
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

fig_count = 0
for element, _ in result.document.iterate_items():
    if isinstance(element, PictureItem):
        fig_count += 1
        with open(output_dir / f"figure_{fig_count}.png", "wb") as f:
            element.get_image(result.document).save(f, "PNG")

print(f"Extracted {fig_count} figures")
```

## Batch Processing

### Using marker-pdf (CLI)

```bash
# Batch process with parallel workers
uv run marker papers_directory/ --workers 4 --output_dir ./converted

# JSON output for all papers
uv run marker papers_directory/ --output_format json

# Skip already converted files
uv run marker papers_directory/ --skip_existing
```

### Using docling (CLI)

```bash
# Process multiple papers
for paper in papers/*.pdf; do
    uv run docling "$paper" --output ./converted
done
```

### Python API for Batch Processing

```python
from pathlib import Path
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Setup
papers_dir = Path("research_papers")
output_dir = Path("converted_papers")
output_dir.mkdir(exist_ok=True)

# Initialize once (reuse for all papers)
converter = PdfConverter(artifact_dict=create_model_dict())

for pdf_file in papers_dir.glob("*.pdf"):
    print(f"Processing: {pdf_file.name}")

    try:
        rendered = converter(str(pdf_file))
        text, metadata, images = text_from_rendered(rendered)

        # Create paper-specific directory
        paper_dir = output_dir / pdf_file.stem
        paper_dir.mkdir(exist_ok=True)

        # Save markdown
        with (paper_dir / "paper.md").open("w") as f:
            f.write(text)

        # Save images
        img_dir = paper_dir / "images"
        img_dir.mkdir(exist_ok=True)
        for img_name, img_data in images.items():
            img_data.save(img_dir / img_name)

        print(f"  ✓ Success - {len(images)} images")

    except Exception as e:
        print(f"  ✗ Error: {e}")
```

## Advanced Features

### OCR for Scanned Papers

```bash
# marker (OCR enabled by default)
uv run marker_single scanned_paper.pdf

# marker with high-resolution OCR
uv run marker_single scanned_paper.pdf --highres_image_dpi 300

# docling with OCR
uv run docling --ocr scanned_paper.pdf --ocr-engine tesseract
```

### LLM/VLM Enhancement

```bash
# marker with LLM (for cross-page table merging)
uv run marker_single paper.pdf --llm_service marker.services.gemini.GoogleGeminiService

# docling with VLM (for complex layout understanding)
uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf
```

### Specific Page Ranges

```bash
# marker - process specific pages
uv run marker_single paper.pdf --page_range "0,5-10,20"

# Process just the appendix (e.g., pages 30-50)
uv run marker_single paper.pdf --page_range "30-50"
```

## Output Formats

### Markdown (Default)

- Human-readable format
- Image references
- Formatted tables
- LaTeX equations

```bash
uv run marker_single paper.pdf --output_format markdown
uv run docling paper.pdf --to md
```

### JSON (Structured Data)

- Programmatic access
- Complete document structure
- Ideal for data extraction

```bash
uv run marker_single paper.pdf --output_format json
uv run docling paper.pdf --to json
```

### HTML (Web-Ready)

```bash
uv run marker_single paper.pdf --output_format html
uv run docling paper.pdf --to html
```

### Chunks (RAG/Embeddings)

```bash
# marker only - optimized for vector databases
uv run marker_single paper.pdf --output_format chunks
```

## Best Practices

1. **Start with marker for speed**: Default to marker-pdf unless you need specific docling features

2. **Use JSON for data extraction**: Structured format makes parsing easier

   ```bash
   uv run marker_single paper.pdf --output_format json
   ```

3. **Enable VLM for complex papers**: When standard extraction struggles

   ```bash
   uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf
   ```

4. **Batch with parallel processing**: Faster for many papers

   ```bash
   uv run marker papers/ --workers 4
   ```

5. **High-resolution for detailed figures**:

   ```bash
   uv run marker_single paper.pdf --highres_image_dpi 300
   ```

6. **Save in multiple formats**: For downstream flexibility

   ```python
   # Save markdown and JSON
   with open("paper.md", "w") as f:
       f.write(text)
   with open("paper.json", "w") as f:
       json.dump(rendered, f)
   ```

## Troubleshooting

### Tables Not Extracted Correctly

**marker solution:**

```bash
# Enable LLM enhancement
uv run marker_single paper.pdf --llm_service marker.services.gemini.GoogleGeminiService

# Use table-specific converter
uv run marker_single paper.pdf --converter_cls marker.converters.table.TableConverter
```

**docling solution:**

```bash
# Use ACCURATE mode
uv run docling paper.pdf

# Try VLM pipeline
uv run docling --pipeline vlm paper.pdf
```

### Poor Quality Figures

```bash
# marker: increase DPI
uv run marker_single paper.pdf --highres_image_dpi 300

# docling: increase image scale
# (via Python API: pipeline_options.images_scale = 3.0)
```

### Slow Processing

```bash
# marker: use GPU, multiple workers
uv run marker papers/ --workers 8

# docling: use GPU
uv run docling --device cuda paper.pdf
```

### Memory Issues

```bash
# marker: process page ranges
uv run marker_single paper.pdf --page_range "0-50"

# docling: reduce batch size
uv run docling --page-batch-size 2 paper.pdf
```

## Comparison: marker vs docling

| Feature | marker | docling |
|---------|--------|---------|
| **Speed** | ⚡⚡⚡ Very Fast (25 pages/sec) | ⚡⚡ Fast |
| **Table Extraction** | ⭐⭐⭐ Excellent | ⭐⭐⭐ Excellent |
| **Figures** | ⭐⭐⭐ Excellent | ⭐⭐⭐ Excellent |
| **VLM Support** | Optional (Gemini) | ✓ Built-in (Granite) |
| **DOCX Support** | ✓ | ⭐⭐⭐ Better |
| **Output Formats** | MD, JSON, HTML, chunks | MD, JSON, HTML, text, DocTags |
| **RAG Optimization** | ⭐⭐⭐ Chunks format | ⭐⭐ Good |
| **GPU Support** | ✓ CUDA/MPS | ✓ CUDA/MPS |
| **Batch Processing** | ⭐⭐⭐ Parallel workers | ⭐⭐ Good |
| **License** | GPL-3.0 | Open source |

**Recommendation:**

- **Default to marker** for most research papers (faster, excellent accuracy)
- **Use docling** when you need VLM features or are processing DOCX files
- **Try both** if one doesn't work well for your specific paper

## Integration with Research Workflow

This skill integrates with:

- **research-analyst**: Extract tables → feed to structured extraction
- **stat-convert**: PDF → tables → DuckDB conversion
- **pyfixest**: Extract data → econometric analysis
- **quarto**: Include extracted figures in reports

## Resources

### marker-pdf

- GitHub: <https://github.com/datalab-to/marker>
- PyPI: <https://pypi.org/project/marker-pdf/>
- Discord: discord.gg/KuZwXNGnfH

### docling

- Docs: <https://docling-project.github.io/docling/>
- GitHub: <https://github.com/docling-project/docling>
- PyPI: <https://pypi.org/project/docling/>

## Reference Files

For detailed examples and advanced usage:

- `references/marker_details.md` - Complete marker-pdf reference
- `references/docling_details.md` - Complete docling reference
- `references/comparison.md` - Detailed feature comparison
- `scripts/` - Helper scripts for common workflows
