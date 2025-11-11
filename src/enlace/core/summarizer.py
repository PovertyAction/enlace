"""Research paper summarization using LLMs."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

from enlace.core.config import SummaryConfig
from enlace.exceptions import LLMError, SummaryError
from enlace.models.extraction import ExtractionResult
from enlace.models.summary import SummaryResult
from enlace.models.tables import BalanceTable, RegressionTable, SummaryStatisticsTable
from enlace.models.validation import ValidationResult

logger = logging.getLogger(__name__)


class PaperSummarizer:
    """Generate LLM-based summaries of research papers from extraction artifacts."""

    # System prompt for the summarization LLM
    SYSTEM_PROMPT = """You are a research analyst specializing in development economics and impact evaluation. Your task is to create structured, accurate summaries of research papers based on extracted data.

CRITICAL ANTI-HALLUCINATION RULES:
1. ALL information must come ONLY from the provided extraction and validation data
2. NEVER fabricate or infer:
   - Author names, institutions, or affiliations
   - Statistical results, effect sizes, or p-values
   - Sample sizes, dates, or locations
   - Research methods or study design details
   - Partner organizations not explicitly mentioned
3. If information is missing, use EXACTLY these phrases:
   - "Not specified"
   - "Unknown"
   - "Not mentioned in extraction"
4. Do NOT use generic placeholders like "the researchers" or "the study found"
5. Do NOT round or approximate numbers - use exact figures from extraction
6. When uncertain, OMIT the detail rather than guess

Your summary should be clear, concise, and accessible to non-technical audiences while maintaining scientific accuracy."""

    # Prompt templates for different sections
    SUMMARY_TEMPLATE = """Based on the extraction and validation data provided, generate a structured summary of this research paper.

# EXTRACTION DATA
{extraction_data}

# VALIDATION REPORT
Quality Score: {validation_score}
Extraction Quality: {extraction_quality}

Issues:
{validation_issues}

Recommendations:
{validation_recommendations}

# TABLE SUMMARIES
{table_data}

---

Generate a JSON response with the following structure:

{{{{
  "title": "50-60 character jargon-free title",
  "overview": "2-3 sentence overview of the research question and significance",
  "research_question": "Main research question or objective",
  "methodology": "Study design, approach, and key methods (2-3 sentences)",
  "sample_info": "Sample size and population description",
  "treatment_info": "Description of treatment and control groups",
  "assignment": "Description of treatment assignment or exogenous variation",
  "key_findings": [
    "Finding 1 with specific metrics",
    "Finding 2 with specific metrics",
    "..."
  ],
  "treatment_effects": [
    "Outcome 1: effect size, standard error, p-value, subgroup info",
    "Outcome 2: effect size, standard error, p-value, subgroup info",
    "..."
  ],
  "implications": "Policy implications or broader significance (2-3 sentences)",
  "authors": ["Author 1", "Author 2", "..."],
  "institutions": ["Institution 1", "Institution 2", "..."],
  "timeline": "YYYY-YYYY format for study period",
  "study_status": "Results Available" or "In Progress",
  "study_type": "RCT, Quasi-experimental, Observational, etc.",
  "sample_size": "N units (e.g., '1,200 households', '50 schools')",
}}}}

