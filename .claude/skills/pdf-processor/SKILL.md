---
name: pdf-processor
description: Convert PDF research papers to Markdown with table/figure extraction using docling. Use for extracting regression tables, summary statistics, balance tables, and figures from academic papers.
---

# PDF Research Paper Processing

Skill for converting PDF research papers to Markdown with high-accuracy table and figure extraction using docling.

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

## Tool Features

This skill uses **docling** for PDF processing:

- 🤖 **VLM support**: Vision Language Models for complex understanding
- 🏢 **IBM Research**: Production-grade tool
- 📊 **Excellent table extraction**: Optimized for research paper tables
- 🖼️ **Image extraction**: Automatic figure and chart extraction
- 📑 **DOCX support**: Processes DOCX/DOC files
- 🎨 **Layout analysis**: Advanced page layout understanding
- 🔄 **Multiple formats**: PDF, DOCX, PPTX, XLSX, HTML

## Quick Start

### Python API - Quick Conversion

```python
# Basic conversion
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("research_paper.pdf")

# Export to markdown
markdown = result.document.export_to_markdown()
with open("output.md", "w") as f:
    f.write(markdown)
```

## Extracting Tables from Research Papers

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

```python
from docling.document_converter import DocumentConverter
from pathlib import Path

converter = DocumentConverter()
result = converter.convert("research_paper.pdf")

# Export figures
output_dir = Path("figures")
output_dir.mkdir(exist_ok=True)

for i, picture in enumerate(result.document.pictures):
    # Access image data
    if picture.image:
        picture.image.pil_image.save(output_dir / f"figure_{i+1}.png")
        print(f"Figure {i+1}: Saved to {output_dir}/figure_{i+1}.png")
```

## Batch Processing

### Python API for Batch Processing

```python
from docling.document_converter import DocumentConverter
from pathlib import Path
import asyncio

async def process_paper(pdf_path: Path, output_dir: Path):
    """Process single paper."""
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))

    # Save markdown
    md_path = output_dir / pdf_path.with_suffix(".md").name
    markdown = result.document.export_to_markdown()
    md_path.write_text(markdown)

    # Extract tables
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(exist_ok=True)
    for i, table in enumerate(result.document.tables):
        df = table.export_to_dataframe()
        table_path = tables_dir / f"{pdf_path.stem}_table_{i+1}.csv"
        df.to_csv(table_path, index=False)

    return {
        "paper": pdf_path.name,
        "tables": len(result.document.tables),
        "figures": len(result.document.pictures)
    }

async def batch_process(papers_dir: Path, output_dir: Path):
    """Process multiple papers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = list(papers_dir.glob("*.pdf"))

    tasks = [process_paper(pdf, output_dir) for pdf in pdf_files]
    results = await asyncio.gather(*tasks)

    print(f"Processed {len(results)} papers")
    for result in results:
        print(f"  {result['paper']}: {result['tables']} tables, {result['figures']} figures")

# Run batch processing
papers_dir = Path("papers")
output_dir = Path("converted")
asyncio.run(batch_process(papers_dir, output_dir))
```

## Advanced Features

### OCR for Scanned Papers

Docling automatically handles OCR for scanned PDFs:

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Enable OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True

converter = DocumentConverter()
result = converter.convert("scanned_paper.pdf")
```

### VLM Enhancement for Complex Papers

Use Vision Language Models for better understanding of complex layouts:

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.docling_parse_backend import DoclingParseBackend

# Enable VLM
pipeline_options = PdfPipelineOptions()
pipeline_options.use_vlm = True

converter = DocumentConverter()
result = converter.convert("complex_paper.pdf")
```

### Specific Page Ranges

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

# Process specific pages only
result = converter.convert("large_paper.pdf", page_numbers=[1, 2, 3, 10, 11])
```

## Output Formats

### Markdown (Default)

```python
markdown = result.document.export_to_markdown()
```

### JSON (Structured Data)

```python
import json

# Get structured document data
doc_dict = result.document.model_dump()

with open("output.json", "w") as f:
    json.dump(doc_dict, f, indent=2)
```

### HTML (Web-Ready)

```python
html = result.document.export_to_html()
with open("output.html", "w") as f:
    f.write(html)
```

## Best Practices

### For Research Papers

1. **Use ACCURATE mode** for table extraction to preserve statistical precision
2. **Extract tables separately** for validation and data analysis
3. **Save both markdown and JSON** for different downstream uses
4. **Track table captions** for proper identification in papers

### For Batch Processing

1. **Process papers in parallel** when possible
2. **Save extraction logs** with paper metadata
3. **Handle errors gracefully** with try-except blocks
4. **Verify table counts** match paper references

### For Quality

1. **Check table extraction** visually before downstream analysis
2. **Use VLM for complex layouts** or unusual formatting
3. **Validate critical numbers** manually for important papers
4. **Compare with source PDF** when in doubt

### Performance

1. **Batch similar papers together** for efficiency
2. **Use page ranges** for large documents when only specific sections needed
3. **Enable GPU** if available for faster processing
4. **Cache converted papers** to avoid re-processing

## Troubleshooting

### Tables Not Extracted Correctly

- **Try ACCURATE mode**: Use `TableFormerMode.ACCURATE` for better precision
- **Check table complexity**: Very complex multi-level headers may need manual review
- **Verify source quality**: Low-quality scans may need OCR preprocessing
- **Use VLM**: Enable VLM for better understanding of complex table layouts

### Poor Quality Figures

- **Check PDF resolution**: Low-resolution PDFs produce low-quality figures
- **Extract from high-res PDFs**: Use original paper PDFs when available
- **Verify figure references**: Ensure figures are properly embedded in PDF

### Slow Processing

- **Use page ranges**: Process only needed pages
- **Reduce quality settings** if speed is critical
- **Batch process overnight** for large document sets
- **Enable GPU** for faster processing

### Memory Issues

- **Process papers sequentially** instead of in parallel
- **Use page ranges** to process large documents in chunks
- **Close converter objects** after each paper
- **Monitor memory usage** and adjust batch size

## Integration with Research Workflow

This skill integrates with:

- **research-analyst**: Extract tables → feed to structured extraction
- **stat-convert**: PDF → tables → DuckDB conversion
- **pyfixest**: Extract data → econometric analysis
- **table-validator**: Validate extraction quality
- **content-extractor**: Full paper extraction pipeline

## Resources

### docling

- Docs: <https://docling-project.github.io/docling/>
- GitHub: <https://github.com/docling-project/docling>
- PyPI: <https://pypi.org/project/docling/>

## Reference Files

For detailed examples and advanced usage:

- `references/docling_details.md` - Complete docling reference
- `scripts/` - Example extraction scripts
