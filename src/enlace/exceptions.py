"""Custom exceptions for enlace package."""

from pathlib import Path


class EnlaceError(Exception):
    """Base exception for all enlace errors."""

    pass


class ConfigError(EnlaceError):
    """Configuration-related errors."""

    pass


class PaperNotFoundError(EnlaceError):
    """Paper file not found."""

    def __init__(self, path: Path):
        """Initialize PaperNotFoundError.

        Args:
            path: Path to the missing paper file

        """
        super().__init__(f"Paper file not found: {path}")
        self.path = path


class UnsupportedFormatError(EnlaceError):
    """Unsupported file format."""

    def __init__(self, path: Path, supported_formats: list[str]):
        """Initialize UnsupportedFormatError.

        Args:
            path: Path to the file with unsupported format
            supported_formats: List of supported file formats

        """
        super().__init__(
            f"Unsupported format for {path}. "
            f"Supported formats: {', '.join(supported_formats)}"
        )
        self.path = path
        self.supported_formats = supported_formats


class ExtractionError(EnlaceError):
    """Extraction operation failed."""

    pass


class AugmentationError(EnlaceError):
    """Semantic augmentation failed."""

    pass


class ModelNotFoundError(EnlaceError):
    """Required model not found or not available."""

    def __init__(self, model_name: str, model_type: str):
        """Initialize ModelNotFoundError.

        Args:
            model_name: Name of the missing model
            model_type: Type of the model (e.g., 'embedding', 'LLM')

        """
        super().__init__(f"{model_type} model not found: {model_name}")
        self.model_name = model_name
        self.model_type = model_type


class ValidationError(EnlaceError):
    """Validation operation failed."""

    pass


class SummaryError(EnlaceError):
    """Summary generation failed."""

    pass


class LLMError(SummaryError):
    """LLM API call failed."""

    pass


class WebSearchError(SummaryError):
    """Web search enhancement failed."""

    pass
