"""Configuration for semantic table augmentation and validation.

This module provides dataclass-based configuration for the semantic search
and table augmentation pipeline, with environment variable support.
"""

import os
from dataclasses import dataclass, field


@dataclass
class AugmentationConfig:
    """Configuration for semantic augmentation of extracted tables.

    Controls embedding generation, semantic search, validation, and
    context extraction for augmenting parsed table data with rich
    semantic information from paper text.
    """

    # ========================================================================
    # EMBEDDING CONFIGURATION
    # ========================================================================

    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "AUGMENTATION_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
    )
    """Embedding model for semantic search.

    Options:
    - sentence-transformers/all-MiniLM-L6-v2 (fast, 384 dim)
    - sentence-transformers/all-mpnet-base-v2 (best quality, 768 dim)
    - minishlab/potion-base-8M (lightweight, 256 dim)
    """

    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("AUGMENTATION_CHUNK_SIZE", "1000"))
    )
    """Size of text chunks for embedding (characters)."""

    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("AUGMENTATION_CHUNK_OVERLAP", "200"))
    )
    """Overlap between consecutive chunks (characters)."""

    # ========================================================================
    # LLM CONFIGURATION
    # ========================================================================

    llm_model: str = field(
        default_factory=lambda: os.getenv(
            "AUGMENTATION_LLM_MODEL", "claude-haiku-4-5-20251001"
        )
    )
    """LLM for question-answering and context extraction.

    Use fast model (Haiku) for validation and extraction tasks.
    """

    temperature: float = field(
        default_factory=lambda: float(os.getenv("AUGMENTATION_TEMPERATURE", "0.1"))
    )
    """LLM temperature (low for factual extraction)."""

    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("AUGMENTATION_MAX_TOKENS", "2048"))
    )
    """Maximum tokens for LLM responses."""

    # ========================================================================
    # SEMANTIC SEARCH CONFIGURATION
    # ========================================================================

    top_k_chunks: int = field(
        default_factory=lambda: int(os.getenv("AUGMENTATION_TOP_K", "5"))
    )
    """Number of top chunks to retrieve for each semantic search query."""

    similarity_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("AUGMENTATION_SIMILARITY_THRESHOLD", "0.3")
        )
    )
    """Minimum similarity score for chunk retrieval (0-1).

    Note: Scores are normalized from cosine distance [-1, 1] to [0, 1].
    A threshold of 0.3 corresponds to cosine similarity of -0.4.
    """

    # ========================================================================
    # VALIDATION CONFIGURATION
    # ========================================================================

    enable_validation: bool = field(
        default_factory=lambda: os.getenv(
            "AUGMENTATION_ENABLE_VALIDATION", "true"
        ).lower()
        == "true"
    )
    """Enable cross-validation of parsed values via semantic search."""

    validation_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("AUGMENTATION_VALIDATION_THRESHOLD", "0.05")
        )
    )
    """Relative tolerance for numerical discrepancies (5% = 0.05)."""

    validation_absolute_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("AUGMENTATION_VALIDATION_ABS_THRESHOLD", "0.01")
        )
    )
    """Absolute tolerance for small values (e.g., coefficients near 0)."""

    # ========================================================================
    # AUGMENTATION FEATURES
    # ========================================================================

    augment_variables: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_VARIABLES", "true").lower()
        == "true"
    )
    """Extract semantic context for each variable in tables."""

    augment_treatments: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_TREATMENTS", "true").lower()
        == "true"
    )
    """Extract treatment/intervention descriptions."""

    augment_methods: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_METHODS", "true").lower()
        == "true"
    )
    """Extract statistical methods context for tables."""

    augment_study_context: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_STUDY_CONTEXT", "true").lower()
        == "true"
    )
    """Extract study design and sample context."""

    # ========================================================================
    # PERFORMANCE CONFIGURATION
    # ========================================================================

    use_async: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_USE_ASYNC", "true").lower()
        == "true"
    )
    """Use async processing for parallel augmentation."""

    max_concurrent_queries: int = field(
        default_factory=lambda: int(os.getenv("AUGMENTATION_MAX_CONCURRENT", "10"))
    )
    """Maximum concurrent semantic search queries."""

    cache_embeddings: bool = field(
        default_factory=lambda: os.getenv(
            "AUGMENTATION_CACHE_EMBEDDINGS", "true"
        ).lower()
        == "true"
    )
    """Cache embeddings to disk for reuse."""

    cache_dir: str = field(
        default_factory=lambda: os.getenv(
            "AUGMENTATION_CACHE_DIR", "data/augmentation_cache"
        )
    )
    """Directory for caching embeddings and vectorstores."""

    # ========================================================================
    # OUTPUT CONFIGURATION
    # ========================================================================

    include_source_citations: bool = field(
        default_factory=lambda: os.getenv("AUGMENTATION_CITATIONS", "true").lower()
        == "true"
    )
    """Include source page/section citations in context fields."""

    min_confidence_to_include: float = field(
        default_factory=lambda: float(os.getenv("AUGMENTATION_MIN_CONFIDENCE", "0.5"))
    )
    """Minimum confidence score to include extracted context (0-1)."""

    def __post_init__(self):
        """Validate configuration values."""
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        if not 0 <= self.similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")

        if not 0 <= self.validation_threshold <= 1:
            raise ValueError("validation_threshold must be between 0 and 1")

        if not 0 <= self.min_confidence_to_include <= 1:
            raise ValueError("min_confidence_to_include must be between 0 and 1")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        if self.top_k_chunks < 1:
            raise ValueError("top_k_chunks must be at least 1")

        if self.max_concurrent_queries < 1:
            raise ValueError("max_concurrent_queries must be at least 1")


# Singleton instance with defaults
default_config = AugmentationConfig()
