"""Tests for the semantic_validator module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enlace.augmentation_config import AugmentationConfig
from enlace.context_models import ValidationResult
from enlace.semantic_validator import SemanticValidator


@pytest.mark.unit
class TestSemanticValidator:
    """Tests for SemanticValidator class."""

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_init_with_default_config(self, mock_search_pipeline):
        """Test initialization with default configuration."""
        mock_pipeline = MagicMock()
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()

        assert validator.config is not None
        assert validator.search is not None
        assert validator.exact_match_threshold == 0.001
        assert validator.close_match_threshold == 0.05
        assert validator.warning_threshold == 0.10

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_init_with_custom_config(self, mock_search_pipeline):
        """Test initialization with custom configuration."""
        config = AugmentationConfig(chunk_size=500)
        mock_pipeline = MagicMock()

        validator = SemanticValidator(config=config, search_pipeline=mock_pipeline)

        assert validator.config == config
        assert validator.search == mock_pipeline

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_coefficient_exact_match(self, mock_search_pipeline):
        """Test coefficient validation with exact match."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "The coefficient for treatment is 0.450",
                "confidence": 0.9,
                "source_chunks": [
                    {
                        "text": "The treatment effect coefficient is 0.450 (SE=0.05)",
                        "page": 12,
                    }
                ],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_coefficient(
            variable_name="treatment",
            parsed_value=0.450,
            table_id="Table 3",
        )

        assert isinstance(result, ValidationResult)
        assert result.parsed_value == 0.450
        assert result.rag_extracted_value == 0.450
        assert result.matches is True
        assert result.confidence > 0.9  # Boosted for exact match
        assert result.source_page == 12

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_coefficient_close_match(self, mock_search_pipeline):
        """Test coefficient validation with close match."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "The coefficient is approximately 0.448",
                "confidence": 0.85,
                "source_chunks": [{"text": "Coefficient: 0.448", "page": 12}],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_coefficient(
            variable_name="treatment", parsed_value=0.450
        )

        assert result.parsed_value == 0.450
        assert result.rag_extracted_value == 0.448
        assert result.matches is True  # Within 5% threshold
        assert result.relative_discrepancy < 0.05

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_coefficient_mismatch(self, mock_search_pipeline):
        """Test coefficient validation with mismatch."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "The coefficient is 0.650",
                "confidence": 0.8,
                "source_chunks": [{"text": "Coefficient: 0.650", "page": 12}],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_coefficient(
            variable_name="treatment", parsed_value=0.450
        )

        assert result.parsed_value == 0.450
        assert result.rag_extracted_value == 0.650
        assert result.matches is False  # Beyond 5% threshold
        assert result.relative_discrepancy > 0.05
        assert result.confidence < 0.8  # Penalized for mismatch

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_coefficient_no_rag_value(self, mock_search_pipeline):
        """Test coefficient validation when RAG finds no value."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "Information not found",
                "confidence": 0.3,
                "source_chunks": [],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_coefficient(
            variable_name="treatment", parsed_value=0.450
        )

        assert result.parsed_value == 0.450
        assert result.rag_extracted_value is None
        assert result.matches is False
        assert result.discrepancy_size is None

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_summary_statistic_success(self, mock_search_pipeline):
        """Test summary statistic validation."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "The mean age is 35.2 years",
                "confidence": 0.88,
                "source_chunks": [{"text": "Mean age: 35.2", "page": 8}],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_summary_statistic(
            variable_name="age",
            statistic_type="mean",
            parsed_value=35.2,
            group="treatment",
        )

        assert result.parsed_value == 35.2
        assert result.rag_extracted_value == 35.2
        assert result.matches is True
        assert result.confidence > 0.88

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_sample_size_success(self, mock_search_pipeline):
        """Test sample size validation."""
        mock_pipeline = MagicMock()
        mock_pipeline.semantic_qa = AsyncMock(
            return_value={
                "answer": "The sample includes 5000 students",
                "confidence": 0.95,
                "source_chunks": [{"text": "N = 5000", "page": 5}],
            }
        )
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        result = await validator.validate_sample_size(
            parsed_value=5000, group="treatment"
        )

        assert result.parsed_value == 5000
        assert result.rag_extracted_value == 5000
        assert result.matches is True

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_batch_validate_coefficients(self, mock_search_pipeline):
        """Test batch coefficient validation."""
        mock_pipeline = MagicMock()

        # Mock different responses for different variables
        async def mock_qa(question, k=None):
            if "var1" in question:
                return {
                    "answer": "Coefficient is 0.50",
                    "confidence": 0.9,
                    "source_chunks": [{"text": "var1: 0.50", "page": 10}],
                }
            elif "var2" in question:
                return {
                    "answer": "Coefficient is 0.30",
                    "confidence": 0.85,
                    "source_chunks": [{"text": "var2: 0.30", "page": 10}],
                }
            return {
                "answer": "Not found",
                "confidence": 0.1,
                "source_chunks": [],
            }

        mock_pipeline.semantic_qa = mock_qa
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        coefficients = [
            {"variable": "var1", "value": 0.50},
            {"variable": "var2", "value": 0.30},
        ]

        results = await validator.batch_validate_coefficients(
            coefficients, table_id="Table 1"
        )

        assert len(results) == 2
        assert "var1" in results
        assert "var2" in results
        assert results["var1"].matches is True
        assert results["var2"].matches is True

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_validate_table_summary(self, mock_search_pipeline):
        """Test table validation summary generation."""
        mock_pipeline = MagicMock()

        async def mock_qa(question, k=None):
            return {
                "answer": "Coefficient is 0.45",
                "confidence": 0.9,
                "source_chunks": [{"text": "coef: 0.45", "page": 10}],
            }

        mock_pipeline.semantic_qa = mock_qa
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        table_data = {
            "models": [
                {
                    "coefficients": [
                        {"variable": "treatment", "value": 0.45},
                        {"variable": "control", "value": 0.20},
                    ]
                }
            ]
        }

        summary = await validator.validate_table_summary(table_data, table_id="Table 3")

        assert summary["table_id"] == "Table 3"
        assert summary["total_values_checked"] == 2
        assert summary["matches"] >= 0
        assert summary["mismatches"] >= 0
        assert "average_confidence" in summary
        assert isinstance(summary["flagged_issues"], list)

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_number_from_text_decimal(self, mock_search_pipeline):
        """Test extracting decimal number from text."""
        validator = SemanticValidator()

        value = validator._extract_number_from_text("The coefficient is 0.456")

        assert value == 0.456

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_number_from_text_integer(self, mock_search_pipeline):
        """Test extracting integer from text."""
        validator = SemanticValidator()

        value = validator._extract_number_from_text("Sample size: 5000 students")

        assert value == 5000.0

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_number_from_text_scientific(self, mock_search_pipeline):
        """Test extracting scientific notation."""
        validator = SemanticValidator()

        value = validator._extract_number_from_text("P-value is 2.5e-4")

        assert value == 2.5e-4

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_number_from_text_negative(self, mock_search_pipeline):
        """Test extracting negative number."""
        validator = SemanticValidator()

        value = validator._extract_number_from_text("The coefficient is -0.345")

        assert value == -0.345

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_number_from_text_no_number(self, mock_search_pipeline):
        """Test extracting when no number present."""
        validator = SemanticValidator()

        value = validator._extract_number_from_text("Information not found")

        assert value is None

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_compare_values_exact_match(self, mock_search_pipeline):
        """Test value comparison with exact match."""
        validator = SemanticValidator()

        matches, abs_disc, rel_disc = validator._compare_values(0.450, 0.450)

        assert matches is True
        assert abs_disc == 0.0
        assert rel_disc == 0.0

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_compare_values_close_match(self, mock_search_pipeline):
        """Test value comparison with close match."""
        validator = SemanticValidator()

        matches, abs_disc, rel_disc = validator._compare_values(0.450, 0.448)

        assert matches is True  # Within 5% threshold
        assert abs_disc == pytest.approx(0.002, abs=1e-6)
        assert rel_disc < 0.05

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_compare_values_mismatch(self, mock_search_pipeline):
        """Test value comparison with mismatch."""
        validator = SemanticValidator()

        matches, abs_disc, rel_disc = validator._compare_values(0.450, 0.650)

        assert matches is False  # Beyond 5% threshold
        assert abs_disc == pytest.approx(0.200, abs=1e-6)
        assert rel_disc > 0.05

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_compare_values_both_zero(self, mock_search_pipeline):
        """Test value comparison with both zeros."""
        validator = SemanticValidator()

        matches, abs_disc, rel_disc = validator._compare_values(0.0, 0.0)

        assert matches is True
        assert abs_disc == 0.0
        assert rel_disc == 0.0

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_compare_values_one_none(self, mock_search_pipeline):
        """Test value comparison with None."""
        validator = SemanticValidator()

        matches, abs_disc, rel_disc = validator._compare_values(0.450, None)

        assert matches is False
        assert abs_disc is None
        assert rel_disc is None

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_adjust_confidence_exact_match(self, mock_search_pipeline):
        """Test confidence adjustment for exact match."""
        validator = SemanticValidator()

        adjusted = validator._adjust_confidence_for_match(
            base_confidence=0.8, matches=True, relative_disc=0.0001
        )

        # Should boost confidence
        assert adjusted > 0.8
        assert adjusted <= 1.0

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_adjust_confidence_close_match(self, mock_search_pipeline):
        """Test confidence adjustment for close match."""
        validator = SemanticValidator()

        adjusted = validator._adjust_confidence_for_match(
            base_confidence=0.8, matches=True, relative_disc=0.03
        )

        # Should slightly boost confidence
        assert adjusted >= 0.8
        assert adjusted <= 1.0

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_adjust_confidence_minor_mismatch(self, mock_search_pipeline):
        """Test confidence adjustment for minor mismatch."""
        validator = SemanticValidator()

        adjusted = validator._adjust_confidence_for_match(
            base_confidence=0.8, matches=False, relative_disc=0.08
        )

        # Should penalize confidence
        assert adjusted < 0.8
        assert adjusted == pytest.approx(0.8 * 0.6)

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_adjust_confidence_major_mismatch(self, mock_search_pipeline):
        """Test confidence adjustment for major mismatch."""
        validator = SemanticValidator()

        adjusted = validator._adjust_confidence_for_match(
            base_confidence=0.8, matches=False, relative_disc=0.15
        )

        # Should heavily penalize confidence
        assert adjusted < 0.5
        assert adjusted == pytest.approx(0.8 * 0.3)

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_source_info(self, mock_search_pipeline):
        """Test extracting source info from QA result."""
        validator = SemanticValidator()

        qa_result = {
            "source_chunks": [
                {"text": "First chunk text", "page": 12},
                {"text": "Second chunk text", "page": 13},
            ]
        }

        source_text, source_page = validator._extract_source_info(qa_result)

        assert source_text == "First chunk text"
        assert source_page == 12

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_extract_source_info_no_chunks(self, mock_search_pipeline):
        """Test extracting source info with no chunks."""
        validator = SemanticValidator()

        qa_result = {"source_chunks": []}

        source_text, source_page = validator._extract_source_info(qa_result)

        assert source_text is None
        assert source_page is None

    @patch("semantic_validator.SemanticSearchPipeline")
    def test_reset(self, mock_search_pipeline):
        """Test validator reset."""
        mock_pipeline = MagicMock()
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        validator.reset()

        mock_pipeline.reset.assert_called_once()


