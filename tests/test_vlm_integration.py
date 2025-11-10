"""Test VLM integration infrastructure.

This module tests the Granite-Docling VLM pipeline integration
and quality trigger mechanisms.
"""

import pytest

from enlace.core.config import ExtractionConfig
from enlace.core.vlm_extractor import GraniteVLMExtractor
from enlace.models.tables import RegressionCoefficient, RegressionModel, RegressionTable


class TestVLMConfiguration:
    """Test VLM configuration options."""

    def test_vlm_config_defaults(self):
        """Test VLM configuration default values."""
        config = ExtractionConfig()

        assert config.enable_vlm is False
        assert config.vlm_backend == "granite"
        assert config.vlm_model == "granite-docling"
        assert config.vlm_framework == "auto"
        assert config.vlm_null_se_threshold == 0.30
        assert config.vlm_null_coef_threshold == 0.20
        assert config.vlm_confidence_threshold == 0.70

    def test_vlm_config_from_env(self, monkeypatch):
        """Test VLM configuration from environment variables."""
        monkeypatch.setenv("ENLACE_ENABLE_VLM", "true")
        monkeypatch.setenv("ENLACE_VLM_FRAMEWORK", "mlx")
        monkeypatch.setenv("ENLACE_VLM_NULL_SE_THRESHOLD", "0.25")

        config = ExtractionConfig()

        assert config.enable_vlm is True
        assert config.vlm_framework == "mlx"
        assert config.vlm_null_se_threshold == 0.25

    def test_claude_config_defaults(self):
        """Test Claude cleanup configuration defaults."""
        config = ExtractionConfig()

        assert config.enable_claude_cleanup is False
        assert config.claude_model == "claude-3-5-sonnet-20241022"
        assert config.claude_api_key is None
        assert config.claude_null_se_threshold == 0.15
        assert config.claude_max_cost_per_table == 0.05


class TestGraniteVLMExtractor:
    """Test Granite-Docling VLM extractor."""

    def test_granite_extractor_initialization(self):
        """Test Granite VLM extractor initialization."""
        config = ExtractionConfig(enable_vlm=True)
        extractor = GraniteVLMExtractor(config)

        assert extractor.config == config
        assert extractor.converter is None  # Lazy-loaded
        assert extractor._docling_imported is False

    @pytest.mark.skip(reason="Requires docling VLM dependencies")
    def test_granite_pipeline_initialization(self):
        """Test Granite VLM pipeline initialization."""
        config = ExtractionConfig(enable_vlm=True, vlm_framework="transformers")
        extractor = GraniteVLMExtractor(config)

        # Initialize pipeline
        extractor._initialize_vlm_pipeline()

        assert extractor._docling_imported is True
        assert extractor.converter is not None

    @pytest.mark.skip(reason="Requires test PDF file")
    def test_granite_extraction(self, tmp_path):
        """Test Granite VLM extraction from PDF."""
        # This test would require a sample PDF file
        # Will be implemented in Phase 9.2.6 with benchmark dataset
        pass


