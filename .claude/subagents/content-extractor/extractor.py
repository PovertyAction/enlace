"""Content Extractor Subagent Implementation

This module implements the content-extractor subagent for systematic extraction
of structured content from research papers.

Usage:
    uv run python extractor.py paper.pdf --output-dir extracted
    uv run python extractor.py batch papers_catalog.json --parallel --workers 4
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContentExtractor:
    """Content Extractor Subagent

    Performs comprehensive extraction of structured content from research papers,
    including tables, figures, citations, and methodology details.
    """

    def __init__(self, output_dir: str = "extracted"):
        """Initialize the content extractor.

        Args:
            output_dir: Base directory for extraction outputs

        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"ContentExtractor initialized with output_dir={self.output_dir}")

    async def process_paper(
        self,
        paper_path: str,
        paper_id: str | None = None,
        extract_tables: bool = True,
        extract_figures: bool = True,
        extract_citations: bool = True,
        extract_methodology: bool = True,
    ) -> dict:
        """Extract all content from a single research paper.

        Args:
            paper_path: Path to PDF or markdown file
            paper_id: Unique identifier (defaults to filename stem)
            extract_tables: Whether to extract tables
            extract_figures: Whether to extract figures
            extract_citations: Whether to extract citations
            extract_methodology: Whether to extract methodology details

        Returns:
            Complete extraction output dictionary with all extracted content

        """
        start_time = datetime.now()
        paper_path = Path(paper_path)
        paper_id = paper_id or paper_path.stem

        logger.info(f"[{paper_id}] Starting extraction from {paper_path.name}")

        # Create output directory for this paper
        paper_output_dir = self.output_dir / paper_id
        paper_output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize result structure
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
            "extraction_report": {},
        }

        try:
            # Step 1: Convert PDF to markdown (if needed)
            logger.info(f"[{paper_id}] Step 1: Converting to markdown")
            markdown_path = await self._convert_to_markdown(
                paper_path, paper_output_dir
            )

            # Step 2: Extract metadata
            logger.info(f"[{paper_id}] Step 2: Extracting metadata")
            result["metadata"] = await self._extract_metadata(markdown_path, paper_path)

            # Step 3: Extract tables
            if extract_tables:
                logger.info(f"[{paper_id}] Step 3: Extracting tables")
                result["tables"] = await self._extract_tables(
                    paper_path, markdown_path, paper_output_dir
                )
                logger.info(f"[{paper_id}] Found {len(result['tables'])} tables")

            # Step 4: Extract figures
            if extract_figures:
                logger.info(f"[{paper_id}] Step 4: Extracting figures")
                result["figures"] = await self._extract_figures(
                    paper_path, markdown_path, paper_output_dir
                )
                logger.info(f"[{paper_id}] Found {len(result['figures'])} figures")

            # Step 5: Extract citations
            if extract_citations:
                logger.info(f"[{paper_id}] Step 5: Extracting citations")
                result["citations"] = await self._extract_citations(markdown_path)
                logger.info(f"[{paper_id}] Found {len(result['citations'])} citations")

            # Step 6: Extract methodology
            if extract_methodology:
                logger.info(f"[{paper_id}] Step 6: Extracting methodology")
                result["methodology"] = await self._extract_methodology(markdown_path)

            # Step 7: Calculate quality score
            result["extraction_quality"] = self._calculate_quality_score(result)
            logger.info(
                f"[{paper_id}] Extraction quality: {result['extraction_quality']:.2f}"
            )

            # Step 8: Generate extraction report
            processing_time = (datetime.now() - start_time).total_seconds()
            result["extraction_report"] = self._generate_report(result, processing_time)
            result["extraction_report"]["status"] = "success"

            # Save extraction output
            output_file = paper_output_dir / "extraction.json"
            with output_file.open("w") as f:
                json.dump(result, f, indent=2)

            logger.info(
                f"[{paper_id}] ✓ Extraction complete: "
                f"{len(result['tables'])} tables, "
                f"{len(result['figures'])} figures, "
                f"quality={result['extraction_quality']:.2f}, "
                f"time={processing_time:.1f}s"
            )

            return result

        except Exception as e:
            logger.error(f"[{paper_id}] ✗ Extraction failed: {str(e)}", exc_info=True)
            result["extraction_report"]["error"] = str(e)
            result["extraction_report"]["status"] = "failed"
            return result

    async def process_batch(
        self,
        papers: list[dict],
        parallel: bool = True,
        workers: int = 4,
        **extraction_kwargs,
    ) -> dict:
        """Extract content from multiple papers in batch.

        Args:
            papers: List of paper dictionaries with 'paper_id' and 'path' keys
            parallel: Whether to process papers in parallel
            workers: Number of parallel workers (if parallel=True)
            **extraction_kwargs: Additional arguments passed to process_paper

        Returns:
            Batch extraction summary with aggregated statistics

        """
        start_time = datetime.now()
        batch_id = f"batch_{datetime.now().strftime('%Y_%m_%d_%H%M%S')}"

        logger.info(f"Starting batch extraction: {batch_id} with {len(papers)} papers")
        logger.info(
            f"Mode: {'parallel' if parallel else 'sequential'}, workers={workers if parallel else 1}"
        )

        if parallel:
            # Parallel processing with semaphore to limit concurrency
            semaphore = asyncio.Semaphore(workers)

            async def process_with_semaphore(paper):
                async with semaphore:
                    return await self.process_paper(
                        paper_path=paper["path"],
                        paper_id=paper.get("paper_id"),
                        **extraction_kwargs,
                    )

            results = await asyncio.gather(
                *[process_with_semaphore(paper) for paper in papers],
                return_exceptions=True,
            )
        else:
            # Sequential processing
            results = []
            for i, paper in enumerate(papers, 1):
                logger.info(f"Processing paper {i}/{len(papers)}")
                result = await self.process_paper(
                    paper_path=paper["path"],
                    paper_id=paper.get("paper_id"),
                    **extraction_kwargs,
                )
                results.append(result)

        # Compile batch summary
        successful = [
            r
            for r in results
            if not isinstance(r, Exception)
            and r.get("extraction_report", {}).get("status") != "failed"
        ]
        failed = [
            r
            for r in results
            if isinstance(r, Exception)
            or r.get("extraction_report", {}).get("status") == "failed"
        ]

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
                    sum(r.get("extraction_quality", 0) for r in successful)
                    / len(successful)
                    if successful
                    else 0
                ),
                "processing_time_seconds": (
                    datetime.now() - start_time
                ).total_seconds(),
            },
            "papers": [
                {
                    "paper_id": r["paper_id"],
                    "status": "success",
                    "output_path": str(
                        self.output_dir / r["paper_id"] / "extraction.json"
                    ),
                    "quality_score": r["extraction_quality"],
                    "tables": len(r["tables"]),
                    "figures": len(r["figures"]),
                }
                for r in successful
            ],
            "failed_papers": [
                {
                    "paper_id": (
                        r.get("paper_id", "unknown")
                        if not isinstance(r, Exception)
                        else "unknown"
                    ),
                    "error": (
                        str(r)
                        if isinstance(r, Exception)
                        else r.get("extraction_report", {}).get(
                            "error", "Unknown error"
                        )
                    ),
                }
                for r in failed
            ],
            "output_directory": str(self.output_dir),
            "catalog_path": str(self.output_dir / "batch_catalog.json"),
        }

        # Save batch summary
        catalog_path = self.output_dir / "batch_catalog.json"
        with catalog_path.open("w") as f:
            json.dump(batch_summary, f, indent=2)

        logger.info(
            f"Batch extraction complete: "
            f"{batch_summary['papers_successful']}/{batch_summary['papers_processed']} successful, "
            f"total_tables={batch_summary['summary']['total_tables']}, "
            f"avg_quality={batch_summary['summary']['avg_quality_score']:.2f}, "
            f"time={batch_summary['summary']['processing_time_seconds']:.1f}s"
        )

        return batch_summary

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _convert_to_markdown(self, paper_path: Path, output_dir: Path) -> Path:
        """Convert PDF to markdown using docling Python API.

        Uses docling directly (no subprocess) for better stability and memory management.
        Docling is the primary converter used in src/parse.py.
        """
        markdown_path = output_dir / f"{paper_path.stem}.md"

        if paper_path.suffix == ".md":
            # Already markdown
            return paper_path

        # Check if markdown already exists
        if markdown_path.exists():
            logger.info(f"Using existing markdown: {markdown_path}")
            return markdown_path

        # Use docling Python API for conversion (safer than subprocess)
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption

            logger.info(f"Converting PDF to markdown using docling: {paper_path}")

            # Configure pipeline for table extraction
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            pipeline_options.do_ocr = False  # Disable OCR by default for speed

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            # Convert PDF
            result = converter.convert(str(paper_path))

            # Export to markdown
            markdown_text = result.document.export_to_markdown()

            # Save markdown
            with markdown_path.open("w", encoding="utf-8") as f:
                f.write(markdown_text)

            logger.info(f"PDF conversion complete: {markdown_path}")
            return markdown_path

        except Exception as e:
            logger.error(f"PDF conversion error: {str(e)}", exc_info=True)
            # Create empty markdown file as fallback
            markdown_path.touch()
            return markdown_path

    async def _extract_metadata(self, markdown_path: Path, pdf_path: Path) -> dict:
        """Extract paper metadata (title, authors, year, etc).

        Uses bibliography skill and text parsing.
        """
        metadata = {
            "title": "",
            "authors": [],
            "year": None,
            "doi": None,
            "journal": "",
            "abstract": "",
        }

        if not markdown_path.exists():
            return metadata

        try:
            text = markdown_path.read_text()[:2000]  # First 2000 chars

            # Extract title (usually first heading)
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

            # Extract DOI
            doi_match = re.search(r'10\.\d{4,}(?:\.\d+)*\/(?:(?!["&\'<>])\S)+', text)
            if doi_match:
                metadata["doi"] = doi_match.group(0)

            # Extract year
            year_match = re.search(r"\b(19|20)\d{2}\b", text)
            if year_match:
                metadata["year"] = int(year_match.group(0))

            # TODO: Invoke bibliography skill for better extraction
            # This would extract more detailed author info, etc.

        except Exception as e:
            logger.warning(f"Metadata extraction error: {str(e)}")

        return metadata

    async def _extract_tables(
        self, pdf_path: Path, markdown_path: Path, output_dir: Path
    ) -> list[dict]:
        """Extract and classify all tables from the paper using docling.

        Uses docling Python API directly for reliable table extraction.
        """
        tables_dir = output_dir / "tables"
        tables_dir.mkdir(exist_ok=True)

        tables = []

        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                TableStructureOptions,
            )
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling_core.types.doc import TableCell

            logger.info(f"Extracting tables from {pdf_path.name} using docling")

            # Configure for table extraction
            table_structure_options = TableStructureOptions(do_cell_matching=True)
            pipeline_options = PdfPipelineOptions(
                do_table_structure=True,
                do_ocr=False,
                table_structure_options=table_structure_options,
            )

            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            # Convert and extract tables
            result = converter.convert(str(pdf_path))

            # Helper function to extract cell text
            def extract_cell_value(cell: TableCell) -> str:
                if cell and hasattr(cell, "text"):
                    return cell.text.strip()
                return ""

            # Process each table
            table_num = 1
            for table in result.document.tables:
                # Extract table data
                structure = {
                    "data": [],
                    "num_rows": 0,
                    "num_cols": 0,
                    "caption": "",
                    "page": None,
                }

                # Extract grid data
                if hasattr(table, "data"):
                    table_data = table.data
                    if hasattr(table_data, "grid"):
                        structure["data"] = [
                            [extract_cell_value(cell) for cell in row]
                            for row in table_data.grid
                        ]
                        structure["num_rows"] = len(table_data.grid)
                        structure["num_cols"] = (
                            len(table_data.grid[0]) if table_data.grid else 0
                        )

                # Extract caption with multiple fallback strategies
                caption = ""

                # Strategy 1: Direct caption attribute (but filter out docling refs)
                if hasattr(table, "caption") and table.caption:
                    if hasattr(table.caption, "text"):
                        caption = table.caption.text.strip()
                    else:
                        caption = str(table.caption).strip()

                    # Ignore docling internal references like "#/tables/0"
                    if caption.startswith("#/"):
                        caption = ""

                # Strategy 2: Check table references in the document
                if not caption and hasattr(table, "self_ref"):
                    ref = table.self_ref.strip() if table.self_ref else ""
                    if ref and not ref.startswith("#/"):
                        caption = ref

                # Strategy 3: Look for caption in table metadata
                if not caption and hasattr(table, "metadata"):
                    metadata = table.metadata
                    if isinstance(metadata, dict) and "caption" in metadata:
                        cap = metadata["caption"].strip()
                        if cap and not cap.startswith("#/"):
                            caption = cap

                # Strategy 4: Search markdown for table reference
                if not caption:
                    # Look for "Table N" or "TABLE N" near the table position
                    caption = self._find_table_caption_in_markdown(
                        markdown_path, table_num
                    )

                structure["caption"] = caption

                # Extract page number
                if hasattr(table, "prov") and table.prov:
                    if hasattr(table.prov[0], "page_no"):
                        structure["page"] = table.prov[0].page_no

                # Classify table type
                table_type = self._classify_table(structure)

                # Create table metadata
                table_data = {
                    "table_id": f"table_{table_num}",
                    "type": table_type,
                    "caption": structure.get("caption", ""),
                    "page": structure.get("page"),
                    "num_rows": structure.get("num_rows", 0),
                    "num_cols": structure.get("num_cols", 0),
                    "data": structure.get("data", []),
                    "quality_score": self._calculate_table_quality(structure),
                }

                # Save table in multiple formats
                table_id = table_data["table_id"]

                # Save as JSON
                with (tables_dir / f"{table_id}.json").open("w") as f:
                    json.dump(table_data, f, indent=2)

                # Save as CSV if data exists
                if structure.get("data"):
                    import csv

                    with (tables_dir / f"{table_id}.csv").open("w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerows(structure["data"])

                tables.append(table_data)
                table_num += 1

            logger.info(f"Extracted {len(tables)} tables from {pdf_path.name}")

        except Exception as e:
            logger.error(f"Table extraction error: {str(e)}", exc_info=True)

        return tables

    async def _extract_figures(
        self, pdf_path: Path, markdown_path: Path, output_dir: Path
    ) -> list[dict]:
        """Extract all figures from the paper.

        Uses pdf-processor skill.
        """
        figures_dir = output_dir / "figures"
        figures_dir.mkdir(exist_ok=True)

        figures = []

        # TODO: Invoke pdf-processor to extract figures
        # This would extract images and save with metadata

        return figures

    async def _extract_citations(self, markdown_path: Path) -> list[dict]:
        """Extract citations from the paper.

        Uses bibliography skill.
        """
        citations = []

        if not markdown_path.exists():
            return citations

        try:
            text = markdown_path.read_text()

            # Simple pattern matching for citations
            # Pattern: (Author Year) or (Author et al. Year)
            patterns = [
                r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?\s+\d{4}[a-z]?)\)",
                r"\[(\d+)\]",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    citations.append(
                        {
                            "citation_id": f"ref_{len(citations) + 1}",
                            "text": match,
                            "context": "extracted",
                        }
                    )

            # TODO: Invoke bibliography skill for better citation extraction
            # This would parse citations more accurately and extract DOIs

        except Exception as e:
            logger.warning(f"Citation extraction error: {str(e)}")

        return citations

    async def _extract_methodology(self, markdown_path: Path) -> dict:
        """Extract methodology details.

        Uses research-analyst skill templates.
        """
        methodology = {
            "study_design": None,
            "sample_size": None,
            "treatment_arms": None,
            "randomization_level": None,
            "outcome_primary": None,
            "outcomes_secondary": [],
            "treatment_description": None,
            "control_description": None,
            "location": None,
            "duration": None,
        }

        if not markdown_path.exists():
            return methodology

        try:
            text = markdown_path.read_text()

            # Simple pattern matching for methodology
            # Look for common keywords

            # Study design
            if "randomized controlled trial" in text.lower() or "rct" in text.lower():
                methodology["study_design"] = "Randomized Controlled Trial"
            elif "quasi-experimental" in text.lower():
                methodology["study_design"] = "Quasi-experimental"

            # Sample size
            n_match = re.search(r"[Nn]\s*=\s*([0-9,]+)", text)
            if n_match:
                methodology["sample_size"] = int(n_match.group(1).replace(",", ""))

            # TODO: Invoke research-analyst skill for comprehensive extraction
            # This would use structured templates to extract all methodology details

        except Exception as e:
            logger.warning(f"Methodology extraction error: {str(e)}")

        return methodology

    def _find_table_caption_in_markdown(
        self, markdown_path: Path, table_num: int
    ) -> str:
        """Search markdown text for table caption by looking for table references.

        Searches for patterns like:
        - "Table 1:", "Table 1.", "TABLE 1:"
        - "Table 1: Caption text here"
        - Lines containing table references near the table position
        """
        try:
            with markdown_path.open("r", encoding="utf-8") as f:
                markdown_text = f.read()

            # Pattern 1: Look for "Table N:" or "Table N." followed by caption text
            # Matches: "Table 1: Description" or "TABLE 1. Description"
            pattern1 = rf"(?:Table|TABLE)\s+{table_num}[\.:]\s*([^\n]+)"
            match = re.search(pattern1, markdown_text)
            if match:
                caption = match.group(1).strip()
                # Clean up common artifacts
                caption = re.sub(r"\s+", " ", caption)  # Normalize whitespace
                return f"Table {table_num}: {caption}"

            # Pattern 2: Look for just "Table N" as standalone reference
            pattern2 = rf"(?:Table|TABLE)\s+{table_num}(?:\s|$|[,.])"
            match = re.search(pattern2, markdown_text)
            if match:
                return f"Table {table_num}"

            # Pattern 3: Look for table references in headings (markdown ##, ###)
            pattern3 = rf"#+\s*(?:Table|TABLE)\s+{table_num}[\.:]\s*([^\n]+)"
            match = re.search(pattern3, markdown_text)
            if match:
                caption = match.group(1).strip()
                caption = re.sub(r"\s+", " ", caption)
                return f"Table {table_num}: {caption}"

            # If no caption found, return minimal reference
            return f"Table {table_num}"

        except Exception as e:
            logger.debug(f"Caption search error: {str(e)}")
            return f"Table {table_num}"

    def _classify_table(self, structure: dict) -> str:
        """Classify table type based on content and caption.

        Returns: One of 'regression', 'summary', 'balance', 'descriptive', 'other'
        """
        caption = structure.get("caption", "").lower()
        data = structure.get("data", [])

        # Check caption for keywords
        if any(kw in caption for kw in ["regression", "ols", "coefficient", "effect"]):
            return "regression"
        elif any(kw in caption for kw in ["summary", "descriptive", "statistic"]):
            return "summary"
        elif any(kw in caption for kw in ["balance", "baseline", "comparison"]):
            return "balance"

        # Check data structure (first column content)
        if data and len(data) > 1:
            first_col_text = " ".join(str(row[0]) for row in data[:5] if row).lower()

            if any(
                kw in first_col_text
                for kw in ["coefficient", "std", "t-stat", "p-value"]
            ):
                return "regression"
            elif any(
                kw in first_col_text for kw in ["mean", "median", "std dev", "n obs"]
            ):
                return "descriptive"

        return "other"

    def _calculate_table_quality(self, structure: dict) -> float:
        """Calculate quality score for a single table (0-1).

        Based on:
        - Has caption (30%)
        - Reasonable size (30%)
        - Has data with numeric content bonus (40% + 5% bonus)
        """
        score = 0.0

        # Has caption (30%)
        if structure.get("caption"):
            score += 0.3

        # Reasonable size (30%) - More lenient thresholds
        num_rows = structure.get("num_rows", 0)
        num_cols = structure.get("num_cols", 0)
        # Relaxed from (2-100 rows, 2-20 cols) to (1-200 rows, 1-30 cols)
        if 1 <= num_rows <= 200 and 1 <= num_cols <= 30:
            score += 0.3

        # Has data (40%) with bonus for high fill rates and numeric content
        data = structure.get("data", [])
        if data and len(data) > 0:
            # Check if cells have content
            non_empty = sum(1 for row in data for cell in row if str(cell).strip())
            total_cells = sum(len(row) for row in data)

            if total_cells > 0:
                fill_rate = non_empty / total_cells

                # Base data score (40%)
                # Reward high fill rates (>80%) with sigmoid-like boost
                if fill_rate > 0.8:
                    data_score = 0.4 * (1 + 0.2 * (fill_rate - 0.8))
                else:
                    data_score = 0.4 * fill_rate

                score += data_score

                # Bonus for numeric/statistical data (5%)
                # Suggests proper data table rather than text-only
                numeric_cells = 0
                for row in data:
                    for cell in row:
                        cell_str = str(cell).strip()
                        # Check for numbers, decimals, parentheses (std errors), stars
                        if re.search(r"[\d.]+|\([\d.]+\)|\*+", cell_str):
                            numeric_cells += 1

                if total_cells > 0:
                    numeric_ratio = numeric_cells / total_cells
                    if numeric_ratio > 0.3:
                        score += 0.05

        return round(min(score, 1.0), 2)

    def _calculate_quality_score(self, result: dict) -> float:
        """Calculate overall extraction quality score (0-1).

        Weighted combination of:
        - Table extraction completeness (40%)
        - Metadata completeness (30%)
        - Figure extraction (15%)
        - Citation extraction (15%)
        """
        scores = []
        weights = []

        # Table score (40%)
        if result["tables"]:
            table_score = min(
                len(result["tables"]) / 5, 1.0
            )  # Assume 5 tables is "complete"
            scores.append(table_score)
            weights.append(0.40)

        # Metadata score (30%)
        metadata = result["metadata"]
        metadata_fields = ["title", "authors", "year", "doi", "journal"]
        metadata_completeness = sum(
            1 for f in metadata_fields if metadata.get(f)
        ) / len(metadata_fields)
        scores.append(metadata_completeness)
        weights.append(0.30)

        # Figure score (15%)
        if result["figures"]:
            figure_score = min(
                len(result["figures"]) / 3, 1.0
            )  # Assume 3 figures is "complete"
            scores.append(figure_score)
            weights.append(0.15)

        # Citation score (15%)
        if result["citations"]:
            citation_score = min(
                len(result["citations"]) / 20, 1.0
            )  # Assume 20 citations is "complete"
            scores.append(citation_score)
            weights.append(0.15)

        # Calculate weighted average
        if scores:
            total_weight = sum(weights)
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            return round(weighted_score, 2)
        else:
            return 0.0

    def _generate_report(self, result: dict, processing_time: float) -> dict:
        """Generate extraction report with statistics and issues."""
        warnings = []

        # Check for low quality tables
        for table in result["tables"]:
            if table.get("quality_score", 1.0) < 0.75:
                warnings.append(
                    f"Table {table['table_id']}: Low quality score "
                    f"({table['quality_score']:.2f}) - possible extraction error"
                )

        # Check if no tables found
        if not result["tables"]:
            warnings.append("No tables extracted - verify PDF has tables")

        return {
            "tables_found": len(result["tables"]),
            "tables_extracted": len(result["tables"]),
            "tables_classified": sum(1 for t in result["tables"] if t.get("type")),
            "figures_found": len(result["figures"]),
            "figures_extracted": len(result["figures"]),
            "citations_found": len(result["citations"]),
            "issues": [],
            "warnings": warnings,
            "processing_time_seconds": round(processing_time, 2),
        }


