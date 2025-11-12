# %% [markdown]
# # Semantic Augmentation Example
#
# This example demonstrates using semantic augmentation to enhance
# table extraction with context from the paper text using RAG (Retrieval-Augmented Generation).
#
# **Requirements:**
# - ANTHROPIC_API_KEY environment variable set
# - sentence-transformers installed

# %%
import os
from pathlib import Path

import pandas as pd

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor

# %% [markdown]
# ## Check API Key

# %%
# Check for API key
if not os.getenv("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY environment variable not set")
    print("Set it with: export ANTHROPIC_API_KEY=your_api_key")
else:
    print("✓ API key found")

# %% [markdown]
# ## Configure Extraction with Augmentation

# %%
# Configure extraction with augmentation
config = ExtractionConfig(
    enable_ocr=True,  # Enable OCR for better text extraction
    enable_augmentation=True,  # Enable semantic augmentation
    llm_model="claude-4-5-haiku",  # LLM for context extraction
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Embedding model
    output_format="both",  # Save as JSON and CSV
    output_dir=Path("augmented_output"),
)

# %% [markdown]
# ## Extract and Augment

# %%
# Create extractor
extractor = PaperExtractor(config)

# Extract and augment
paper_path = Path("paper.pdf")
print(f"Extracting from {paper_path.name}...")
result = extractor.extract(paper_path)

print("\nAugmenting with semantic context...")
augmented = extractor.augment(result)

# %% [markdown]
# ## Display Augmented Results

# %%
# Display augmented results
print("\n=== Augmented Extraction Results ===")
print(f"Paper ID: {augmented.paper_id}")
print(f"Tables: {augmented.tables_extracted}")
print(f"Quality: {augmented.extraction_quality:.2f}")

# %% [markdown]
# ## Show Augmented Table Information

# %%
# Show augmented table information
for i, table in enumerate(augmented.tables, 1):
    print(f"\n--- Table {i}: {table.title} ---")

    # Study context (if available)
    if hasattr(table, "study_context") and table.study_context:
        print("\nStudy Context:")
        print(f"  Description: {table.study_context.get('description', 'N/A')}")
        print(
            f"  Sample: {table.study_context.get('sample_description', 'N/A')[:100]}..."
        )

    # Regression table details
    if table.table_type == "regression":
        print(f"\nDependent variable: {table.dependent_variable}")

        # Show augmented coefficient information
        for model in table.models[:1]:  # Show first model
            print(f"\nModel {model.model_number} coefficients:")

            for coef in model.coefficients[:5]:  # Show first 5 coefficients
                print(f"\n  {coef.variable_name}:")
                print(f"    Coefficient: {coef.coefficient}")
                print(f"    SE: {coef.standard_error}")

                # Variable context from augmentation
                if coef.variable_context:
                    print("    Context:")
                    print(
                        f"      Definition: {coef.variable_context.get('definition', 'N/A')}"
                    )
                    print(f"      Units: {coef.variable_context.get('units', 'N/A')}")
                    print(
                        f"      Source: {coef.variable_context.get('data_source', 'N/A')}"
                    )

                # Validation results
                if coef.validation:
                    status = coef.validation.get("status", "unknown")
                    print(f"    Validation: {status}")
                    if coef.validation.get("discrepancy"):
                        discrepancy = coef.validation["discrepancy"]
                        print(f"    Discrepancy: {discrepancy:.1%}")

# %% [markdown]
# ## Save Augmented Results

# %%
# Save augmented results
augmented.save(config.output_dir, format=config.output_format)
print(f"\n✓ Augmented results saved to {config.output_dir}")

# %% [markdown]
# ## Export Augmented Data to Pandas
#
# Convert augmented extraction results to pandas DataFrames for analysis.

# %%

# Extract regression coefficients with context
regression_data = []

for table in augmented.tables:
    if table.table_type == "regression":
        for model in table.models:
            for coef in model.coefficients:
                row = {
                    "table": table.title,
                    "model": model.model_number,
                    "variable": coef.variable_name,
                    "coefficient": coef.coefficient,
                    "se": coef.standard_error,
                    "pvalue": coef.p_value,
                    "sig": coef.significance_stars,
                }

                # Add context fields if available
                if coef.variable_context:
                    row["definition"] = coef.variable_context.get("definition")
                    row["units"] = coef.variable_context.get("units")
                    row["data_source"] = coef.variable_context.get("data_source")

                # Add validation results
                if coef.validation:
                    row["validation_status"] = coef.validation.get("status")
                    row["discrepancy"] = coef.validation.get("discrepancy")

                regression_data.append(row)

