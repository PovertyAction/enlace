"""Pydantic models for research paper summaries."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from enlace.exceptions import SummaryError


class TableSummary(BaseModel):
    """Summary of an extracted table."""

    table_number: str | None = Field(None, description="Table number or identifier")
    table_type: str = Field(description="Type: regression, summary_stats, balance")
    description: str = Field(description="Brief description of table content")
    key_findings: list[str] = Field(
        default_factory=list, description="Key findings from this table"
    )
    row_count: int | None = Field(None, description="Number of rows/coefficients")
    quality_issues: list[str] = Field(
        default_factory=list, description="Data quality issues if any"
    )


class SummaryResult(BaseModel):
    """LLM-generated research paper summary."""

    paper_id: str = Field(description="Unique paper identifier")
    source_extraction: Path = Field(description="Path to source extraction.json")
    summary_date: datetime = Field(
        default_factory=datetime.now, description="When summary was generated"
    )

    # Core summary sections
    title: str | None = Field(None, description="50-60 character title")
    overview: str | None = Field(
        None, description="High-level overview (2-3 sentences)"
    )
    research_question: str | None = Field(None, description="Main research question")
    methodology: str | None = Field(None, description="Study design and methodology")
    sample_info: str | None = Field(None, description="Sample size and population")
    treatment_info: str | None = Field(
        None, description="Description of treatment and control groups"
    )
    assignment: str | None = Field(
        None, description="Description of treatment assignment or exogenous variation"
    )
    key_findings: list[str] = Field(
        default_factory=list, description="Main findings with metrics"
    )
    implications: str | None = Field(
        None, description="Policy implications and significance"
    )

    # Paper metadata
    authors: list[str] = Field(default_factory=list, description="All authors listed")
    institutions: list[str] = Field(
        default_factory=list, description="Author institutions/affiliations"
    )
    timeline: str | None = Field(None, description="Study period (e.g., '2012-2013')")
    study_status: str | None = Field(
        None, description="'Results Available' or 'In Progress'"
    )
    study_type: str | None = Field(None, description="RCT, Quasi-experimental, etc.")
    sample_size: str | None = Field(
        None, description="Sample size with units (e.g., '1,200 households')"
    )

    # Table and validation insights
    table_summaries: list[TableSummary] = Field(
        default_factory=list, description="Summaries of extracted tables"
    )
    extraction_quality: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall extraction quality score"
    )
    validation_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Validation quality score"
    )
    validation_issues: list[str] = Field(
        default_factory=list, description="Critical validation issues"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )

    # Generation metadata
    llm_model: str = Field(description="LLM model used for generation")
    llm_temperature: float = Field(default=0.3, description="Temperature setting")
    generation_config: dict[str, Any] = Field(
        default_factory=dict, description="Full generation configuration"
    )
    web_search_used: bool = Field(
        default=False, description="Whether web search enhancement was used"
    )
    web_search_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Web search results if used"
    )
    processing_time_seconds: float | None = Field(
        None, description="Total processing time"
    )

    def save(self, output_dir: Path, format: str = "json") -> None:
        """Save summary to file.

        Args:
            output_dir: Directory to save summary
                       (summary.json will be saved to output_dir/paper_id/)
            format: Output format ('json', 'markdown', or 'both')

        Raises:
            SummaryError: If save operation fails

        """
        try:
            output_dir = Path(output_dir)
            # Create paper-specific subdirectory (matching extraction structure)
            paper_output_dir = output_dir / self.paper_id
            paper_output_dir.mkdir(parents=True, exist_ok=True)

            # Save JSON format
            if format in ("json", "both"):
                json_path = paper_output_dir / "summary.json"
                with open(json_path, "w") as f:
                    json.dump(self.model_dump(mode="json"), f, indent=2, default=str)

            # Save Markdown format
            if format in ("markdown", "both"):
                md_path = paper_output_dir / "summary.md"
                with open(md_path, "w") as f:
                    f.write(self.to_markdown())

        except Exception as e:
            raise SummaryError(f"Failed to save summary: {e}") from e

    def to_markdown(self) -> str:
        """Convert summary to markdown format.

        Returns:
            Markdown-formatted summary text

        """
        lines = []

        # Title
        if self.title:
            lines.append(f"# {self.title}\n")

        # Metadata section
        lines.append("## Study Details\n")

        if self.authors:
            lines.append(f"**Authors:** {', '.join(self.authors)}\n")
        if self.institutions:
            lines.append(f"**Institutions:** {', '.join(self.institutions)}\n")
        if self.timeline:
            lines.append(f"**Timeline:** {self.timeline}\n")
        if self.study_type:
            lines.append(f"**Study Type:** {self.study_type}\n")
        if self.treatment_info:
            lines.append(f"**Treatment Information:** {self.treatment_info}\n")
        if self.assignment:
            lines.append(f"**Assignment:** {self.assignment}\n")
        if self.sample_size:
            lines.append(f"**Sample Size:** {self.sample_size}\n")

        # Overview
        if self.overview:
            lines.append(f"\n## Overview\n\n{self.overview}\n")

        # Research Question
        if self.research_question:
            lines.append(f"\n## Research Question\n\n{self.research_question}\n")

        # Methodology
        if self.methodology:
            lines.append(f"\n## Methodology\n\n{self.methodology}\n")

        # Sample Information
        if self.sample_info:
            lines.append(f"\n## Sample Information\n\n{self.sample_info}\n")

        # Key Findings
        if self.key_findings:
            lines.append("\n## Key Findings\n")
            for finding in self.key_findings:
                lines.append(f"- {finding}\n")

        # Implications
        if self.implications:
            lines.append(f"\n## Implications\n\n{self.implications}\n")

        # Table Summaries
        if self.table_summaries:
            lines.append("\n## Extracted Tables\n")
            for table in self.table_summaries:
                table_title = table.table_number or "Table"
                lines.append(f"\n### {table_title} ({table.table_type})\n")
                lines.append(f"\n{table.description}\n")
                if table.key_findings:
                    lines.append("\n**Key findings:**\n")
                    for finding in table.key_findings:
                        lines.append(f"- {finding}\n")
                if table.quality_issues:
                    lines.append("\n**Quality issues:**\n")
                    for issue in table.quality_issues:
                        lines.append(f"- {issue}\n")

        # Data Quality
        lines.append("\n## Data Quality Assessment\n")
        lines.append(f"\n**Extraction Quality:** {self.extraction_quality:.2f}\n")
        lines.append(f"**Validation Score:** {self.validation_score:.2f}\n")

        if self.validation_issues:
            lines.append("\n**Issues:**\n")
            for issue in self.validation_issues:
                lines.append(f"- {issue}\n")

        if self.recommendations:
            lines.append("\n**Recommendations:**\n")
            for rec in self.recommendations:
                lines.append(f"- {rec}\n")

        # Generation metadata
        lines.append("\n---\n")
        lines.append("\n## Generation Metadata\n")
        lines.append(
            f"\n**Generated:** {self.summary_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        lines.append(f"**Model:** {self.llm_model}\n")
        lines.append(f"**Temperature:** {self.llm_temperature}\n")
        if self.web_search_used:
            lines.append("**Web Search:** Enabled\n")
        if self.processing_time_seconds:
            lines.append(f"**Processing Time:** {self.processing_time_seconds:.1f}s\n")

        return "".join(lines)
