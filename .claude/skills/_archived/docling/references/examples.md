# Docling Code Examples Reference

This file contains complete, ready-to-use code examples for common docling operations.

**Note:** Docling is installed in your project via `pyproject.toml`:

- **CLI Usage:** Use `uv run docling` for command-line operations
- **Python API:** Import directly (e.g., `from docling.document_converter import
  DocumentConverter`)

**CLI Examples:**

```bash
# Basic conversion
uv run docling research_paper.pdf

# JSON output
uv run docling --to json paper.pdf

# With VLM
uv run docling --pipeline vlm --vlm-model granite_docling paper.pdf

# If installed globally, use: docling paper.pdf
```

## Table of Contents

1. [Basic Conversion](#basic-conversion)
2. [Table Extraction](#table-extraction)
3. [Figure Extraction](#figure-extraction)
4. [Batch Processing](#batch-processing)
5. [Research Paper Workflows](#research-paper-workflows)

## Basic Conversion

### Convert PDF to Markdown

```python
from docling.document_converter import DocumentConverter

# Local file or URL
source = "research_paper.pdf"
converter = DocumentConverter()
result = converter.convert(source)

# Print markdown
print(result.document.export_to_markdown())

# Save to file
with open("output.md", "w") as f:
    f.write(result.document.export_to_markdown())
```

### Convert Multiple Formats

```python
from docling.document_converter import DocumentConverter
from pathlib import Path

converter = DocumentConverter()

# Convert different file types
files = ["paper.pdf", "document.docx", "slides.pptx"]

for file in files:
    result = converter.convert(file)
    output_path = Path(file).stem + ".md"

    with open(output_path, "w") as f:
        f.write(result.document.export_to_markdown())

    print(f"Converted {file} -> {output_path}")
```

## Table Extraction

### Extract All Tables to CSV

```python
import logging
from pathlib import Path
import pandas as pd
from docling.document_converter import DocumentConverter

logging.basicConfig(level=logging.INFO)

# Initialize converter
doc_converter = DocumentConverter()

# Convert document
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

### Advanced Table Extraction Configuration

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure pipeline for complex tables (regression tables, etc.)
pipeline_options = PdfPipelineOptions()

# Use ACCURATE mode for complex research paper tables
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# Disable cell matching for multi-column layouts
pipeline_options.table_structure_options.do_cell_matching = False

# Create converter with custom options
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Convert and extract
conv_res = doc_converter.convert("research_paper.pdf")

# Process tables...
for table in conv_res.document.tables:
    df = table.export_to_dataframe()
    print(df)
```

## Figure Extraction

### Extract Figures with High Resolution

```python
from pathlib import Path
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure for high-resolution image export
IMAGE_RESOLUTION_SCALE = 2.0

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

# Export page images
for page_no, page in conv_res.document.pages.items():
    page_image_filename = output_dir / f"{doc_filename}_page_{page_no}.png"
    with page_image_filename.open("wb") as fp:
        page.image.pil_image.save(fp, format="PNG")

# Export figures and table images
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
conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.EMBEDDED)

# Export markdown with image references
md_filename = output_dir / f"{doc_filename}_with_refs.md"
conv_res.document.save_as_markdown(md_filename, image_mode=ImageRefMode.REFERENCED)
```

## Batch Processing

### Process Multiple Papers

```python
from pathlib import Path
from docling.document_converter import DocumentConverter
import logging

logging.basicConfig(level=logging.INFO)

# Setup directories
papers_dir = Path("research_papers")
output_dir = Path("processed_papers")
output_dir.mkdir(parents=True, exist_ok=True)

converter = DocumentConverter()
pdf_files = list(papers_dir.glob("*.pdf"))

# Process each paper
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
        print(f"  - Tables: {len(result.document.tables)}")
        print(f"  - Pages: {len(result.document.pages)}")

    except Exception as e:
        print(f"  ✗ Error: {e}")

print(f"\nProcessed {len(pdf_files)} papers")
```

## Research Paper Workflows

### Extract All Tables and Figures from Multiple Papers

```python
from pathlib import Path
from docling_core.types.doc import PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

# Configure for comprehensive extraction
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 2.0
pipeline_options.generate_picture_images = True
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

papers_dir = Path("papers")
output_base = Path("extracted_data")

for paper_path in papers_dir.glob("*.pdf"):
    print(f"\nProcessing: {paper_path.name}")

    try:
        # Create paper-specific output directory
        paper_output = output_base / paper_path.stem
        paper_output.mkdir(parents=True, exist_ok=True)

        result = doc_converter.convert(paper_path)

        # Extract tables
        for i, table in enumerate(result.document.tables):
            df = table.export_to_dataframe()
            df.to_csv(paper_output / f"table_{i+1}.csv", index=False)
            df.to_excel(paper_output / f"table_{i+1}.xlsx", index=False)

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

        print(f"  ✓ Success - Tables: {len(result.document.tables)}, "
              f"Figures: {fig_count}")

    except Exception as e:
        print(f"  ✗ Error: {e}")
```

### Extract Only Regression Tables

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
pipeline_options.table_structure_options.do_cell_matching = False

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Process paper
paper_path = Path("economics_paper.pdf")
result = doc_converter.convert(paper_path)

# Extract and save all tables (typically regression tables in appendix)
tables_dir = Path("regression_tables")
tables_dir.mkdir(exist_ok=True)

for i, table in enumerate(result.document.tables):
    df = table.export_to_dataframe()

    # Save in multiple formats
    base_name = f"{paper_path.stem}_table_{i+1}"

    df.to_csv(tables_dir / f"{base_name}.csv", index=False)
    df.to_excel(tables_dir / f"{base_name}.xlsx", index=False)

    with open(tables_dir / f"{base_name}.md", "w") as f:
        f.write(df.to_markdown(index=False))

    print(f"Table {i+1}: {df.shape[0]} rows × {df.shape[1]} columns")
```

### OCR Processing for Scanned Papers

```python
from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Configure OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.ocr_options.force_full_page_ocr = True  # Force OCR on all pages

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Process scanned paper
scanned_paper = Path("scanned_paper.pdf")
result = doc_converter.convert(scanned_paper)

# Save output
with open("scanned_paper_ocr.md", "w") as f:
    f.write(result.document.export_to_markdown())

print(f"Processed {len(result.document.pages)} pages with OCR")
```

## CLI Examples

### Basic Usage

```bash
# Convert PDF to markdown
docling research_paper.pdf

# Convert from URL
docling https://arxiv.org/pdf/2408.09869

# Specify output directory
docling --output ./results paper.pdf

# Convert to different formats
docling --to json paper.pdf
docling --to html paper.pdf
```

### Advanced Processing

```bash
# Use Vision Language Model for better accuracy
docling --pipeline vlm --vlm-model granite_docling paper.pdf

# Enable OCR for scanned papers
docling --ocr --ocr-engine tesseract scanned_paper.pdf

# GPU acceleration
docling --device cuda paper.pdf

# High-resolution image export
docling --image-export-mode embedded paper.pdf

# Multi-threaded processing
docling --num-threads 8 --page-batch-size 8 large_paper.pdf
```

### Debugging

```bash
# Visualize table detection
docling --debug-visualize-tables paper.pdf

# Verbose output
docling -vv paper.pdf

# Show layout bounding boxes
docling --show-layout paper.pdf
```
