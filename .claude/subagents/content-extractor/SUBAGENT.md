---
name: content-extractor
description: Deep extraction of all structured content from research papers - tables, figures, citations, methodology. This subagent systematically extracts and classifies all data from academic papers for downstream analysis.
trigger: Use this subagent when you need to extract structured data from one or more research papers. Invoke with paper paths or a paper catalog.
---

# Content Extractor Subagent

**Version:** 1.0
**Status:** Active
**Phase:** Extraction (Phase 2 of research workflow)

## Purpose

The **Content Extractor** is a specialized subagent that performs comprehensive, systematic extraction of all structured content from research papers. It goes beyond simple table extraction to identify, classify, and structure all relevant data for meta-analysis and systematic reviews.

## When to Use This Subagent

Use the content-extractor when you need to:

- Extract all tables from one or more papers
- Identify and classify table types (regression, summary stats, balance)
- Extract figures with captions and metadata
- Build citation networks from papers
- Extract methodology and study design details
- Extract sample characteristics and treatment details
- Process papers in batch with quality scoring
- Generate extraction reports for quality control

## Core Capabilities

### 1. Table Extraction & Classification

- Extract all tables from PDFs/markdown
- Classify tables automatically:
  - Regression tables (treatment effects)
  - Summary statistics tables
  - Balance tables (baseline characteristics)
  - Appendix tables
  - Other (miscellaneous)
- Generate structured data for each table
- Calculate quality scores

### 2. Figure Extraction

- Extract all figures/images
- Preserve captions and metadata
- Link figures to relevant text
- Store with source page numbers

### 3. Citation Extraction

- Build complete citation list
- Extract DOIs where available
- Create citation network
- Link to bibliography database

### 4. Methodology Extraction

- Study design (RCT, quasi-experimental, etc.)
- Sample size and characteristics
- Treatment details
- Outcome measures
- Statistical methods

### 5. Quality Assurance

- Generate extraction quality scores
- Flag potential issues
- Create detailed extraction reports
- Track extraction metadata

## Skills Used

This subagent leverages:

- **pdf-processor (docling)** - Convert PDFs and extract tables using docling Python API
- **research-analyst** - Extraction templates and methodology
- **table-validator** - Validate extraction quality
- **bibliography** - Citation extraction and management

**Note**: This subagent uses **docling** directly via Python API (not marker subprocess) for better stability, memory management, and reliability.

## Input Specification

### Single Paper Input

```json
{
  "paper_path": "papers/smith2020.pdf",
  "extract_tables": true,
  "extract_figures": true,
  "extract_citations": true,
  "extract_methodology": true,
  "output_dir": "extracted/smith2020"
}
```

### Batch Input

```json
{
  "papers": [
    {"paper_id": "smith2020", "path": "papers/smith2020.pdf"},
    {"paper_id": "jones2021", "path": "papers/jones2021.pdf"}
  ],
  "extract_tables": true,
  "extract_figures": true,
  "extract_citations": true,
  "parallel": true,
  "workers": 4,
  "output_dir": "extracted/"
}
```

### Paper Catalog Input

```json
{
  "catalog_path": "papers_catalog.json",
  "filter": {
    "year_min": 2015,
    "study_type": "RCT"
  },
  "extract_all": true,
  "output_dir": "extracted/"
}
```

## Output Specification

### Per-Paper Output Structure

