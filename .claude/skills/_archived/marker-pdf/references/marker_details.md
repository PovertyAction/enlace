---
name: marker-pdf
description: This skill should be used when users need to convert PDF files to Markdown with high accuracy, extract tables (especially balance tables, summary tables, regression tables, and appendix tables from research papers), extract figures and images, or process academic documents. Use this skill for fast, accurate document conversion optimized for research papers and structured data extraction. Marker is available via `uv run marker` for batch processing or `uv run marker_single` for individual PDFs.
---

# Marker-PDF Research Paper Processing Skill

This skill provides expertise in using marker-pdf, a high-performance open-source
document conversion tool specifically optimized for converting PDFs (especially research
papers and academic documents) to Markdown with exceptional accuracy for tables, figures,
equations, and complex layouts.

## About Marker-PDF

Marker is a GPL-3.0 licensed tool that converts PDFs, images, and other documents to
markdown, JSON, HTML, and structured formats. It achieves benchmark-leading accuracy on
research papers and books, with speeds up to 25 pages/second on GPU hardware.

### Key Capabilities

- **High Accuracy Conversion**: Optimized for books and research papers with complex
  layouts
- **Research Paper Tables**: Extract balance tables, summary statistics, regression
  tables, appendix tables with proper formatting
- **Figure & Image Extraction**: Automatic extraction and saving of images
- **Equation Support**: LaTeX-formatted equations with $$-fenced output
- **Multi-format Output**: Markdown, JSON, HTML, chunks (for RAG)
- **LLM Enhancement**: Optional LLM integration for improved accuracy (table merging,
  inline math, form extraction)
- **GPU/CPU/MPS Support**: Hardware acceleration for faster processing
- **Batch Processing**: Parallel conversion of multiple documents
- **Format Support**: PDF, images, PPTX, DOCX, XLSX, HTML, EPUB
- **Header/Footer Removal**: Automatic cleaning of repetitive elements

## When to Use This Skill

Use this skill when users:

- Need to convert research papers (PDF) to Markdown with high accuracy
- Want to extract regression tables, summary statistics, balance tables from economics
  papers
- Need to preserve complex table structures with merged cells
- Want to extract figures and charts from research documents
- Need to convert equations to LaTeX format
- Want fast batch processing of multiple papers
- Need structured JSON output for programmatic access
- Want to build RAG systems with research paper content
- Need OCR for scanned research documents
- Want cross-page table merging (with LLM enhancement)

## Installation

Marker is already installed in your project via pyproject.toml:

```toml
dependencies = [
    "marker-pdf>=1.10.1",
]
```

Verify installation:

```bash
uv run python -c "from marker.converters.pdf import PdfConverter; print('OK')"
```

## How to Use This Skill

### Command-Line Usage

Since marker is installed via uv, all commands must be prefixed with `uv run`:

#### Single PDF Conversion

Convert a single research paper:

```bash
# Basic conversion
uv run marker_single research_paper.pdf

# Specify output directory
uv run marker_single research_paper.pdf --output_dir ./output

# JSON output (best for structured data extraction)
uv run marker_single research_paper.pdf --output_format json

# HTML output
uv run marker_single research_paper.pdf --output_format html

# Chunks output (ideal for RAG systems)
uv run marker_single research_paper.pdf --output_format chunks

# Convert specific pages only
uv run marker_single paper.pdf --page_range "0,5-10,20"
```

#### Batch Processing Multiple Papers

Process all PDFs in a directory:

```bash
# Convert all PDFs in a folder
uv run marker papers_directory/

# Specify output location
uv run marker papers_directory/ --output_dir ./converted_papers

# JSON output for all papers
uv run marker papers_directory/ --output_format json

# Parallel processing with multiple workers
uv run marker papers_directory/ --workers 4

# Skip already converted files
uv run marker papers_directory/ --skip_existing

# Limit number of files to process
uv run marker papers_directory/ --max_files 10
```

