"""Semantic augmentation example.

This example demonstrates using semantic augmentation to enhance
table extraction with context from the paper text.

Requirements:
- ANTHROPIC_API_KEY environment variable set
- sentence-transformers installed
"""

import os
from pathlib import Path

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor


def main():
    """Extract paper with semantic augmentation."""
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your_api_key")
        return

    # Configure extraction with augmentation
    config = ExtractionConfig(
        enable_ocr=True,  # Enable OCR for better text extraction
        enable_augmentation=True,  # Enable semantic augmentation
        llm_model="claude-4-5-haiku",  # LLM for context extraction
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",  # Embedding model
        output_format="both",  # Save as JSON and CSV
        output_dir=Path("augmented_output"),
    )

    # Create extractor
    extractor = PaperExtractor(config)

    # Extract and augment
    paper_path = Path("paper.pdf")
    print(f"Extracting from {paper_path.name}...")
    result = extractor.extract(paper_path)

    print("\nAugmenting with semantic context...")
    augmented = extractor.augment(result)

    # Display augmented results
    print("\n=== Augmented Extraction Results ===")
    print(f"Paper ID: {augmented.paper_id}")
    print(f"Tables: {augmented.tables_extracted}")
    print(f"Quality: {augmented.extraction_quality:.2f}")

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
                        print(
                            f"      Units: {coef.variable_context.get('units', 'N/A')}"
                        )
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

    # Save augmented results
    augmented.save(config.output_dir, format=config.output_format)
    print(f"\n✓ Augmented results saved to {config.output_dir}")


def compare_with_without_augmentation():
    """Compare extraction results with and without augmentation."""
    paper_path = Path("paper.pdf")

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
        has_study_context = (
            hasattr(table_aug, "study_context") and table_aug.study_context
        )
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


def export_augmented_data():
    """Export augmented data for analysis."""
    import json

    import pandas as pd

    # Load augmented extraction
    with open("augmented_output/paper/extraction.json") as f:
        data = json.load(f)

    # Extract regression coefficients with context
    regression_data = []

    for table in data["tables"]:
        if table["table_type"] == "regression":
            for model in table["models"]:
                for coef in model["coefficients"]:
                    row = {
                        "table": table["title"],
                        "model": model["model_number"],
                        "variable": coef["variable_name"],
                        "coefficient": coef["coefficient"],
                        "se": coef["standard_error"],
                        "pvalue": coef["p_value"],
                    }

                    # Add context fields if available
                    if coef.get("variable_context"):
                        row["definition"] = coef["variable_context"].get("definition")
                        row["units"] = coef["variable_context"].get("units")
                        row["data_source"] = coef["variable_context"].get("data_source")

                    # Add validation results
                    if coef.get("validation"):
                        row["validation_status"] = coef["validation"].get("status")
                        row["discrepancy"] = coef["validation"].get("discrepancy")

                    regression_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(regression_data)

    # Save to CSV
    output_path = Path("augmented_coefficients.csv")
    df.to_csv(output_path, index=False)
    print(f"Exported {len(df)} coefficients to {output_path}")

    # Show summary
    print("\n=== Export Summary ===")
    print(f"Total coefficients: {len(df)}")
    print(f"With context: {df['definition'].notna().sum()}")
    print(f"With validation: {df['validation_status'].notna().sum()}")


def use_custom_embedding_model():
    """Use alternative embedding model for faster processing."""
    # Alternative embedding models:
    # - "minishlab/potion-base-8M" - Faster, smaller model
    # - "sentence-transformers/all-mpnet-base-v2" - Higher quality
    # - "sentence-transformers/multi-qa-MiniLM-L6-cos-v1" - Question-answering focused

    config = ExtractionConfig(
        enable_augmentation=True,
        embedding_model="minishlab/potion-base-8M",  # Smaller, faster model
        llm_model="claude-4-5-haiku",
        output_dir=Path("output_fast"),
    )

    extractor = PaperExtractor(config)

    paper_path = Path("paper.pdf")
    result = extractor.extract(paper_path)
    augmented = extractor.augment(result)

    print(f"Processing time: {augmented.processing_time_seconds:.1f}s")
    print(f"Quality: {augmented.extraction_quality:.2f}")


def detect_ocr_errors_with_validation():
    """Use semantic validation to detect OCR errors."""
    config = ExtractionConfig(
        enable_ocr=True,
        enable_augmentation=True,
        output_dir=Path("output_validated"),
    )

    extractor = PaperExtractor(config)

    # Extract and augment
    result = extractor.extract(Path("scanned_paper.pdf"))
    augmented = extractor.augment(result)

    # Check for OCR errors detected by validation
    print("=== OCR Error Detection ===")

    for table in augmented.tables:
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


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY=your_api_key")
        print("\nOr add to .env file:")
        print("  echo 'ANTHROPIC_API_KEY=your_api_key' >> .env")
    else:
        # Run main example
        main()

        # Uncomment to try other examples:
        # compare_with_without_augmentation()
        # export_augmented_data()
        # use_custom_embedding_model()
        # detect_ocr_errors_with_validation()
