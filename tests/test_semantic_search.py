"""Tests for the semantic_search module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from augmentation_config import AugmentationConfig
from semantic_search import SemanticSearchPipeline


@pytest.mark.unit
class TestSemanticSearchPipeline:
    """Tests for SemanticSearchPipeline class."""

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_init_with_default_config(self, mock_chat, mock_embeddings):
        """Test initialization with default configuration."""
        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm

        pipeline = SemanticSearchPipeline()

        assert pipeline.config is not None
        assert pipeline.embedding_model == mock_embeddings_instance
        assert pipeline.text_splitter is not None
        assert pipeline.llm == mock_llm
        assert pipeline.vectorstore is None
        assert pipeline.current_document_path is None

        mock_embeddings.assert_called_once()
        mock_chat.assert_called_once()

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_init_with_custom_config(self, mock_chat, mock_embeddings):
        """Test initialization with custom configuration."""
        config = AugmentationConfig(
            embedding_model="custom/model",
            chunk_size=500,
            chunk_overlap=50,
            llm_model="claude-3-5-sonnet-20241022",
        )

        mock_embeddings_instance = MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance

        pipeline = SemanticSearchPipeline(config=config)

        assert pipeline.config == config
        mock_embeddings.assert_called_once()
        assert mock_embeddings.call_args[1]["model_name"] == "custom/model"

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.PdfReader")
    def test_extract_text_from_pdf_success(
        self, mock_pdf_reader, mock_chat, mock_embeddings
    ):
        """Test successful PDF text extraction."""
        pipeline = SemanticSearchPipeline()

        # Mock PDF pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "This is page 1 text."
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "This is page 2 text."

        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader_instance

        # Create temp test PDF
        test_pdf = Path(__file__).parent / "test_data" / "test.pdf"

        with patch("semantic_search.Path.exists", return_value=True):
            documents = pipeline._extract_text_from_pdf(str(test_pdf))

        assert len(documents) == 2
        assert documents[0].page_content == "This is page 1 text."
        assert documents[0].metadata["page"] == 1
        assert documents[0].metadata["total_pages"] == 2
        assert documents[1].page_content == "This is page 2 text."
        assert documents[1].metadata["page"] == 2

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_extract_text_from_pdf_file_not_found(self, mock_chat, mock_embeddings):
        """Test PDF extraction with non-existent file."""
        pipeline = SemanticSearchPipeline()

        with pytest.raises(FileNotFoundError):
            pipeline._extract_text_from_pdf("/nonexistent/file.pdf")

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.PdfReader")
    def test_extract_text_from_pdf_error_handling(
        self, mock_pdf_reader, mock_chat, mock_embeddings
    ):
        """Test PDF extraction error handling."""
        pipeline = SemanticSearchPipeline()

        mock_pdf_reader.side_effect = Exception("PDF read error")

        test_pdf = Path(__file__).parent / "test_data" / "test.pdf"

        with patch("semantic_search.Path.exists", return_value=True):
            with pytest.raises(Exception) as exc_info:
                pipeline._extract_text_from_pdf(str(test_pdf))

            assert "PDF read error" in str(exc_info.value)

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_chunk_documents(self, mock_chat, mock_embeddings):
        """Test document chunking."""
        pipeline = SemanticSearchPipeline()

        # Create sample documents
        documents = [
            Document(
                page_content="This is a test document with some content. " * 50,
                metadata={"page": 1, "source": "test.pdf"},
            ),
            Document(
                page_content="Another page with different content. " * 30,
                metadata={"page": 2, "source": "test.pdf"},
            ),
        ]

        chunks = pipeline._chunk_documents(documents)

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify metadata was preserved and enhanced
        for chunk in chunks:
            assert "page" in chunk.metadata
            assert "source" in chunk.metadata
            assert "chunk_index" in chunk.metadata
            assert "total_chunks_in_page" in chunk.metadata

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_process_document_success(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test successful document processing."""
        pipeline = SemanticSearchPipeline()

        # Mock extraction and chunking
        mock_docs = [
            Document(page_content="Test content", metadata={"page": 1}),
        ]

        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore

        with (
            patch.object(
                pipeline, "_extract_text_from_pdf", return_value=mock_docs
            ) as mock_extract,
            patch.object(
                pipeline, "_chunk_documents", return_value=mock_docs
            ) as mock_chunk,
        ):
            await pipeline.process_document("test.pdf")

        mock_extract.assert_called_once_with("test.pdf")
        mock_chunk.assert_called_once()
        assert pipeline.vectorstore == mock_vectorstore
        assert pipeline.current_document_path == "test.pdf"
        mock_vectorstore.add_documents.assert_called_once()

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_process_document_already_processed(self, mock_chat, mock_embeddings):
        """Test processing already-processed document."""
        pipeline = SemanticSearchPipeline()
        pipeline.current_document_path = "test.pdf"

        with patch.object(pipeline, "_extract_text_from_pdf") as mock_extract:
            await pipeline.process_document("test.pdf")

        # Should not re-process
        mock_extract.assert_not_called()

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_search_no_document(self, mock_chat, mock_embeddings):
        """Test semantic search without processed document."""
        pipeline = SemanticSearchPipeline()

        with pytest.raises(ValueError) as exc_info:
            await pipeline.semantic_search("test query")

        assert "No document processed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_search_success(self, mock_chat, mock_embeddings):
        """Test successful semantic search."""
        pipeline = SemanticSearchPipeline()

        # Mock vectorstore
        mock_vectorstore = MagicMock()
        mock_doc = Document(
            page_content="Test content about regression coefficients",
            metadata={"page": 5, "source": "paper.pdf", "chunk_index": 2},
        )
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.85),
            (mock_doc, 0.75),
        ]
        pipeline.vectorstore = mock_vectorstore

        results = await pipeline.semantic_search("regression coefficients", k=5)

        assert len(results) == 2
        assert results[0]["text"] == "Test content about regression coefficients"
        assert results[0]["page"] == 5
        assert results[0]["similarity_score"] == 0.85
        assert results[1]["similarity_score"] == 0.75

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_search_filter_by_threshold(
        self, mock_chat, mock_embeddings
    ):
        """Test semantic search filters by similarity threshold."""
        config = AugmentationConfig(similarity_threshold=0.7)
        pipeline = SemanticSearchPipeline(config=config)

        # Mock vectorstore with mixed similarity scores
        mock_vectorstore = MagicMock()
        mock_doc = Document(page_content="Test", metadata={"page": 1})
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.85),  # Above threshold
            (mock_doc, 0.65),  # Below threshold
            (mock_doc, 0.75),  # Above threshold
        ]
        pipeline.vectorstore = mock_vectorstore

        results = await pipeline.semantic_search("test query", k=3)

        # Only 2 results above 0.7 threshold
        assert len(results) == 2
        assert all(r["similarity_score"] >= 0.7 for r in results)

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_qa_no_document(self, mock_chat, mock_embeddings):
        """Test semantic QA without processed document."""
        pipeline = SemanticSearchPipeline()

        with pytest.raises(ValueError) as exc_info:
            await pipeline.semantic_qa("What is the coefficient?")

        assert "No document processed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_qa_success(self, mock_chat, mock_embeddings):
        """Test successful semantic QA."""
        # Create mock response with proper string content
        mock_response = MagicMock()
        mock_response.content = "The coefficient is 0.45"

        # Mock the chain's ainvoke (chain = qa_prompt | self.llm)
        mock_chain = AsyncMock(return_value=mock_response)

        pipeline = SemanticSearchPipeline()
        # Mock that document has been processed
        pipeline.vectorstore = MagicMock()

        # Mock semantic search
        mock_chunks = [
            {"text": "Context about coefficient", "page": 5, "similarity_score": 0.85}
        ]

        with (
            patch.object(
                pipeline, "semantic_search", return_value=mock_chunks
            ) as mock_search,
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation (qa_prompt | self.llm)
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain)
            )

            result = await pipeline.semantic_qa("What is the coefficient?")

        mock_search.assert_called_once()
        assert result["answer"] == "The coefficient is 0.45"
        assert result["source_chunks"] == mock_chunks
        assert result["confidence"] > 0.0
        assert result["question"] == "What is the coefficient?"

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_qa_no_chunks_found(self, mock_chat, mock_embeddings):
        """Test semantic QA with no relevant chunks."""
        pipeline = SemanticSearchPipeline()
        # Mock that document has been processed
        pipeline.vectorstore = MagicMock()

        # Mock semantic search returning no results
        with patch.object(pipeline, "semantic_search", return_value=[]):
            result = await pipeline.semantic_qa("What is missing?")

        assert result["answer"] is None
        assert result["source_chunks"] == []
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_semantic_qa_llm_error(self, mock_chat, mock_embeddings):
        """Test semantic QA with LLM error."""
        # Mock chain that raises an error
        mock_chain = AsyncMock(side_effect=Exception("LLM error"))

        pipeline = SemanticSearchPipeline()
        # Mock that document has been processed
        pipeline.vectorstore = MagicMock()

        # Mock semantic search
        mock_chunks = [{"text": "Context", "page": 1, "similarity_score": 0.8}]

        with (
            patch.object(pipeline, "semantic_search", return_value=mock_chunks),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation to raise error
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain)
            )

            result = await pipeline.semantic_qa("Test question")

        assert result["answer"] is None
        assert result["confidence"] == 0.0
        assert "error" in result

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_batch_qa_async(self, mock_chat, mock_embeddings):
        """Test batch QA with async processing."""
        config = AugmentationConfig(use_async=True, max_concurrent_queries=2)
        pipeline = SemanticSearchPipeline(config=config)

        # Mock semantic_qa
        async def mock_qa(question, k=None):
            return {
                "answer": f"Answer to {question}",
                "source_chunks": [],
                "confidence": 0.8,
                "question": question,
            }

        with patch.object(pipeline, "semantic_qa", side_effect=mock_qa):
            questions = ["Q1", "Q2", "Q3"]
            results = await pipeline.batch_qa(questions)

        assert len(results) == 3
        assert all("answer" in r for r in results)
        assert results[0]["question"] == "Q1"
        assert results[1]["question"] == "Q2"
        assert results[2]["question"] == "Q3"

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    async def test_batch_qa_sequential(self, mock_chat, mock_embeddings):
        """Test batch QA with sequential processing."""
        config = AugmentationConfig(use_async=False)
        pipeline = SemanticSearchPipeline(config=config)

        # Mock semantic_qa
        async def mock_qa(question, k=None):
            return {"answer": f"Answer {question}", "question": question}

        with patch.object(pipeline, "semantic_qa", side_effect=mock_qa):
            questions = ["Q1", "Q2"]
            results = await pipeline.batch_qa(questions)

        assert len(results) == 2

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_estimate_confidence_no_answer(self, mock_chat, mock_embeddings):
        """Test confidence estimation with no answer."""
        pipeline = SemanticSearchPipeline()

        confidence = pipeline._estimate_confidence("Information not found", [])

        assert confidence == 0.0

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_estimate_confidence_with_chunks(self, mock_chat, mock_embeddings):
        """Test confidence estimation with chunks."""
        pipeline = SemanticSearchPipeline()

        chunks = [
            {"similarity_score": 0.9},
            {"similarity_score": 0.8},
        ]

        confidence = pipeline._estimate_confidence(
            "The coefficient is 0.45 with standard error 0.02", chunks
        )

        # Should have reasonable confidence
        assert 0.0 < confidence <= 1.0
        assert confidence > 0.5  # Good chunks + good answer

    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    def test_reset(self, mock_chat, mock_embeddings):
        """Test pipeline reset."""
        pipeline = SemanticSearchPipeline()
        pipeline.vectorstore = MagicMock()
        pipeline.current_document_path = "test.pdf"

        pipeline.reset()

        assert pipeline.vectorstore is None
        assert pipeline.current_document_path is None