```json
{
  "paper_id": "smith2020",
  "extraction_date": "2025-11-05T14:30:00Z",
  "source_file": "papers/smith2020.pdf",
  "extraction_quality": 0.95,

  "metadata": {
    "title": "Effects of Cash Transfers on Child Health",
    "authors": ["Smith, John", "Doe, Jane"],
    "year": 2020,
    "doi": "10.1016/j.jdeveco.2020.102468",
    "journal": "Journal of Development Economics",
    "abstract": "..."
  },

  "tables": [
    {
      "table_id": "table_1",
      "table_number": "Table 1",
      "type": "summary_statistics",
      "page": 12,
      "caption": "Summary Statistics by Treatment Group",
      "quality_score": 0.98,
      "rows": 15,
      "columns": 5,
      "data": {
        "format": "json",
        "path": "extracted/smith2020/tables/table_1.json",
        "preview": {
          "variables": ["age", "income", "education"],
          "treatment_groups": ["control", "treatment"],
          "n_observations": 1500
        }
      },
      "html": "extracted/smith2020/tables/table_1.html",
      "csv": "extracted/smith2020/tables/table_1.csv"
    },
    {
      "table_id": "table_3",
      "table_number": "Table 3",
      "type": "regression",
      "page": 18,
      "caption": "Treatment Effects on Child Health",
      "quality_score": 0.93,
      "rows": 20,
      "columns": 4,
      "data": {
        "format": "json",
        "path": "extracted/smith2020/tables/table_3.json",
        "preview": {
          "dependent_variable": "child_health_z_score",
          "models": 4,
          "treatment_effects": [0.25, 0.23, 0.28, 0.26],
          "standard_errors": [0.08, 0.09, 0.08, 0.09],
          "n_observations": [1500, 1500, 1450, 1450]
        }
      },
      "html": "extracted/smith2020/tables/table_3.html",
      "csv": "extracted/smith2020/tables/table_3.csv"
    }
  ],

  "figures": [
    {
      "figure_id": "figure_1",
      "figure_number": "Figure 1",
      "page": 10,
      "caption": "Distribution of Treatment Effects",
      "path": "extracted/smith2020/figures/figure_1.png",
      "metadata": {
        "type": "histogram",
        "related_table": "table_3"
      }
    }
  ],

  "citations": [
    {
      "citation_id": "ref_1",
      "text": "Banerjee et al. (2015)",
      "authors": ["Banerjee", "et al."],
      "year": 2015,
      "context": "cash transfer programs",
      "doi": null
    }
  ],

  "methodology": {
    "study_design": "Randomized Controlled Trial",
    "sample_size": 1500,
    "treatment_arms": 2,
    "randomization_level": "household",
    "outcome_primary": "child_health_z_score",
    "outcomes_secondary": ["height", "weight", "nutrition_score"],
    "treatment_description": "Monthly cash transfer of $50 for 24 months",
    "control_description": "No intervention",
    "location": "Rural Kenya",
    "duration": "24 months"
  },

  "extraction_report": {
    "tables_found": 8,
    "tables_extracted": 8,
    "tables_classified": 8,
    "figures_found": 3,
    "figures_extracted": 3,
    "citations_found": 45,
    "issues": [],
    "warnings": [
      "Table 5: Low quality score (0.72) - possible extraction error"
    ],
    "processing_time_seconds": 45
  }
}
```

### Batch Output Structure

```json
{
  "batch_id": "batch_2025_11_05",
  "extraction_date": "2025-11-05T14:30:00Z",
  "papers_processed": 25,
  "papers_successful": 24,
  "papers_failed": 1,

  "summary": {
    "total_tables": 200,
    "total_figures": 75,
    "total_citations": 1125,
    "avg_quality_score": 0.91,
    "processing_time_seconds": 1200
  },

  "papers": [
    {
      "paper_id": "smith2020",
      "status": "success",
      "output_path": "extracted/smith2020/extraction.json",
      "quality_score": 0.95,
      "tables": 8,
      "figures": 3
    }
  ],

  "failed_papers": [
    {
      "paper_id": "broken2019",
      "error": "PDF conversion failed - file corrupted"
    }
  ],

  "output_directory": "extracted/",
  "catalog_path": "extracted/batch_catalog.json"
}
```

## Implementation

### Main Extraction Workflow