# Create DataFrame
df = pd.DataFrame(regression_data)
df.to_csv("augmented_coefficients.csv", index=False)
print(f"\nExported {len(df)} coefficients to augmented_coefficients.csv")

# %%
# Show summary
print("\n=== Export Summary ===")
print(f"Total coefficients: {len(df)}")
if "definition" in df.columns:
    print(f"With context: {df['definition'].notna().sum()}")
if "validation_status" in df.columns:
    print(f"With validation: {df['validation_status'].notna().sum()}")

# Display first few rows
print("\n=== Sample Data ===")
print(df.head())

# %% [markdown]
# ## Alternative Embedding Models
#
# Use alternative embedding models for faster processing or higher quality.

# %%
# Alternative embedding models:
# - "minishlab/potion-base-8M" - Faster, smaller model
# - "sentence-transformers/all-mpnet-base-v2" - Higher quality
# - "sentence-transformers/multi-qa-MiniLM-L6-cos-v1" - Question-answering focused

config_fast = ExtractionConfig(
    enable_augmentation=True,
    embedding_model="minishlab/potion-base-8M",  # Smaller, faster model
    llm_model="claude-4-5-haiku",
    output_dir=Path("output_fast"),
)

extractor_fast = PaperExtractor(config_fast)

paper_path = Path("paper.pdf")
result_fast = extractor_fast.extract(paper_path)
augmented_fast = extractor_fast.augment(result_fast)

print(f"Processing time: {augmented_fast.processing_time_seconds:.1f}s")
print(f"Quality: {augmented_fast.extraction_quality:.2f}")

# %% [markdown]
# ## OCR Error Detection with Validation
#
# Use semantic validation to detect OCR errors by cross-checking parsed values against paper text.

# %%
config_validated = ExtractionConfig(
    enable_ocr=True,
    enable_augmentation=True,
    output_dir=Path("output_validated"),
)

extractor_validated = PaperExtractor(config_validated)

# Extract and augment
result_validated = extractor_validated.extract(Path("scanned_paper.pdf"))
augmented_validated = extractor_validated.augment(result_validated)

# Check for OCR errors detected by validation
print("=== OCR Error Detection ===")

for table in augmented_validated.tables:
    if table.table_type == "regression":
        print(f"\nTable: {table.title}")

        for model in table.models:
            errors_found = 0
            for coef in model.coefficients:
                if coef.validation:
                    discrepancy = coef.validation.get("discrepancy", 0)

                    # Flag potential OCR errors (large discrepancy)
                    if discrepancy > 0.15:  # >15% difference
                        errors_found += 1
                        print(f"  ⚠ {coef.variable_name}:")
                        print(f"    Parsed: {coef.coefficient}")
                        print(f"    Discrepancy: {discrepancy:.1%}")

                        if coef.validation.get("text_value"):
                            print(f"    Text says: {coef.validation['text_value']}")

            if errors_found:
                print(
                    "\n  → Recommend re-extracting with EasyOCR backend for better accuracy"
                )

# %% [markdown]
# ## Benefits of Semantic Augmentation
#
# Compare extraction results with and without augmentation.

# %%
# Extract without augmentation
print("=== Extracting WITHOUT augmentation ===")
config_basic = ExtractionConfig(enable_augmentation=False)
extractor_basic = PaperExtractor(config_basic)
result_basic = extractor_basic.extract(paper_path)

# Extract with augmentation
print("\n=== Extracting WITH augmentation ===")
config_augmented = ExtractionConfig(enable_augmentation=True)
extractor_augmented = PaperExtractor(config_augmented)
result_augmented = extractor_augmented.extract(paper_path)
result_augmented = extractor_augmented.augment(result_augmented)

# Compare results
print("\n=== Comparison ===")
print(f"Tables extracted: {result_basic.tables_extracted} (both)")
print(
    f"Quality score: {result_basic.extraction_quality:.2f} → {result_augmented.extraction_quality:.2f}"
)

# Show what augmentation adds
print("\n=== Augmentation Benefits ===")
for table_basic, table_aug in zip(result_basic.tables, result_augmented.tables):
    print(f"\nTable: {table_basic.title}")

    # Check for study context
    has_study_context = hasattr(table_aug, "study_context") and table_aug.study_context
    print(f"  Study context: {'✓' if has_study_context else '✗'}")

    # Check for variable context (regression tables)
    if table_basic.table_type == "regression":
        coefs_with_context = 0
        coefs_with_validation = 0

        for model in table_aug.models:
            for coef in model.coefficients:
                if coef.variable_context:
                    coefs_with_context += 1
                if coef.validation:
                    coefs_with_validation += 1

        print(f"  Variables with context: {coefs_with_context}")
        print(f"  Variables with validation: {coefs_with_validation}")