@pytest.mark.integration
class TestSemanticSearchIntegration:
    """Integration tests for SemanticSearchPipeline."""

    @pytest.mark.asyncio
    @patch("semantic_search.HuggingFaceEmbeddings")
    @patch("semantic_search.ChatAnthropic")
    @patch("semantic_search.chromadb.Client")
    @patch("semantic_search.Chroma")
    async def test_full_pipeline_workflow(
        self, mock_chroma, mock_chroma_client, mock_chat, mock_embeddings
    ):
        """Test complete pipeline workflow from document to QA."""
        # Setup mocks
        mock_response = MagicMock()
        mock_response.content = "The sample size is 5000 students"
        mock_chain = AsyncMock(return_value=mock_response)

        mock_vectorstore = MagicMock()
        mock_doc = Document(
            page_content="The study included 5000 students",
            metadata={"page": 3},
        )
        mock_vectorstore.similarity_search_with_relevance_scores.return_value = [
            (mock_doc, 0.92)
        ]
        mock_chroma.return_value = mock_vectorstore

        pipeline = SemanticSearchPipeline()

        # Mock document processing
        mock_docs = [Document(page_content="Test paper content", metadata={"page": 1})]

        with (
            patch.object(pipeline, "_extract_text_from_pdf", return_value=mock_docs),
            patch.object(pipeline, "_chunk_documents", return_value=mock_docs),
            patch("semantic_search.ChatPromptTemplate") as mock_prompt,
        ):
            # Mock the chain creation for QA
            mock_prompt_instance = MagicMock()
            mock_prompt.from_messages.return_value = mock_prompt_instance
            mock_prompt_instance.__or__ = MagicMock(
                return_value=MagicMock(ainvoke=mock_chain)
            )

            # Process document
            await pipeline.process_document("test.pdf")

            # Perform semantic search
            search_results = await pipeline.semantic_search("sample size", k=3)
            assert len(search_results) > 0

            # Perform QA
            qa_result = await pipeline.semantic_qa("What is the sample size?")
            assert qa_result["answer"] == "The sample size is 5000 students"
            assert qa_result["confidence"] > 0.0
