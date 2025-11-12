# %% [markdown]
# # Basic Paper Extraction Example
#
# This example demonstrates the simplest usage of enlace for extracting
# tables, figures, and metadata from a research paper.
#
# ## Quick Start (Camelot-only mode - default, faster)

# %%
from pathlib import Path

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor

# %% [markdown]
# ## Configure Extraction (Camelot-only)
#
# By default, enlace uses Camelot-only extraction for simplicity and speed.

# %%
# Input paper path
paper_path = Path("paper.pdf")

# Configure extraction (Camelot-only by default)
config = ExtractionConfig(
    enable_camelot=True,  # Default: True
    enable_docling_tables=False,  # Default: False (Camelot-only mode)
    enable_ocr=True,
    enable_augmentation=False,
    output_format="csv",
)

# %% [markdown]
# ## Extract from Paper

# %%
# Create extractor
extractor = PaperExtractor(config)

# Extract from paper
print(f"Extracting from {paper_path.name}...")
result = extractor.extract(paper_path)

# %% [markdown]
# ## Display Results

# %%
# Display summary
print("\n=== Extraction Summary ===")
print(f"Paper ID: {result.paper_id}")
print(f"Tables extracted: {result.tables_extracted}")
print(f"Figures extracted: {result.figures_extracted}")
print(f"Extraction quality: {result.extraction_quality:.2f}")

# %%
# Display metadata
if result.metadata:
    print("\n=== Metadata ===")
    print(f"Title: {result.metadata.title}")
    print(f"Authors: {', '.join(result.metadata.authors)}")
    print(f"Year: {result.metadata.year}")
    print(f"DOI: {result.metadata.doi}")

# %%
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

# %%
# Display figures
if result.figures:
    print("\n=== Figures ===")
    for i, figure in enumerate(result.figures, 1):
        print(f"{i}. {figure.title}")
        print(f"   - Type: {figure.figure_type}")
        print(f"   - Path: {figure.image_path}")

# %%
# Display warnings
if result.warnings:
    print("\n=== Warnings ===")
    for warning in result.warnings:
        print(f"  - {warning}")

# %% [markdown]
# ## Save Results

# %%
# Save results
print(f"\nSaving results to {config.output_dir}...")
result.save(config.output_dir, format=config.output_format)

print("\n✓ Extraction complete!")
print(f"  Output: {config.output_dir / result.paper_id}")

# %% [markdown]
# ## Alternative: Dual Extraction Mode (Docling + Camelot)
#
# For comparison purposes, you can enable both extraction methods and reconcile results.

# %%
# Dual extraction: runs both docling and Camelot, then reconciles
config_dual = ExtractionConfig(
    enable_camelot=True,
    enable_docling_tables=True,  # Enable docling extraction
    reconciliation_strategy="camelot_primary",  # Default: prefer Camelot data
    output_format="both",
)

extractor_dual = PaperExtractor(config_dual)
result_dual = extractor_dual.extract(paper_path)

# Dual extraction tables contain all three versions
if (
    hasattr(result_dual, "dual_extraction_tables")
    and result_dual.dual_extraction_tables
):
    print("\n=== Dual Extraction Results ===")
    for dual_table in result_dual.dual_extraction_tables:
        print(f"Docling table: {dual_table.docling_table.title}")
        print(f"Camelot quality: {dual_table.camelot_quality}")
        print(f"Reconciled table: {dual_table.reconciled_table.title}")

    # Output: tables/docling/, tables/camelot/, tables/reconciled/
    result_dual.save(Path("output"), format="both")
    print("\n✓ Dual extraction saved with all three versions")
