"""Semantic search pipeline for table augmentation and validation.

This module provides semantic search capabilities using vector embeddings
and ChromaDB for retrieving relevant context from research papers.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from pypdf import PdfReader

from augmentation_config import AugmentationConfig

logger = logging.getLogger(__name__)


class SemanticSearchPipeline:
    """Semantic search pipeline using embeddings and vector database.

    Provides semantic similarity search and question-answering capabilities
    for extracting context from research papers.
    """

    def __init__(self, config: AugmentationConfig | None = None):
        """Initialize semantic search pipeline.

        Args:
            config: Augmentation configuration. Uses defaults if None.

        """
        self.config = config or AugmentationConfig()

        # Initialize embedding model
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model,
            model_kwargs={"device": "cpu"},  # Use CPU for compatibility
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Initialize LLM for QA
        self.llm = ChatAnthropic(
            model=self.config.llm_model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        # Vectorstore (initialized per document)
        self.vectorstore: Chroma | None = None
        self.current_document_path: str | None = None

        # Cache directory
        if self.config.cache_embeddings:
            cache_dir = Path(self.config.cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized semantic search with model: {self.config.embedding_model}"
        )

    def _extract_text_from_pdf(self, pdf_path: str) -> list[Document]:
        """Extract text from PDF with page metadata.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of Document objects with page content and metadata

        """
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        logger.info(f"Extracting text from {pdf_path_obj.name}")

        documents = []
        try:
            reader = PdfReader(str(pdf_path_obj))

            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()

                if text.strip():
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": pdf_path_obj.name,
                            "page": page_num,
                            "total_pages": len(reader.pages),
                        },
                    )
                    documents.append(doc)

            logger.info(f"Extracted {len(documents)} pages from {pdf_path_obj.name}")

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            raise

        return documents

    def _chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into smaller chunks for embedding.

        Args:
            documents: List of page-level documents

        Returns:
            List of chunked documents with metadata

        """
        logger.info(f"Chunking {len(documents)} documents")

        chunks = []
        for doc in documents:
            split_docs = self.text_splitter.split_documents([doc])

            # Add chunk index to metadata
            for i, chunk_doc in enumerate(split_docs):
                chunk_doc.metadata["chunk_index"] = i
                chunk_doc.metadata["total_chunks_in_page"] = len(split_docs)
                chunks.append(chunk_doc)

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    async def process_document(self, pdf_path: str) -> None:
        """Process PDF document and create vector store.

        Args:
            pdf_path: Path to PDF file

        """
        pdf_path_obj = Path(pdf_path)

        # Check if already processed
        if self.current_document_path == str(pdf_path_obj):
            logger.info(f"Document already processed: {pdf_path_obj.name}")
            return

        # Extract text
        documents = self._extract_text_from_pdf(str(pdf_path_obj))

        # Chunk documents
        chunks = self._chunk_documents(documents)

        # Create vectorstore
        logger.info(f"Creating vectorstore with {len(chunks)} chunks")

        # Use in-memory ChromaDB (fast, no persistence needed)
        chroma_client = chromadb.Client(
            Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        self.vectorstore = Chroma(
            client=chroma_client,
            collection_name="paper_context",
            embedding_function=self.embedding_model,
        )

        # Add documents
        self.vectorstore.add_documents(chunks)

        self.current_document_path = str(pdf_path_obj)

        logger.info(f"Vectorstore created for {pdf_path_obj.name}")

    async def semantic_search(
        self,
        query: str,
        k: int | None = None,
        filter_sections: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Perform semantic similarity search.

        Args:
            query: Search query
            k: Number of top results to return (uses config default if None)
            filter_sections: Optional list of section names to filter by

        Returns:
            List of search results with text, metadata, and similarity score

        """
        if self.vectorstore is None:
            raise ValueError("No document processed. Call process_document() first.")

        k = k or self.config.top_k_chunks

        logger.debug(f"Semantic search: {query[:100]}... (k={k})")

        # Perform similarity search
        results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

        # Filter by similarity threshold
        filtered_results = [
            {
                "text": doc.page_content,
                "page": doc.metadata.get("page"),
                "source": doc.metadata.get("source"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "similarity_score": score,
            }
            for doc, score in results
            if score >= self.config.similarity_threshold
        ]

        logger.debug(
            f"Found {len(filtered_results)} results above threshold "
            f"({self.config.similarity_threshold})"
        )

        return filtered_results

    async def semantic_qa(self, question: str, k: int | None = None) -> dict[str, Any]:
        """Question-answering via semantic search + LLM.

        Args:
            question: Question to answer
            k: Number of context chunks to use (uses config default if None)

        Returns:
            Dict with answer, source chunks, and confidence score

        """
        if self.vectorstore is None:
            raise ValueError("No document processed. Call process_document() first.")

        k = k or self.config.top_k_chunks

        logger.debug(f"QA query: {question[:100]}...")

        # Semantic search for relevant chunks
        chunks = await self.semantic_search(question, k=k)

        if not chunks:
            logger.warning(f"No relevant chunks found for: {question[:100]}...")
            return {
                "answer": None,
                "source_chunks": [],
                "confidence": 0.0,
                "question": question,
            }

        # Build context from top chunks
        context = "\n\n".join(
            [f"[Page {chunk['page']}] {chunk['text']}" for chunk in chunks]
        )

        # Create QA prompt
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a precise research assistant extracting information from academic papers.

Your task:
- Answer the question using ONLY information from the provided context
- Be concise and factual
- If the context doesn't contain the answer, say "Information not found"
- Include specific numbers, names, and details when present
- Do not make assumptions or infer information not explicitly stated

Context from paper:
{context}""",
                ),
                ("human", "{question}"),
            ]
        )

        # Get answer from LLM
        chain = qa_prompt | self.llm

        try:
            response = await chain.ainvoke({"context": context, "question": question})
            answer = response.content.strip()

            # Estimate confidence based on answer quality and chunk similarity
            confidence = self._estimate_confidence(answer, chunks)

            logger.debug(f"QA answer: {answer[:100]}... (confidence: {confidence:.2f})")

            return {
                "answer": answer,
                "source_chunks": chunks,
                "confidence": confidence,
                "question": question,
            }

        except Exception as e:
            logger.error(f"Error in QA: {e}")
            return {
                "answer": None,
                "source_chunks": chunks,
                "confidence": 0.0,
                "question": question,
                "error": str(e),
            }

    def _estimate_confidence(self, answer: str, chunks: list[dict]) -> float:
        """Estimate confidence in QA answer.

        Args:
            answer: LLM answer
            chunks: Source chunks used

        Returns:
            Confidence score (0-1)

        """
        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
        ]:
            return 0.0

        # Base confidence on chunk similarity scores
        if not chunks:
            return 0.0

        avg_similarity = sum(c["similarity_score"] for c in chunks) / len(chunks)

        # Adjust for answer length (very short answers may be incomplete)
        length_factor = min(len(answer) / 50, 1.0)  # Penalize answers < 50 chars

        # Combine factors
        confidence = avg_similarity * 0.7 + length_factor * 0.3

        return min(confidence, 1.0)

    async def batch_qa(
        self, questions: list[str], k: int | None = None
    ) -> list[dict[str, Any]]:
        """Answer multiple questions concurrently.

        Args:
            questions: List of questions
            k: Number of context chunks per question

        Returns:
            List of QA results in same order as questions

        """
        if self.config.use_async:
            # Limit concurrency
            semaphore = asyncio.Semaphore(self.config.max_concurrent_queries)

            async def bounded_qa(question: str) -> dict[str, Any]:
                async with semaphore:
                    return await self.semantic_qa(question, k=k)

            tasks = [bounded_qa(q) for q in questions]
            results = await asyncio.gather(*tasks)
        else:
            # Sequential
            results = []
            for question in questions:
                result = await self.semantic_qa(question, k=k)
                results.append(result)

        return results

    def reset(self) -> None:
        """Reset vectorstore and clear current document."""
        if self.vectorstore is not None:
            # ChromaDB in-memory doesn't need explicit cleanup
            self.vectorstore = None

        self.current_document_path = None
        logger.info("Semantic search pipeline reset")
