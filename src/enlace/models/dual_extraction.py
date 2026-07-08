"""Data models for dual extraction (docling + Camelot).

This module defines models for storing results from both extraction sources
and the reconciled/merged results.
"""

from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from enlace.models.tables import BalanceTable, RegressionTable, SummaryStatisticsTable


class ReconciliationMetadata(BaseModel):
    """Metadata about table reconciliation process.

    Attributes:
        source: Source of the table data ('camelot_primary', 'docling_only', 'camelot_only', 'merged')
        cells_total: Total number of cells in table
        cells_from_docling: Cells where docling value was selected
        cells_from_camelot: Cells where Camelot value was selected
        cells_agreed: Number of cells where both extractors agreed
        cells_disagreed: Number of cells with different values
        agreement_rate: Proportion of cells that agreed (0-1)
        cells_reconciled_by_heuristic: Cells reconciled using heuristics
        reconciliation_strategy: Strategy used for reconciliation
        confidence_score: Overall confidence in reconciled result (0-1)
        docling_avg_confidence: Average OCR confidence from docling (if available)
        camelot_accuracy: Camelot accuracy score (0-100)
        camelot_whitespace: Camelot whitespace score (0-100)

    """

    source: str = Field(default="unknown", description="Source of the table data")
    cells_total: int = Field(default=0, description="Total number of cells in table")
    cells_from_docling: int = Field(
        default=0, description="Cells where docling value was selected"
    )
    cells_from_camelot: int = Field(
        default=0, description="Cells where Camelot value was selected"
    )
    cells_agreed: int = Field(
        default=0, description="Number of cells where extractors agreed"
    )
    cells_disagreed: int = Field(
        default=0, description="Number of cells with disagreements"
    )
    agreement_rate: float = Field(
        default=0.0,
        description="Proportion of cells that agreed (0-1)",
        ge=0.0,
        le=1.0,
    )
    cells_reconciled_by_heuristic: int = Field(
        default=0,
        description="Cells reconciled using heuristics",
    )
    reconciliation_strategy: str = Field(
        default="unknown",
        description="Strategy used (confidence_based, prefer_camelot, prefer_docling)",
    )
    confidence_score: float = Field(
        default=0.0,
        description="Overall confidence in reconciled result (0-1)",
        ge=0.0,
        le=1.0,
    )
    docling_avg_confidence: float | None = Field(
        None,
        description="Average OCR confidence from docling",
    )
    camelot_accuracy: float = Field(
        default=0.0,
        description="Camelot accuracy score (0-100)",
        ge=0.0,
        le=100.0,
    )
    camelot_whitespace: float = Field(
        default=0.0,
        description="Camelot whitespace score (0-100)",
        ge=0.0,
        le=100.0,
    )


class DualExtractionTable(BaseModel):
    """Stores results from both docling and Camelot extraction.

    This model preserves all three versions of the table:
    1. Original docling extraction (structured or raw DataFrame)
    2. Original Camelot extraction (raw DataFrame)
    3. Reconciled/merged result (structured or raw DataFrame)

    Attributes:
        table_id: Unique identifier for this table
        docling_table: Table extracted by docling parser (optional for raw mode)
        docling_dataframe: Raw DataFrame from Docling (for raw extraction)
        camelot_dataframe: Raw DataFrame from Camelot (serialized as dict)
        camelot_quality: Camelot quality metrics
        reconciled_table: Final merged table (optional for raw mode)
        reconciled_dataframe: Final merged DataFrame (for raw extraction)
        reconciliation_metadata: Metadata about reconciliation process

    """

    table_id: str = Field(description="Unique identifier for this table")
    docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable | None = (
        Field(None, description="Table extracted by docling (semantic parsing)")
    )
    docling_dataframe: Any | None = Field(
        None,
        description="Docling raw DataFrame (for structure-preserving extraction)",
    )
    camelot_dataframe: Any | None = Field(
        None,
        description="Camelot DataFrame serialized (flexible format for integer column names)",
    )
    camelot_quality: dict[str, Any] = Field(
        default_factory=dict,
        description="Camelot quality metrics (accuracy, whitespace, flavor, etc)",
    )
    reconciled_table: RegressionTable | SummaryStatisticsTable | BalanceTable | None = (
        Field(None, description="Final reconciled/merged table (semantic)")
    )
    reconciled_dataframe: Any | None = Field(
        None,
        description="Final reconciled/merged DataFrame (raw mode)",
    )
    reconciliation_metadata: ReconciliationMetadata = Field(
        description="Metadata about reconciliation process"
    )

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True

    @classmethod
    def from_dataframe(
        cls,
        table_id: str,
        docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable,
        camelot_df: pd.DataFrame,
        camelot_quality: dict[str, float],
        reconciled_table: RegressionTable | SummaryStatisticsTable | BalanceTable,
        reconciliation_metadata: ReconciliationMetadata,
    ) -> "DualExtractionTable":
        """Create DualExtractionTable from pandas DataFrame.

        Args:
            table_id: Unique identifier for this table
            docling_table: Table extracted by docling
            camelot_df: Camelot DataFrame
            camelot_quality: Camelot quality metrics
            reconciled_table: Final reconciled table
            reconciliation_metadata: Reconciliation metadata

        Returns:
            DualExtractionTable instance

        """
        # Serialize DataFrame to dict
        camelot_dict = (
            camelot_df.to_dict(orient="records") if camelot_df is not None else None
        )

        return cls(
            table_id=table_id,
            docling_table=docling_table,
            camelot_dataframe=camelot_dict,
            camelot_quality=camelot_quality,
            reconciled_table=reconciled_table,
            reconciliation_metadata=reconciliation_metadata,
        )

    def get_camelot_dataframe(self) -> pd.DataFrame | None:
        """Reconstruct Camelot DataFrame from serialized dict.

        Returns:
            Pandas DataFrame, or None if Camelot extraction not available

        """
        if self.camelot_dataframe is None:
            return None
        return pd.DataFrame.from_records(self.camelot_dataframe)

    def to_export_dict(self) -> dict[str, Any]:
        """Export as dictionary for JSON serialization.

        Returns:
            Dictionary with all three table versions and metadata

        """
        return {
            "table_id": self.table_id,
            "docling_table": self.docling_table.model_dump(),
            "camelot_dataframe": self.camelot_dataframe,
            "camelot_quality": self.camelot_quality,
            "reconciled_table": self.reconciled_table.model_dump(),
            "reconciliation_metadata": self.reconciliation_metadata.model_dump(),
        }


class ConversionMetadata(BaseModel):
    """Metadata about DOCX to PDF conversion.

    Attributes:
        source_file: Original DOCX/DOC file path
        output_file: Generated PDF file path
        conversion_time: Time taken for conversion in seconds
        libreoffice_version: LibreOffice version string
        keep_pdf: Whether converted PDF should be kept

    """

    source_file: str = Field(description="Original DOCX/DOC file path")
    output_file: str = Field(description="Generated PDF file path")
    conversion_time: float = Field(
        description="Time taken for conversion in seconds",
        ge=0.0,
    )
    libreoffice_version: str = Field(
        default="unknown",
        description="LibreOffice version string",
    )
    keep_pdf: bool = Field(
        default=False,
        description="Whether converted PDF should be kept",
    )
