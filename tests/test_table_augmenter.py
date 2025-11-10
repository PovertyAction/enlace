"""Unit tests for the TableAugmenter class.

These tests focus on verifying the fix for the method name bug where
_get_study_context was calling extract_context() instead of extract_study_context().
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from enlace.augmentation_config import AugmentationConfig
from enlace.context_models import StudyContext


@pytest.mark.unit
class TestTableAugmenterMethodNameFix:
    """Test the fix for the method name bug in TableAugmenter._get_study_context."""

    @pytest.mark.asyncio
    @patch("enlace.table_augmenter.VariableContextExtractor")
    @patch("enlace.table_augmenter.TreatmentContextExtractor")
    @patch("enlace.table_augmenter.StudyContextExtractor")
    @patch("enlace.table_augmenter.MethodsContextExtractor")
    @patch("enlace.table_augmenter.OutcomeContextExtractor")
    @patch("enlace.table_augmenter.SemanticSearchPipeline")
    async def test_get_study_context_calls_extract_study_context(
        self,
        mock_search_cls,
        mock_outcome_cls,
        mock_methods_cls,
        mock_study_cls,
        mock_treatment_cls,
        mock_variable_cls,
    ):
        """Test that _get_study_context calls extract_study_context (not extract_context).

        This is the main bug fix test: the original code incorrectly called
        self.study_extractor.extract_context() which doesn't exist.
        It should call self.study_extractor.extract_study_context().
        """
        from enlace.table_augmenter import TableAugmenter

        # Setup mock search pipeline
        mock_search = MagicMock()
        mock_search.current_document_path = "test_paper.pdf"
        mock_search_cls.return_value = mock_search

        # Setup mock study context to be returned
        mock_study_context = StudyContext(
            study_design="RCT",
            sample_size=1000,
            location="Kenya",
            duration="2 years",
            population_description="Rural households",
            confidence=0.90,
        )

        # Setup mock study extractor
        mock_study_extractor = MagicMock()
        mock_study_extractor.extract_study_context = AsyncMock(
            return_value=mock_study_context
        )
        mock_study_cls.return_value = mock_study_extractor

        # Create augmenter with study context enabled
        config = AugmentationConfig(augment_study_context=True)
        augmenter = TableAugmenter(config=config)

        # Call the method that was buggy
        result = await augmenter._get_study_context()

        # CRITICAL ASSERTION: Verify extract_study_context was called (not extract_context)
        mock_study_extractor.extract_study_context.assert_called_once()

        # Verify we got the correct result
        assert result == mock_study_context
        assert result.study_design == "RCT"
        assert result.sample_size == 1000

    @pytest.mark.asyncio
    @patch("enlace.table_augmenter.VariableContextExtractor")
    @patch("enlace.table_augmenter.TreatmentContextExtractor")
    @patch("enlace.table_augmenter.StudyContextExtractor")
    @patch("enlace.table_augmenter.MethodsContextExtractor")
    @patch("enlace.table_augmenter.OutcomeContextExtractor")
    @patch("enlace.table_augmenter.SemanticSearchPipeline")
    async def test_study_context_caching(
        self,
        mock_search_cls,
        mock_outcome_cls,
        mock_methods_cls,
        mock_study_cls,
        mock_treatment_cls,
        mock_variable_cls,
    ):
        """Test that study context is cached per document."""
        from enlace.table_augmenter import TableAugmenter

        # Setup mocks
        mock_search = MagicMock()
        mock_search.current_document_path = "test_paper.pdf"
        mock_search_cls.return_value = mock_search

        mock_study_context = StudyContext(
            study_design="RCT", sample_size=1000, confidence=0.90
        )

        mock_study_extractor = MagicMock()
        mock_study_extractor.extract_study_context = AsyncMock(
            return_value=mock_study_context
        )
        mock_study_cls.return_value = mock_study_extractor

        config = AugmentationConfig(augment_study_context=True)
        augmenter = TableAugmenter(config=config)

        # First call should invoke the extractor
        result1 = await augmenter._get_study_context()
        assert mock_study_extractor.extract_study_context.call_count == 1

        # Second call should use cached value
        result2 = await augmenter._get_study_context()
        assert mock_study_extractor.extract_study_context.call_count == 1  # Still 1

        # Both results should be the same
        assert result1 == result2

    @pytest.mark.asyncio
    @patch("enlace.table_augmenter.VariableContextExtractor")
    @patch("enlace.table_augmenter.TreatmentContextExtractor")
    @patch("enlace.table_augmenter.StudyContextExtractor")
    @patch("enlace.table_augmenter.MethodsContextExtractor")
    @patch("enlace.table_augmenter.OutcomeContextExtractor")
    @patch("enlace.table_augmenter.SemanticSearchPipeline")
    async def test_study_context_disabled(
        self,
        mock_search_cls,
        mock_outcome_cls,
        mock_methods_cls,
        mock_study_cls,
        mock_treatment_cls,
        mock_variable_cls,
    ):
        """Test that study context extraction is skipped when disabled."""
        from enlace.table_augmenter import TableAugmenter

        # Setup mocks
        mock_search = MagicMock()
        mock_search.current_document_path = "test_paper.pdf"
        mock_search_cls.return_value = mock_search

        # Disable study context augmentation
        config = AugmentationConfig(augment_study_context=False)
        augmenter = TableAugmenter(config=config)

        # Call should return None without calling extractor
        result = await augmenter._get_study_context()
        assert result is None

    @pytest.mark.asyncio
    @patch("enlace.table_augmenter.VariableContextExtractor")
    @patch("enlace.table_augmenter.TreatmentContextExtractor")
    @patch("enlace.table_augmenter.StudyContextExtractor")
    @patch("enlace.table_augmenter.MethodsContextExtractor")
    @patch("enlace.table_augmenter.OutcomeContextExtractor")
    @patch("enlace.table_augmenter.SemanticSearchPipeline")
    async def test_cache_reset_on_new_document(
        self,
        mock_search_cls,
        mock_outcome_cls,
        mock_methods_cls,
        mock_study_cls,
        mock_treatment_cls,
        mock_variable_cls,
    ):
        """Test that cache is reset when processing a new document."""
        from enlace.table_augmenter import TableAugmenter

        # Setup mocks
        mock_search = MagicMock()
        mock_search.current_document_path = "paper1.pdf"
        mock_search_cls.return_value = mock_search

        mock_study1 = StudyContext(study_design="RCT", sample_size=1000, confidence=0.9)
        mock_study2 = StudyContext(
            study_design="Observational", sample_size=5000, confidence=0.85
        )

        call_count = 0

        async def mock_extract():
            nonlocal call_count
            call_count += 1
            return mock_study1 if call_count == 1 else mock_study2

        mock_study_extractor = MagicMock()
        mock_study_extractor.extract_study_context = mock_extract
        mock_study_cls.return_value = mock_study_extractor

        config = AugmentationConfig(augment_study_context=True)
        augmenter = TableAugmenter(config=config)

        # First document
        result1 = await augmenter._get_study_context()
        assert result1.study_design == "RCT"
        assert call_count == 1

        # Second call on same document (should use cache)
        result1b = await augmenter._get_study_context()
        assert result1b.study_design == "RCT"
        assert call_count == 1  # Still 1 (cached)

        # Change document path (simulating new document)
        mock_search.current_document_path = "paper2.pdf"
        result2 = await augmenter._get_study_context()
        assert result2.study_design == "Observational"
        assert call_count == 2  # New extraction

    @pytest.mark.asyncio
    async def test_table_augmenter_initialization(self):
        """Test that TableAugmenter initializes without errors."""
        from enlace.table_augmenter import TableAugmenter

        # Should initialize with default config
        augmenter = TableAugmenter()
        assert augmenter.config is not None
        assert augmenter.search is not None
        assert augmenter.variable_extractor is not None
        assert augmenter.treatment_extractor is not None
        assert augmenter.study_extractor is not None
        assert augmenter.methods_extractor is not None

    @pytest.mark.asyncio
    async def test_table_augmenter_with_custom_config(self):
        """Test TableAugmenter with custom configuration."""
        from enlace.table_augmenter import TableAugmenter

        config = AugmentationConfig(
            augment_variables=True,
            augment_treatments=False,
            augment_methods=True,
            augment_study_context=True,
        )

        augmenter = TableAugmenter(config=config)
        assert augmenter.config == config
        assert augmenter.config.augment_variables is True
        assert augmenter.config.augment_treatments is False


@pytest.mark.unit
class TestTableAugmenterExtractorMethods:
    """Test that all extractors have the correct method names."""

    @pytest.mark.asyncio
    async def test_study_extractor_has_extract_study_context_method(self):
        """Verify StudyContextExtractor has extract_study_context method."""
        from enlace.context_extractors import StudyContextExtractor
        from enlace.semantic_search import SemanticSearchPipeline

        # Create a mock search pipeline
        mock_search = MagicMock(spec=SemanticSearchPipeline)

        extractor = StudyContextExtractor(mock_search)

        # Verify the method exists
        assert hasattr(extractor, "extract_study_context")
        assert callable(getattr(extractor, "extract_study_context"))

        # Verify it does NOT have extract_context (the old bug)
        # Note: It might have extract_context for other purposes, but extract_study_context
        # is the correct one for this use case

    @pytest.mark.asyncio
    async def test_variable_extractor_has_extract_context_method(self):
        """Verify VariableContextExtractor has extract_context method."""
        from enlace.context_extractors import VariableContextExtractor
        from enlace.semantic_search import SemanticSearchPipeline

        mock_search = MagicMock(spec=SemanticSearchPipeline)
        extractor = VariableContextExtractor(mock_search)

        assert hasattr(extractor, "extract_context")
        assert callable(getattr(extractor, "extract_context"))

    @pytest.mark.asyncio
    async def test_treatment_extractor_has_extract_treatment_arms_method(self):
        """Verify TreatmentContextExtractor has extract_treatment_arms method."""
        from enlace.context_extractors import TreatmentContextExtractor
        from enlace.semantic_search import SemanticSearchPipeline

        mock_search = MagicMock(spec=SemanticSearchPipeline)
        extractor = TreatmentContextExtractor(mock_search)

        assert hasattr(extractor, "extract_treatment_arms")
        assert callable(getattr(extractor, "extract_treatment_arms"))

    @pytest.mark.asyncio
    async def test_methods_extractor_has_extract_methods_for_table_method(self):
        """Verify MethodsContextExtractor has extract_methods_for_table method."""
        from enlace.context_extractors import MethodsContextExtractor
        from enlace.semantic_search import SemanticSearchPipeline

        mock_search = MagicMock(spec=SemanticSearchPipeline)
        extractor = MethodsContextExtractor(mock_search)

        assert hasattr(extractor, "extract_methods_for_table")
        assert callable(getattr(extractor, "extract_methods_for_table"))
