# Set the shell to use
# set shell := ["nu", "-c"]
# Set shell for Windows

set windows-shell := ["powershell.exe", "-NoLogo", "-Command"]

# Set path to virtual environment's python

venv_dir := ".venv"
python := venv_dir + if os_family() == "windows" { "/Scripts/python.exe" } else { "/bin/python3" }

QUARTO_VERSION := "1.7.32"

# Display system information
system-info:
    @echo "CPU architecture: {{ arch() }}"
    @echo "Operating system type: {{ os_family() }}"
    @echo "Operating system: {{ os() }}"

# Clean venv
clean:
    rm -rf .venv

# Setup environment
get-started: pre-install venv install-readstat

# Update project software versions in requirements
update-reqs:
    uv lock
    pre-commit autoupdate

# create virtual environment
venv:
    uv sync
    uv tool install pre-commit
    uv run pre-commit install

activate-venv:
    uv shell

# launch jupyter lab
lab:
    uv run jupyter lab

# Install the read_stat extension (run once)
install-readstat:
    duckdb -c "INSTALL read_stat FROM community"

# Convert a Stata/SAS/SPSS file to CSV
convert input output:
    duckdb -c "LOAD read_stat; COPY (FROM read_stat('{{input}}')) TO '{{output}}'"

# Convert using replacement scan (shorter, works after extension is installed)
convert-csv input output:
    duckdb -c "COPY (FROM '{{input}}') TO '{{output}}'"

# Convert and preview first 10 rows
preview-csv input:
    duckdb -c "LOAD read_stat; FROM read_stat('{{input}}') LIMIT 10" -markdown

# # Batch convert all .dta files in a directory to CSV
# convert-all pattern="*.dta":
#     #!/usr/bin/env bash
#     for file in {{pattern}}; do
#         output="${file%.*}.csv"
#         duckdb -c "COPY (FROM '$file') TO '$output'"
#         echo "Converted: $file -> $output"
#     done

# Lint python code
lint-python:
    uv run ruff check

# Format python code
fmt-python:
    uv run ruff format

# Format a single python file, "f"
fmt-py f:
    uv run ruff format {{ f }}

# Lint sql scripts
lint-sql:
    uv run sqlfluff fix --dialect duckdb

# Format all markdown and config files
fmt-markdown:
    markdownlint-cli2 --config .markdownlint.yaml "**/*.qmd" "**/*.md" "#.venv" "#_archive" --fix

# Format a single markdown file, "f"
fmt-md f:
    markdownlint-cli2 --config .markdownlint.yaml {{ f }} --fix

# Check format of all markdown files
fmt-check-markdown:
    markdownlint-cli2 --config .markdownlint.yaml "**/*.qmd" "**/*.md" "#.venv" "#_archive"

fmt-all: fmt-python lint-python lint-sql fmt-markdown

# Run pre-commit hooks
pre-commit-run:
    pre-commit run

# Run all tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src --cov-report=term-missing --cov-report=html

# Run only unit tests
test-unit:
    uv run pytest -m unit

# Run only integration tests
test-integration:
    uv run pytest -m integration

# Run tests excluding slow tests
test-fast:
    uv run pytest -m "not slow"

# Run tests in verbose mode
test-verbose:
    uv run pytest -vv

# Run a specific test file
test-file f:
    uv run pytest {{ f }} -v

[windows]
pre-install:
    @echo "Checking and installing required tools..."
    @powershell -Command "if (!(Get-Command uv -ErrorAction SilentlyContinue)) { winget install --silent astral-sh.uv }"
    @powershell -Command "if (!(Get-Command pixi -ErrorAction SilentlyContinue)) { winget install --silent prefix-dev.pixi }"
    @powershell -Command "if (!(Get-Command gh -ErrorAction SilentlyContinue)) { winget install --silent GitHub.cli }"
    @powershell -Command "if (!(Get-Command rg -ErrorAction SilentlyContinue)) { winget install --silent BurntSushi.ripgrep.GNU }"
    @powershell -Command "if (!(Get-Command eza -ErrorAction SilentlyContinue)) { winget install --silent eza-community.eza }"
    @powershell -Command "if (!(Get-Command duckdb -ErrorAction SilentlyContinue)) { winget install --silent DuckDB.cli }"
    @powershell -Command "if (!(Get-Command quarto -ErrorAction SilentlyContinue)) { winget install --silent Posit.Quarto }"
    @powershell -Command "if (!(Get-Command node -ErrorAction SilentlyContinue)) { winget install --silent OpenJS.NodeJS }"
    @powershell -Command "if (!(Get-Command markdownlint-cli2 -ErrorAction SilentlyContinue)) { npm install -g markdownlint-cli2 }"
    @powershell -Command "if (!(Get-Command xan -ErrorAction SilentlyContinue)) { pixi global install xan }"

[linux]
pre-install:
    brew install just uv gh markdownlint-cli2 ripgrep eza duckdb xan jq

[macos]
pre-install:
    brew install just uv gh markdownlint-cli2 ripgrep eza duckdb xan jq
    brew install --cask quarto
