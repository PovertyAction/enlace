"""Batch processing for multiple research papers.

This module provides batch processing capabilities for extracting and validating
multiple research papers in parallel.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.exceptions import EnlaceError

logger = logging.getLogger("enlace.batch")


class BatchSummary:
    """Summary of batch processing results."""

    def __init__(
        self,
        batch_id: str,
        papers_processed: int = 0,
        papers_successful: int = 0,
        papers_failed: int = 0,
        total_tables: int = 0,
        total_figures: int = 0,
        validation_passed: int = 0,
        validation_failed: int = 0,
        processing_time_seconds: float = 0.0,
        results: list[dict[str, Any]] | None = None,
    ):
        """Initialize batch summary.

        Args:
            batch_id: Unique identifier for this batch
            papers_processed: Total papers processed
            papers_successful: Papers successfully extracted
            papers_failed: Papers that failed extraction
            total_tables: Total tables extracted
            total_figures: Total figures extracted
            validation_passed: Papers that passed validation
            validation_failed: Papers that failed validation
            processing_time_seconds: Total processing time
            results: Individual paper results

        """
        self.batch_id = batch_id
        self.papers_processed = papers_processed
        self.papers_successful = papers_successful
        self.papers_failed = papers_failed
        self.total_tables = total_tables
        self.total_figures = total_figures
        self.validation_passed = validation_passed
        self.validation_failed = validation_failed
        self.processing_time_seconds = processing_time_seconds
        self.results = results or []

    def save(self, output_dir: Path) -> None:
        """Save batch summary to JSON file.

        Args:
            output_dir: Directory to save summary

        """
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "batch_summary.json"

        summary_dict = {
            "batch_id": self.batch_id,
            "timestamp": datetime.now().isoformat(),
            "papers_processed": self.papers_processed,
            "papers_successful": self.papers_successful,
            "papers_failed": self.papers_failed,
            "total_tables": self.total_tables,
            "total_figures": self.total_figures,
            "validation_passed": self.validation_passed,
            "validation_failed": self.validation_failed,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "results": self.results,
        }

        with summary_path.open("w") as f:
            json.dump(summary_dict, f, indent=2)

        logger.info(f"Batch summary saved to {summary_path}")


class BatchProcessor:
    """Process multiple research papers in batch."""

    SUPPORTED_EXTENSIONS = [".pdf", ".docx"]

    def __init__(
        self,
        output_dir: Path,
        workers: int = 4,
        enable_augmentation: bool = False,
        enable_validation: bool = True,
        validation_level: str = "standard",
        config_file: Path | None = None,
        verbose: bool = False,
    ):
        """Initialize batch processor.

        Args:
            output_dir: Output directory for results
            workers: Number of parallel workers
            enable_augmentation: Enable semantic augmentation
            enable_validation: Run validation after extraction
            validation_level: Validation level to use
            config_file: Optional configuration file
            verbose: Enable verbose logging

        """
        self.output_dir = Path(output_dir)
        self.workers = workers
        self.enable_validation = enable_validation
        self.validation_level = validation_level

        # Create extraction config
        self.extraction_config = ExtractionConfig.load_config(
            config_file=config_file,
            enable_augmentation=enable_augmentation,
            output_dir=output_dir,
            verbose=verbose,
        )

        # Create validation config if needed
        if enable_validation:
            self.validation_config = ValidationConfig.load_config(
                config_file=config_file,
                level=validation_level,
                output_dir=output_dir,  # Same dir as extraction - saves to paper_id subdirs
                verbose=verbose,
            )
        else:
            self.validation_config = None

        logger.info(
            f"BatchProcessor initialized: workers={workers}, "
            f"augmentation={enable_augmentation}, validation={enable_validation}"
        )

    def process(self, input_dir: Path) -> BatchSummary:
        """Process all papers in directory.

        Args:
            input_dir: Directory containing PDF/DOCX files

        Returns:
            BatchSummary with processing results

        """
        start_time = datetime.now()
        batch_id = f"batch_{start_time.strftime('%Y%m%d_%H%M%S')}"

        # Find all supported papers
        papers = self._find_papers(input_dir)
        if not papers:
            logger.warning(f"No papers found in {input_dir}")
            return BatchSummary(batch_id=batch_id)

        logger.info(f"Found {len(papers)} papers to process")

        # Process papers in parallel
        results = []
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_paper = {
                executor.submit(self._process_paper, paper): paper for paper in papers
            }

            # Collect results as they complete
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(
                        f"Completed {result['paper_id']}: "
                        f"success={result['success']}, "
                        f"tables={result.get('tables_extracted', 0)}"
                    )
                except Exception as e:
                    logger.error(f"Failed to process {paper.name}: {e}")
                    results.append(
                        {
                            "paper_path": str(paper),
                            "paper_id": paper.stem,
                            "success": False,
                            "error": str(e),
                        }
                    )

        # Calculate summary statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        summary = self._create_summary(batch_id, results, processing_time)

        logger.info(
            f"Batch processing complete: "
            f"{summary.papers_successful}/{summary.papers_processed} successful"
        )

        return summary

    def _find_papers(self, input_dir: Path) -> list[Path]:
        """Find all supported paper files in directory.

        Args:
            input_dir: Directory to search

        Returns:
            List of paper file paths

        """
        papers = []
        for ext in self.SUPPORTED_EXTENSIONS:
            papers.extend(input_dir.glob(f"*{ext}"))

        return sorted(papers)

    def _process_paper(self, paper_path: Path) -> dict[str, Any]:
        """Process a single paper.

        Args:
            paper_path: Path to paper file

        Returns:
            Dictionary with processing results

        """
        result = {
            "paper_path": str(paper_path),
            "paper_id": paper_path.stem,
            "success": False,
        }

        try:
            # Extract
            extractor = PaperExtractor(self.extraction_config)
            extraction = extractor.extract(paper_path)

            # Augment if enabled
            if self.extraction_config.enable_augmentation:
                extraction = extractor.augment(extraction)

            # Save extraction
            paper_output_dir = self.output_dir / extraction.paper_id
            extraction.save(
                paper_output_dir, format=self.extraction_config.output_format
            )

            result["success"] = True
            result["paper_id"] = extraction.paper_id
            result["tables_extracted"] = extraction.tables_extracted
            result["figures_extracted"] = extraction.figures_extracted
            result["extraction_quality"] = extraction.extraction_quality
            result["output_dir"] = str(paper_output_dir)

            # Validate if enabled
            if self.enable_validation and self.validation_config:
                try:
                    validator = ExtractionValidator(self.validation_config)
                    validation = validator.validate(
                        extraction, level=self.validation_level
                    )

                    result["validation_passed"] = validation.passed
                    result["validation_score"] = validation.score
                    result["validation_issues"] = len(validation.issues)

                    # Save validation report
                    validation.save(self.validation_config.output_dir)

                except Exception as e:
                    logger.error(f"Validation failed for {extraction.paper_id}: {e}")
                    result["validation_error"] = str(e)

        except EnlaceError as e:
            logger.error(f"Extraction failed for {paper_path.name}: {e}")
            result["error"] = str(e)
        except Exception as e:
            logger.error(f"Unexpected error processing {paper_path.name}: {e}")
            result["error"] = f"Unexpected error: {str(e)}"

        return result

    def _create_summary(
        self, batch_id: str, results: list[dict[str, Any]], processing_time: float
    ) -> BatchSummary:
        """Create batch summary from results.

        Args:
            batch_id: Batch identifier
            results: List of processing results
            processing_time: Total processing time in seconds

        Returns:
            BatchSummary object

        """
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        total_tables = sum(r.get("tables_extracted", 0) for r in successful)
        total_figures = sum(r.get("figures_extracted", 0) for r in successful)

        validation_passed = sum(
            1 for r in successful if r.get("validation_passed", False)
        )
        validation_failed = sum(
            1 for r in successful if r.get("validation_passed") is False
        )

        return BatchSummary(
            batch_id=batch_id,
            papers_processed=len(results),
            papers_successful=len(successful),
            papers_failed=len(failed),
            total_tables=total_tables,
            total_figures=total_figures,
            validation_passed=validation_passed,
            validation_failed=validation_failed,
            processing_time_seconds=processing_time,
            results=results,
        )