#### Advanced Options

```bash
# Enable LLM enhancement for better table/equation handling
uv run marker_single paper.pdf --llm_service \
  marker.services.gemini.GoogleGeminiService

# Disable image extraction (faster, text only)
uv run marker_single paper.pdf --disable_image_extraction

# High-resolution OCR for better quality
uv run marker_single paper.pdf --highres_image_dpi 300

# Debug mode for troubleshooting
uv run marker_single paper.pdf --debug

# Disable OCR (if PDF already has good text)
uv run marker_single paper.pdf --disable_ocr
```

### Python API Usage

#### Basic PDF to Markdown Conversion

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Initialize converter
converter = PdfConverter(
    artifact_dict=create_model_dict(),
)

# Convert PDF
rendered = converter("research_paper.pdf")

# Extract text, metadata, and images
text, metadata, images = text_from_rendered(rendered)

# Save markdown
with open("output.md", "w", encoding="utf-8") as f:
    f.write(text)

# Images are returned as dict: {filename: PIL.Image}
for img_name, img_data in images.items():
    img_data.save(f"extracted_images/{img_name}")

print(f"Converted successfully!")
print(f"Extracted {len(images)} images")
```

#### Advanced Configuration

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered

# Custom configuration
config = {
    "output_format": "json",
    "disable_image_extraction": False,
    "highres_image_dpi": 300,  # High-resolution for better OCR
    "lowres_image_dpi": 96,
}

config_parser = ConfigParser(config)

# Create converter with custom config
converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)

# Convert
rendered = converter("research_paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

### Table Extraction from Research Papers

Marker excels at extracting complex tables from research papers.

#### Extract All Tables to Markdown

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.schema import BlockTypes
import re

# Initialize converter
converter = PdfConverter(artifact_dict=create_model_dict())

# Build document structure
document = converter.build_document("economics_paper.pdf")

# Extract all table blocks
tables = document.contained_blocks((BlockTypes.Table,))

print(f"Found {len(tables)} tables in the paper")

# Save each table separately
for i, table in enumerate(tables):
    # Get table HTML
    table_html = table.html

    # Get table position info
    page_id = table.page_id
    polygon = table.polygon

    # Save table
    with open(f"table_{i+1}.html", "w", encoding="utf-8") as f:
        f.write(table_html)

    print(f"Table {i+1}: Page {page_id}, {len(table_html)} chars")
```

#### Specialized Table Converter

For table-focused extraction:

```python
from marker.converters.table import TableConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Initialize table-specific converter
converter = TableConverter(artifact_dict=create_model_dict())

# Convert PDF
rendered = converter("paper_with_tables.pdf")
text, metadata, images = text_from_rendered(rendered)

# Output focuses on table structure
with open("tables_only.md", "w", encoding="utf-8") as f:
    f.write(text)
```

Command-line equivalent:

```bash
uv run marker_single paper.pdf \
  --force_layout_block Table \
  --converter_cls marker.converters.table.TableConverter \
  --output_format json
```

#### Extract Tables to Structured Format (JSON)

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
import json
from pathlib import Path

# Configure for JSON output
config = {"output_format": "json"}
config_parser = ConfigParser(config)

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    renderer=config_parser.get_renderer(),
)

# Convert
rendered = converter("research_paper.pdf")

# Rendered is already JSON structure with all blocks
# Save full JSON
output_path = Path("paper_structure.json")
with output_path.open("w", encoding="utf-8") as f:
    json.dump(rendered, f, indent=2)

# Extract just tables from JSON structure
tables = []
for page_id, page_data in rendered.items():
    if isinstance(page_data, dict) and "blocks" in page_data:
        for block in page_data["blocks"]:
            if block.get("block_type") == "Table":
                tables.append({
                    "page": page_id,
                    "html": block.get("html"),
                    "polygon": block.get("polygon"),
                })

print(f"Extracted {len(tables)} tables")

