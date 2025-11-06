---
name: docling
description: This skill should be used when users need to convert PDF, DOCX, or DOC files to Markdown, extract tables (especially balance tables, summary tables, regression tables, and appendix tables from research papers), extract figures and images, or process academic documents. Use this skill for document conversion, structured data extraction from research papers, and working with complex document layouts.
---

# Docling Research Paper Processing Skill

This skill provides expertise in using docling, an AI-powered document processing tool
developed by IBM Research, specifically optimized for extracting structured data from
research papers including tables, figures, formulas, and complex layouts.

## About Docling

Docling is an open-source library that simplifies document processing with advanced PDF
understanding capabilities. It preserves relationships between text, tables, and formulas,
making it ideal for academic and research document processing.

### Key Capabilities

- **Advanced PDF Understanding**: Page layout, reading order, table structure, code,
  formulas, image classification
- **Research Paper Tables**: Extract balance tables, summary statistics, regression
  tables, appendix tables
- **Figure Extraction**: Export figures and images with high resolution
- **Multiple Export Formats**: Markdown, HTML, JSON, DocTags
- **Vision Language Models**: Enhanced understanding with GraniteDocling and other VLMs
- **OCR Support**: Process scanned documents
- **Batch Processing**: Handle multiple documents efficiently
- **Format Support**: PDF, DOCX, PPTX, XLSX, HTML, images (PNG, TIFF, JPEG)

## When to Use This Skill

Use this skill when users:

- Need to convert research papers (PDF/DOCX) to Markdown
- Want to extract tables from academic papers (regression tables, summary statistics,
  balance tables, appendix tables)
- Need to extract figures, charts, and images from research documents
- Want to preserve complex document structure and formatting
- Need to process multiple research papers in batch
- Want to extract formulas and equations from papers
- Need OCR for scanned research documents
- Want to build RAG systems with research paper content

## How to Use This Skill

### Installation

Docling is already installed in your project via pyproject.toml:

```toml
dependencies = [
    "docling>=2.60.1",
]
```

Verify installation:

```bash
uv run docling --help
```

For standalone installation:

```bash
pip install docling

# Or with all features including VLM support
pip install "docling[all]"
```

### Basic Workflow

#### 1. Simple PDF to Markdown Conversion

Convert a research paper to Markdown:

```python
from docling.document_converter import DocumentConverter

# Local file or URL
source = "path/to/research_paper.pdf"
# Or: source = "https://arxiv.org/pdf/2408.09869"

converter = DocumentConverter()
result = converter.convert(source)

# Export to markdown
markdown_content = result.document.export_to_markdown()
print(markdown_content)

# Save to file
with open("output.md", "w") as f:
    f.write(markdown_content)
```

#### 2. CLI Usage

Quick conversion from command line using `uv run docling` (since docling is installed
in your virtual environment):

```bash
# Convert PDF to markdown
uv run docling research_paper.pdf

# Convert from URL
uv run docling https://arxiv.org/pdf/2206.01062

# Use Vision Language Model for better accuracy
uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf

# Specify output format
uv run docling --to md paper.pdf
uv run docling --to json paper.pdf
uv run docling --to html paper.pdf

# Specify output directory
uv run docling --output ./output_dir paper.pdf
```

**Note:** If docling is installed globally, you can use `docling` directly without
`uv run`.

### Extracting Tables from Research Papers

This is crucial for extracting regression tables, summary statistics, balance tables,
and appendix tables from research papers.

#### Export All Tables

```python
import logging
from pathlib import Path
import pandas as pd
from docling.document_converter import DocumentConverter

# Initialize converter
doc_converter = DocumentConverter()

# Convert research paper
input_doc_path = Path("research_paper.pdf")
conv_res = doc_converter.convert(input_doc_path)

# Create output directory
output_dir = Path("extracted_tables")
output_dir.mkdir(parents=True, exist_ok=True)

doc_filename = conv_res.input.file.stem

# Export all tables
for table_ix, table in enumerate(conv_res.document.tables):
    # Convert to pandas DataFrame
    table_df: pd.DataFrame = table.export_to_dataframe()

    print(f"\n## Table {table_ix + 1}")
    print(table_df.to_markdown())

    # Save as CSV
    csv_filename = output_dir / f"{doc_filename}_table_{table_ix + 1}.csv"
    table_df.to_csv(csv_filename, index=False)

    # Save as HTML
    html_filename = output_dir / f"{doc_filename}_table_{table_ix + 1}.html"
    with html_filename.open("w") as fp:
        fp.write(table.export_to_html(doc=conv_res.document))

    # Save as Markdown
    md_filename = output_dir / f"{doc_filename}_table_{table_ix + 1}.md"
    with md_filename.open("w") as fp:
        fp.write(table_df.to_markdown(index=False))

print(f"\nExtracted {len(conv_res.document.tables)} tables")
```

