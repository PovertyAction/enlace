"""Custom validation configuration example.

This example demonstrates how to create custom validation levels
and use the validation system programmatically.
"""

from pathlib import Path

from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator


def main():
    """Validate extraction with custom validation level."""
    # Extract paper first
    print("Extracting paper...")
    extraction_config = ExtractionConfig(
        enable_ocr=True, enable_augmentation=False, output_dir=Path("output")
    )
    extractor = PaperExtractor(extraction_config)
    result = extractor.extract(Path("paper.pdf"))
    result.save(Path("output"))

    # Create custom validation configuration
    validation_config = ValidationConfig(
        level="custom",
        output_dir=Path("output"),  # Saves to output/{paper_id}/validation.json
        fail_on_issues=False,
        levels={
            # Quick screening checks
            "screening": ["structure", "completeness"],
            # Regression-focused validation
            "regression_only": ["structure", "accuracy", "statistical_consistency"],
            # OCR quality checks
            "ocr_focused": ["structure", "ocr_quality", "accuracy"],
            # Custom comprehensive validation
            "custom": [
                "structure",
                "completeness",
                "accuracy",
                "statistical_consistency",
                "missing_data",
            ],
        },
    )

    # Create validator
    validator = ExtractionValidator(validation_config)

    # Validate with custom level
    print("\nValidating with custom checks...")
    validation_result = validator.validate(result, level="custom")

    # Display results
    print("\n=== Validation Results ===")
    print(f"Paper ID: {validation_result.paper_id}")
    print(f"Status: {'PASSED' if validation_result.passed else 'FAILED'}")
    print(f"Score: {validation_result.score:.2f}")
    print(f"Issues: {len(validation_result.issues)}")
    print(f"Warnings: {len(validation_result.warnings)}")

    # Display checks performed
    print("\n=== Checks Performed ===")
    for check_name, check_result in validation_result.checks.items():
        status = "✓" if check_result.passed else "✗"
        print(f"{status} {check_name}: {check_result.score:.2f}")

    # Display issues
    if validation_result.issues:
        print("\n=== Issues ===")
        for issue in validation_result.issues:
            print(f"[{issue.severity}] {issue.check_name}: {issue.message}")
            if issue.location:
                print(f"  Location: {issue.location}")

    # Display warnings
    if validation_result.warnings:
        print("\n=== Warnings ===")
        for warning in validation_result.warnings:
            print(f"  {warning.check_name}: {warning.message}")

    # Display recommendations
    if validation_result.recommendations:
        print("\n=== Recommendations ===")
        for rec in validation_result.recommendations:
            print(f"  - {rec}")

    # Save validation report
    validation_result.save(validation_config.output_dir)
    print(f"\n✓ Validation report saved to {validation_config.output_dir}")


def validate_batch():
    """Validate multiple extractions with custom configuration."""
    # Custom validation config
    config = ValidationConfig(
        level="comprehensive",
        output_dir=Path(
            "batch_output"
        ),  # Saves to batch_output/{paper_id}/validation.json
        fail_on_issues=False,
    )

    validator = ExtractionValidator(config)

    # Validate all extractions in directory
    print("Validating batch extractions...")
    batch_result = validator.validate_batch(Path("output"))

    # Display batch summary
    print("\n=== Batch Validation Summary ===")
    print(f"Total papers: {batch_result.total_papers}")
    print(f"Passed: {batch_result.passed_papers}")
    print(f"Failed: {batch_result.failed_papers}")
    print(f"Average score: {batch_result.avg_score:.2f}")

    # Display failed papers
    if batch_result.failed_validations:
        print("\n=== Failed Papers ===")
        for paper_id, validation in batch_result.failed_validations.items():
            print(f"{paper_id}: {validation.score:.2f}")
            for issue in validation.issues[:3]:  # Show first 3 issues
                print(f"  - {issue.message}")


def validate_with_different_levels():
    """Compare validation results across different levels."""
    from enlace.models.extraction import ExtractionResult

    # Load extraction result
    extraction = ExtractionResult.parse_file("output/paper/extraction.json")

    # Define validation levels to test
    levels = ["quick", "standard", "comprehensive"]

    config = ValidationConfig()
    validator = ExtractionValidator(config)

    print("=== Comparing Validation Levels ===\n")

    for level in levels:
        print(f"{level.upper()} validation:")

        result = validator.validate(extraction, level=level)

        print(f"  Score: {result.score:.2f}")
        print(f"  Checks: {len(result.checks)}")
        print(f"  Issues: {len(result.issues)}")
        print(f"  Status: {'PASSED' if result.passed else 'FAILED'}")
        print()


def validate_specific_checks():
    """Run specific validation checks programmatically."""
    from enlace.models.extraction import ExtractionResult
    from enlace.validators import accuracy, completeness, structure

    # Load extraction
    extraction = ExtractionResult.parse_file("output/paper/extraction.json")

    print("=== Running Specific Checks ===\n")

    # Structure validation
    structure_result = structure.validate_structure(extraction)
    print(f"Structure: {'✓' if structure_result.passed else '✗'}")
    print(f"  Score: {structure_result.score:.2f}")

    # Completeness validation
    completeness_result = completeness.validate_completeness(extraction)
    print(f"Completeness: {'✓' if completeness_result.passed else '✗'}")
    print(f"  Score: {completeness_result.score:.2f}")

    # Accuracy validation
    accuracy_result = accuracy.validate_accuracy(extraction)
    print(f"Accuracy: {'✓' if accuracy_result.passed else '✗'}")
    print(f"  Score: {accuracy_result.score:.2f}")

    # Show issues from any check
    for check_name, result in [
        ("structure", structure_result),
        ("completeness", completeness_result),
        ("accuracy", accuracy_result),
    ]:
        if result.issues:
            print(f"\n{check_name.upper()} Issues:")
            for issue in result.issues:
                print(f"  - {issue}")


def validate_with_fail_on_issues():
    """Validate and exit with error if issues found."""
    import sys

    from enlace.models.extraction import ExtractionResult

    config = ValidationConfig(level="comprehensive", fail_on_issues=True)

    validator = ExtractionValidator(config)

    extraction = ExtractionResult.parse_file("output/paper/extraction.json")

    result = validator.validate(extraction)

    if not result.passed:
        print(f"✗ Validation failed (score: {result.score:.2f})")
        print(f"Issues: {len(result.issues)}")

        for issue in result.issues:
            print(f"  - {issue.message}")

        sys.exit(1)
    else:
        print(f"✓ Validation passed (score: {result.score:.2f})")


if __name__ == "__main__":
    # Run main validation example
    main()

    # Uncomment to try other examples:
    # validate_batch()
    # validate_with_different_levels()
    # validate_specific_checks()
    # validate_with_fail_on_issues()
