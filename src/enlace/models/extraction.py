"""Pydantic models for extraction results and paper metadata."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field

from enlace.exceptions import ExtractionError
from enlace.models.dual_extraction import ConversionMetadata, DualExtractionTable
from enlace.models.figures import Figure
from enlace.models.tables import (
    BalanceTable,
    RegressionTable,
    SummaryStatisticsTable,
)

logger = logging.getLogger(__name__)


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

    # Dual extraction (Camelot integration)
    dual_extraction_tables: list[DualExtractionTable] | None = Field(
        None,
        description="Tables from dual extraction (docling + Camelot)",
    )
    camelot_enabled: bool = Field(
        default=False,
        description="Whether Camelot extraction was enabled",
    )
    docx_converted: bool = Field(
        default=False,
        description="Whether DOCX was converted to PDF",
    )
    conversion_metadata: ConversionMetadata | None = Field(
        None,
        description="Metadata about DOCX to PDF conversion",
    )

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

            # Save dual extraction tables if available
            if self.dual_extraction_tables:
                self._save_dual_extraction(paper_output_dir, format)

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

    def _save_dual_extraction(self, output_dir: Path, format: str = "json") -> None:
        """Save dual extraction tables (docling + Camelot + reconciled).

        Creates separate directories for each extraction source:
        - tables/docling/: Original docling extractions
        - tables/camelot/: Original Camelot extractions
        - tables/reconciled/: Final reconciled tables
        - reconciliation_report.json: Metadata about merging

        Args:
            output_dir: Directory to save dual extraction output
            format: Output format: "json", "csv", or "both"

        """
        if not self.dual_extraction_tables:
            return

        # Create subdirectories with new structure
        tables_dir = output_dir / "tables"
        docling_dir = tables_dir / "docling"
        camelot_dir = tables_dir / "camelot"
        reconciled_dir = tables_dir / "reconciled"

        docling_dir.mkdir(parents=True, exist_ok=True)
        camelot_dir.mkdir(parents=True, exist_ok=True)
        reconciled_dir.mkdir(parents=True, exist_ok=True)

        # Save reconciliation report
        report = []

        for idx, dual_table in enumerate(self.dual_extraction_tables):
            table_num = idx + 1

            # Save docling table
            if format in ("json", "both"):
                docling_path = docling_dir / f"table_{table_num}.json"
                with open(docling_path, "w") as f:
                    json.dump(
                        dual_table.docling_table.model_dump(), f, indent=2, default=str
                    )

            if format in ("csv", "both"):
                # Convert docling table to CSV
                docling_df = self._table_to_dataframe(dual_table.docling_table)
                if docling_df is not None:
                    docling_csv_path = docling_dir / f"table_{table_num}.csv"
                    docling_df.to_csv(docling_csv_path, index=False)

            # Save Camelot data
            if dual_table.camelot_dataframe:
                camelot_df = dual_table.get_camelot_dataframe()
                if camelot_df is not None:
                    if format in ("csv", "both"):
                        camelot_path = camelot_dir / f"table_{table_num}.csv"
                        camelot_df.to_csv(camelot_path, index=False)

                    if format in ("json", "both"):
                        # Convert DataFrame to JSON
                        camelot_json_path = camelot_dir / f"table_{table_num}.json"
                        with open(camelot_json_path, "w") as f:
                            json.dump(
                                camelot_df.to_dict(orient="records"),
                                f,
                                indent=2,
                                default=str,
                            )

            # Save reconciled table
            if format in ("json", "both"):
                reconciled_path = reconciled_dir / f"table_{table_num}.json"
                with open(reconciled_path, "w") as f:
                    json.dump(
                        dual_table.reconciled_table.model_dump(),
                        f,
                        indent=2,
                        default=str,
                    )

            if format in ("csv", "both"):
                # Convert reconciled table to CSV
                reconciled_df = self._table_to_dataframe(dual_table.reconciled_table)
                if reconciled_df is not None:
                    reconciled_csv_path = reconciled_dir / f"table_{table_num}.csv"
                    reconciled_df.to_csv(reconciled_csv_path, index=False)

            # Add to report
            report.append(
                {
                    "table_id": dual_table.table_id,
                    "table_number": table_num,
                    "reconciliation": dual_table.reconciliation_metadata.model_dump(),
                    "camelot_quality": dual_table.camelot_quality,
                }
            )

        # Save reconciliation report
        report_path = output_dir / "reconciliation_report.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "paper_id": self.paper_id,
                    "extraction_date": str(self.extraction_date),
                    "camelot_enabled": self.camelot_enabled,
                    "tables_reconciled": len(self.dual_extraction_tables),
                    "tables": report,
                },
                f,
                indent=2,
            )

    def _table_to_dataframe(
        self, table: RegressionTable | SummaryStatisticsTable | BalanceTable
    ) -> pd.DataFrame | None:
        """Convert a table to pandas DataFrame for CSV export.

        Args:
            table: Table to convert

        Returns:
            DataFrame or None if conversion fails

        """
        try:
            if isinstance(table, RegressionTable):
                # Flatten regression table to DataFrame
                rows = []
                for model in table.models:
                    for coef in model.coefficients:
                        row = {
                            "model": model.model_number,
                            "variable": coef.variable_name,
                            "coefficient": coef.coefficient,
                            "std_error": coef.std_error,
                            "t_statistic": coef.t_statistic,
                            "p_value": coef.p_value,
                            "significance": coef.significance,
                        }
                        rows.append(row)
                return pd.DataFrame(rows) if rows else None

            elif isinstance(table, SummaryStatisticsTable):
                # Flatten summary stats table
                rows = []
                for stat in table.statistics:
                    rows.append(stat.model_dump())
                return pd.DataFrame(rows) if rows else None

            elif isinstance(table, BalanceTable):
                # Flatten balance table
                rows = []
                for comparison in table.comparisons:
                    rows.append(comparison.model_dump())
                return pd.DataFrame(rows) if rows else None

            else:
                return None

        except Exception as e:
            logger.warning(f"Failed to convert table to DataFrame: {e}")
            return None
