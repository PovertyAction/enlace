"""Integration tests for the complete semantic augmentation pipeline."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from augmentation_config import AugmentationConfig
from semantic_search import SemanticSearchPipeline
from semantic_validator import SemanticValidator


@pytest.mark.integration
class TestSemanticAugmentationPipeline:
    """Integration tests for the complete semantic augmentation pipeline."""

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_complete_pipeline_with_mocks(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test complete pipeline from document processing to validation."""
        # Setup LLM mock
        mock_response = MagicMock()
        mock_response.content = "The treatment coefficient is 0.450 with SE 0.05"
        mock_chain = AsyncMock(return_value=mock_response)

        # Setup embedding mock
        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance

        # Setup vectorstore mock
        mock_vectorstore = MagicMock()
        mock_doc = Document(
            page_content="Treatment effect coefficient: 0.450 (SE=0.05)",
            metadata={"page": 12, "source": "paper.pdf"},
        )
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.92)
        ]
        mock_chroma.return_value = mock_vectorstore

        # Initialize pipeline
        config = AugmentationConfig()
        search_pipeline = SemanticSearchPipeline(config=config)

        # Mock document processing
        mock_docs = [
            Document(
                page_content="This paper studies treatment effects. "
                "The treatment coefficient is 0.450 with standard error 0.05. "
                "The sample includes 5000 students.",
                metadata={"page": 1},
            )
        ]

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=mock_docs),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation for QA
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain)
            )

            # Step 1: Process document
            await search_pipeline.process_document("test_paper.pdf")

            assert search_pipeline.vectorstore is not None
            assert search_pipeline.current_document_path == "test_paper.pdf"

            # Step 2: Perform semantic search
            search_results = await search_pipeline.semantic_search(
                "treatment coefficient", k=3
            )

            assert len(search_results) > 0
            assert search_results[0]["similarity_score"] >= 0.7

            # Step 3: Perform QA
            qa_result = await search_pipeline.semantic_qa(
                "What is the treatment coefficient?"
            )

            assert qa_result["answer"] is not None
            assert "0.450" in qa_result["answer"]
            assert qa_result["confidence"] > 0.0

            # Step 4: Initialize validator with shared pipeline
            validator = SemanticValidator(
                config=config, search_pipeline=search_pipeline
            )

            # Step 5: Validate coefficient
            validation_result = await validator.validate_coefficient(
                variable_name="treatment",
                parsed_value=0.450,
                table_id="Table 3",
            )

            assert validation_result.parsed_value == 0.450
            assert validation_result.rag_extracted_value == 0.450
            assert validation_result.matches is True
            assert validation_result.confidence > 0.8

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_with_multiple_tables(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test pipeline with multiple tables from same document."""

        # Different responses for different queries
        async def mock_chain_invoke(inputs):
            question = inputs.get("question", "")
            response = MagicMock()
            if "Table 1" in question or "baseline" in question.lower():
                response.content = "Table 1 baseline coefficient is 0.320"
            elif "Table 2" in question or "treatment" in question.lower():
                response.content = "Table 2 treatment coefficient is 0.450"
            else:
                response.content = "Information not found"
            return response

        # Setup vectorstore
        mock_vectorstore = MagicMock()
        mock_doc1 = Document(
            page_content="Table 1: Baseline results. Coefficient: 0.320",
            metadata={"page": 10},
        )
        mock_doc2 = Document(
            page_content="Table 2: Treatment effects. Coefficient: 0.450",
            metadata={"page": 12},
        )

        def mock_search(query, k=5):
            if "baseline" in query.lower() or "Table 1" in query:
                return [(mock_doc1, 0.90)]
            elif "treatment" in query.lower() or "Table 2" in query:
                return [(mock_doc2, 0.92)]
            return []

        mock_vectorstore.similarity_search_with_relevance_scores = mock_search
        mock_chroma.return_value = mock_vectorstore

        # Initialize pipeline
        search_pipeline = SemanticSearchPipeline()

        mock_docs = [mock_doc1, mock_doc2]

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=mock_docs),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain_invoke)
            )

            await search_pipeline.process_document("paper.pdf")

            # Validate coefficients from different tables
            validator = SemanticValidator(search_pipeline=search_pipeline)

            result1 = await validator.validate_coefficient(
                "baseline", 0.320, table_id="Table 1"
            )

            result2 = await validator.validate_coefficient(
                "treatment", 0.450, table_id="Table 2"
            )

            assert result1.parsed_value == 0.320
            assert result1.matches is True

            assert result2.parsed_value == 0.450
            assert result2.matches is True

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_detects_parsing_errors(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test that pipeline detects OCR/parsing errors."""
        # Setup LLM mock - correct value in paper
        mock_response = MagicMock()
        mock_response.content = "The coefficient is 0.450"
        mock_chain = AsyncMock(return_value=mock_response)

        # Setup vectorstore
        mock_vectorstore = MagicMock()
        mock_doc = Document(
            page_content="Treatment coefficient: 0.450", metadata={"page": 12}
        )
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.95)
        ]
        mock_chroma.return_value = mock_vectorstore

        search_pipeline = SemanticSearchPipeline()

        mock_docs = [mock_doc]

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=mock_docs),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain)
            )

            await search_pipeline.process_document("paper.pdf")

            validator = SemanticValidator(search_pipeline=search_pipeline)

            # Simulate OCR error: parsed as 0.480 instead of 0.450
            result = await validator.validate_coefficient(
                "treatment",
                parsed_value=0.480,  # Wrong value
            )

            # Should detect mismatch
            assert result.parsed_value == 0.480
            assert result.rag_extracted_value == 0.450
            assert result.matches is False  # Beyond 5% threshold
            assert result.relative_discrepancy is not None
            assert result.relative_discrepancy > 0.05

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_batch_validation(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test batch validation of multiple coefficients."""

        # Mock responses for different variables
        async def mock_chain_invoke(inputs):
            question = inputs.get("question", "")
            if "var1" in question:
                response = MagicMock()
                response.content = "var1 coefficient is 0.450"
                return response
            elif "var2" in question:
                response = MagicMock()
                response.content = "var2 coefficient is 0.320"
                return response
            elif "var3" in question:
                response = MagicMock()
                response.content = "var3 coefficient is 0.180"
                return response
            response = MagicMock()
            response.content = "Not found"
            return response

        # Setup vectorstore
        mock_vectorstore = MagicMock()
        mock_doc = Document(
            page_content="Coefficients: var1=0.450, var2=0.320, var3=0.180",
            metadata={"page": 10},
        )
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.90)
        ]
        mock_chroma.return_value = mock_vectorstore

        search_pipeline = SemanticSearchPipeline()

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=[mock_doc]
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=[mock_doc]),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain_invoke)
            )

            await search_pipeline.process_document("paper.pdf")

            validator = SemanticValidator(search_pipeline=search_pipeline)

            # Batch validate
            coefficients = [
                {"variable": "var1", "value": 0.450},
                {"variable": "var2", "value": 0.320},
                {"variable": "var3", "value": 0.180},
            ]

            results = await validator.batch_validate_coefficients(
                coefficients, table_id="Table 1"
            )

            assert len(results) == 3
            assert all(var in results for var in ["var1", "var2", "var3"])
            assert all(r.matches for r in results.values())

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_table_validation_summary(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test generating validation summary for entire table."""

        async def mock_chain_invoke(inputs):
            response = MagicMock()
            response.content = "Coefficient is 0.450"
            return response

        mock_vectorstore = MagicMock()
        mock_doc = Document(page_content="Coefficients: 0.450", metadata={"page": 10})
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.90)
        ]
        mock_chroma.return_value = mock_vectorstore

        search_pipeline = SemanticSearchPipeline()

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=[mock_doc]
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=[mock_doc]),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain_invoke)
            )

            await search_pipeline.process_document("paper.pdf")

            validator = SemanticValidator(search_pipeline=search_pipeline)

            # Mock table data
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

            summary = await validator.validate_table_summary(
                table_data, table_id="Table 3"
            )

            assert summary["table_id"] == "Table 3"
            assert summary["total_values_checked"] == 2
            assert "matches" in summary
            assert "mismatches" in summary
            assert "average_confidence" in summary
            assert isinstance(summary["flagged_issues"], list)

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_handles_missing_data(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test pipeline gracefully handles missing/incomplete data."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Information not found in the document"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat.return_value = mock_llm

        mock_vectorstore = MagicMock()
        # Return empty results (no relevant chunks)
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = []
        mock_chroma.return_value = mock_vectorstore

        search_pipeline = SemanticSearchPipeline()
        search_pipeline.llm = mock_llm

        mock_docs = [
            Document(page_content="Some unrelated content", metadata={"page": 1})
        ]

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=mock_docs),
        ):
            await search_pipeline.process_document("paper.pdf")

            validator = SemanticValidator(search_pipeline=search_pipeline)

            # Try to validate coefficient that doesn't exist in paper
            result = await validator.validate_coefficient("nonexistent_variable", 0.450)

            assert result.parsed_value == 0.450
            assert result.rag_extracted_value is None
            assert result.matches is False
            assert result.confidence < 0.5

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_pipeline_reset_and_reprocess(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test resetting pipeline and processing new document."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Coefficient is 0.450"
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_chat.return_value = mock_llm

        mock_vectorstore = MagicMock()
        mock_doc = Document(page_content="Data", metadata={"page": 1})
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.90)
        ]
        mock_chroma.return_value = mock_vectorstore

        search_pipeline = SemanticSearchPipeline()
        search_pipeline.llm = mock_llm

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=[mock_doc]
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=[mock_doc]),
        ):
            # Process first document
            await search_pipeline.process_document("paper1.pdf")
            assert search_pipeline.current_document_path == "paper1.pdf"

            # Reset
            search_pipeline.reset()
            assert search_pipeline.vectorstore is None
            assert search_pipeline.current_document_path is None

            # Process second document
            await search_pipeline.process_document("paper2.pdf")
            assert search_pipeline.current_document_path == "paper2.pdf"
            assert search_pipeline.vectorstore is not None