```python
"""
Content Extractor Subagent Implementation

This subagent orchestrates comprehensive content extraction from research papers.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Skills (these would be invoked via Claude's skill system)
from skills import (
    pdf_processor,
    research_analyst,
    table_validator,
    bibliography
)

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Content Extractor Subagent

    Performs comprehensive extraction of structured content from research papers.
    """

    def __init__(self, output_dir: str = "extracted"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def process_paper(
        self,
        paper_path: str,
        paper_id: Optional[str] = None,
        extract_tables: bool = True,
        extract_figures: bool = True,
        extract_citations: bool = True,
        extract_methodology: bool = True
    ) -> Dict:
        """
        Extract all content from a single paper.

        Args:
            paper_path: Path to PDF or markdown file
            paper_id: Unique identifier (defaults to filename stem)
            extract_tables: Extract tables
            extract_figures: Extract figures
            extract_citations: Extract citations
            extract_methodology: Extract methodology details

        Returns:
            Complete extraction output dictionary
        """
        start_time = datetime.now()
        paper_path = Path(paper_path)
        paper_id = paper_id or paper_path.stem

        logger.info(f"Starting extraction for {paper_id}")

        # Create output directory for this paper
        paper_output_dir = self.output_dir / paper_id
        paper_output_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "paper_id": paper_id,
            "extraction_date": datetime.now().isoformat(),
            "source_file": str(paper_path),
            "extraction_quality": 0.0,
            "metadata": {},
            "tables": [],
            "figures": [],
            "citations": [],
            "methodology": {},
            "extraction_report": {}
        }

        try:
            # Step 1: Convert PDF to markdown (if needed)
            markdown_path = await self._convert_to_markdown(paper_path, paper_output_dir)

            # Step 2: Extract metadata
            result["metadata"] = await self._extract_metadata(markdown_path)

            # Step 3: Extract tables
            if extract_tables:
                result["tables"] = await self._extract_tables(
                    paper_path,
                    markdown_path,
                    paper_output_dir
                )

            # Step 4: Extract figures
            if extract_figures:
                result["figures"] = await self._extract_figures(
                    paper_path,
                    markdown_path,
                    paper_output_dir
                )

            # Step 5: Extract citations
            if extract_citations:
                result["citations"] = await self._extract_citations(markdown_path)

            # Step 6: Extract methodology
            if extract_methodology:
                result["methodology"] = await self._extract_methodology(markdown_path)

            # Step 7: Calculate quality score
            result["extraction_quality"] = self._calculate_quality_score(result)

            # Step 8: Generate extraction report
            processing_time = (datetime.now() - start_time).total_seconds()
            result["extraction_report"] = self._generate_report(result, processing_time)

            # Save extraction output
            output_file = paper_output_dir / "extraction.json"
            with output_file.open("w") as f:
                json.dump(result, f, indent=2)

            logger.info(
                f"Extraction complete for {paper_id}: "
                f"{len(result['tables'])} tables, "
                f"{len(result['figures'])} figures, "
                f"quality={result['extraction_quality']:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Extraction failed for {paper_id}: {str(e)}")
            result["extraction_report"]["error"] = str(e)
            result["extraction_report"]["status"] = "failed"
            return result

    async def process_batch(
        self,
        papers: List[Dict],
        parallel: bool = True,
        workers: int = 4,
        **extraction_kwargs
    ) -> Dict:
        """
        Extract content from multiple papers.

        Args:
            papers: List of paper dictionaries with 'paper_id' and 'path'
            parallel: Process papers in parallel
            workers: Number of parallel workers
            **extraction_kwargs: Additional arguments for process_paper

        Returns:
            Batch extraction summary
        """
        start_time = datetime.now()
        batch_id = f"batch_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}"

        logger.info(f"Starting batch extraction: {batch_id} with {len(papers)} papers")

        if parallel:
            # Parallel processing
            semaphore = asyncio.Semaphore(workers)

            async def process_with_semaphore(paper):
                async with semaphore:
                    return await self.process_paper(
                        paper_path=paper["path"],
                        paper_id=paper.get("paper_id"),
                        **extraction_kwargs
                    )

            results = await asyncio.gather(
                *[process_with_semaphore(paper) for paper in papers],
                return_exceptions=True
            )
        else:
            # Sequential processing
            results = []
            for paper in papers:
                result = await self.process_paper(
                    paper_path=paper["path"],
                    paper_id=paper.get("paper_id"),
                    **extraction_kwargs
                )
                results.append(result)

        # Compile batch summary
        successful = [r for r in results if not isinstance(r, Exception)
                      and r.get("extraction_report", {}).get("status") != "failed"]
        failed = [r for r in results if isinstance(r, Exception)
                  or r.get("extraction_report", {}).get("status") == "failed"]

        batch_summary = {
            "batch_id": batch_id,
            "extraction_date": datetime.now().isoformat(),
            "papers_processed": len(papers),
            "papers_successful": len(successful),
            "papers_failed": len(failed),
            "summary": {
                "total_tables": sum(len(r.get("tables", [])) for r in successful),
                "total_figures": sum(len(r.get("figures", [])) for r in successful),
                "total_citations": sum(len(r.get("citations", [])) for r in successful),
                "avg_quality_score": (
                    sum(r.get("extraction_quality", 0) for r in successful) / len(successful)
                    if successful else 0
                ),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            },
            "papers": [
                {
                    "paper_id": r["paper_id"],
                    "status": "success",
                    "output_path": str(self.output_dir / r["paper_id"] / "extraction.json"),
                    "quality_score": r["extraction_quality"],
                    "tables": len(r["tables"]),
                    "figures": len(r["figures"])
                }
                for r in successful
            ],
            "failed_papers": [
                {
                    "paper_id": r.get("paper_id", "unknown") if not isinstance(r, Exception)
                                else "unknown",
                    "error": str(r) if isinstance(r, Exception)
                             else r.get("extraction_report", {}).get("error", "Unknown error")
                }
                for r in failed
            ],
            "output_directory": str(self.output_dir),
            "catalog_path": str(self.output_dir / "batch_catalog.json")
        }

        # Save batch summary
        catalog_path = self.output_dir / "batch_catalog.json"
        with catalog_path.open("w") as f:
            json.dump(batch_summary, f, indent=2)

        logger.info(
            f"Batch extraction complete: "
            f"{batch_summary['papers_successful']}/{batch_summary['papers_processed']} successful"
        )

        return batch_summary

    # Private helper methods for each extraction task
    async def _convert_to_markdown(
        self,
        paper_path: Path,
        output_dir: Path
    ) -> Path:
        """Convert PDF to markdown using pdf-processor skill."""
        # This would invoke the pdf-processor skill
        # For now, showing the interface
        markdown_path = output_dir / f"{paper_path.stem}.md"

        # Invoke pdf-processor skill
        # Result: markdown file created
        return markdown_path

    async def _extract_metadata(self, markdown_path: Path) -> Dict:
        """Extract paper metadata."""
        # Use bibliography skill to extract metadata
        # Return structured metadata
        return {
            "title": "",
            "authors": [],
            "year": None,
            "doi": None,
            "journal": ""
        }

    async def _extract_tables(
        self,
        pdf_path: Path,
        markdown_path: Path,
        output_dir: Path
    ) -> List[Dict]:
        """Extract and classify all tables."""
        tables_dir = output_dir / "tables"
        tables_dir.mkdir(exist_ok=True)

        # Use pdf-processor to extract tables
        # Use table classification logic
        # Validate with table-validator
        # Return list of table dictionaries

        return []

    async def _extract_figures(
        self,
        pdf_path: Path,
        markdown_path: Path,
        output_dir: Path
    ) -> List[Dict]:
        """Extract all figures."""
        figures_dir = output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)

        # Use pdf-processor to extract figures
        # Save with metadata
        # Return list of figure dictionaries

        return []

    async def _extract_citations(self, markdown_path: Path) -> List[Dict]:
        """Extract citations."""
        # Use bibliography skill
        # Return list of citation dictionaries
        return []

    async def _extract_methodology(self, markdown_path: Path) -> Dict:
        """Extract methodology details."""
        # Use research-analyst skill templates
        # Extract study design, sample size, etc.
        return {}

    def _calculate_quality_score(self, result: Dict) -> float:
        """Calculate overall extraction quality score."""
        # Weighted combination of:
        # - Table extraction completeness
        # - Table quality scores
        # - Metadata completeness
        # - Citation extraction
        return 0.0

    def _generate_report(self, result: Dict, processing_time: float) -> Dict:
        """Generate extraction report."""
        return {
            "tables_found": len(result["tables"]),
            "tables_extracted": len(result["tables"]),
            "figures_found": len(result["figures"]),
            "figures_extracted": len(result["figures"]),
            "citations_found": len(result["citations"]),
            "issues": [],
            "warnings": [],
            "processing_time_seconds": processing_time,
            "status": "success"
        }


# CLI Interface (if run directly)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Content Extractor Subagent")
    parser.add_argument("paper_path", help="Path to paper PDF")
    parser.add_argument("--output-dir", default="extracted", help="Output directory")
    parser.add_argument("--paper-id", help="Paper ID (defaults to filename)")

    args = parser.parse_args()

    extractor = ContentExtractor(output_dir=args.output_dir)

    # Run extraction
    result = asyncio.run(extractor.process_paper(
        paper_path=args.paper_path,
        paper_id=args.paper_id
    ))

    print(f"Extraction complete: {result['paper_id']}")
    print(f"Quality score: {result['extraction_quality']:.2f}")
    print(f"Tables: {len(result['tables'])}")
    print(f"Figures: {len(result['figures'])}")
```