#### Advanced Table Extraction Configuration

For complex tables (common in research papers):

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure pipeline for better table extraction
pipeline_options = PdfPipelineOptions()

# Use ACCURATE mode for complex research paper tables
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# Disable cell matching for multi-column layouts (common in research papers)
pipeline_options.table_structure_options.do_cell_matching = False

# Create converter with custom options
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

conv_res = doc_converter.convert("research_paper.pdf")
```

### Extracting Figures and Images

Critical for extracting charts, plots, diagrams, and visual data from research papers.

#### Export Figures with High Resolution

```python
from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure for high-resolution image export
IMAGE_RESOLUTION_SCALE = 2.0  # Increase for higher quality

pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Convert document
input_doc_path = Path("research_paper.pdf")
conv_res = doc_converter.convert(input_doc_path)

# Create output directory
output_dir = Path("extracted_figures")
output_dir.mkdir(parents=True, exist_ok=True)

doc_filename = conv_res.input.file.stem

# Export page images (useful for presentations/references)
for page_no, page in conv_res.document.pages.items():
    page_image_filename = output_dir / f"{doc_filename}_page_{page_no}.png"
    with page_image_filename.open("wb") as fp:
        page.image.pil_image.save(fp, format="PNG")

# Export figures and table images separately
table_counter = 0
figure_counter = 0

for element, _level in conv_res.document.iterate_items():
    if isinstance(element, TableItem):
        table_counter += 1
        element_image_filename = (
            output_dir / f"{doc_filename}_table_image_{table_counter}.png"
        )
        with element_image_filename.open("wb") as fp:
            element.get_image(conv_res.document).save(fp, "PNG")

    elif isinstance(element, PictureItem):
        figure_counter += 1
        element_image_filename = (
            output_dir / f"{doc_filename}_figure_{figure_counter}.png"
        )
        with element_image_filename.open("wb") as fp:
            element.get_image(conv_res.document).save(fp, "PNG")

print(f"\nExtracted {figure_counter} figures and {table_counter} table images")

# Export markdown with embedded images
md_filename = output_dir / f"{doc_filename}_with_images.md"
conv_res.document.save_as_markdown(
    md_filename,
    image_mode=ImageRefMode.EMBEDDED
)

# Export markdown with image references (smaller file size)
md_filename = output_dir / f"{doc_filename}_with_refs.md"
conv_res.document.save_as_markdown(
    md_filename,
    image_mode=ImageRefMode.REFERENCED
)
```

### Batch Processing Research Papers

Process multiple papers efficiently:

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

# Get all PDFs in directory
papers_dir = Path("research_papers")
output_dir = Path("processed_papers")
output_dir.mkdir(parents=True, exist_ok=True)

converter = DocumentConverter()

pdf_files = list(papers_dir.glob("*.pdf"))

for pdf_file in pdf_files:
    print(f"\nProcessing: {pdf_file.name}")

    try:
        result = converter.convert(pdf_file)

        # Save markdown
        md_output = output_dir / f"{pdf_file.stem}.md"
        with md_output.open("w") as f:
            f.write(result.document.export_to_markdown())

        # Save JSON (preserves all structure)
        json_output = output_dir / f"{pdf_file.stem}.json"
        with json_output.open("w") as f:
            f.write(result.document.export_to_json())

        print(f"  ✓ Converted successfully")
        print(f"  - Tables found: {len(result.document.tables)}")
        print(f"  - Pages: {len(result.document.pages)}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"\nProcessed {len(pdf_files)} papers")
```

### Using Vision Language Models

For enhanced understanding of complex layouts and figures:

```bash
# CLI with VLM
uv run docling --pipeline vlm --vlm-model granite_docling research_paper.pdf

# Available VLM models:
# - granite_docling (recommended, fast on Apple Silicon with MLX)
# - smoldocling
# - granite_vision
# - got_ocr_2
```

Python API:

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.document_converter import DocumentConverter, VlmFormatOption

pipeline_options = VlmPipelineOptions()
# Configure VLM options as needed

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: VlmFormatOption(pipeline_options=pipeline_options)
    }
)

result = doc_converter.convert("research_paper.pdf")
```

### OCR for Scanned Research Papers

```bash
# Enable OCR
uv run docling --ocr paper_scan.pdf

# Force OCR (replace existing text)
uv run docling --force-ocr paper_scan.pdf

# Specify OCR engine
uv run docling --ocr --ocr-engine tesseract paper_scan.pdf
uv run docling --ocr --ocr-engine easyocr paper_scan.pdf

