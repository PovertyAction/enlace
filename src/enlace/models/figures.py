"""Pydantic models for figure/image extraction from research papers."""

from typing import Any

from pydantic import BaseModel, Field


class Figure(BaseModel):
    """Model for extracted figure/image from research paper."""

    figure_id: str = Field(description="Unique identifier for this figure")
    figure_number: str | None = Field(None, description="Figure number from paper")
    caption: str | None = Field(None, description="Figure caption/title")
    page_number: int | None = Field(
        None, description="Page number where figure appears"
    )

    # Image file information
    image_path: str | None = Field(
        None, description="Relative path to saved image file"
    )
    image_format: str | None = Field(None, description="Image format (png, jpg, etc)")
    image_width: int | None = Field(None, description="Image width in pixels")
    image_height: int | None = Field(None, description="Image height in pixels")

    # Classification
    figure_type: str | None = Field(
        None,
        description="Type of figure (chart, diagram, photo, map, etc)",
    )

    # Quality metrics
    quality_score: float | None = Field(
        None, description="Extraction quality score (0-1)"
    )

    # Metadata
    source_file: str | None = None
    context_before: str | None = Field(None, description="Text appearing before figure")

    # Semantic augmentation fields (optional)
    figure_context: dict[str, Any] | None = Field(
        None, description="Semantic context describing the figure content"
    )
    annotation: str | None = Field(
        None, description="Vision model annotation describing the image content"
    )
