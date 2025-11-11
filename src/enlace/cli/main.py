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

from enlace.core.config import ExtractionConfig, SummaryConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.summarizer import PaperSummarizer
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
    vlm: bool = typer.Option(
        False, "--vlm", help="Enable VLM fallback for low-quality tables"
    ),
    vlm_framework: str = typer.Option(
        "auto",
        "--vlm-framework",
        help="VLM inference framework (auto, transformers, mlx)",
    ),
    claude_cleanup: bool = typer.Option(
        False, "--claude-cleanup", help="Enable Claude cleanup pass (requires API key)"
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Analyze document structure without full extraction (estimate OCR costs, table count)",
    ),
    show_config: bool = typer.Option(
        False, "--show-config", help="Display effective configuration and exit"
    ),
):
    """Extract tables, figures, and metadata from research papers.

    Examples:
        # Basic extraction
        enlace extract paper.pdf -o output

        # With semantic augmentation
        enlace extract paper.pdf -o output --augment

        # Dry-run to estimate OCR requirements
        enlace extract paper.pdf --ocr auto --dry-run

        # Show effective configuration
        enlace extract paper.pdf --show-config

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
            enable_vlm=vlm,
            vlm_framework=vlm_framework,
            enable_claude_cleanup=claude_cleanup,
            enable_ocr=ocr_backend != "none",
            ocr_backend=ocr_backend if ocr_backend != "none" else "auto",
            hybrid_ocr_enabled=not no_hybrid_ocr,
            ocr_confidence_threshold=ocr_confidence,
            output_format=format,
            output_dir=output_dir,
            verbose=verbose,
            dry_run=dry_run,
        )

        # Show effective configuration and exit if requested
        if show_config:
            console.print("\n[bold cyan]Effective Configuration:[/]")
            console.print()
            effective = config.get_effective_config()
            for field_name, field_info in effective.items():
                source_color = {
                    "cli": "yellow",
                    "file": "green",
                    "default": "dim",
                    "unknown": "red",
                }.get(field_info["source"], "white")
                console.print(
                    f"  [bold]{field_name}[/]: {field_info['value']} "
                    f"[{source_color}]({field_info['source']})[/]"
                )
                if field_info.get("description"):
                    console.print(f"    [dim]{field_info['description']}[/]")
            return

        # Dry-run mode: analyze document structure without full extraction
        if dry_run:
            console.print(
                f"\n[bold yellow]DRY RUN MODE:[/] Analyzing {input_path.name}...\n"
            )

            # Quick document analysis
            from enlace.utils.docling_utils import analyze_document_structure

            analysis = analyze_document_structure(input_path, config)

            # Display analysis results
            console.print("[bold cyan]Document Analysis:[/]")
            console.print(f"  [cyan]Pages:[/] {analysis.get('pages', 'unknown')}")
            console.print(f"  [cyan]Tables detected:[/] {analysis.get('tables', 0)}")
            console.print(f"  [cyan]Figures detected:[/] {analysis.get('figures', 0)}")
            console.print(
                f"  [cyan]Scanned content:[/] {analysis.get('scanned_percentage', 0):.1f}%"
            )

            if config.enable_ocr and analysis.get("scanned_percentage", 0) > 0:
                console.print("\n[bold cyan]OCR Estimate:[/]")
                console.print(f"  [cyan]Primary backend:[/] {config.ocr_backend}")
                if config.hybrid_ocr_enabled and config.ocr_backend == "auto":
                    console.print(
                        "  [cyan]Hybrid fallback:[/] Enabled (Tesseract → EasyOCR)"
                    )
                    console.print(
                        f"  [yellow]Estimated fallback usage:[/] "
                        f"~{analysis.get('estimated_fallback_pct', 20):.0f}% of cells"
                    )
                console.print(
                    f"  [cyan]Confidence threshold:[/] {config.ocr_confidence_threshold}"
                )

            console.print(
                "\n[dim]To proceed with extraction, run without --dry-run flag[/]"
            )
            return

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

            # Build CLI command for reproducibility
            import sys

            cli_command = " ".join(sys.argv)

            # Get config as dict for reproducibility (safely excludes API keys)
            config_dict = config.to_safe_dict()

            extractor = PaperExtractor(config)
            result = extractor.extract(
                input_path, cli_command=cli_command, config_dict=config_dict
            )
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
    checks: list[str] = typer.Option(
        None,
        "--check",
        help="Custom validation checks (overrides --level). Can specify multiple times.",
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

    Examples:
        # Use predefined level
        enlace validate output/paper/extraction.json --level comprehensive

        # Custom checks
        enlace validate output/paper/extraction.json --check structure --check accuracy

        # List available checks
        enlace validate --help  # See validator module for available checks

    """
    try:
        setup_logging(level=log_level, verbose=verbose)

        # Infer output directory from extraction path if using default
        if output_dir == Path("validation_reports"):
            # If extraction_path is like "output/paper_id/extraction.json"
            # use "output" as the output_dir
            if extraction_path.name == "extraction.json":
                output_dir = extraction_path.parent.parent
            else:
                # If extraction_path is a directory, use its parent
                output_dir = (
                    extraction_path.parent
                    if extraction_path.is_file()
                    else extraction_path
                )

        config = ValidationConfig.load_config(
            config_file=config_file,
            level=level,
            output_dir=output_dir,
            fail_on_issues=fail_on_issues,
            verbose=verbose,
        )

        # If custom checks provided, display what will be run
        if checks:
            console.print(
                f"\n[bold cyan]Running custom validation checks:[/] {', '.join(checks)}\n"
            )

        validator = ExtractionValidator(config)
        result = validator.validate(extraction_path, level=level, custom_checks=checks)

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

        typer.echo(f"\nReport: {output_dir / result.paper_id / 'validation.json'}")

        if fail_on_issues and not result.passed:
            raise typer.Exit(code=1)

    except EnlaceError as e:
        logger.error(str(e))
        typer.secho(f"✗ Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


@app.command()
def summarize(
    extraction_path: Path = typer.Argument(
        ...,
        help="Path to extraction.json or directory containing it",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory (default: same as extraction)",
    ),
    validation_path: Path | None = typer.Option(
        None,
        "--validation",
        help="Path to validation.json (auto-detected if not provided)",
    ),
    pdf_path: Path | None = typer.Option(
        None,
        "--pdf",
        help="Path to original PDF (enables direct PDF analysis)",
    ),
    llm_model: str = typer.Option(
        "claude-3-5-haiku-20241022",
        "--model",
        help="LLM model to use for summarization",
    ),
    detail_level: str = typer.Option(
        "standard",
        "--level",
        help="Summary detail level: brief, standard, or detailed",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        help="Output format: json, markdown, or both",
    ),
    use_web_search: bool = typer.Option(
        False,
        "--web-search",
        help="Enhance summary with web search",
    ),
    config_file: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Configuration file",
        exists=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
):
    """Generate LLM-based summary from extraction results.

    This command creates structured summaries of research papers using the
    extraction artifacts and optional validation results. The summary includes
    research questions, methodology, findings, and quality assessments.

    Examples:
        # Basic usage
        enlace summarize output/paper/extraction.json

        # With validation and custom output
        enlace summarize output/paper --output summaries/

        # Generate markdown format
        enlace summarize output/paper --format markdown

        # Use different model with detailed summary
        enlace summarize output/paper --model claude-3-5-haiku-20241022 --level detailed

    """
    try:
        setup_logging(level=log_level, verbose=verbose)
        logger.info(f"Starting summarization: {extraction_path}")

        # Convert to Path
        extraction_path = Path(extraction_path)

        # Infer output directory from extraction path if not provided
        if output_dir is None:
            # If extraction_path is like "output/paper_id/extraction.json"
            # use "output" as the output_dir
            if extraction_path.name == "extraction.json":
                output_dir = extraction_path.parent.parent
            else:
                # If extraction_path is a directory, use its parent
                output_dir = (
                    extraction_path.parent
                    if extraction_path.is_file()
                    else extraction_path
                )

        # Auto-detect validation.json if not provided
        if validation_path is None:
            # Try to find validation.json in same directory
            if extraction_path.name == "extraction.json":
                potential_validation = extraction_path.parent / "validation.json"
            else:
                potential_validation = extraction_path / "validation.json"

            if potential_validation.exists():
                validation_path = potential_validation
                logger.info(f"Auto-detected validation file: {validation_path}")

        # Load configuration
        config = SummaryConfig.load_config(
            config_file=config_file,
            llm_model=llm_model,
            detail_level=detail_level,
            output_format=output_format,
            use_web_search=use_web_search,
            output_dir=output_dir,
            verbose=verbose,
        )

        # Create summarizer and generate summary
        console.print("\n[bold cyan]Generating summary...[/]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Calling LLM...", total=3)

            # Initialize
            summarizer = PaperSummarizer(config)
            progress.advance(task)

            # Generate summary
            progress.update(task, description="[cyan]Generating summary...")
            result = summarizer.summarize(
                extraction_path=extraction_path,
                validation_path=validation_path,
                pdf_path=pdf_path,
            )
            progress.advance(task)

            # Save results
            progress.update(task, description="[cyan]Saving results...")
            result.save(output_dir, format=output_format)
            progress.advance(task)

        # Display results
        console.print(f"\n[bold green]✓ Summary complete: {result.paper_id}[/]")

        if result.title:
            console.print(f"\n[bold]Title:[/] {result.title}")
        if result.overview:
            console.print(f"\n[bold]Overview:[/]\n{result.overview}")

        console.print("\n[bold cyan]Quality Metrics:[/]")
        console.print(f"  Extraction Quality: {result.extraction_quality:.2f}")
        console.print(f"  Validation Score: {result.validation_score:.2f}")

        if result.key_findings:
            console.print("\n[bold cyan]Key Findings:[/]")
            for finding in result.key_findings[:3]:
                console.print(f"  • {finding}")
            if len(result.key_findings) > 3:
                console.print(f"  ... and {len(result.key_findings) - 3} more")

        # Output location
        paper_dir = output_dir / result.paper_id
        if output_format == "both":
            console.print(
                f"\n[bold]Output:[/] {paper_dir / 'summary.json'}, {paper_dir / 'summary.md'}"
            )
        else:
            ext = "json" if output_format == "json" else "md"
            console.print(f"\n[bold]Output:[/] {paper_dir / f'summary.{ext}'}")

        if result.processing_time_seconds:
            console.print(
                f"[dim]Processing time: {result.processing_time_seconds:.1f}s[/]"
            )

    except EnlaceError as e:
        logger.error(str(e))
        console.print(f"[bold red]✗ Error:[/] {e}")
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
