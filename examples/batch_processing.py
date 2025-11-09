"""Batch processing example.

This example demonstrates processing multiple research papers in parallel
with automatic validation and summary reporting.
"""

from pathlib import Path

from enlace.core.batch import BatchProcessor


def main():
    """Process multiple papers with batch processing."""
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

    # Process all papers
    print(f"Processing papers from {papers_dir}...")
    print(f"Output directory: {output_dir}")
    print(f"Workers: {processor.workers}")
    print(f"Validation: {processor.enable_validation}")
    print()

    summary = processor.process(papers_dir)

    # Display summary
    print("\n=== Batch Processing Summary ===")
    print(f"Papers processed: {summary.papers_processed}")
    print(f"Successful: {summary.papers_successful}")
    print(f"Failed: {summary.papers_failed}")
    print(f"Total tables: {summary.total_tables}")
    print(f"Total figures: {summary.total_figures}")
    print(f"Average quality: {summary.avg_quality:.2f}")
    print(f"Processing time: {summary.processing_time_seconds:.1f}s")

    # Display failed papers
    if summary.failed_papers:
        print("\n=== Failed Papers ===")
        for paper in summary.failed_papers:
            print(f"  - {paper}")

    # Save summary
    summary.save(output_dir)
    print(f"\n✓ Batch summary saved to {output_dir / 'batch_summary.json'}")

    # Display validation summary if enabled
    if processor.enable_validation and summary.validation_summary:
        print("\n=== Validation Summary ===")
        val_summary = summary.validation_summary
        print(f"Papers validated: {val_summary['total_validated']}")
        print(f"Passed: {val_summary['passed']}")
        print(f"Failed: {val_summary['failed']}")
        print(f"Average score: {val_summary['avg_score']:.2f}")

        if val_summary["failed_papers"]:
            print("\n=== Failed Validation ===")
            for paper in val_summary["failed_papers"]:
                print(f"  - {paper}")


def main_with_custom_config():
    """Process papers with custom configuration."""
    # Create processor with custom configs
    processor = BatchProcessor(
        output_dir=Path("batch_output"),
        workers=8,
        enable_augmentation=True,
        enable_validation=True,
        validation_level="comprehensive",
    )

    # Process papers
    summary = processor.process(Path("papers"))

    print(f"Processed {summary.papers_successful}/{summary.papers_processed} papers")


def main_with_filtering():
    """Process papers with custom filtering and error handling."""
    import concurrent.futures
    from pathlib import Path

    from enlace.core.config import ExtractionConfig
    from enlace.core.extractor import PaperExtractor
    from enlace.exceptions import EnlaceError

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

    # Get all PDF files
    papers_dir = Path("papers")
    papers = list(papers_dir.glob("*.pdf"))

    # Filter papers (e.g., only papers from specific year)
    # papers = [p for p in papers if "2020" in p.stem]

    print(f"Processing {len(papers)} papers...")

    # Process in parallel
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_paper, paper, Path("batch_output"))
            for paper in papers
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

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\nProcessed {successful}/{len(results)} papers successfully")


if __name__ == "__main__":
    # Run basic batch processing
    main()

    # Uncomment to try other examples:
    # main_with_custom_config()
    # main_with_filtering()
