"""Validation checks for enlace package.

This package provides modular validation checks for extracted research data.
Each module exports a validation function that takes an ExtractionResult and
returns a CheckResult.
"""

from enlace.validators import (
    accuracy,
    completeness,
    missing_data,
    semantic,
    statistical,
    structure,
)

__all__ = [
    "accuracy",
    "completeness",
    "missing_data",
    "semantic",
    "statistical",
    "structure",
]