# ============================================================================
# CLI INTERFACE
# ============================================================================


async def main():
    """CLI entry point for content-extractor subagent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Content Extractor Subagent - Extract structured content from research papers"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Single paper extraction
    single_parser = subparsers.add_parser("single", help="Extract from a single paper")
    single_parser.add_argument("paper_path", help="Path to paper PDF")
    single_parser.add_argument(
        "--output-dir", default="extracted", help="Output directory"
    )
    single_parser.add_argument("--paper-id", help="Paper ID (defaults to filename)")
    single_parser.add_argument(
        "--no-tables", action="store_true", help="Skip table extraction"
    )
    single_parser.add_argument(
        "--no-figures", action="store_true", help="Skip figure extraction"
    )
    single_parser.add_argument(
        "--no-citations", action="store_true", help="Skip citation extraction"
    )

    # Batch extraction
    batch_parser = subparsers.add_parser("batch", help="Extract from multiple papers")
    batch_parser.add_argument("catalog_path", help="Path to paper catalog JSON")
    batch_parser.add_argument(
        "--output-dir", default="extracted", help="Output directory"
    )
    batch_parser.add_argument(
        "--parallel", action="store_true", help="Process in parallel"
    )
    batch_parser.add_argument(
        "--workers", type=int, default=4, help="Number of parallel workers"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    extractor = ContentExtractor(output_dir=args.output_dir)

    if args.command == "single":
        # Single paper extraction
        result = await extractor.process_paper(
            paper_path=args.paper_path,
            paper_id=args.paper_id,
            extract_tables=not args.no_tables,
            extract_figures=not args.no_figures,
            extract_citations=not args.no_citations,
        )

        print("\n" + "=" * 70)
        print(f"EXTRACTION COMPLETE: {result['paper_id']}")
        print("=" * 70)
        print(f"Quality score:  {result['extraction_quality']:.2f}")
        print(f"Tables:         {len(result['tables'])}")
        print(f"Figures:        {len(result['figures'])}")
        print(f"Citations:      {len(result['citations'])}")
        print(
            f"Processing time: {result['extraction_report']['processing_time_seconds']:.1f}s"
        )
        print(
            f"\nOutput saved to: {args.output_dir}/{result['paper_id']}/extraction.json"
        )

    elif args.command == "batch":
        # Batch extraction
        with open(args.catalog_path) as f:
            catalog = json.load(f)

        papers = [
            {"paper_id": p["id"], "path": p["file_path"]}
            for p in catalog.get("papers", [])
        ]

        result = await extractor.process_batch(
            papers=papers, parallel=args.parallel, workers=args.workers
        )

        print("\n" + "=" * 70)
        print(f"BATCH EXTRACTION COMPLETE: {result['batch_id']}")
        print("=" * 70)
        print(f"Papers processed: {result['papers_processed']}")
        print(f"Successful:       {result['papers_successful']}")
        print(f"Failed:           {result['papers_failed']}")
        print(f"Total tables:     {result['summary']['total_tables']}")
        print(f"Total figures:    {result['summary']['total_figures']}")
        print(f"Avg quality:      {result['summary']['avg_quality_score']:.2f}")
        print(f"Processing time:  {result['summary']['processing_time_seconds']:.1f}s")
        print(f"\nCatalog saved to: {result['catalog_path']}")


if __name__ == "__main__":
    asyncio.run(main())