@pytest.mark.integration
@pytest.mark.slow
class TestSemanticAugmentationWorkflows:
    """Test realistic workflows that mirror actual usage."""

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_realistic_research_paper_workflow(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test realistic workflow: process paper → extract tables → validate."""

        # Setup comprehensive mocks
        async def mock_chain_invoke(inputs):
            question = inputs.get("question", "")
            response = MagicMock()

            # Simulate realistic QA responses
            if "treatment" in question.lower() and "coefficient" in question.lower():
                response.content = (
                    "The treatment effect coefficient is 0.450 (SE=0.05), "
                    "statistically significant at p<0.01"
                )
            elif (
                "sample size" in question.lower() or "observations" in question.lower()
            ):
                response.content = "The study included 5000 students"
            elif "mean" in question.lower() and "age" in question.lower():
                response.content = "The mean age is 12.5 years (SD=1.8)"
            else:
                response.content = "Information not available"

            return response

        # Setup vectorstore with realistic document
        mock_vectorstore = MagicMock()

        def mock_search(query, k=5):
            mock_doc = Document(
                page_content="Treatment effect results. "
                "The coefficient is 0.450 (SE=0.05), significant at p<0.01. "
                "Sample: 5,000 students, mean age 12.5 years (SD=1.8).",
                metadata={"page": 12},
            )
            return [(mock_doc, 0.95)]

        mock_vectorstore.similarity_search_with_relevance_scores = mock_search
        mock_chroma.return_value = mock_vectorstore

        # Initialize pipeline
        config = AugmentationConfig(
            chunk_size=1000, top_k_chunks=5, similarity_threshold=0.7
        )

        search_pipeline = SemanticSearchPipeline(config=config)

        mock_docs = [
            Document(
                page_content="Full paper content with treatment effects...",
                metadata={"page": i},
            )
            for i in range(1, 21)
        ]

        with (
            patch.object(
                search_pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ),
            patch.object(search_pipeline, "_chunk_documents", return_value=mock_docs),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain_invoke)
            )

            # Step 1: Process research paper
            await search_pipeline.process_document("research_paper.pdf")

            # Step 2: Extract and validate regression coefficients
            validator = SemanticValidator(
                config=config, search_pipeline=search_pipeline
            )

            coef_result = await validator.validate_coefficient(
                "treatment", 0.450, table_id="Table 3"
            )

            assert coef_result.matches is True
            assert coef_result.confidence > 0.9

            # Step 3: Validate sample size
            n_result = await validator.validate_sample_size(5000)

            assert n_result.matches is True

            # Step 4: Validate summary statistics
            stat_result = await validator.validate_summary_statistic(
                "age", "mean", 12.5
            )

            assert stat_result.matches is True

            # Step 5: Generate validation summary
            table_data = {
                "models": [
                    {
                        "coefficients": [
                            {"variable": "treatment", "value": 0.450},
                        ]
                    }
                ]
            }

            summary = await validator.validate_table_summary(table_data, "Table 3")

            assert summary["matches"] > 0
            assert summary["average_confidence"] > 0.8
