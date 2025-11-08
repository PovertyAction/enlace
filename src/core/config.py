"""Configuration management for enlace package.

This module provides configuration classes for extraction and validation
with priority loading from defaults, config files, environment variables,
and command-line arguments.
"""

import tomllib
from pathlib import Path
from typing import Any

from enlace.exceptions import ConfigError
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        default="claude-3-5-sonnet",
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
        return cls(**{**file_config, **cli_config})


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
            "standard": ["structure", "completeness", "accuracy", "missing_data"],
            "comprehensive": [
                "structure",
                "completeness",
                "accuracy",
                "statistical_consistency",
                "missing_data",
                "semantic_validation",
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

    def get_checks_for_level(self, level: str | None = None) -> list[str]:
        """Get validation checks for specified level."""
        level = level or self.level
        if level not in self.levels:
            raise ConfigError(
                f"Unknown validation level: {level}. "
                f"Available levels: {', '.join(self.levels.keys())}"
            )
        return self.levels[level]
