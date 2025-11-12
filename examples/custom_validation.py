# %% [markdown]
# # Custom Validation Configuration Example
#
# This example demonstrates how to create custom validation levels
# and use the validation system programmatically.

# %%
from pathlib import Path

from enlace.core.config import ExtractionConfig, ValidationConfig
from enlace.core.extractor import PaperExtractor
from enlace.core.validator import ExtractionValidator
from enlace.models.extraction import ExtractionResult

# %% [markdown]
# ## Extract Paper First

# %%
# Extract paper first
print("Extracting paper...")
extraction_config = ExtractionConfig(
    enable_ocr=True, enable_augmentation=False, output_dir=Path("output")
)
extractor = PaperExtractor(extraction_config)
result = extractor.extract(Path("paper.pdf"))
result.save(Path("output"))

# %% [markdown]
# ## Configure Custom Validation Levels

# %%
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

# %% [markdown]
# ## Run Validation with Custom Level

# %%
# Create validator
validator = ExtractionValidator(validation_config)

# Validate with custom level
print("\nValidating with custom checks...")
validation_result = validator.validate(result, level="custom")

# %% [markdown]
# ## Display Validation Results

# %%
# Display results
print("\n=== Validation Results ===")
print(f"Paper ID: {validation_result.paper_id}")
print(f"Status: {'PASSED' if validation_result.passed else 'FAILED'}")
print(f"Score: {validation_result.score:.2f}")
print(f"Issues: {len(validation_result.issues)}")
print(f"Warnings: {len(validation_result.warnings)}")

# %%
# Display checks performed
print("\n=== Checks Performed ===")
for check_name, check_result in validation_result.checks.items():
    status = "✓" if check_result.passed else "✗"
    print(f"{status} {check_name}: {check_result.score:.2f}")

# %%
# Display issues
if validation_result.issues:
    print("\n=== Issues ===")
    for issue in validation_result.issues:
        print(f"[{issue.severity}] {issue.check_name}: {issue.message}")
        if issue.location:
            print(f"  Location: {issue.location}")

# %%
# Display warnings
if validation_result.warnings:
    print("\n=== Warnings ===")
    for warning in validation_result.warnings:
        print(f"  {warning.check_name}: {warning.message}")

# %%
# Display recommendations
if validation_result.recommendations:
    print("\n=== Recommendations ===")
    for rec in validation_result.recommendations:
        print(f"  - {rec}")

# %%
# Save validation report
validation_result.save(validation_config.output_dir)
print(f"\n✓ Validation report saved to {validation_config.output_dir}")

# %% [markdown]
# ## Batch Validation
#
# Validate multiple extractions with custom configuration.

# %%
# Custom validation config
config = ValidationConfig(
    level="comprehensive",
    output_dir=Path("batch_output"),  # Saves to batch_output/{paper_id}/validation.json
    fail_on_issues=False,
)

validator = ExtractionValidator(config)

# Validate all extractions in directory
print("Validating batch extractions...")
batch_result = validator.validate_batch(Path("output"))

# %%
# Display batch summary
print("\n=== Batch Validation Summary ===")
print(f"Total papers: {batch_result.total_papers}")
print(f"Passed: {batch_result.passed_papers}")
print(f"Failed: {batch_result.failed_papers}")
print(f"Average score: {batch_result.avg_score:.2f}")

# %%
# Display failed papers
if hasattr(batch_result, "failed_validations") and batch_result.failed_validations:
    print("\n=== Failed Papers ===")
    for paper_id, validation in batch_result.failed_validations.items():
        print(f"{paper_id}: {validation.score:.2f}")
        for issue in validation.issues[:3]:  # Show first 3 issues
            print(f"  - {issue.message}")

# %% [markdown]
# ## Compare Validation Levels
#
# Compare validation results across different levels.

# %%
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

# %% [markdown]
# ## Validation from Path
#
# Validate directly from extraction file path.

# %%
# Validate from path (alternative to loading ExtractionResult)
config = ValidationConfig(level="standard")
validator = ExtractionValidator(config)

# Validate from path
validation_result = validator.validate(Path("output/paper/extraction.json"))

print(f"Validation score: {validation_result.score:.2f}")
print(f"Status: {'PASSED' if validation_result.passed else 'FAILED'}")
