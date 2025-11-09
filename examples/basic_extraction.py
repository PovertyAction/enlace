"""Basic paper extraction example.

This example demonstrates the simplest usage of enlace for extracting
tables, figures, and metadata from a research paper.
"""

from pathlib import Path

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor


def main():
    """Extract data from a single research paper."""
    # Input paper path
    paper_path = Path("paper.pdf")

    # Configure extraction
    config = ExtractionConfig(
        enable_ocr=False,  # Set to True for scanned documents
        enable_augmentation=False,  # Set to True for semantic context
        output_format="json",
        output_dir=Path("output"),
    )

    # Create extractor
    extractor = PaperExtractor(config)

    # Extract from paper
    print(f"Extracting from {paper_path.name}...")
    result = extractor.extract(paper_path)

    # Display summary
    print("\n=== Extraction Summary ===")
    print(f"Paper ID: {result.paper_id}")
    print(f"Tables extracted: {result.tables_extracted}")
    print(f"Figures extracted: {result.figures_extracted}")
    print(f"Extraction quality: {result.extraction_quality:.2f}")

    # Display metadata
    if result.metadata:
        print("\n=== Metadata ===")
        print(f"Title: {result.metadata.title}")
        print(f"Authors: {', '.join(result.metadata.authors)}")
        print(f"Year: {result.metadata.year}")
        print(f"DOI: {result.metadata.doi}")

    # Display tables
    print("\n=== Tables ===")
    for i, table in enumerate(result.tables, 1):
        print(f"{i}. {table.title} ({table.table_type})")

        # Show details for regression tables
        if table.table_type == "regression":
            print(f"   - Models: {len(table.models)}")
            print(f"   - Dependent variable: {table.dependent_variable}")

        # Show details for summary statistics
        elif table.table_type == "summary_statistics":
            print(f"   - Statistics: {len(table.statistics)}")
            print(f"   - Sample size: {table.sample_size}")

        # Show details for balance tables
        elif table.table_type == "balance":
            print(f"   - Variables: {len(table.variables)}")
            print(f"   - Groups: {', '.join(table.groups)}")

    # Display figures
    if result.figures:
        print("\n=== Figures ===")
        for i, figure in enumerate(result.figures, 1):
            print(f"{i}. {figure.title}")
            print(f"   - Type: {figure.figure_type}")
            print(f"   - Path: {figure.image_path}")

    # Display warnings
    if result.warnings:
        print("\n=== Warnings ===")
        for warning in result.warnings:
            print(f"  - {warning}")

    # Save results
    print(f"\nSaving results to {config.output_dir}...")
    result.save(config.output_dir, format=config.output_format)

    print("\n✓ Extraction complete!")
    print(f"  Output: {config.output_dir / result.paper_id}")


if __name__ == "__main__":
    main()
