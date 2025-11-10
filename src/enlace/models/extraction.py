"""Pydantic models for extraction results and paper metadata."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from enlace.exceptions import ExtractionError
from enlace.models.figures import Figure
from enlace.models.tables import (
    BalanceTable,
    RegressionTable,
    SummaryStatisticsTable,
)


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process for reproducibility."""

    enlace_version: str | None = Field(
        None, description="Version of enlace used for extraction"
    )
    extraction_date: datetime = Field(
        default_factory=datetime.now, description="When extraction was performed"
    )
    command: str | None = Field(None, description="CLI command used")
    config: dict[str, Any] = Field(
        default_factory=dict, description="Configuration settings used"
    )
    processing_time_seconds: float | None = Field(
        None, description="Total processing time"
    )


class PaperMetadata(BaseModel):
    """Metadata extracted from research paper."""

    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    journal: str | None = None
    abstract: str | None = None


class ExtractionResult(BaseModel):
    """Result from paper extraction operation."""

    paper_id: str = Field(description="Unique paper identifier")
    source_file: Path = Field(description="Path to source PDF/DOCX")
    extraction_date: datetime = Field(default_factory=datetime.now)

    # Extracted content
    tables: list[RegressionTable | SummaryStatisticsTable | BalanceTable] = Field(
        default_factory=list
    )
    figures: list[Figure] = Field(default_factory=list)
    metadata: PaperMetadata = Field(
        default_factory=PaperMetadata,
        description="Paper metadata (title, authors, etc)",
    )

    # Extraction metadata (for reproducibility)
    extraction_metadata: ExtractionMetadata = Field(
        default_factory=ExtractionMetadata,
        description="Metadata about extraction process",
    )

    # Quality metrics
    extraction_quality: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall quality score"
    )
    warnings: list[str] = Field(default_factory=list)

    # Processing info
    processing_time_seconds: float | None = None
    tables_extracted: int = Field(default=0)
    figures_extracted: int = Field(default=0)

    def save(self, output_dir: Path, format: str = "json") -> None:
        """Save extraction result to file.

        Args:
            output_dir: Directory to save output files
            format: Output format (json, csv, both)

        Raises:
            ExtractionError: If save operation fails

        """
        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_dir)
            paper_output_dir = output_dir / self.paper_id
            paper_output_dir.mkdir(parents=True, exist_ok=True)

            # Save JSON format
            if format in ("json", "both"):
                json_path = paper_output_dir / "extraction.json"
                with open(json_path, "w") as f:
                    json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

            # Save CSV format (for tables)
            if format in ("csv", "both"):
                self._save_csv(paper_output_dir)

        except Exception as e:
            raise ExtractionError(f"Failed to save extraction results: {e}") from e

    def _save_csv(self, output_dir: Path) -> None:
        """Save tables in CSV format.

        Args:
            output_dir: Directory to save CSV files

        """
        import pandas as pd

        # Create tables subdirectory
        tables_dir = output_dir / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)

        # Save each table type to CSV
        for idx, table in enumerate(self.tables):
            if isinstance(table, RegressionTable):
                # Flatten regression table to DataFrame
                rows = []
                for model in table.models:
                    for coef in model.coefficients:
                        rows.append(
                            {
                                "table_number": table.table_number,
                                "model_number": model.model_number,
                                "variable_name": coef.variable_name,
                                "coefficient": coef.coefficient,
                                "std_error": coef.std_error,
                                "t_statistic": coef.t_statistic,
                                "p_value": coef.p_value,
                                "significance": coef.significance,
                            }
                        )
                if rows:
                    df = pd.DataFrame(rows)
                    csv_path = tables_dir / f"regression_table_{idx + 1}.csv"
                    df.to_csv(csv_path, index=False)

            elif isinstance(table, SummaryStatisticsTable):
                # Flatten summary stats to DataFrame
                rows = []
                for stat in table.statistics:
                    rows.append(stat.model_dump())
                if rows:
                    df = pd.DataFrame(rows)
                    csv_path = tables_dir / f"summary_stats_table_{idx + 1}.csv"
                    df.to_csv(csv_path, index=False)

            elif isinstance(table, BalanceTable):
                # Flatten balance table to DataFrame
                rows = []
                for comparison in table.comparisons:
                    rows.append(comparison.model_dump())
                if rows:
                    df = pd.DataFrame(rows)
                    csv_path = tables_dir / f"balance_table_{idx + 1}.csv"
                    df.to_csv(csv_path, index=False)
