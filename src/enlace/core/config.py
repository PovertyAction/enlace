"""Configuration management for enlace package.

This module provides configuration classes for extraction and validation
with priority loading from defaults, config files, environment variables,
and command-line arguments.
"""

import tomllib
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from enlace.exceptions import ConfigError


class ExtractionConfig(BaseSettings):
    """Configuration for paper extraction.

    Configuration is loaded with the following priority (later overrides earlier):
    1. Default values (defined in field defaults)
    2. Configuration file (.enlace.toml or pyproject.toml)
    3. Environment variables (prefixed with ENLACE_)
    4. Command-line arguments (passed to load_config)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="ENLACE_",
        case_sensitive=False,
        extra="ignore",
    )

    # Document processing
    enable_ocr: bool = Field(
        default=False, description="Enable OCR for scanned documents"
    )
    ocr_backend: str = Field(
        default="auto",
        description="OCR backend: auto (Tesseract+EasyOCR fallback), tesseract, or easyocr",
    )
    hybrid_ocr_enabled: bool = Field(
        default=True,
        description="Enable hybrid OCR (fallback to secondary engine for low-confidence cells)",
    )
    ocr_confidence_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for triggering fallback OCR (0.0-1.0)",
    )
    ocr_languages: list[str] = Field(
        default=["eng"], description="OCR language codes (e.g., ['eng', 'fra', 'spa'])"
    )
    ocr_use_gpu: bool = Field(
        default=False, description="Use GPU acceleration for EasyOCR (requires CUDA)"
    )
    extract_figures: bool = Field(
        default=True, description="Extract figures from papers"
    )
    extract_tables: bool = Field(default=True, description="Extract tables from papers")
    extract_metadata: bool = Field(
        default=True, description="Extract metadata from papers"
    )

    # Semantic augmentation
    enable_augmentation: bool = Field(
        default=False, description="Enable semantic augmentation with RAG"
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model for RAG",
    )
    llm_model: str = Field(
        default="claude-4-5-haiku",
        description="LLM model for semantic extraction",
    )

    # Output
    output_format: str = Field(
        default="json", description="Output format: json, csv, or both"
    )
    output_dir: Path = Field(
        default=Path("output"), description="Output directory for results"
    )

    # Performance
    batch_size: int = Field(default=10, description="Batch size for processing")
    max_workers: int = Field(default=4, description="Maximum parallel workers")

    # Logging
    verbose: bool = Field(default=False, description="Enable verbose logging")
    log_file: Path | None = Field(default=None, description="Optional log file path")

    # Dry-run mode
    dry_run: bool = Field(
        default=False,
        description="Dry-run mode: analyze document without full extraction/OCR",
    )

    # Internal tracking for config source (set during load_config)
    _config_sources: dict[str, str] = {}

    @classmethod
    def load_config(
        cls, config_file: Path | None = None, **cli_args: Any
    ) -> "ExtractionConfig":
        """Load configuration with priority: defaults < file < env < CLI args.

        Args:
            config_file: Optional path to .toml configuration file
            **cli_args: Command-line arguments (highest priority)

        Returns:
            Loaded configuration instance

        Raises:
            ConfigError: If configuration file is invalid

        """
        # 1. Defaults are handled by pydantic Field defaults

        # 2. Load from config file
        file_config = {}
        if config_file and config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    data = tomllib.load(f)

                # Support both .enlace.toml and pyproject.toml
                if "tool" in data and "enlace" in data["tool"]:
                    file_config = data["tool"]["enlace"]
                else:
                    file_config = data
            except Exception as e:
                raise ConfigError(f"Invalid config file {config_file}: {e}") from e

        # 3. Environment variables are handled automatically by BaseSettings

        # 4. CLI args (highest priority) - filter out None values
        cli_config = {k: v for k, v in cli_args.items() if v is not None}

        # Merge and instantiate (later overrides earlier)
        instance = cls(**{**file_config, **cli_config})

        # Track configuration sources for debugging
        instance._config_sources = cls._determine_config_sources(
            file_config, cli_config
        )

        return instance

    @classmethod
    def _determine_config_sources(
        cls, file_config: dict[str, Any], cli_config: dict[str, Any]
    ) -> dict[str, str]:
        """Determine the source of each configuration value.

        Args:
            file_config: Configuration from file
            cli_config: Configuration from CLI arguments

        Returns:
            Dictionary mapping field names to their sources

        """
        sources = {}
        for field_name in cls.model_fields:
            if field_name in cli_config:
                sources[field_name] = "cli"
            elif field_name in file_config:
                sources[field_name] = "file"
            # Note: env vars are harder to track with pydantic-settings
            # We could check os.environ, but it's complex with the prefix
            else:
                sources[field_name] = "default"
        return sources

    def get_effective_config(self) -> dict[str, Any]:
        """Return resolved configuration showing which values came from where.

        Returns:
            Dictionary with field names, values, and sources

        Example:
            >>> config = ExtractionConfig.load_config()
            >>> effective = config.get_effective_config()
            >>> print(effective["enable_ocr"])
            {'value': False, 'source': 'default'}

        """
        return {
            field: {
                "value": getattr(self, field),
                "source": self._config_sources.get(field, "unknown"),
                "description": self.model_fields[field].description,
            }
            for field in self.model_fields
            if not field.startswith("_")
        }


class ValidationConfig(BaseSettings):
    """Configuration for validation."""

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="ENLACE_VALIDATION_", case_sensitive=False
    )

    level: str = Field(default="standard", description="Validation level name")
    output_dir: Path = Field(
        default=Path("validation_reports"), description="Output directory for reports"
    )
    fail_on_issues: bool = Field(
        default=False, description="Exit with error code if issues found"
    )

    # Configurable validation levels
    levels: dict[str, list[str]] = Field(
        default={
            "quick": ["structure", "completeness"],
            "standard": [
                "structure",
                "completeness",
                "accuracy",
                "missing_data",
                "ocr_quality",
            ],
            "comprehensive": [
                "structure",
                "completeness",
                "accuracy",
                "statistical_consistency",
                "missing_data",
                "semantic_validation",
                "ocr_quality",
            ],
        },
        description="Mapping of level names to validation check lists",
    )

    # Logging
    verbose: bool = Field(default=False, description="Enable verbose logging")

    @classmethod
    def load_config(
        cls, config_file: Path | None = None, **cli_args: Any
    ) -> "ValidationConfig":
        """Load validation configuration with priority."""
        file_config = {}
        if config_file and config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    data = tomllib.load(f)

                if (
                    "tool" in data
                    and "enlace" in data["tool"]
                    and "validation" in data["tool"]["enlace"]
                ):
                    file_config = data["tool"]["enlace"]["validation"]
            except Exception as e:
                raise ConfigError(f"Invalid config file {config_file}: {e}") from e

        cli_config = {k: v for k, v in cli_args.items() if v is not None}
        return cls(**{**file_config, **cli_config})

    def get_checks_for_level(
        self, level: str | None = None, custom_checks: list[str] | None = None
    ) -> list[str]:
        """Get validation checks for specified level or custom check list.

        Args:
            level: Level name (uses self.level if None)
            custom_checks: Optional custom check list (overrides level)

        Returns:
            List of check names to run

        Raises:
            ConfigError: If level not found and no custom_checks provided

        """
        # Custom checks override level
        if custom_checks is not None:
            return custom_checks

        level = level or self.level
        if level not in self.levels:
            raise ConfigError(
                f"Unknown validation level: {level}. "
                f"Available levels: {', '.join(self.levels.keys())}"
            )
        return self.levels[level]

    def add_custom_level(self, name: str, checks: list[str]) -> None:
        """Add or update a custom validation level.

        Args:
            name: Level name
            checks: List of check names

        Example:
            >>> config = ValidationConfig()
            >>> config.add_custom_level("minimal", ["structure"])
            >>> config.level = "minimal"

        """
        self.levels[name] = checks
