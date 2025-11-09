# enlace

Tools for parsing research papers and connecting to underlying microdata for data
harmonizations and meta-analysis

## Overview

The purpose of this repository is to provide tools and documentation to help
researchers working in development economics to more easily parse research papers,
extract relevant information, and connect to underlying microdata for data
harmonization and meta-analysis. The repository includes code for automating the
extraction of study characteristics, outcome measures, and statistical results from
research papers, as well as tools for linking these extracted data to existing
datasets and harmonizing variables across studies.

## Components

- **Paper Parsing**: Scripts and models for extracting structured data from research
  papers in PDF or DOCX format using docling.
- **Semantic Augmentation** (NEW): RAG-based system that enhances table extraction
  with semantic context from paper text, helping with data harmonization and error detection.
- **Microdata Linking**: Tools for connecting extracted study information to
  underlying microdata sources.
- **Data Harmonization**: Functions for standardizing variables and outcomes across
  studies to facilitate meta-analysis.

## Development set up

Development relies on the following software

- `winget` (Windows) or `homebrew` (MacOS/Linux) or `snap` (Linux) for package management and installation
- `git` for source control management
- `just` for running common command line patterns
- `uv` for installing Python and managing virtual environments

This repository uses a `Justfile` for collecting common command line actions that we run
to set up the computing environment and build the assets of the handbook. Note that you
should also have Git installed

To get started, make sure you have `Just` installed on your computer by running the
following from the command line:

| Platform  | Commands                                                            |
| --------- | ------------------------------------------------------------------- |
| Windows   | `winget install Git.Git Casey.Just astral-sh.uv GitHub.cli` |
| Mac/Linux | `brew install just uv gh`                                          |