# Multiple languages
uv run docling --ocr --ocr-lang eng,fra paper_scan.pdf
```

Python API:

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = False  # Set True to force OCR

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

### Advanced Configuration

#### Document Limits

For large research papers:

```python
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions()
pipeline_options.max_num_pages = 500  # Process up to 500 pages
pipeline_options.max_file_size = 52428800  # 50 MB limit (in bytes)
```

#### GPU Acceleration

```bash
# Use CUDA GPU
uv run docling --device cuda research_paper.pdf

# Use Apple Silicon GPU (MPS)
uv run docling --device mps research_paper.pdf

# Specify number of threads
uv run docling --num-threads 8 research_paper.pdf

# Page batch size (higher = more memory, faster)
uv run docling --page-batch-size 8 research_paper.pdf
```

#### Model Download for Offline Use

```bash
# Download all models for offline processing
uv run docling-tools models download

# Or if installed globally:
# docling-tools models download

# Models are cached in: $HOME/.cache/docling/models
```

Custom model path:

```python
pipeline_options = PdfPipelineOptions()
pipeline_options.artifacts_path = "/path/to/models"
```

Or via environment variable:

```bash
export DOCLING_ARTIFACTS_PATH=/path/to/models
```

### Working with Document Structure

Access structured document elements:

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("research_paper.pdf")
doc = result.document

# Access document structure
print(f"Title: {doc.name}")
print(f"Pages: {len(doc.pages)}")
print(f"Tables: {len(doc.tables)}")

# Iterate through document elements
for element, level in doc.iterate_items():
    print(f"{'  ' * level}{type(element).__name__}: {element.text[:50]}")

# Access metadata (when available)
# Note: metadata extraction is in development
if hasattr(doc, 'metadata'):
    print(f"Metadata: {doc.metadata}")

# Export to different formats
markdown = doc.export_to_markdown()
html = doc.export_to_html()
json_data = doc.export_to_json()
doctags = doc.export_to_doctags()
```

### Research Paper Workflow Examples

#### Complete Regression Table Extraction

```python
from pathlib import Path
import pandas as pd
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import PdfFormatOption

# Configure for accurate table extraction
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Process paper
paper_path = Path("economics_paper.pdf")
result = doc_converter.convert(paper_path)

# Extract and save all regression tables
tables_dir = Path("regression_tables")
tables_dir.mkdir(exist_ok=True)

for i, table in enumerate(result.document.tables):
    df = table.export_to_dataframe()

    # Save in multiple formats for flexibility
    base_name = f"{paper_path.stem}_table_{i+1}"

    df.to_csv(tables_dir / f"{base_name}.csv", index=False)
    df.to_excel(tables_dir / f"{base_name}.xlsx", index=False)

    with open(tables_dir / f"{base_name}.md", "w") as f:
        f.write(df.to_markdown(index=False))

    print(f"Extracted Table {i+1}: {df.shape[0]} rows × {df.shape[1]} columns")
```

#### Extract All Figures and Tables from Multiple Papers

```python
from pathlib import Path
from docling_core.types.doc import PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
import pandas as pd

# Configure for comprehensive extraction
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0
pipeline_options.generate_picture_images = True

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

papers_dir = Path("papers")
output_base = Path("extracted_data")

for paper_path in papers_dir.glob("*.pdf"):
    print(f"\nProcessing: {paper_path.name}")

    # Create paper-specific output directory
    paper_output = output_base / paper_path.stem
    paper_output.mkdir(parents=True, exist_ok=True)

    result = doc_converter.convert(paper_path)

    # Extract tables
    for i, table in enumerate(result.document.tables):
        df = table.export_to_dataframe()
        df.to_csv(paper_output / f"table_{i+1}.csv", index=False)

    # Extract figures
    fig_count = 0
    for element, _ in result.document.iterate_items():
        if isinstance(element, PictureItem):
            fig_count += 1
            img_path = paper_output / f"figure_{fig_count}.png"
            with img_path.open("wb") as fp:
                element.get_image(result.document).save(fp, "PNG")

    # Save full markdown
    with open(paper_output / "full_paper.md", "w") as f:
        f.write(result.document.export_to_markdown())

    print(f"  - Tables: {len(result.document.tables)}")
    print(f"  - Figures: {fig_count}")
```

### CLI Reference

Common command-line patterns (using `uv run docling` since docling is in your virtual
environment):