## Usage Examples

### Example 1: Extract from Single Paper

**User Command:**

```text
Extract all content from smith2020.pdf
```

**Subagent Execution:**

```python
extractor = ContentExtractor(output_dir="extracted")

result = await extractor.process_paper(
    paper_path="papers/smith2020.pdf",
    extract_tables=True,
    extract_figures=True,
    extract_citations=True,
    extract_methodology=True
)

print(f"Extracted {len(result['tables'])} tables")
print(f"Quality score: {result['extraction_quality']:.2f}")
```

**Output:**

```text
Extracted 8 tables
Quality score: 0.95
Output saved to: extracted/smith2020/extraction.json
```

### Example 2: Batch Extract from Catalog

**User Command:**

```text
Extract content from all papers in the RCT catalog
```

**Subagent Execution:**

```python
# Load paper catalog
with open("papers_catalog.json") as f:
    catalog = json.load(f)

papers = [
    {"paper_id": p["id"], "path": p["file_path"]}
    for p in catalog["papers"]
    if p.get("study_type") == "RCT"
]

result = await extractor.process_batch(
    papers=papers,
    parallel=True,
    workers=4
)

print(f"Processed {result['papers_successful']}/{result['papers_processed']} papers")
print(f"Total tables: {result['summary']['total_tables']}")
```

