---
description: Extract structured content from a research paper and generate a comprehensive Quarto report
---

# Extract Paper Content and Generate Report

Extract all structured content (tables, figures, citations, methodology) from a research paper in the papers/ directory and generate a comprehensive Quarto summary report.

## Input

**Paper filename**: $ARGUMENT (name of PDF file in papers/ directory)

## Workflow

### Step 1: Extract Content Using content-extractor Subagent

Run the content-extractor subagent on the specified paper:

```bash
uv run python .claude/subagents/content-extractor/extractor.py single papers/$ARGUMENT --output-dir outputs --augment
```

The `--augment` flag enables semantic augmentation for richer table context and validation.

### Step 2: Organize Outputs

The content-extractor will create an organized directory structure under `outputs/`:

```text
outputs/
└── {paper_id}/
    ├── extraction.json          # Complete extraction metadata
    ├── {paper_id}.md            # Converted markdown
    ├── tables/
    │   ├── table_1.json         # Table data
    │   ├── table_1.csv          # Table in CSV format
    │   ├── table_1_augmented.json  # With semantic context (if --augment)
    │   └── ...
    └── figures/
        ├── figure_1.png
        └── ...
```

### Step 3: Generate Quarto Summary Report

Create a comprehensive Quarto document that:

1. **Summarizes the paper** with metadata (title, authors, year, DOI)
2. **Provides overview** of extraction results (quality score, processing time)
3. **Lists all extracted tables** with:
   - Table number and caption
   - Type classification (regression, summary, balance, other)
   - Page number from original PDF
   - File path to extracted data (JSON and CSV)
   - Quality score
   - Preview of table dimensions and content
4. **Lists all extracted figures** with:
   - Figure number and caption
   - Page number from original PDF
   - File path to extracted image
5. **Documents extraction methodology** if available
6. **Includes visual previews** where appropriate

Use the quarto skill to generate the report.

### Step 4: Report Structure

The Quarto report should be saved as `outputs/{paper_id}/{paper_id}_report.qmd` with this structure:

```yaml
---
title: "Extraction Report: {paper_title}"
author: "Content Extractor"
date: "{extraction_date}"
format:
  html:
    toc: true
    toc-depth: 3
    code-fold: true
    embed-resources: true
    theme: cosmo
---
```

**Sections:**

1. **Paper Metadata**
   - Title, authors, year, journal, DOI
   - Source file path
   - Extraction date and quality score

2. **Extraction Summary**
   - Number of tables, figures, citations extracted
   - Processing time
   - Warnings or issues (if any)

3. **Extracted Tables**
   - For each table, create a subsection with:
     - Table caption and type
     - Page number and quality score
     - File paths (JSON, CSV, augmented JSON if available)
     - Table preview (first few rows as markdown table)
     - Semantic context summary (if augmented)

4. **Extracted Figures**
   - For each figure, create a subsection with:
     - Figure caption
     - Page number
     - Embedded figure image
     - File path

5. **Methodology** (if extracted)
   - Study design, sample size, treatment details

6. **Citations** (if extracted)
   - Number of citations found
   - Sample of key citations

7. **Files and Paths**
   - Summary table mapping all outputs:

     | Type | ID | Page | Caption | File Path |
     |------|----|----- |---------|-----------|
     | Table | table_1 | 12 | Summary Statistics | outputs/.../table_1.json |
     | Figure | figure_1 | 10 | Distribution | outputs/.../figure_1.png |

### Step 5: Render the Report

After creating the .qmd file, render it to HTML:

```bash
quarto render outputs/{paper_id}/{paper_id}_report.qmd
```

This will create `outputs/{paper_id}/{paper_id}_report.html` - a self-contained HTML report.

## Implementation Instructions

1. **Extract the paper_id** from the argument (remove .pdf extension)
2. **Run content-extractor** with --augment flag
3. **Load extraction.json** to get all metadata and results
4. **Invoke quarto skill** to create the .qmd report
5. **Populate report sections** using extraction data
6. **Render to HTML** using quarto
7. **Report completion** with paths to:
   - extraction.json
   - Report HTML file
   - Tables and figures directories

## Error Handling

- If the paper file doesn't exist in papers/, report error and list available papers
- If extraction fails, report the error from extraction.json
- If any tables have quality_score < 0.75, highlight them in the report
- If quarto render fails, provide the .qmd file path for manual rendering

## Success Output

Display a summary like:

```text
✓ Paper extraction complete: {paper_id}

Extraction Results:
  - Quality Score: 0.95
  - Tables: 8 (6 regression, 2 summary stats)
  - Figures: 3
  - Citations: 45
  - Processing Time: 45.2s

Outputs:
  - Extraction Data: outputs/{paper_id}/extraction.json
  - Tables: outputs/{paper_id}/tables/ (8 files)
  - Figures: outputs/{paper_id}/figures/ (3 files)
  - Report: outputs/{paper_id}/{paper_id}_report.html

Open the HTML report in your browser to view the complete extraction summary.
```

## Example Usage

```bash
# Extract content from a paper
/extract_paper BHKM_Liberia.pdf

# This will:
# 1. Extract all tables, figures, citations from papers/BHKM_Liberia.pdf
# 2. Save structured data to outputs/BHKM_Liberia/
# 3. Generate Quarto report at outputs/BHKM_Liberia/BHKM_Liberia_report.qmd
# 4. Render to HTML at outputs/BHKM_Liberia/BHKM_Liberia_report.html
```

## Notes

- The --augment flag enables semantic augmentation which adds context and validation to tables
- All file paths in the report should be relative to the project root
- The HTML report is self-contained (embed-resources: true) for easy sharing
- Processing time depends on paper length and number of tables/figures
- Semantic augmentation may increase processing time but provides richer context