# Save tables separately
with open("tables.json", "w", encoding="utf-8") as f:
    json.dump(tables, f, indent=2)
```

### Figure and Image Extraction

Marker automatically extracts images from PDFs.

#### Basic Image Extraction

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pathlib import Path

# Initialize converter (images extracted by default)
converter = PdfConverter(artifact_dict=create_model_dict())

# Convert PDF
rendered = converter("research_paper.pdf")
text, metadata, images = text_from_rendered(rendered)

# Create output directory
output_dir = Path("extracted_figures")
output_dir.mkdir(exist_ok=True)

# Save all extracted images
for img_name, img_data in images.items():
    img_path = output_dir / img_name
    img_data.save(img_path)
    print(f"Saved: {img_name}")

print(f"\nExtracted {len(images)} images total")

# Markdown contains image references
with open(output_dir / "paper_with_refs.md", "w", encoding="utf-8") as f:
    f.write(text)
```

#### Extract Only Figures (Filter by Block Type)

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from pathlib import Path

converter = PdfConverter(artifact_dict=create_model_dict())
document = converter.build_document("research_paper.pdf")

# Extract picture/figure blocks
figures = document.contained_blocks((BlockTypes.Picture,))

print(f"Found {len(figures)} figures/pictures")

output_dir = Path("figures_only")
output_dir.mkdir(exist_ok=True)

for i, figure in enumerate(figures):
    # Get figure metadata
    page_id = figure.page_id
    polygon = figure.polygon
    html = figure.html

    # Save figure info
    figure_info = {
        "figure_number": i + 1,
        "page": page_id,
        "position": polygon,
        "content": html,
    }

    with open(output_dir / f"figure_{i+1}.json", "w", encoding="utf-8") as f:
        import json
        json.dump(figure_info, f, indent=2)

    print(f"Figure {i+1}: Page {page_id}")
```

### Batch Processing Research Papers

Process multiple papers efficiently:

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from pathlib import Path
import json

# Setup
papers_dir = Path("research_papers")
output_dir = Path("converted_papers")
output_dir.mkdir(exist_ok=True)

# Initialize converter once (reuse for all papers)
converter = PdfConverter(artifact_dict=create_model_dict())

# Get all PDFs
pdf_files = list(papers_dir.glob("*.pdf"))
print(f"Processing {len(pdf_files)} papers...")

results = []

for pdf_file in pdf_files:
    print(f"\nProcessing: {pdf_file.name}")

    try:
        # Convert
        rendered = converter(str(pdf_file))
        text, metadata, images = text_from_rendered(rendered)

        # Create paper-specific directory
        paper_dir = output_dir / pdf_file.stem
        paper_dir.mkdir(exist_ok=True)

        # Save markdown
        md_path = paper_dir / "paper.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(text)

        # Save images
        img_dir = paper_dir / "images"
        img_dir.mkdir(exist_ok=True)
        for img_name, img_data in images.items():
            img_data.save(img_dir / img_name)

        # Save metadata
        meta_path = paper_dir / "metadata.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        results.append({
            "file": pdf_file.name,
            "status": "success",
            "images": len(images),
            "pages": len(metadata.get("page_stats", {}))
        })

        print(f"  ✓ Success - {len(images)} images extracted")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({
            "file": pdf_file.name,
            "status": "error",
            "error": str(e)
        })

# Save processing summary
with open(output_dir / "processing_summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nProcessed {len(pdf_files)} papers")
print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
```

#### Multi-threaded Batch Processing (CLI)

For large-scale processing:

```bash
# Process with 4 workers
uv run marker papers_directory/ --workers 4 --output_dir ./output

# Process specific chunk (for distributed processing)
uv run marker papers_directory/ --chunk_idx 0 --num_chunks 4

# Recycle workers periodically (for memory management)
uv run marker papers_directory/ --workers 8 --max_tasks_per_worker 10
```

