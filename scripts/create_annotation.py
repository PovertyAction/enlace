"""Interactive script to create ground truth annotations for benchmark testing.

This script helps create accurate ground truth annotations by:
1. Running extraction with best settings to generate a template
2. Providing an interactive editor for manual correction
3. Validating the annotation against the schema
4. Saving to the correct location

Usage:
    python scripts/create_annotation.py papers/BHKM_Liberia.pdf
    python scripts/create_annotation.py papers/BHKM_Liberia.pdf --annotator "Your Name"
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enlace.core.config import ExtractionConfig
from enlace.core.extractor import PaperExtractor
from enlace.exceptions import EnlaceError

# Add tests to path for annotation validator
sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))

from fixtures.annotation_validator import Annotation


def extract_to_template(paper_path: Path, output_dir: Path) -> dict:
    """Extract paper content to create annotation template.

    Args:
        paper_path: Path to PDF file
        output_dir: Directory for extraction output

    Returns:
        Dictionary with extraction results as annotation template

    """
    print(f"\n🔍 Extracting {paper_path.name} to create template...")

    # Use best settings for template generation (OCR disabled for speed/compatibility)
    config = ExtractionConfig(
        enable_ocr=False,  # Disable OCR for template generation
        enable_augmentation=False,  # Skip for faster template generation
        output_dir=output_dir,
        verbose=True,
    )

    extractor = PaperExtractor(config)
    result = extractor.extract(paper_path)

    print(
        f"✓ Extracted {result.tables_extracted} tables, {result.figures_extracted} figures"
    )
    print(f"  Quality score: {result.extraction_quality:.2f}")

    # Convert to annotation template
    # Try to make path relative to cwd, if not just use as-is
    try:
        source_file_path = str(paper_path.relative_to(Path.cwd()))
    except ValueError:
        source_file_path = str(paper_path)

    template = {
        "paper_id": result.paper_id,
        "source_file": source_file_path,
        "annotation_date": datetime.now().isoformat(),
        "annotator": None,  # Will be filled in by user
        "ground_truth": {
            "metadata": {
                "title": result.metadata.title or "TODO: Add title",
                "authors": result.metadata.authors or ["TODO: Add authors"],
                "year": result.metadata.year or 2024,
                "doi": result.metadata.doi,
                "journal": result.metadata.journal,
                "abstract": result.metadata.abstract,
            },
            "tables": [],
            "figures": [],
            "semantic_context": {
                "variable_definitions": {},
                "treatment_description": None,
                "study_design": None,
                "population_description": None,
            },
        },
    }

    # Convert extracted tables to annotation format
    for table in result.tables:
        table_dict = {
            "table_id": f"table_{table.table_number}".replace(" ", "_").lower(),
            "table_number": table.table_number,
            "title": table.title,
            "page_number": None,  # TODO: Extract from result
            "table_type": table.__class__.__name__.replace("Table", "").lower(),
            "notes": table.notes,
        }

        # Add type-specific content
        if hasattr(table, "models"):  # Regression table
            table_dict["models"] = [
                {
                    "model_number": i + 1,
                    "dependent_variable": model.dependent_variable,
                    "coefficients": [
                        {
                            "variable_name": coef.variable_name,
                            "coefficient": coef.coefficient,
                            "std_error": coef.std_error,
                            "t_statistic": coef.t_statistic,
                            "p_value": coef.p_value,
                            "significance": coef.significance,
                            "ci_lower": coef.ci_lower,
                            "ci_upper": coef.ci_upper,
                        }
                        for coef in model.coefficients
                    ],
                    "n_observations": model.n_observations,
                    "r_squared": model.r_squared,
                    "adjusted_r_squared": model.adjusted_r_squared,
                    "f_statistic": getattr(model, "f_statistic", None),
                    "se_type": getattr(model, "se_type", None),
                    "fixed_effects": getattr(model, "fixed_effects", []) or [],
                    "clustering": getattr(model, "clustering", None),
                }
                for i, model in enumerate(table.models)
            ]
        elif hasattr(table, "statistics"):  # Summary statistics table
            table_dict["statistics"] = [
                {
                    "variable_name": stat.variable_name,
                    "n_obs": stat.n_obs,
                    "mean": stat.mean,
                    "median": stat.median,
                    "std_dev": stat.std_dev,
                    "min_value": stat.min_value,
                    "max_value": stat.max_value,
                    "p10": stat.p10,
                    "p25": stat.p25,
                    "p50": stat.p50,
                    "p75": stat.p75,
                    "p90": stat.p90,
                }
                for stat in table.statistics
            ]
        elif hasattr(table, "comparisons"):  # Balance table
            table_dict["comparisons"] = [
                {
                    "variable_name": comp.variable_name,
                    "control_mean": comp.control_mean,
                    "control_sd": comp.control_sd,
                    "control_n": comp.control_n,
                    "treatment_mean": comp.treatment_mean,
                    "treatment_sd": comp.treatment_sd,
                    "treatment_n": comp.treatment_n,
                    "difference": comp.difference,
                    "p_value": comp.p_value,
                    "normalized_difference": comp.normalized_difference,
                }
                for comp in table.comparisons
            ]

        template["ground_truth"]["tables"].append(table_dict)

    # Convert extracted figures
    for figure in result.figures:
        template["ground_truth"]["figures"].append(
            {
                "figure_id": figure.figure_id,
                "figure_number": figure.figure_number,
                "caption": figure.caption,
                "page_number": figure.page_number,
                "figure_type": figure.figure_type,
            }
        )

    return template


def save_template(template: dict, output_path: Path) -> None:
    """Save annotation template to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    print(f"\n✓ Template saved to: {output_path}")