**Output:**

```text
Processed 24/25 papers
Total tables: 200
Average quality: 0.91
Failed: 1 paper (broken2019 - PDF corrupted)
```

### Example 3: Extract Regression Tables Only

**User Command:**

```text
Extract only regression tables from these 5 papers
```

**Subagent Execution:**

```python
result = await extractor.process_batch(
    papers=papers,
    extract_tables=True,
    extract_figures=False,
    extract_citations=False,
    extract_methodology=False
)

# Filter for regression tables only
regression_tables = []
for paper in result["papers"]:
    extraction = json.load(open(paper["output_path"]))
    regression_tables.extend([
        t for t in extraction["tables"]
        if t["type"] == "regression"
    ])

print(f"Found {len(regression_tables)} regression tables")
```

## Integration with Other Subagents

### Downstream Usage

**data-quality-checker** receives output:

```python
# Validate extracted tables
validation_result = await data_quality_checker.validate(
    extraction_output="extracted/smith2020/extraction.json",
    source_pdf="papers/smith2020.pdf"
)
```

**data-harmonizer** receives output:

```python
# Harmonize across studies
harmonized = await data_harmonizer.harmonize(
    extraction_outputs=[
        "extracted/smith2020/extraction.json",
        "extracted/jones2021/extraction.json"
    ],
    outcome_variable="child_health"
)
```

### Upstream Usage

**paper-acquisition** provides input:

```python
# Acquisition agent creates catalog
catalog = await paper_acquisition.process(
    query="RCT cash transfers",
    max_papers=50
)

# Content extractor processes catalog
extraction_results = await content_extractor.process_batch(
    papers=catalog["papers"]
)
```

## Quality Assurance

### Extraction Quality Score

Calculated as weighted average:

- **Table extraction (40%):** Completeness and accuracy
- **Table classification (20%):** Correct type identification
- **Figure extraction (15%):** Completeness
- **Citation extraction (10%):** Completeness
- **Metadata extraction (15%):** Completeness

### Quality Thresholds

- **≥ 0.90:** Excellent - proceed with confidence
- **0.75-0.89:** Good - minor manual review recommended
- **0.60-0.74:** Fair - significant manual review needed
- **< 0.60:** Poor - consider re-extraction or manual extraction

## Error Handling

### Common Errors

1. **PDF Conversion Failed**
   - Retry with alternative tool (marker → docling)
   - Try OCR if scanned document

2. **Table Classification Uncertain**
   - Flag for manual classification
   - Provide multiple possible types

3. **Low Quality Score**
   - Generate detailed report
   - Flag for manual review
   - Suggest improvements

## Performance

### Benchmarks

- **Single paper:** 30-60 seconds (8 tables, 3 figures)
- **Batch (10 papers):** 5-10 minutes (parallel, 4 workers)
- **Large batch (100 papers):** 45-90 minutes

### Optimization

- Use parallel processing for batches
- Cache converted markdown files
- Skip already-extracted papers
- Use marker (fast) by default

## Next Steps

After content-extractor:

1. Implement **data-quality-checker** to validate extractions
2. Implement **data-harmonizer** to merge across studies
3. Build orchestrator to chain subagents

## See Also

- `docs/SUBAGENT_ARCHITECTURE.md` - Overall architecture
- `.claude/skills/pdf-processor/` - PDF conversion skill
- `.claude/skills/table-validator/` - Table validation skill
- `.claude/skills/research-analyst/` - Extraction templates