### LLM-Enhanced Conversion

For highest accuracy on complex tables and equations:

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered

# Configure with LLM service
config = {
    "llm_service": "marker.services.gemini.GoogleGeminiService"
}
config_parser = ConfigParser(config)

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    llm_service=config_parser.get_llm_service(),
    processor_list=config_parser.get_processors(),
)

# Convert with LLM enhancement
# - Cross-page table merging
# - Better inline math handling
# - Improved table formatting
# - Form value extraction
rendered = converter("complex_paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

Command-line:

```bash
uv run marker_single paper.pdf \
  --llm_service marker.services.gemini.GoogleGeminiService
```

Note: Requires API key for Google Gemini (default model: gemini-2.0-flash)

### Structured Data Extraction (Beta)

Extract specific structured data using Pydantic schemas:

```python
from marker.converters.extraction import ExtractionConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from pydantic import BaseModel
from typing import List

# Define extraction schema
class AuthorInfo(BaseModel):
    name: str
    affiliation: str

class PaperMetadata(BaseModel):
    title: str
    authors: List[AuthorInfo]
    abstract: str
    keywords: List[str]

# Create schema
schema = PaperMetadata.model_json_schema()

# Configure extractor
config_parser = ConfigParser({"page_schema": schema})

converter = ExtractionConverter(
    artifact_dict=create_model_dict(),
    config=config_parser.generate_config_dict(),
    llm_service=config_parser.get_llm_service(),
)

# Extract structured data
rendered = converter("research_paper.pdf")

# Rendered contains extracted structured data matching schema
import json
print(json.dumps(rendered, indent=2))
```

### Working with Document Structure

Access full document structure programmatically:

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes

converter = PdfConverter(artifact_dict=create_model_dict())

# Build full document structure
document = converter.build_document("paper.pdf")

# Get table of contents
toc = document.table_of_contents
print("Table of Contents:")
for section in toc:
    print(f"  {section['title']} - Page {section['page_id']}")

# Extract specific block types
tables = document.contained_blocks((BlockTypes.Table,))
figures = document.contained_blocks((BlockTypes.Picture,))
equations = document.contained_blocks((BlockTypes.Equation,))
forms = document.contained_blocks((BlockTypes.Form,))

print(f"\nDocument Statistics:")
print(f"  Tables: {len(tables)}")
print(f"  Figures: {len(figures)}")
print(f"  Equations: {len(equations)}")
print(f"  Forms: {len(forms)}")

# Access individual blocks
for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    print(f"  Page: {table.page_id}")
    print(f"  Position: {table.polygon}")
    print(f"  HTML: {table.html[:100]}...")
```

### Output Formats

Marker supports multiple output formats optimized for different use cases.

#### Markdown Output

Default format with image links, formatted tables, LaTeX equations:

```bash
uv run marker_single paper.pdf --output_format markdown
```

Features:

- Image references: `![](image_1.png)`
- Tables in markdown format
- Equations: `$$E = mc^2$$`
- Code blocks with syntax highlighting
- Footnote superscripts
- Header hierarchy

#### JSON Output

Structured tree format ideal for programmatic access:

```bash
uv run marker_single paper.pdf --output_format json
```

Structure:

- Pages containing blocks
- Each block has:
  - `id`: unique identifier
  - `block_type`: Table, Picture, Text, Equation, etc.
  - `html`: formatted content
  - `polygon`: 4-corner coordinates
  - `children`: nested blocks
  - `section_hierarchy`: heading levels
  - `images`: base64-encoded content

#### HTML Output

Web-ready format:

```bash
uv run marker_single paper.pdf --output_format html
```

Features:

- `<img>` tags for images
- `<math>` tags for equations
- `<pre>` tags for code
- Proper table structure

#### Chunks Output

Flattened format ideal for RAG/embedding systems:

```bash
uv run marker_single paper.pdf --output_format chunks
```

Each chunk contains:

- Complete HTML per block
- No nested structure
- Ready for vector database ingestion

### Research Paper Workflow Examples

#### Complete Regression Table Extraction

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from pathlib import Path
import json

# Initialize converter
converter = PdfConverter(artifact_dict=create_model_dict())

# Process economics paper
paper_path = Path("economics_paper.pdf")
document = converter.build_document(str(paper_path))

# Extract all tables (likely regression tables in appendix)
tables = document.contained_blocks((BlockTypes.Table,))

# Create output directory
tables_dir = Path("regression_tables")
tables_dir.mkdir(exist_ok=True)

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    # Get table information
    table_data = {
        "table_number": i + 1,
        "page": table.page_id,
        "position": table.polygon,
        "html": table.html,
    }

    # Save as JSON
    json_path = tables_dir / f"{paper_path.stem}_table_{i+1}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(table_data, f, indent=2)

    # Save HTML for viewing
    html_path = tables_dir / f"{paper_path.stem}_table_{i+1}.html"
    with html_path.open("w", encoding="utf-8") as f:
        f.write(f"<h2>Table {i+1} - Page {table.page_id}</h2>")
        f.write(table.html)

    print(f"Table {i+1}: Page {table.page_id}, {len(table.html)} chars")
```

#### Extract All Data from Multiple Papers

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from pathlib import Path
import json

# Setup
converter = PdfConverter(artifact_dict=create_model_dict())
papers_dir = Path("papers")
output_base = Path("extracted_data")

for paper_path in papers_dir.glob("*.pdf"):
    print(f"\n{'='*60}")
    print(f"Processing: {paper_path.name}")
    print('='*60)

    try:
        # Create paper-specific output directory
        paper_output = output_base / paper_path.stem
        paper_output.mkdir(parents=True, exist_ok=True)

        # Build document
        document = converter.build_document(str(paper_path))

        # Extract tables
        tables = document.contained_blocks((BlockTypes.Table,))
        for i, table in enumerate(tables):
            html_path = paper_output / f"table_{i+1}.html"
            with html_path.open("w", encoding="utf-8") as f:
                f.write(table.html)

        # Extract figures
        figures = document.contained_blocks((BlockTypes.Picture,))
        for i, figure in enumerate(figures):
            json_path = paper_output / f"figure_{i+1}.json"
            with json_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "page": figure.page_id,
                    "position": figure.polygon,
                    "html": figure.html,
                }, f, indent=2)

        # Get full markdown with images
        from marker.output import text_from_rendered
        rendered = converter(str(paper_path))
        text, metadata, images = text_from_rendered(rendered)

        # Save markdown
        md_path = paper_output / "full_paper.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(text)

        # Save images
        img_dir = paper_output / "images"
        img_dir.mkdir(exist_ok=True)
        for img_name, img_data in images.items():
            img_data.save(img_dir / img_name)

        # Save summary
        summary = {
            "paper": paper_path.name,
            "tables": len(tables),
            "figures": len(figures),
            "images": len(images),
            "pages": len(metadata.get("page_stats", {}))
        }

        summary_path = paper_output / "summary.json"
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"  ✓ Tables: {len(tables)}")
        print(f"  ✓ Figures: {len(figures)}")
        print(f"  ✓ Images: {len(images)}")

    except Exception as e:
        print(f"  ✗ Error: {e}")
