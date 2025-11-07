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

### Extract Tables from Research Papers

```bash
# Basic extraction
python src/parse.py paper.pdf -o output/

# With semantic augmentation (adds context from paper text)
uv run python .claude/subagents/content-extractor/extractor.py paper.pdf --augment

# Batch process multiple papers
python src/parse.py papers/ --batch -o output/
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
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

See [docs/SUBAGENT_ARCHITECTURE.md](docs/SUBAGENT_ARCHITECTURE.md) for complete documentation.

## Documentation

- [CLAUDE.md](CLAUDE.md) - Development guide for Claude Code
- [docs/SUBAGENT_ARCHITECTURE.md](docs/SUBAGENT_ARCHITECTURE.md) - Semantic augmentation architecture
- [tests/README.md](tests/README.md) - Testing documentation