This will make sure that you have the latest version of `Just`, as well as
[uv](https://docs.astral.sh/uv/) (installer for Python).

- We use `Just` in order to make it easier for all users to be productive with data
  and technology systems. The goal of using a `Justfile` is to help make the end goal of
  the user easier to achieve without needing to know or remember all of the technical
  details of how we get to that goal.
- We use `uv` to help ease use of Python. `uv` provides a global system for creating and
  building computing environments for Python.
- We use Quarto to allow users to focus on writing and data analytics. Writing in
  markdown, jupyter notebooks, python scripts, R scripts, etc. makes it easier to
  review, update, and deploy technical documentation.
- We also recommend using in Integrated Development Environment (IDE).
  Preferred options are `VS Code` or `Positron`.

| Platform  | Commands                                                            |
| --------- | ------------------------------------------------------------------- |
| Windows   | `winget install Microsoft.VisualStudioCode`                         |
| Mac       | `brew install --cask visual-studio-code`                            |
| Linux     | `sudo snap install code --classic`                                  |

| Platform  | Commands                                                            |
| --------- | ------------------------------------------------------------------- |
| Windows   | `winget install Posit.Positron`                                     |
| Mac       | `brew install --cask positron`                                      |

As a shortcut, if you already have `Just` installed, you can run the following to
install required software and build a python virtual environment that is used to build
the handbook pages:

```bash
just get-started
```

Note: you may need to restart your terminal after running the command above to activate
the installed software.

After the required software is installed, you can activate the Python virtual
environment:

| Shell      | Commands                                |
| ---------- | --------------------------------------- |
| Bash       | `.venv/Scripts/activate`                |
| Powershell | `.venv/Scripts/activate.ps1`            |
| Nushell    | `overlay use .venv/Scripts/activate.nu` |

## Quick Start

### Install the Package

For development, install the package in editable mode:

```bash
# Install in editable mode
uv pip install -e .

# Or use the just command
just venv
```

### Using the CLI

The `enlace` CLI provides three main commands for extracting and validating research paper data.

#### Extract Command

Extract tables, figures, and metadata from a single research paper:

```bash
# Basic extraction (replace paper.pdf with the path to the paper you want to process)
uv run enlace extract paper.pdf

# With custom output directory
uv run enlace extract paper.pdf -o output/

# Enable semantic augmentation (adds context from paper text)
# IMPORTANT: Requires ANTHROPIC_API_KEY environment variable
# Option 1: Use .env file (recommended)
cp .env.example .env  # Copy example file
# Edit .env and add your API key, then:
uv run enlace extract paper.pdf --augment

# Option 2: Set environment variable directly
export ANTHROPIC_API_KEY=your_api_key_here  # Linux/Mac
set ANTHROPIC_API_KEY=your_api_key_here     # Windows CMD
$env:ANTHROPIC_API_KEY="your_api_key_here"  # Windows PowerShell
uv run enlace extract paper.pdf --augment

# Enable OCR for scanned documents
uv run enlace extract paper.pdf --ocr

# Combine options with verbose output
uv run enlace extract paper.pdf -o output/ --augment --verbose

# Set custom logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
uv run enlace extract paper.pdf --log-level DEBUG

# Export as CSV or both formats (CSV and JSON)
uv run enlace extract paper.pdf --format csv
uv run enlace extract paper.pdf --format both

# Note: Logs are automatically saved to output/{paper_name}/logs/extraction.log
# INFO level logs are always saved to file, console verbosity controlled by --verbose or --log-level
```

#### Output Structure

After extraction, the output directory is organized as follows:

```text
output/
└── {paper_name}/              # Named after input file (e.g., "paper" from "paper.pdf")
    ├── extraction.json        # Complete extraction results in JSON format
    ├── logs/                  # Log files
    │   └── extraction.log     # Extraction logs (INFO level and above)
    ├── tables/                # CSV exports of extracted tables (when using --format csv or both)
    │   ├── regression_table_1.csv
    │   ├── regression_table_2.csv
    │   ├── summary_stats_table_1.csv
    │   └── balance_table_1.csv
    └── figures/               # Extracted figures as images
        ├── figure_1.png
        └── figure_2.png
```

**Notes:**

- `extraction.json` always contains the complete extraction results including all metadata
- `tables/` directory is only created when using `--format csv` or `--format both`
- `figures/` directory contains extracted figures from the paper
- `logs/` directory contains detailed extraction logs for debugging and review

#### Validate Command

Validate extracted data quality:

```bash
# Standard validation
uv run enlace validate output/paper/extraction.json

# Quick validation (structure and completeness only)
uv run enlace validate output/paper/extraction.json --level quick

# Comprehensive validation (all checks including semantic)
uv run enlace validate output/paper/extraction.json --level comprehensive

# Save validation report to custom directory
uv run enlace validate output/paper/extraction.json -o reports/

# Fail on issues (exit with error code if validation fails)
uv run enlace validate output/paper/extraction.json --fail-on-issues
```

#### Batch Command

Process multiple papers in parallel:

```bash
# Process all papers in a directory
uv run enlace batch papers/ -o batch_output/

# Use 8 parallel workers
uv run enlace batch papers/ --workers 8

# Enable semantic augmentation for all papers
uv run enlace batch papers/ --augment

# Skip validation after extraction
uv run enlace batch papers/ --no-validate

# Combine options
uv run enlace batch papers/ -o output/ --workers 8 --augment --verbose
```

#### Get Help

```bash
# Show all commands
uv run enlace --help

# Show help for specific command
uv run enlace extract --help
uv run enlace validate --help
uv run enlace batch --help
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run only unit tests (fast)
uv run pytest -m unit

# Run semantic augmentation tests
uv run pytest tests/test_semantic*.py -v
```

## Features

### Semantic Table Augmentation (NEW)

The semantic augmentation system enhances table extraction by adding context from the paper text:

- **Variable Context**: Definitions, measurement units, data sources
- **Treatment Context**: Intervention details, implementation
- **Sample Context**: Population characteristics, selection criteria
- **Methods Context**: Estimation techniques, standard error types
- **Error Detection**: Cross-validates parsed values to catch OCR errors
- **Confidence Scores**: Quality metrics for extracted information

**Requirements**: Semantic augmentation requires an Anthropic API key. Set the `ANTHROPIC_API_KEY` environment variable before using the `--augment` flag.

See [docs/SUBAGENT_ARCHITECTURE.md](docs/SUBAGENT_ARCHITECTURE.md) for complete documentation.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Development guide for Claude Code
- [docs/SUBAGENT_ARCHITECTURE.md](docs/SUBAGENT_ARCHITECTURE.md) - Semantic augmentation architecture
- [tests/README.md](tests/README.md) - Testing documentation