class TestQualityTriggers:
    """Test VLM quality trigger mechanisms."""

    def test_table_quality_calculation_high_missing_se(self):
        """Test quality calculation with high missing SE rate."""
        from enlace.core.parser import TableParser

        config = ExtractionConfig(
            enable_vlm=True,
            vlm_null_se_threshold=0.30,
        )
        parser = TableParser(config=config)

        # Create mock table with 50% missing SEs
        table = RegressionTable(
            title="Test Table",
            models=[
                RegressionModel(
                    model_number=1,
                    coefficients=[
                        RegressionCoefficient(
                            variable_name="var1", coefficient=0.5, std_error=0.1
                        ),
                        RegressionCoefficient(
                            variable_name="var2", coefficient=0.3, std_error=None
                        ),  # Missing SE
                        RegressionCoefficient(
                            variable_name="var3", coefficient=0.2, std_error=0.05
                        ),
                        RegressionCoefficient(
                            variable_name="var4", coefficient=0.1, std_error=None
                        ),  # Missing SE
                    ],
                )
            ],
        )

        quality = parser._calculate_table_quality(table)

        assert quality["null_se_rate"] == 0.5  # 2/4 missing
        assert quality["null_coef_rate"] == 0.0  # All coefficients present
        assert quality["total_coefficients"] == 4
        assert quality["missing_se"] == 2
        assert quality["needs_vlm"] is True  # 50% > 30% threshold

    def test_table_quality_calculation_high_missing_coef(self):
        """Test quality calculation with high missing coefficient rate."""
        from enlace.core.parser import TableParser

        config = ExtractionConfig(
            enable_vlm=True,
            vlm_null_coef_threshold=0.20,
        )
        parser = TableParser(config=config)

        # Create mock table with 25% missing coefficients
        table = RegressionTable(
            title="Test Table",
            models=[
                RegressionModel(
                    model_number=1,
                    coefficients=[
                        RegressionCoefficient(
                            variable_name="var1", coefficient=0.5, std_error=0.1
                        ),
                        RegressionCoefficient(
                            variable_name="var2", coefficient=None, std_error=0.05
                        ),  # Missing coef
                        RegressionCoefficient(
                            variable_name="var3", coefficient=0.2, std_error=0.03
                        ),
                        RegressionCoefficient(
                            variable_name="var4", coefficient=0.1, std_error=0.02
                        ),
                    ],
                )
            ],
        )

        quality = parser._calculate_table_quality(table)

        assert quality["null_coef_rate"] == 0.25  # 1/4 missing
        assert quality["needs_vlm"] is True  # 25% > 20% threshold

    def test_table_quality_calculation_low_ocr_confidence(self):
        """Test quality calculation with low OCR confidence."""
        from enlace.core.parser import TableParser

        config = ExtractionConfig(
            enable_vlm=True,
            vlm_confidence_threshold=0.70,
        )
        parser = TableParser(config=config)

        # Create mock table with low OCR confidence
        table = RegressionTable(
            title="Test Table",
            models=[
                RegressionModel(
                    model_number=1,
                    coefficients=[
                        RegressionCoefficient(
                            variable_name="var1",
                            coefficient=0.5,
                            std_error=0.1,
                            ocr_confidence=0.65,  # Low confidence
                        ),
                        RegressionCoefficient(
                            variable_name="var2",
                            coefficient=0.3,
                            std_error=0.05,
                            ocr_confidence=0.68,  # Low confidence
                        ),
                    ],
                )
            ],
        )

        quality = parser._calculate_table_quality(table)

        assert quality["avg_ocr_confidence"] == 0.665  # (0.65 + 0.68) / 2
        assert quality["needs_vlm"] is True  # 0.665 < 0.70 threshold

    def test_table_quality_calculation_good_quality(self):
        """Test quality calculation with good quality extraction."""
        from enlace.core.parser import TableParser

        config = ExtractionConfig(
            enable_vlm=True,
            vlm_null_se_threshold=0.30,
            vlm_null_coef_threshold=0.20,
        )
        parser = TableParser(config=config)

        # Create mock table with complete data
        table = RegressionTable(
            title="Test Table",
            models=[
                RegressionModel(
                    model_number=1,
                    coefficients=[
                        RegressionCoefficient(
                            variable_name="var1", coefficient=0.5, std_error=0.1
                        ),
                        RegressionCoefficient(
                            variable_name="var2", coefficient=0.3, std_error=0.05
                        ),
                        RegressionCoefficient(
                            variable_name="var3", coefficient=0.2, std_error=0.03
                        ),
                    ],
                )
            ],
        )

        quality = parser._calculate_table_quality(table)

        assert quality["null_se_rate"] == 0.0  # All SEs present
        assert quality["null_coef_rate"] == 0.0  # All coefficients present
        assert quality["needs_vlm"] is False  # Good quality, no VLM needed
