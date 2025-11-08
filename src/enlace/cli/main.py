"""Enlace CLI - Extract and validate research paper data.

This module provides the main command-line interface for the enlace package,
supporting extraction, validation, and batch processing of research papers.
"""

import logging
from pathlib import Path

import typer

from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.exceptions import EnlaceError
from enlace.utils.logging import setup_logging

app = typer.Typer(
    name="enlace",
    help="Extract and validate research paper data",
    add_completion=False,
)

logger = logging.getLogger("enlace.cli")


@app.command()
def extract(
    input_path: Path = typer.Argument(
        ..., help="Path to PDF or DOCX file", exists=True
    ),
    output_dir: Path = typer.Option(
        Path("output"), "--output", "-o", help="Output directory"
    ),
    augment: bool = typer.Option(
        False, "--augment", help="Enable semantic augmentation"
    ),
    ocr: bool = typer.Option(False, "--ocr", help="Enable OCR for scanned documents"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format (json, csv, both)"
    ),
    config_file: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file", exists=True
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Extract tables, figures, and metadata from research papers.

    Example:
        enlace extract paper.pdf -o output --augment

    """
    try:
        # Setup logging
        setup_logging(verbose=verbose)

        # Load configuration
        config = ExtractionConfig.load_config(
            config_file=config_file,
            enable_augmentation=augment,
            enable_ocr=ocr,
            output_format=format,
            output_dir=output_dir,
            verbose=verbose,
        )

        # Extract
        logger.info(f"Extracting from {input_path.name}")
        extractor = PaperExtractor(config)
        result = extractor.extract(input_path)

        # Augment if requested
        if augment:
            logger.info("Running semantic augmentation...")
            result = extractor.augment(result)

        # Save
        result.save(output_dir, format=format)

        # Display results
        typer.secho(f"✓ Extraction complete: {result.paper_id}", fg=typer.colors.GREEN)
        typer.echo(f"  Tables: {result.tables_extracted}")
        typer.echo(f"  Figures: {result.figures_extracted}")
        typer.echo(f"  Quality: {result.extraction_quality:.2f}")
        typer.echo(f"  Output: {output_dir / result.paper_id}")

    except EnlaceError as e:
        logger.error(str(e))
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        typer.secho(f"✗ Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def validate(
    extraction_path: Path = typer.Argument(
        ..., help="Path to extraction.json or directory", exists=True
    ),
    level: str = typer.Option(
        "standard",
        "--level",
        "-l",
        help="Validation level (quick, standard, comprehensive)",
    ),
    output_dir: Path = typer.Option(
        Path("validation_reports"), "--output", "-o", help="Output directory"
    ),
    config_file: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file", exists=True
    ),
    fail_on_issues: bool = typer.Option(
        False, "--fail-on-issues", help="Exit with error if issues found"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Validate extracted research data.

    Example:
        enlace validate output/paper/extraction.json --level comprehensive

    """
    try:
        setup_logging(verbose=verbose)

        config = ValidationConfig.load_config(
            config_file=config_file,
            level=level,
            output_dir=output_dir,
            fail_on_issues=fail_on_issues,
            verbose=verbose,
        )

        validator = ExtractionValidator(config)
        result = validator.validate(extraction_path, level=level)

        result.save(output_dir)

        # Display results
        status = (
            typer.style("✓ PASSED", fg=typer.colors.GREEN)
            if result.passed
            else typer.style("✗ FAILED", fg=typer.colors.RED)
        )
        typer.echo(f"{status}: {result.paper_id}")
        typer.echo(f"  Score: {result.score:.2f}")
        typer.echo(f"  Issues: {len(result.issues)}")
        typer.echo(f"  Warnings: {len(result.warnings)}")

        if result.issues:
            typer.echo("\nIssues:")
            for issue in result.issues[:5]:
                typer.secho(f"  - {issue.message}", fg=typer.colors.RED)
            if len(result.issues) > 5:
                typer.echo(f"  ... and {len(result.issues) - 5} more")

        if result.recommendations:
            typer.echo("\nRecommendations:")
            for rec in result.recommendations:
                typer.echo(f"  - {rec}")

        typer.echo(f"\nReport: {output_dir / f'{result.paper_id}_validation.json'}")

        if fail_on_issues and not result.passed:
            raise typer.Exit(code=1)

    except EnlaceError as e:
        logger.error(str(e))
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def batch(
    input_dir: Path = typer.Argument(
        ..., help="Directory containing papers", exists=True, dir_okay=True
    ),
    output_dir: Path = typer.Option(
        Path("batch_output"), "--output", "-o", help="Output directory"
    ),
    workers: int = typer.Option(
        4, "--workers", "-w", help="Number of parallel workers"
    ),
    augment: bool = typer.Option(
        False, "--augment", help="Enable semantic augmentation"
    ),
    validate_results: bool = typer.Option(
        True, "--validate/--no-validate", help="Run validation after extraction"
    ),
    validation_level: str = typer.Option(
        "standard", "--validation-level", help="Validation level to use"
    ),
    config_file: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file", exists=True
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Process multiple papers in batch.

    Example:
        enlace batch papers/ -o output --workers 8 --augment

    """
    try:
        setup_logging(verbose=verbose)

        from enlace.core.batch import BatchProcessor

        processor = BatchProcessor(
            output_dir=output_dir,
            workers=workers,
            enable_augmentation=augment,
            enable_validation=validate_results,
            validation_level=validation_level,
            config_file=config_file,
            verbose=verbose,
        )

        logger.info(f"Starting batch processing of {input_dir}")
        summary = processor.process(input_dir)
        summary.save(output_dir)

        typer.secho("✓ Batch processing complete", fg=typer.colors.GREEN)
        typer.echo(f"  Papers processed: {summary.papers_processed}")
        typer.echo(f"  Successful: {summary.papers_successful}")
        typer.echo(f"  Failed: {summary.papers_failed}")
        typer.echo(f"  Total tables: {summary.total_tables}")
        typer.echo(f"  Total figures: {summary.total_figures}")
        if validate_results:
            typer.echo(f"  Validation passed: {summary.validation_passed}")
            typer.echo(f"  Validation failed: {summary.validation_failed}")
        typer.echo(f"  Output: {output_dir}")

    except EnlaceError as e:
        logger.error(str(e))
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