IMPORTANT:
- Return ONLY valid JSON, no additional text
- Use null for any missing values
- Base everything on the provided data
- If authors/timeline/sample_size not in extraction, use null"""

    def __init__(self, config: SummaryConfig):
        """Initialize the paper summarizer.

        Args:
            config: Summary configuration

        Raises:
            SummaryError: If initialization fails

        """
        self.config = config
        logger.info(
            f"Initializing PaperSummarizer with model {config.llm_model} "
            f"(temperature={config.temperature})"
        )

        try:
            # Initialize Anthropic LLM
            # API key can come from config or ANTHROPIC_API_KEY env var
            llm_kwargs = {
                "model": config.llm_model,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
            }
            if config.claude_api_key:
                llm_kwargs["api_key"] = config.claude_api_key

            self.llm = ChatAnthropic(**llm_kwargs)
            logger.info("Successfully initialized LLM client")

        except Exception as e:
            error_msg = f"Failed to initialize LLM client: {e}"
            logger.error(error_msg)
            raise SummaryError(error_msg) from e

    def _load_extraction(self, extraction_path: Path) -> ExtractionResult:
        """Load extraction result from JSON file.

        Args:
            extraction_path: Path to extraction.json file or directory

        Returns:
            Loaded ExtractionResult

        Raises:
            SummaryError: If loading fails

        """
        try:
            # Handle directory path
            if extraction_path.is_dir():
                extraction_path = extraction_path / "extraction.json"

            if not extraction_path.exists():
                raise SummaryError(f"Extraction file not found: {extraction_path}")

            logger.info(f"Loading extraction from {extraction_path}")
            with open(extraction_path) as f:
                data = json.load(f)

            return ExtractionResult.model_validate(data)

        except Exception as e:
            error_msg = f"Failed to load extraction: {e}"
            logger.error(error_msg)
            raise SummaryError(error_msg) from e

    def _load_validation(self, validation_path: Path | None) -> ValidationResult | None:
        """Load validation result from JSON file.

        Args:
            validation_path: Path to validation.json file (optional)

        Returns:
            Loaded ValidationResult or None if not found

        """
        if validation_path is None:
            logger.info("No validation path provided, skipping validation data")
            return None

        try:
            # Handle directory path
            if validation_path.is_dir():
                validation_path = validation_path / "validation.json"

            if not validation_path.exists():
                logger.warning(f"Validation file not found: {validation_path}")
                return None

            logger.info(f"Loading validation from {validation_path}")
            with open(validation_path) as f:
                data = json.load(f)

            return ValidationResult.model_validate(data)

        except Exception as e:
            logger.warning(f"Failed to load validation: {e}")
            return None

    def _format_extraction_data(self, extraction: ExtractionResult) -> str:
        """Format extraction data for LLM prompt.

        Args:
            extraction: Extraction result

        Returns:
            Formatted string representation

        """
        lines = []

        # Paper metadata
        lines.append("## Paper Metadata")
        if extraction.metadata.title:
            lines.append(f"Title: {extraction.metadata.title}")
        if extraction.metadata.authors:
            lines.append(f"Authors: {', '.join(extraction.metadata.authors)}")
        if extraction.metadata.year:
            lines.append(f"Year: {extraction.metadata.year}")
        if extraction.metadata.journal:
            lines.append(f"Journal: {extraction.metadata.journal}")
        if extraction.metadata.abstract:
            lines.append(f"\nAbstract: {extraction.metadata.abstract[:500]}...")

        # Extraction statistics
        lines.append("\n## Extraction Statistics")
        lines.append(f"Tables Extracted: {extraction.tables_extracted}")
        lines.append(f"Figures Extracted: {extraction.figures_extracted}")
        lines.append(f"Extraction Quality: {extraction.extraction_quality:.2f}")

        # Processing info
        if extraction.processing_time_seconds:
            lines.append(f"Processing Time: {extraction.processing_time_seconds:.1f}s")

        return "\n".join(lines)

    def _format_table_data(self, extraction: ExtractionResult) -> str:
        """Format table data for LLM prompt.

        Args:
            extraction: Extraction result

        Returns:
            Formatted string representation of tables

        """
        if not extraction.tables:
            return "No tables extracted."

        lines = []
        for idx, table in enumerate(extraction.tables, 1):
            if isinstance(table, RegressionTable):
                lines.append(f"\n### Table {idx}: Regression Results")
                if table.title:
                    lines.append(f"Title: {table.title}")
                if table.table_number:
                    lines.append(f"Table Number: {table.table_number}")
                lines.append(f"Models: {len(table.models)}")

                # Show first model as example
                if table.models:
                    model = table.models[0]
                    lines.append(f"\nExample Model ({model.model_name}):")
                    if model.dependent_variable:
                        lines.append(
                            f"  Dependent Variable: {model.dependent_variable}"
                        )
                    lines.append(f"  Coefficients: {len(model.coefficients)}")

                    # Show first few coefficients
                    for coef in model.coefficients[:3]:
                        coef_str = f"  - {coef.variable_name}"
                        if coef.coefficient is not None:
                            coef_str += f": {coef.coefficient:.4f}"
                        if coef.std_error is not None:
                            coef_str += f" (SE: {coef.std_error:.4f})"
                        lines.append(coef_str)

                    if len(model.coefficients) > 3:
                        lines.append(
                            f"  ... and {len(model.coefficients) - 3} more coefficients"
                        )

            elif isinstance(table, SummaryStatisticsTable):
                lines.append(f"\n### Table {idx}: Summary Statistics")
                if table.title:
                    lines.append(f"Title: {table.title}")
                lines.append(f"Variables: {len(table.statistics)}")

            elif isinstance(table, BalanceTable):
                lines.append(f"\n### Table {idx}: Balance Table")
                if table.title:
                    lines.append(f"Title: {table.title}")
                lines.append(f"Comparisons: {len(table.comparisons)}")

        return "\n".join(lines)

    def _format_validation_data(
        self, validation: ValidationResult | None
    ) -> tuple[str, str, str, float]:
        """Format validation data for LLM prompt.

        Args:
            validation: Validation result or None

        Returns:
            Tuple of (validation_score, issues_text, recommendations_text, score_float)

        """
        if validation is None:
            return "N/A", "No validation data available", "None", 0.0

        # Format issues
        issues_lines = []
        for issue in validation.issues[:10]:  # Limit to first 10
            issues_lines.append(f"- {issue.message}")
        if len(validation.issues) > 10:
            issues_lines.append(f"... and {len(validation.issues) - 10} more issues")
        issues_text = "\n".join(issues_lines) if issues_lines else "None"

        # Format recommendations
        rec_lines = []
        for rec in validation.recommendations[:5]:  # Limit to first 5
            rec_lines.append(f"- {rec}")
        if len(validation.recommendations) > 5:
            rec_lines.append(
                f"... and {len(validation.recommendations) - 5} more recommendations"
            )
        rec_text = "\n".join(rec_lines) if rec_lines else "None"

        return f"{validation.score:.2f}", issues_text, rec_text, validation.score

    def _remove_appendices(self, content: str) -> str:
        """Remove appendix and reference sections from markdown.

        Args:
            content: Markdown content

        Returns:
            Content with appendices removed

        """
        import re

        # Pattern to match appendix/reference sections
        # Matches: # Appendix, ## References, ### Bibliography, etc.
        pattern = r"\n#+\s+(Appendix|Appendices|References|Bibliography|Works Cited|Literature Cited).*$"

        match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            # Remove everything from the appendix onwards
            truncated = content[: match.start()]
            removed_chars = len(content) - len(truncated)
            logger.info(
                f"Removed appendix/references section ({removed_chars} chars, "
                f"{removed_chars / len(content) * 100:.1f}%)"
            )
            return truncated + "\n\n[Appendix and references removed]"

        return content

    def _remove_markdown_tables(self, content: str) -> str:
        """Remove markdown table content while preserving captions.

        Args:
            content: Markdown content

        Returns:
            Content with table content removed

        """
        lines = content.split("\n")
        result_lines = []
        in_table = False
        tables_removed = 0
        chars_removed = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Check if this is a table row (contains | and is not a code block)
            is_table_row = "|" in line and not line.strip().startswith("```")

            if is_table_row:
                if not in_table:
                    # Starting a new table
                    in_table = True
                    tables_removed += 1
                    result_lines.append("[Table content removed - see extraction data]")

                # Skip this table line
                chars_removed += len(line) + 1  # +1 for newline

            else:
                if in_table:
                    # Ending a table
                    in_table = False

                # Keep non-table lines
                result_lines.append(line)

            i += 1

        if tables_removed > 0:
            logger.info(
                f"Removed {tables_removed} markdown tables ({chars_removed} chars, "
                f"{chars_removed / len(content) * 100:.1f}%)"
            )

        return "\n".join(result_lines)

    def _smart_truncate_markdown(self, content: str, max_chars: int) -> str:
        """Intelligently truncate markdown while preserving important content.

        Args:
            content: Markdown content
            max_chars: Maximum character limit

        Returns:
            Truncated content

        """
        original_length = len(content)

        if original_length <= max_chars:
            return content

        logger.info(
            f"Markdown exceeds limit ({original_length} chars > {max_chars}), "
            "applying smart truncation"
        )

        # Tier 1: Remove appendices and references (usually 20-40% savings)
        content = self._remove_appendices(content)

        if len(content) <= max_chars:
            logger.info(
                f"After removing appendices: {len(content)} chars "
                f"({(1 - len(content) / original_length) * 100:.1f}% reduction)"
            )
            return content

        # Tier 2: Remove markdown tables (keep captions, 30-50% savings)
        content = self._remove_markdown_tables(content)

        if len(content) <= max_chars:
            logger.info(
                f"After removing tables: {len(content)} chars "
                f"({(1 - len(content) / original_length) * 100:.1f}% reduction)"
            )
            return content

        # Tier 3: Hard truncate at section boundary
        logger.warning(
            f"Still over limit after smart truncation ({len(content)} chars), "
            "applying hard truncation"
        )

        # Try to find last section header before max_chars
        import re

        truncate_pos = max_chars
        section_matches = list(re.finditer(r"\n#+\s+", content[:max_chars]))

        if section_matches:
            # Truncate at last section before limit
            truncate_pos = section_matches[-1].start()
            logger.info(f"Truncating at section boundary (position {truncate_pos})")

        content = content[:truncate_pos] + "\n\n[... truncated ...]"

        logger.info(
            f"Final size: {len(content)} chars "
            f"({(1 - len(content) / original_length) * 100:.1f}% reduction)"
        )

        return content

    def _load_markdown_text(
        self, extraction: ExtractionResult, extraction_path: Path
    ) -> str:
        """Load full markdown text from extraction.

        Args:
            extraction: Extraction result
            extraction_path: Path to extraction.json (used to find markdown file)

        Returns:
            Full markdown text or empty string if not found

        """
        try:
            # Construct markdown path: same directory as extraction.json
            # with filename {paper_id}.md
            if extraction_path.name == "extraction.json":
                markdown_dir = extraction_path.parent
            else:
                markdown_dir = extraction_path

            markdown_path = markdown_dir / f"{extraction.paper_id}.md"

            if not markdown_path.exists():
                logger.warning(f"Markdown file not found: {markdown_path}")
                return ""

            logger.info(f"Loading markdown text from {markdown_path}")
            with open(markdown_path, encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Loaded markdown: {len(content)} characters")

            # Apply smart truncation if needed (limit: 100k chars)
            content = self._smart_truncate_markdown(content, max_chars=100000)

            logger.info(f"Final markdown size: {len(content)} characters")
            return content

        except Exception as e:
            logger.warning(f"Failed to load markdown text: {e}")
            return ""

    def _generate_summary(
        self,
        extraction: ExtractionResult,
        validation: ValidationResult | None,
        extraction_path: Path,
        pdf_path: Path | None = None,
    ) -> dict[str, Any]:
        """Generate summary using LLM.

        Args:
            extraction: Extraction result
            validation: Validation result (optional)
            extraction_path: Path to extraction.json (for finding markdown file)
            pdf_path: Optional path to original PDF for direct analysis

        Returns:
            Dictionary with summary data

        Raises:
            LLMError: If LLM call fails
            SummaryError: If response parsing fails

        """
        logger.info("Generating summary with LLM")

        # Format data for prompt
        extraction_data = self._format_extraction_data(extraction)
        table_data = self._format_table_data(extraction)
        validation_score, issues_text, rec_text, score_float = (
            self._format_validation_data(validation)
        )

        # Load full markdown text from extraction
        markdown_text = self._load_markdown_text(extraction, extraction_path)

        # Build prompt with markdown text
        prompt_text = self.SUMMARY_TEMPLATE.format(
            extraction_data=extraction_data,
            validation_score=validation_score,
            extraction_quality=f"{extraction.extraction_quality:.2f}",
            validation_issues=issues_text,
            validation_recommendations=rec_text,
            table_data=table_data,
        )

        # Add full paper text if available
        # Escape curly braces in markdown text to avoid LangChain template errors
        if markdown_text:
            # Replace single { and } with {{ and }} to escape them
            escaped_markdown = markdown_text.replace("{", "{{").replace("}", "}}")
            prompt_text += f"\n\n# FULL PAPER TEXT\n\n{escaped_markdown}"

        # Create prompt messages
        messages = [
            ("system", self.SYSTEM_PROMPT),
            ("human", prompt_text),
        ]

        # If PDF provided, include it directly using Claude's PDF support
        if pdf_path and pdf_path.exists():
            logger.info(f"Including PDF file directly: {pdf_path}")
            # Read PDF as base64
            import base64

            with open(pdf_path, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Add PDF to messages using Claude's document format
            messages = [
                ("system", self.SYSTEM_PROMPT),
                (
                    "human",
                    [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                        {"type": "text", "text": prompt_text},
                    ],
                ),
            ]

        prompt = ChatPromptTemplate.from_messages(messages)

        try:
            # Call LLM
            logger.info("Calling LLM API")
            chain = prompt | self.llm
            response = chain.invoke({})

            # Parse JSON response
            content = response.content
            if isinstance(content, list):
                # Handle case where content is a list of content blocks
                content = " ".join(str(block) for block in content)

            logger.info(f"Received response: {len(content)} characters")

            # Extract JSON from response (may have markdown code blocks)
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                json_str = json_match.group(0) if json_match else content

            summary_data = json.loads(json_str)
            logger.info("Successfully parsed LLM response")

            return summary_data

        except Exception as e:
            error_msg = f"LLM call or response parsing failed: {e}"
            logger.error(error_msg)
            raise LLMError(error_msg) from e

    def summarize(
        self,
        extraction_path: Path,
        validation_path: Path | None = None,
        pdf_path: Path | None = None,
    ) -> SummaryResult:
        """Generate summary from extraction and validation artifacts.

        Args:
            extraction_path: Path to extraction.json or directory containing it
            validation_path: Optional path to validation.json
            pdf_path: Optional path to original PDF (for future PDF analysis feature)

        Returns:
            SummaryResult with complete summary

        Raises:
            SummaryError: If summarization fails

        """
        start_time = time.time()
        logger.info(f"Starting summarization for {extraction_path}")

        try:
            # Load artifacts
            extraction = self._load_extraction(Path(extraction_path))
            validation = self._load_validation(
                Path(validation_path) if validation_path else None
            )

            # Generate LLM summary
            summary_data = self._generate_summary(
                extraction, validation, Path(extraction_path), pdf_path
            )

            # Create SummaryResult (handle null values for list fields)
            result = SummaryResult(
                paper_id=extraction.paper_id,
                source_extraction=Path(extraction_path),
                # Core summary from LLM
                title=summary_data.get("title"),
                overview=summary_data.get("overview"),
                research_question=summary_data.get("research_question"),
                methodology=summary_data.get("methodology"),
                sample_info=summary_data.get("sample_size"),  # Map to sample_info
                treatment_info=summary_data.get("treatment_info"),
                assignment=summary_data.get("assignment"),
                key_findings=summary_data.get("key_findings") or [],
                implications=summary_data.get("implications"),
                # Metadata from LLM
                authors=summary_data.get("authors") or [],
                institutions=summary_data.get("institutions") or [],
                timeline=summary_data.get("timeline"),
                study_status=summary_data.get("study_status"),
                study_type=summary_data.get("study_type"),
                sample_size=summary_data.get("sample_size"),
                # Extraction/validation metrics
                extraction_quality=extraction.extraction_quality,
                validation_score=validation.score if validation else 0.0,
                validation_issues=[issue.message for issue in validation.issues[:10]]
                if validation
                else [],
                recommendations=validation.recommendations[:5] if validation else [],
                # Generation metadata
                llm_model=self.config.llm_model,
                llm_temperature=self.config.temperature,
                generation_config=self.config.to_safe_dict(),
                web_search_used=False,  # TODO: Implement web search
                processing_time_seconds=time.time() - start_time,
            )

            # Update generation config with PDF usage
            if pdf_path and pdf_path.exists():
                result.generation_config["pdf_included"] = True
                result.generation_config["pdf_path"] = str(pdf_path)

            logger.info(
                f"Summary generation complete in {result.processing_time_seconds:.1f}s"
            )
            return result

        except Exception as e:
            error_msg = f"Summarization failed: {e}"
            logger.error(error_msg)
            raise SummaryError(error_msg) from e
