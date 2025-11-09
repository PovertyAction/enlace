"""Enlace CLI - Extract and validate research paper data.

This module provides the main command-line interface for the enlace package,
supporting extraction, validation, and batch processing of research papers.
"""

import asyncio
import logging
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.exceptions import EnlaceError
from enlace.utils.logging import setup_logging

# Load environment variables from .env file
load_dotenv()

# Rich console for better output
console = Console()

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
    ocr_backend: str = typer.Option(
        "none",
        "--ocr",
        help="OCR backend (auto, tesseract, easyocr, or none to disable)",
    ),
    ocr_confidence: float = typer.Option(
        0.8,
        "--ocr-confidence",
        min=0.0,
        max=1.0,
        help="OCR confidence threshold for hybrid fallback (0.0-1.0)",
    ),
    no_hybrid_ocr: bool = typer.Option(
        False, "--no-hybrid-ocr", help="Disable hybrid OCR fallback"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format (json, csv, both)"
    ),
    config_file: Path | None = typer.Option(
        None, "--config", "-c", help="Configuration file", exists=True
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
):
    """Extract tables, figures, and metadata from research papers.

    Example:
        enlace extract paper.pdf -o output --augment

    """
    try:
        # Derive paper_id from input filename for logging setup
        paper_id = input_path.stem

        # Setup logging with file output to {output_dir}/{paper_id}/logs/
        setup_logging(
            level=log_level, verbose=verbose, paper_id=paper_id, output_dir=output_dir
        )

        # Load configuration
        config = ExtractionConfig.load_config(
            config_file=config_file,
            enable_augmentation=augment,
            enable_ocr=ocr_backend != "none",
            ocr_backend=ocr_backend if ocr_backend != "none" else "auto",
            hybrid_ocr_enabled=not no_hybrid_ocr,
            ocr_confidence_threshold=ocr_confidence,
            output_format=format,
            output_dir=output_dir,
            verbose=verbose,
        )

        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            # Define extraction steps
            total_steps = 4 if augment else 3
            task = progress.add_task(
                f"[cyan]Processing {input_path.name}...", total=total_steps
            )

            # Step 1: Extract
            progress.update(
                task, description=f"[cyan]Extracting from {input_path.name}"
            )
            logger.info(f"Extracting from {input_path.name}")
            extractor = PaperExtractor(config)
            result = extractor.extract(input_path)
            progress.advance(task)

            # Step 2: Augment if requested
            if augment:
                progress.update(
                    task, description="[yellow]Running semantic augmentation"
                )
                logger.info("Running semantic augmentation...")
                result = asyncio.run(extractor.augment(result))
                progress.advance(task)

            # Step 3: Save
            progress.update(task, description="[blue]Saving results")
            result.save(output_dir, format=format)
            progress.advance(task)

            # Step 4: Complete
            progress.update(
                task, description=f"[green]✓ Extraction complete: {result.paper_id}"
            )
            progress.advance(task)

        # Display results summary
        console.print()
        console.print(f"[bold green]✓ Extraction complete: {result.paper_id}[/]")
        console.print(f"  [cyan]Tables:[/] {result.tables_extracted}")
        console.print(f"  [cyan]Figures:[/] {result.figures_extracted}")
        console.print(f"  [cyan]Quality:[/] {result.extraction_quality:.2f}")
        console.print(f"  [cyan]Output:[/] {output_dir / result.paper_id}")

    except EnlaceError as e:
        logger.error(str(e))
        console.print(f"[bold red]✗ Error:[/] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception("Unexpected error")
        console.print(f"[bold red]✗ Unexpected error:[/] {e}")
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
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
):
    """Validate extracted research data.

    Example:
        enlace validate output/paper/extraction.json --level comprehensive

    """
    try:
        setup_logging(level=log_level, verbose=verbose)

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
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
):
    """Process multiple papers in batch.

    Example:
        enlace batch papers/ -o output --workers 8 --augment

    """
    try:
        setup_logging(level=log_level, verbose=verbose)

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