```

### OCR for Scanned Papers

```bash
# OCR is enabled by default
uv run marker_single scanned_paper.pdf

# High-resolution OCR for better quality
uv run marker_single scanned_paper.pdf --highres_image_dpi 300

# Disable OCR if PDF already has good text
uv run marker_single paper.pdf --disable_ocr
```

Python API:

```python
from marker.converters.ocr import OCRConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Use OCR-specific converter
converter = OCRConverter(artifact_dict=create_model_dict())
rendered = converter("scanned_paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

### Best Practices for Research Papers

1. **Use JSON output for structured extraction**:

   ```bash
   uv run marker_single paper.pdf --output_format json
   ```

2. **Enable LLM for complex tables**: Cross-page table merging and better formatting

   ```bash
   uv run marker_single paper.pdf --llm_service \
     marker.services.gemini.GoogleGeminiService
   ```

3. **Batch processing**: Reuse converter instance for multiple papers

   ```python
   converter = PdfConverter(artifact_dict=create_model_dict())
   for paper in papers:
       rendered = converter(paper)
   ```

4. **Extract specific page ranges**: For large papers, process sections separately

   ```bash
   uv run marker_single paper.pdf --page_range "0-10"
   ```

5. **High-resolution for figures**: Increase DPI for better image quality

   ```bash
   uv run marker_single paper.pdf --highres_image_dpi 300
   ```

6. **Use chunks format for RAG**: Pre-formatted for embedding pipelines

   ```bash
   uv run marker_single paper.pdf --output_format chunks
   ```

7. **Access document structure**: Use `build_document()` for programmatic access

   ```python
   document = converter.build_document("paper.pdf")
   tables = document.contained_blocks((BlockTypes.Table,))
   ```

### CLI Reference

#### marker_single Options

```bash
# Output formats
--output_format [markdown|json|html|chunks]

# Page selection
--page_range "0,5-10,20"

# Image handling
--disable_image_extraction
--highres_image_dpi 300
--lowres_image_dpi 96

# OCR control
--disable_ocr
--force_ocr

# LLM enhancement
--llm_service marker.services.gemini.GoogleGeminiService

# Performance
--disable_multiprocessing
--debug

# Output location
--output_dir PATH

# Advanced
--converter_cls TEXT
--config_json PATH
--force_layout_block Table
```

#### marker (Batch) Options

```bash
# Processing control
--workers N
--max_files N
--max_tasks_per_worker N

# Chunking (distributed processing)
--chunk_idx N
--num_chunks N

# File management
--skip_existing
--debug_print

# Same options as marker_single
--output_format [markdown|json|html|chunks]
--output_dir PATH
```

### Troubleshooting

#### Tables Not Extracted Properly

- Use LLM enhancement: `--llm_service marker.services.gemini.GoogleGeminiService`
- Try table-specific converter: `--converter_cls marker.converters.table.TableConverter`
- Use JSON output to access raw structure: `--output_format json`

#### Poor OCR Quality

- Increase DPI: `--highres_image_dpi 300`
- Check if OCR is needed: `--disable_ocr` if PDF has embedded text

#### Memory Issues

- Process in batches with page ranges: `--page_range "0-50"`
- Reduce workers: `--workers 1`
- Disable image extraction: `--disable_image_extraction`

#### Slow Processing

- Use GPU if available (automatic detection)
- Disable multiprocessing for small files: `--disable_multiprocessing`
- Reduce image DPI: `--lowres_image_dpi 72`

#### Missing Figures

- Check images dict: `images = text_from_rendered(rendered)[2]`
- Ensure image extraction enabled (default)
- Verify output directory has images

## Performance Notes

- **Speed**: Up to 25 pages/second on H100 GPU
- **Accuracy**: Benchmark-leading on research papers and books
- **Models**: Only used where necessary (not on every page)
- **Hardware**: Supports CUDA, CPU, and Apple MPS

## Licensing

- **Code**: GPL-3.0 license
- **Models**: Modified AI Pubs Open Rail-M license (free for research, personal use,
  and startups under $2M funding/revenue)
- **Commercial**: Available at datalab.to/pricing

## Resources

- GitHub repository: <https://github.com/datalab-to/marker>
- PyPI package: <https://pypi.org/project/marker-pdf/>
- Discord community: discord.gg/KuZwXNGnfH
- Commercial licensing: <https://datalab.to/pricing>

## Reference Files

For detailed code examples, see `references/` directory for additional Python scripts
and usage patterns.