def validate_annotation(annotation_path: Path) -> bool:
    """Validate annotation file against schema.

    Args:
        annotation_path: Path to annotation JSON

    Returns:
        True if valid, False otherwise

    """
    try:
        annotation = Annotation.load(annotation_path)
        print("\n✅ Annotation is valid!")
        print(f"   Paper: {annotation.ground_truth.metadata.title}")
        print(f"   Tables: {len(annotation.ground_truth.tables)}")
        print(f"   Figures: {len(annotation.ground_truth.figures)}")
        return True
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False


def main():
    """Run annotation creation script."""
    parser = argparse.ArgumentParser(
        description="Create ground truth annotation for benchmark testing"
    )
    parser.add_argument("paper_path", type=Path, help="Path to PDF file to annotate")
    parser.add_argument(
        "--annotator", type=str, help="Name of person creating annotation"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tests/fixtures/benchmark_data"),
        help="Output directory for annotations",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing annotation, don't create new one",
    )

    args = parser.parse_args()

    if not args.paper_path.exists():
        print(f"❌ Error: Paper not found: {args.paper_path}")
        sys.exit(1)

    paper_id = args.paper_path.stem
    annotation_file = args.output_dir / f"{paper_id}_ground_truth.json"

    # Validate mode
    if args.validate_only:
        if not annotation_file.exists():
            print(f"❌ Error: Annotation not found: {annotation_file}")
            sys.exit(1)
        success = validate_annotation(annotation_file)
        sys.exit(0 if success else 1)

    print("=" * 70)
    print("Ground Truth Annotation Creator")
    print("=" * 70)
    print(f"\nPaper: {args.paper_path.name}")
    print(f"Output: {annotation_file}")

    # Check if annotation already exists
    if annotation_file.exists():
        print("\n⚠️  Warning: Annotation already exists")
        response = input("Overwrite? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(0)

    try:
        # Extract to create template
        template = extract_to_template(args.paper_path, Path("temp_extraction"))

        # Add annotator if provided
        if args.annotator:
            template["annotator"] = args.annotator

        # Save template
        save_template(template, annotation_file)

        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        print(f"\n1. Open the PDF: {args.paper_path}")
        print(f"2. Open the annotation: {annotation_file}")
        print("3. Manually review and correct each value:")
        print("   - Check all coefficients, SEs, p-values against PDF")
        print("   - Verify variable names (case, spelling)")
        print("   - Confirm N, R², F-statistics")
        print("   - Update metadata (title, authors, year, DOI)")
        print("   - Add page numbers for tables/figures")
        print("\n4. Validate when done:")
        print(
            f"   python scripts/create_annotation.py {args.paper_path} --validate-only"
        )

        print(
            "\n💡 Tip: Use PDF viewer side-by-side with JSON editor for fastest annotation"
        )

    except EnlaceError as e:
        print(f"\n❌ Extraction error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
