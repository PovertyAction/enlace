# Marker-PDF Code Examples Reference

This file contains complete, ready-to-use code examples for common marker-pdf
operations, specifically optimized for research paper processing.

## Table of Contents

1. [Basic Conversion](#basic-conversion)
2. [Table Extraction](#table-extraction)
3. [Figure Extraction](#figure-extraction)
4. [Batch Processing](#batch-processing)
5. [Research Paper Workflows](#research-paper-workflows)
6. [Advanced Usage](#advanced-usage)

## Basic Conversion

### Simple PDF to Markdown

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Initialize converter
converter = PdfConverter(artifact_dict=create_model_dict())

# Convert PDF
rendered = converter("research_paper.pdf")

# Extract text, metadata, and images
text, metadata, images = text_from_rendered(rendered)

# Save markdown
with open("output.md", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Converted successfully!")
print(f"Extracted {len(images)} images")
```

### Convert with Custom Configuration

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import text_from_rendered

# Custom configuration
config = {
    "output_format": "json",
    "highres_image_dpi": 300,
    "lowres_image_dpi": 96,
}

config_parser = ConfigParser(config)

# Create converter with custom config
converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=create_model_dict(),
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
)

# Convert
rendered = converter("research_paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

### CLI Basic Usage

```bash
# Basic conversion
uv run marker_single research_paper.pdf

# Specify output directory
uv run marker_single paper.pdf --output_dir ./output

# JSON output
uv run marker_single paper.pdf --output_format json

# HTML output
uv run marker_single paper.pdf --output_format html

# Chunks format (for RAG)
uv run marker_single paper.pdf --output_format chunks

# Convert specific pages
uv run marker_single paper.pdf --page_range "0,5-10,20"
```

## Table Extraction

### Extract All Tables from PDF

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
import json

# Initialize converter
converter = PdfConverter(artifact_dict=create_model_dict())

# Build document structure
document = converter.build_document("economics_paper.pdf")

# Extract all table blocks
tables = document.contained_blocks((BlockTypes.Table,))

print(f"Found {len(tables)} tables in the paper")

# Save each table separately
for i, table in enumerate(tables):
    # Get table information
    table_data = {
        "table_number": i + 1,
        "page": table.page_id,
        "position": table.polygon,
        "html": table.html,
    }

    # Save as JSON
    with open(f"table_{i+1}.json", "w", encoding="utf-8") as f:
        json.dump(table_data, f, indent=2)

    # Save HTML for viewing
    with open(f"table_{i+1}.html", "w", encoding="utf-8") as f:
        f.write(f"<h2>Table {i+1} - Page {table.page_id}</h2>")
        f.write(table.html)

    print(f"Table {i+1}: Page {table.page_id}, {len(table.html)} chars")
```

### Table-Specific Converter

```python
from marker.converters.table import TableConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Initialize table-specific converter
converter = TableConverter(artifact_dict=create_model_dict())

# Convert PDF (focuses on tables)
rendered = converter("paper_with_tables.pdf")
text, metadata, images = text_from_rendered(rendered)

# Save output
with open("tables_only.md", "w", encoding="utf-8") as f:
    f.write(text)
```

CLI equivalent:

```bash
uv run marker_single paper.pdf \
  --force_layout_block Table \
  --converter_cls marker.converters.table.TableConverter \
  --output_format json
```

### Extract Tables to Structured JSON

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

# Save full JSON structure
with open("paper_structure.json", "w", encoding="utf-8") as f:
    json.dump(rendered, f, indent=2)

# Extract just tables
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

with open("tables.json", "w", encoding="utf-8") as f:
    json.dump(tables, f, indent=2)
```

### Regression Tables Extraction

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

# Extract all tables (likely regression tables)
tables = document.contained_blocks((BlockTypes.Table,))

# Create output directory
tables_dir = Path("regression_tables")
tables_dir.mkdir(exist_ok=True)

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    # Save as JSON
    json_path = tables_dir / f"{paper_path.stem}_table_{i+1}.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({
            "table_number": i + 1,
            "page": table.page_id,
            "position": table.polygon,
            "html": table.html,
        }, f, indent=2)

    # Save HTML
    html_path = tables_dir / f"{paper_path.stem}_table_{i+1}.html"
    with html_path.open("w", encoding="utf-8") as f:
        f.write(f"<h2>Table {i+1} - Page {table.page_id}</h2>")
        f.write(table.html)

    print(f"Table {i+1}: Page {table.page_id}")
```

## Figure Extraction

### Extract All Images and Figures

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

# Save markdown with image references
with open(output_dir / "paper_with_refs.md", "w", encoding="utf-8") as f:
    f.write(text)
```

### Extract Figure Metadata

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from pathlib import Path
import json

converter = PdfConverter(artifact_dict=create_model_dict())
document = converter.build_document("research_paper.pdf")

# Extract picture/figure blocks
figures = document.contained_blocks((BlockTypes.Picture,))

print(f"Found {len(figures)} figures")

output_dir = Path("figures_metadata")
output_dir.mkdir(exist_ok=True)

for i, figure in enumerate(figures):
    # Save figure metadata
    figure_info = {
        "figure_number": i + 1,
        "page": figure.page_id,
        "position": figure.polygon,
        "content": figure.html,
    }

    with open(output_dir / f"figure_{i+1}.json", "w", encoding="utf-8") as f:
        json.dump(figure_info, f, indent=2)

    print(f"Figure {i+1}: Page {figure.page_id}")
```

### High-Resolution Image Extraction

```bash
# CLI with high DPI
uv run marker_single paper.pdf --highres_image_dpi 300

# Save images separately
uv run marker_single paper.pdf \
  --highres_image_dpi 300 \
  --output_dir ./high_res_output
```

## Batch Processing

### Process Multiple Papers (Python)

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

# Initialize converter once (reuse for efficiency)
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
        with (paper_dir / "paper.md").open("w", encoding="utf-8") as f:
            f.write(text)

        # Save images
        img_dir = paper_dir / "images"
        img_dir.mkdir(exist_ok=True)
        for img_name, img_data in images.items():
            img_data.save(img_dir / img_name)

        # Save metadata
        with (paper_dir / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        results.append({
            "file": pdf_file.name,
            "status": "success",
            "images": len(images),
            "pages": len(metadata.get("page_stats", {}))
        })

        print(f"  ✓ Success - {len(images)} images")

    except Exception as e:
        print(f"  ✗ Error: {e}")
        results.append({
            "file": pdf_file.name,
            "status": "error",
            "error": str(e)
        })

# Save summary
with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nProcessed {len(pdf_files)} papers")
print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
```

### Batch Processing (CLI)

```bash
# Process all PDFs in directory
uv run marker papers_directory/ --output_dir ./converted_papers

# Parallel processing with 4 workers
uv run marker papers_directory/ --workers 4

# JSON output for all papers
uv run marker papers_directory/ --output_format json

# Skip existing files
uv run marker papers_directory/ --skip_existing

# Limit number of files
uv run marker papers_directory/ --max_files 10

# Distributed processing (chunk 0 of 4)
uv run marker papers_directory/ --chunk_idx 0 --num_chunks 4
```

## Research Paper Workflows

### Complete Paper Analysis Pipeline

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from marker.output import text_from_rendered
from pathlib import Path
import json

def analyze_paper(paper_path: Path, output_dir: Path):
    """Complete analysis of research paper."""

    # Initialize converter
    converter = PdfConverter(artifact_dict=create_model_dict())

    # Create output directory
    paper_output = output_dir / paper_path.stem
    paper_output.mkdir(parents=True, exist_ok=True)

    print(f"Analyzing: {paper_path.name}")

    # Build document structure
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

    # Get full text with images
    rendered = converter(str(paper_path))
    text, metadata, images = text_from_rendered(rendered)

    # Save markdown
    with (paper_output / "full_paper.md").open("w", encoding="utf-8") as f:
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
        "pages": len(metadata.get("page_stats", {})),
        "toc": metadata.get("table_of_contents", [])
    }

    with (paper_output / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary

# Use it
papers_dir = Path("papers")
output_dir = Path("analyzed_papers")

for paper_path in papers_dir.glob("*.pdf"):
    try:
        summary = analyze_paper(paper_path, output_dir)
        print(f"  ✓ Tables: {summary['tables']}, Figures: {summary['figures']}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
```

### Extract All Tables and Figures from Multiple Papers

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes
from pathlib import Path
import json

converter = PdfConverter(artifact_dict=create_model_dict())
papers_dir = Path("papers")
output_base = Path("extracted_data")

for paper_path in papers_dir.glob("*.pdf"):
    print(f"\n{'='*60}")
    print(f"Processing: {paper_path.name}")
    print('='*60)

    try:
        paper_output = output_base / paper_path.stem
        paper_output.mkdir(parents=True, exist_ok=True)

        # Build document
        document = converter.build_document(str(paper_path))

        # Extract and save tables
        tables = document.contained_blocks((BlockTypes.Table,))
        for i, table in enumerate(tables):
            html_path = paper_output / f"table_{i+1}.html"
            with html_path.open("w", encoding="utf-8") as f:
                f.write(table.html)

        # Extract and save figures
        figures = document.contained_blocks((BlockTypes.Picture,))
        for i, figure in enumerate(figures):
            json_path = paper_output / f"figure_{i+1}.json"
            with json_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "page": figure.page_id,
                    "position": figure.polygon,
                }, f, indent=2)

        print(f"  ✓ Tables: {len(tables)}, Figures: {len(figures)}")

    except Exception as e:
        print(f"  ✗ Error: {e}")
```

## Advanced Usage

### LLM-Enhanced Conversion

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
# - Better inline math
# - Improved table formatting
rendered = converter("complex_paper.pdf")
text, metadata, images = text_from_rendered(rendered)
```

CLI:

```bash
uv run marker_single paper.pdf \
  --llm_service marker.services.gemini.GoogleGeminiService
```

### Access Document Structure

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.schema import BlockTypes

converter = PdfConverter(artifact_dict=create_model_dict())
document = converter.build_document("paper.pdf")

# Get table of contents
toc = document.table_of_contents
print("Table of Contents:")
for section in toc:
    print(f"  {section['title']} - Page {section['page_id']}")

# Get statistics
tables = document.contained_blocks((BlockTypes.Table,))
figures = document.contained_blocks((BlockTypes.Picture,))
equations = document.contained_blocks((BlockTypes.Equation,))

print(f"\nDocument Statistics:")
print(f"  Tables: {len(tables)}")
print(f"  Figures: {len(figures)}")
print(f"  Equations: {len(equations)}")
```

### OCR for Scanned Papers

```python
from marker.converters.ocr import OCRConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# Use OCR-specific converter
converter = OCRConverter(artifact_dict=create_model_dict())
rendered = converter("scanned_paper.pdf")
text, metadata, images = text_from_rendered(rendered)

with open("scanned_output.md", "w", encoding="utf-8") as f:
    f.write(text)
```

CLI:

```bash
# High-resolution OCR
uv run marker_single scanned_paper.pdf --highres_image_dpi 300

# Force OCR on all pages
uv run marker_single paper.pdf --force_ocr

# Disable OCR if PDF has good embedded text
uv run marker_single paper.pdf --disable_ocr
```

### Structured Extraction with Pydantic

```python
from marker.converters.extraction import ExtractionConverter
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from pydantic import BaseModel
from typing import List

# Define schema
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

# Output matches schema
import json
print(json.dumps(rendered, indent=2))
```

## CLI Quick Reference

```bash
# Basic conversion
uv run marker_single paper.pdf

# Output formats
uv run marker_single paper.pdf --output_format json
uv run marker_single paper.pdf --output_format html
uv run marker_single paper.pdf --output_format chunks

# Page selection
uv run marker_single paper.pdf --page_range "0-10"
uv run marker_single paper.pdf --page_range "0,5,10-20"

# Image control
uv run marker_single paper.pdf --disable_image_extraction
uv run marker_single paper.pdf --highres_image_dpi 300

# Table extraction
uv run marker_single paper.pdf \
  --converter_cls marker.converters.table.TableConverter

# LLM enhancement
uv run marker_single paper.pdf \
  --llm_service marker.services.gemini.GoogleGeminiService

# Batch processing
uv run marker papers_dir/ --workers 4
uv run marker papers_dir/ --output_format json --skip_existing

# Debug
uv run marker_single paper.pdf --debug
```