```bash
# Basic conversion
uv run docling paper.pdf
uv run docling paper.docx

# Output format options
uv run docling --to md paper.pdf              # Markdown (default)
uv run docling --to json paper.pdf            # JSON
uv run docling --to html paper.pdf            # HTML
uv run docling --to text paper.pdf            # Plain text

# Pipeline selection
uv run docling --pipeline standard paper.pdf   # Default pipeline
uv run docling --pipeline vlm paper.pdf        # Vision Language Model
uv run docling --pipeline legacy paper.pdf     # Legacy pipeline

# Image handling
uv run docling --image-export-mode embedded paper.pdf     # Embed images
uv run docling --image-export-mode referenced paper.pdf   # Reference images
uv run docling --image-export-mode placeholder paper.pdf  # Placeholders

# OCR options
uv run docling --ocr paper.pdf                           # Enable OCR
uv run docling --force-ocr paper.pdf                     # Force full OCR
uv run docling --ocr-engine tesseract paper.pdf          # Specific OCR engine
uv run docling --ocr-lang eng,spa,fra paper.pdf          # Multiple languages

# Performance tuning
uv run docling --device cuda paper.pdf                   # Use GPU
uv run docling --num-threads 8 paper.pdf                 # Parallel processing
uv run docling --page-batch-size 4 paper.pdf             # Batch size

# Output control
uv run docling --output ./results paper.pdf              # Output directory
uv run docling -v paper.pdf                              # Verbose output
uv run docling -vv paper.pdf                             # Very verbose

# Debugging
uv run docling --debug-visualize-tables paper.pdf        # Visualize tables
uv run docling --debug-visualize-ocr paper.pdf           # Visualize OCR
uv run docling --debug-visualize-layout paper.pdf        # Visualize layout
```

**Note:** If docling is installed globally, you can omit `uv run` and use `docling`
directly.

### Best Practices for Research Papers

1. **Use ACCURATE mode for tables**: Research papers often have complex tables with
   merged cells and multi-level headers

   ```python
   pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
   ```

2. **Increase image resolution**: For figures with small text or detailed charts

   ```python
   pipeline_options.images_scale = 2.0  # or higher
   ```

3. **Disable cell matching for multi-column layouts**: Improves accuracy for papers
   with two-column formats

   ```python
   pipeline_options.table_structure_options.do_cell_matching = False
   ```

4. **Use VLM for complex layouts**: When standard pipeline struggles with
   figures/tables

   ```bash
   uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf
   ```

5. **Save in multiple formats**: For maximum flexibility in downstream analysis

   ```python
   # Save as Markdown, JSON, and CSV
   doc.save_as_markdown("paper.md")
   with open("paper.json", "w") as f:
       f.write(doc.export_to_json())
   ```

6. **Process in batches**: For large collections of papers

   ```python
   # Use batch processing with error handling
   for paper in papers:
       try:
           result = converter.convert(paper)
       except Exception as e:
           log_error(paper, e)
   ```

7. **Enable OCR for scanned papers**: Many older papers are scanned images

   ```python
   pipeline_options.do_ocr = True
   ```

### Troubleshooting

#### Tables Not Detected

- Use ACCURATE mode: `pipeline_options.table_structure_options.mode =
  TableFormerMode.ACCURATE`
- Try VLM pipeline: `uv run docling --pipeline vlm paper.pdf`
- Disable cell matching: `pipeline_options.table_structure_options.do_cell_matching =
  False`

#### Poor Quality Figures

- Increase resolution: `pipeline_options.images_scale = 3.0`
- Ensure image generation is enabled:
  `pipeline_options.generate_picture_images = True`

#### Scanned Papers Not Processing

- Enable OCR: `uv run docling --ocr paper.pdf`
- Try different OCR engines: `--ocr-engine tesseract` or `--ocr-engine easyocr`
- Force OCR: `--force-ocr`

#### Out of Memory Errors

- Reduce batch size: `--page-batch-size 2`
- Reduce threads: `--num-threads 2`
- Set page limit: `pipeline_options.max_num_pages = 100`
- Process on GPU: `--device cuda`

#### Slow Processing

- Use GPU: `--device cuda` or `--device mps`
- Increase threads: `--num-threads 8`
- Increase batch size: `--page-batch-size 8`
- Use FAST mode for tables: `TableFormerMode.FAST` (less accurate)

## Installation

Docling is already installed in your project via `pyproject.toml`:

```toml
dependencies = [
    "docling>=2.60.1",
]
```

Verify installation:

```bash
uv run docling --help
uv run python -c "from docling.document_converter import DocumentConverter; print('OK')"
```

For standalone installation:

```bash
pip install docling

# With all features (VLM, OCR, etc.)
pip install "docling[all]"
```

Download models for offline use:

```bash
pip install docling-tools
uv run docling-tools models download
# Or: docling-tools models download (if installed globally)
```

## Integration with Other Tools

Docling integrates with popular frameworks:

- **LangChain**: Document loaders for RAG
- **LlamaIndex**: Data connectors
- **Haystack**: Document converters
- **Crew AI**: Research agents

See the official documentation for integration examples.

## Resources

- Official documentation: <https://docling-project.github.io/docling/>
- GitHub repository: <https://github.com/docling-project/docling>
- PyPI package: <https://pypi.org/project/docling/>
- Discussion forum: <https://github.com/docling-project/docling/discussions>

## Reference Files

For detailed API documentation:

- Check `references/` directory for additional examples and code snippets
