# %% [markdown]
# # Batch Processing Example
#
# This example demonstrates processing multiple research papers in parallel
# with automatic validation and summary reporting.

# %%
import concurrent.futures
from pathlib import Path

from enlace.core.batch import BatchProcessor
from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.exceptions import EnlaceError

# %% [markdown]
# ## Basic Batch Processing

# %%
# Input directory containing papers
papers_dir = Path("papers")

# Output directory for results
output_dir = Path("batch_output")

# Create batch processor with configuration
processor = BatchProcessor(
    output_dir=output_dir,
    workers=4,  # Number of parallel workers
    enable_augmentation=False,  # Enable for semantic context
    enable_validation=True,  # Validate after extraction
    validation_level="standard",  # quick, standard, or comprehensive
)

# %% [markdown]
# ## Process All Papers

# %%
# Process all papers
print(f"Processing papers from {papers_dir}...")
print(f"Output directory: {output_dir}")
print(f"Workers: {processor.workers}")
print(f"Validation: {processor.enable_validation}")
print()

summary = processor.process(papers_dir)

# %% [markdown]
# ## Display Results

# %%
# Display summary
print("\n=== Batch Processing Summary ===")
print(f"Papers processed: {summary.papers_processed}")
print(f"Successful: {summary.papers_successful}")
print(f"Failed: {summary.papers_failed}")
print(f"Total tables: {summary.total_tables}")
print(f"Total figures: {summary.total_figures}")
print(f"Average quality: {summary.avg_quality:.2f}")
print(f"Processing time: {summary.processing_time_seconds:.1f}s")

# %%
# Display failed papers
if hasattr(summary, "failed_papers") and summary.failed_papers:
    print("\n=== Failed Papers ===")
    for paper in summary.failed_papers:
        print(f"  - {paper}")

# %%
# Save summary
summary.save(output_dir)
print(f"\n✓ Batch summary saved to {output_dir / 'batch_summary.json'}")

# %%
# Display validation summary if enabled
if processor.enable_validation and hasattr(summary, "validation_summary"):
    print("\n=== Validation Summary ===")
    val_summary = summary.validation_summary
    print(f"Papers validated: {val_summary['total_validated']}")
    print(f"Passed: {val_summary['passed']}")
    print(f"Failed: {val_summary['failed']}")
    print(f"Average score: {val_summary['avg_score']:.2f}")

    if val_summary.get("failed_papers"):
        print("\n=== Failed Validation ===")
        for paper in val_summary["failed_papers"]:
            print(f"  - {paper}")

# %% [markdown]
# ## Advanced: Custom Parallel Processing
#
# Build custom batch processing workflows with error handling.


def process_paper(paper_path: Path, output_dir: Path) -> dict:
    """Process single paper with error handling."""
    config = ExtractionConfig(
        enable_ocr=True, enable_augmentation=False, output_dir=output_dir
    )
    extractor = PaperExtractor(config)

    try:
        result = extractor.extract(paper_path)
        result.save(output_dir / paper_path.stem)

        return {
            "paper": paper_path.name,
            "success": True,
            "tables": result.tables_extracted,
            "quality": result.extraction_quality,
        }
    except EnlaceError as e:
        return {"paper": paper_path.name, "success": False, "error": str(e)}


# %%
# Get all PDF files
papers_dir = Path("papers")
papers = list(papers_dir.glob("*.pdf"))

# Filter papers (e.g., only papers from specific year)
# papers = [p for p in papers if "2020" in p.stem]

print(f"Processing {len(papers)} papers...")

# %%
# Process in parallel
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_paper, paper, Path("batch_output")) for paper in papers
    ]

    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)

        if result["success"]:
            print(
                f"✓ {result['paper']}: {result['tables']} tables "
                f"(quality: {result['quality']:.2f})"
            )
        else:
            print(f"✗ {result['paper']}: {result['error']}")

# %%
# Summary
successful = sum(1 for r in results if r["success"])
print(f"\nProcessed {successful}/{len(results)} papers successfully")

# %% [markdown]
# ## Advanced: Comprehensive Batch Processing with Validation
#
# Process papers with extraction, augmentation, and comprehensive validation.


def process_paper_comprehensive(paper_path: Path, output_dir: Path):
    """Process single paper with extraction, augmentation, and validation."""
    config = ExtractionConfig(
        enable_ocr=True, enable_augmentation=True, output_dir=output_dir
    )
    extractor = PaperExtractor(config)

    try:
        # Extract and augment
        result = extractor.extract(paper_path)
        result = extractor.augment(result)
        result.save(output_dir / paper_path.stem)

        # Validate
        val_config = ValidationConfig(level="comprehensive")
        validator = ExtractionValidator(val_config)
        val_result = validator.validate(result)
        val_result.save(output_dir / "validation")

        return {
            "paper": paper_path.name,
            "success": True,
            "quality": result.extraction_quality,
            "validation_passed": val_result.passed,
        }
    except Exception as e:
        return {"paper": paper_path.name, "success": False, "error": str(e)}


# %%
# Parallel processing with comprehensive workflow
papers = list(Path("papers").glob("*.pdf"))
results = []

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_paper_comprehensive, paper, Path("output"))
        for paper in papers
    ]
    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

# Summary
successful = sum(1 for r in results if r["success"])
print(f"Processed {successful}/{len(results)} papers successfully")