@pytest.mark.integration
class TestSemanticValidatorIntegration:
    """Integration tests for SemanticValidator."""

    @pytest.mark.asyncio
    @patch("semantic_validator.SemanticSearchPipeline")
    async def test_full_validation_workflow(self, mock_search_pipeline):
        """Test complete validation workflow."""
        mock_pipeline = MagicMock()

        # Mock QA responses
        async def mock_qa(question, k=None):
            if "treatment" in question.lower():
                return {
                    "answer": "The treatment coefficient is 0.450 (SE=0.05)",
                    "confidence": 0.92,
                    "source_chunks": [
                        {
                            "text": "Treatment effect: 0.450 (0.05)",
                            "page": 12,
                            "similarity_score": 0.95,
                        }
                    ],
                }
            elif "control" in question.lower():
                return {
                    "answer": "Control coefficient is 0.200",
                    "confidence": 0.88,
                    "source_chunks": [
                        {
                            "text": "Control: 0.200",
                            "page": 12,
                            "similarity_score": 0.90,
                        }
                    ],
                }
            return {
                "answer": "Not found",
                "confidence": 0.1,
                "source_chunks": [],
            }

        mock_pipeline.semantic_qa = mock_qa
        mock_search_pipeline.return_value = mock_pipeline

        validator = SemanticValidator()
        validator.search = mock_pipeline

        # Validate individual coefficients
        result1 = await validator.validate_coefficient("treatment", 0.450)
        assert result1.matches is True
        assert result1.confidence > 0.9

        result2 = await validator.validate_coefficient("control", 0.200)
        assert result2.matches is True

        # Batch validate
        coefficients = [
            {"variable": "treatment", "value": 0.450},
            {"variable": "control", "value": 0.200},
        ]
        batch_results = await validator.batch_validate_coefficients(coefficients)

        assert len(batch_results) == 2
        assert all(r.matches for r in batch_results.values())

        # Table summary
        table_data = {
            "models": [
                {
                    "coefficients": [
                        {"variable": "treatment", "value": 0.450},
                        {"variable": "control", "value": 0.200},
                    ]
                }
            ]
        }

        summary = await validator.validate_table_summary(table_data, "Table 3")
        assert summary["matches"] == 2
        assert summary["mismatches"] == 0
        assert summary["average_confidence"] > 0.8
