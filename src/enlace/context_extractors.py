"""Context extractors for semantic table augmentation.

This module provides specialized extractors that use semantic search
to extract rich contextual information from research papers.
"""

import logging
import re
from typing import Any

from enlace.context_models import (
    MethodsContext,
    OutcomeContext,
    StudyContext,
    TreatmentContext,
    VariableContext,
)
from enlace.semantic_search import SemanticSearchPipeline

logger = logging.getLogger(__name__)


class VariableContextExtractor:
    """Extract semantic context for variables using targeted questions.

    Uses semantic search to find and extract detailed information
    about what variables measure, their units, and data sources.
    """

    def __init__(self, semantic_search: SemanticSearchPipeline):
        """Initialize variable context extractor.

        Args:
            semantic_search: Configured semantic search pipeline

        """
        self.search = semantic_search

    async def extract_context(
        self, variable_name: str, table_context: str | None = None
    ) -> VariableContext:
        """Extract semantic context for a variable.

        Args:
            variable_name: Name of the variable
            table_context: Optional context about which table this is from

        Returns:
            VariableContext with extracted information

        """
        logger.info(f"Extracting context for variable: {variable_name}")

        # Build context-aware questions
        context_suffix = f" in {table_context}" if table_context else ""

        questions = [
            f"What does the variable '{variable_name}' measure{context_suffix}?",
            f"How is the variable '{variable_name}' defined or operationalized{context_suffix}?",
            f"What are the units of measurement for '{variable_name}'{context_suffix}?",
            f"What is the data source for '{variable_name}'{context_suffix}?",
        ]

        # Get answers concurrently
        results = await self.search.batch_qa(questions, k=3)

        # Extract field values from answers
        definition = self._extract_answer(results[0])
        measurement_method = self._extract_answer(results[1])
        units = self._extract_answer(results[2])
        data_source = self._extract_answer(results[3])

        # Collect source sections
        source_sections = self._collect_source_sections(results)

        # Calculate average confidence
        confidences = [r["confidence"] for r in results if r["confidence"] > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return VariableContext(
            variable_name=variable_name,
            definition=definition,
            units=units,
            measurement_method=measurement_method,
            data_source=data_source,
            source_sections=source_sections,
            confidence=avg_confidence,
        )

    def _extract_answer(self, qa_result: dict[str, Any]) -> str | None:
        """Extract clean answer from QA result.

        Args:
            qa_result: QA result dict

        Returns:
            Extracted answer or None if not found

        """
        answer = qa_result.get("answer")

        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
            "not specified",
        ]:
            return None

        return answer.strip()

    def _collect_source_sections(self, qa_results: list[dict]) -> list[str]:
        """Collect unique source sections from multiple QA results.

        Args:
            qa_results: List of QA result dicts

        Returns:
            List of unique source section references

        """
        sections = set()

        for result in qa_results:
            for chunk in result.get("source_chunks", []):
                page = chunk.get("page")
                if page:
                    sections.add(f"page {page}")

        return sorted(sections)


class TreatmentContextExtractor:
    """Extract treatment/intervention descriptions via semantic search."""

    def __init__(self, semantic_search: SemanticSearchPipeline):
        """Initialize treatment context extractor.

        Args:
            semantic_search: Configured semantic search pipeline

        """
        self.search = semantic_search

    async def extract_treatment_arms(self) -> list[TreatmentContext]:
        """Extract all treatment arm descriptions.

        Returns:
            List of TreatmentContext for each arm (treatment, control, etc.)

        """
        logger.debug("Extracting treatment arm contexts")

        # Extract individual arms
        questions = [
            "What did the treatment group receive? Describe the intervention in detail.",
            "What did the control group receive? Describe in detail.",
            "What was the duration of the intervention?",
            "What was the dosage, intensity, or frequency of the intervention?",
            "How was the intervention delivered to participants?",
            "When did the intervention occur (dates, timeline)?",
        ]

        results = await self.search.batch_qa(questions, k=3)

        # Parse treatment context
        treatment_context = TreatmentContext(
            arm_name="Treatment",
            description=self._extract_answer(results[0]),
            duration=self._extract_answer(results[2]),
            intensity=self._extract_answer(results[3]),
            delivery_mechanism=self._extract_answer(results[4]),
            timing=self._extract_answer(results[5]),
            source_sections=self._collect_source_sections(results),
            confidence=self._average_confidence(results),
        )

        # Parse control context
        control_context = TreatmentContext(
            arm_name="Control",
            description=self._extract_answer(results[1]),
            source_sections=self._collect_source_sections([results[1]]),
            confidence=results[1].get("confidence", 0.0),
        )

        arms = [treatment_context, control_context]

        # Filter out arms with no description
        arms = [arm for arm in arms if arm.description is not None]

        logger.info(f"Extracted {len(arms)} treatment arms")

        return arms

    def _extract_answer(self, qa_result: dict[str, Any]) -> str | None:
        """Extract clean answer from QA result."""
        answer = qa_result.get("answer")

        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
        ]:
            return None

        return answer.strip()

    def _collect_source_sections(self, qa_results: list[dict]) -> list[str]:
        """Collect unique source sections."""
        sections = set()

        for result in qa_results:
            for chunk in result.get("source_chunks", []):
                page = chunk.get("page")
                if page:
                    sections.add(f"page {page}")

        return sorted(sections)

    def _average_confidence(self, qa_results: list[dict]) -> float:
        """Calculate average confidence from multiple results."""
        confidences = [
            r.get("confidence", 0.0) for r in qa_results if r.get("confidence", 0) > 0
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0


class StudyContextExtractor:
    """Extract study design and sample context via semantic search."""

    def __init__(self, semantic_search: SemanticSearchPipeline):
        """Initialize study context extractor.

        Args:
            semantic_search: Configured semantic search pipeline

        """
        self.search = semantic_search

    async def extract_study_context(self) -> StudyContext:
        """Extract overall study design and sample context.

        Returns:
            StudyContext with study design details

        """
        logger.debug("Extracting study context")

        questions = [
            "What type of study design was used (RCT, quasi-experimental, observational)?",
            "What was the total sample size for this study?",
            "What was the study population? Who were the participants?",
            "What was the unit of randomization (if RCT)?",
            "What was the geographic setting and location of the study?",
            "What was the time period of data collection?",
            "What were the inclusion criteria for participants?",
            "What were the exclusion criteria for participants?",
            "What was the attrition or dropout rate?",
        ]

        results = await self.search.batch_qa(questions, k=3)

        # Extract sample size (needs special parsing)
        sample_size = self._extract_sample_size(results[1])

        # Extract attrition rate (needs special parsing)
        attrition_rate = self._extract_rate(results[8])

        # Extract inclusion/exclusion criteria (may be lists)
        inclusion_criteria = self._extract_criteria_list(results[6])
        exclusion_criteria = self._extract_criteria_list(results[7])

        return StudyContext(
            study_design=self._extract_answer(results[0]),
            sample_size=sample_size,
            population_description=self._extract_answer(results[2]),
            randomization_unit=self._extract_answer(results[3]),
            geographic_setting=self._extract_answer(results[4]),
            time_period=self._extract_answer(results[5]),
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            attrition_rate=attrition_rate,
            source_sections=self._collect_source_sections(results),
            confidence=self._average_confidence(results),
        )

    def _extract_answer(self, qa_result: dict[str, Any]) -> str | None:
        """Extract clean answer from QA result."""
        answer = qa_result.get("answer")

        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
        ]:
            return None

        return answer.strip()

    def _extract_sample_size(self, qa_result: dict[str, Any]) -> int | None:
        """Extract sample size number from answer."""
        answer = self._extract_answer(qa_result)

        if not answer:
            return None

        # Look for numbers in answer
        numbers = re.findall(r"\d[\d,]*", answer)

        if numbers:
            # Take largest number (likely total sample size)
            sample_sizes = [int(n.replace(",", "")) for n in numbers]
            return max(sample_sizes)

        return None

    def _extract_rate(self, qa_result: dict[str, Any]) -> float | None:
        """Extract rate (percentage or proportion) from answer."""
        answer = self._extract_answer(qa_result)

        if not answer:
            return None

        # Look for percentages or proportions
        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", answer)
        if percent_match:
            return float(percent_match.group(1)) / 100

        # Look for decimal proportions (0.15, etc.)
        decimal_match = re.search(r"0\.\d+", answer)
        if decimal_match:
            return float(decimal_match.group())

        return None

    def _extract_criteria_list(self, qa_result: dict[str, Any]) -> list[str]:
        """Extract list of criteria from answer."""
        answer = self._extract_answer(qa_result)

        if not answer:
            return []

        # Try to split by common list patterns
        # Look for numbered lists: 1. 2. or (1) (2)
        numbered = re.split(r"\d+\.\s+|\(\d+\)\s+", answer)
        if len(numbered) > 2:  # At least 2 items
            return [item.strip() for item in numbered if item.strip()]

        # Look for bulleted lists: - or •
        bulleted = re.split(r"[-•]\s+", answer)
        if len(bulleted) > 1:
            return [item.strip() for item in bulleted if item.strip()]

        # Return as single item if no list structure
        return [answer]

    def _collect_source_sections(self, qa_results: list[dict]) -> list[str]:
        """Collect unique source sections."""
        sections = set()

        for result in qa_results:
            for chunk in result.get("source_chunks", []):
                page = chunk.get("page")
                if page:
                    sections.add(f"page {page}")

        return sorted(sections)

    def _average_confidence(self, qa_results: list[dict]) -> float:
        """Calculate average confidence."""
        confidences = [
            r.get("confidence", 0.0) for r in qa_results if r.get("confidence", 0) > 0
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0


class MethodsContextExtractor:
    """Extract statistical methods context for specific tables."""

    def __init__(self, semantic_search: SemanticSearchPipeline):
        """Initialize methods context extractor.

        Args:
            semantic_search: Configured semantic search pipeline

        """
        self.search = semantic_search

    async def extract_methods_for_table(
        self, table_caption: str, table_number: str | None = None
    ) -> MethodsContext:
        """Extract statistical methods context for a specific table.

        Args:
            table_caption: Caption/title of the table
            table_number: Table number (e.g., "Table 3")

        Returns:
            MethodsContext with statistical methods details

        """
        logger.debug(
            f"Extracting methods context for {table_number or 'table'}: {table_caption[:50]}..."
        )

        table_ref = table_number or "this table"

        questions = [
            f"What statistical estimation method was used for {table_ref}?",
            f"What type of standard errors were used in {table_ref}?",
            f"What control variables or covariates were included in {table_ref}?",
            f"Were fixed effects used in {table_ref}? If so, which ones?",
            f"How was missing data handled in the analysis for {table_ref}?",
            "What statistical software was used?",
        ]

        results = await self.search.batch_qa(questions, k=3)

        # Extract control variables (may be a list)
        control_variables = self._extract_variable_list(results[2])

        # Extract fixed effects (may be a list)
        fixed_effects = self._extract_variable_list(results[3])

        # Extract clustering variable from SE type answer
        se_answer = self._extract_answer(results[1])
        clustering_variable = self._extract_clustering_variable(se_answer)

        return MethodsContext(
            estimation_method=self._extract_answer(results[0]),
            standard_error_type=se_answer,
            clustering_variable=clustering_variable,
            control_variables=control_variables,
            fixed_effects=fixed_effects,
            missing_data_handling=self._extract_answer(results[4]),
            software=self._extract_answer(results[5]),
            source_sections=self._collect_source_sections(results),
            confidence=self._average_confidence(results),
        )

    def _extract_answer(self, qa_result: dict[str, Any]) -> str | None:
        """Extract clean answer from QA result."""
        answer = qa_result.get("answer")

        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
        ]:
            return None

        return answer.strip()

    def _extract_variable_list(self, qa_result: dict[str, Any]) -> list[str]:
        """Extract list of variables from answer."""
        answer = self._extract_answer(qa_result)

        if not answer or "no" in answer.lower():
            return []

        # Common separators for variable lists
        separators = [",", ";", " and ", "&"]

        for sep in separators:
            if sep in answer:
                variables = answer.split(sep)
                return [v.strip() for v in variables if v.strip()]

        # Return as single item if no list structure
        return [answer]

    def _extract_clustering_variable(self, se_answer: str | None) -> str | None:
        """Extract clustering variable from standard error description."""
        if not se_answer:
            return None

        # Look for "clustered at X" or "clustered by X" patterns
        cluster_match = re.search(
            r"cluster(?:ed)?\s+(?:at|by|on)\s+(\w+)", se_answer, re.IGNORECASE
        )

        if cluster_match:
            return cluster_match.group(1)

        return None

    def _collect_source_sections(self, qa_results: list[dict]) -> list[str]:
        """Collect unique source sections."""
        sections = set()

        for result in qa_results:
            for chunk in result.get("source_chunks", []):
                page = chunk.get("page")
                if page:
                    sections.add(f"page {page}")

        return sorted(sections)

    def _average_confidence(self, qa_results: list[dict]) -> float:
        """Calculate average confidence."""
        confidences = [
            r.get("confidence", 0.0) for r in qa_results if r.get("confidence", 0) > 0
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0


class OutcomeContextExtractor:
    """Extract outcome measurement details via semantic search."""

    def __init__(self, semantic_search: SemanticSearchPipeline):
        """Initialize outcome context extractor.

        Args:
            semantic_search: Configured semantic search pipeline

        """
        self.search = semantic_search

    async def extract_outcome_context(
        self, outcome_variable_name: str
    ) -> OutcomeContext:
        """Extract detailed context about outcome measurement.

        Args:
            outcome_variable_name: Name of outcome variable

        Returns:
            OutcomeContext with measurement details

        """
        logger.info(f"Extracting outcome context for: {outcome_variable_name}")

        questions = [
            f"How was the outcome '{outcome_variable_name}' measured?",
            f"What survey instrument or measurement tool was used for '{outcome_variable_name}'?",
            f"What is the scale or range of '{outcome_variable_name}'?",
            f"When was '{outcome_variable_name}' measured (baseline, endline, etc.)?",
            f"How was data for '{outcome_variable_name}' collected?",
        ]

        results = await self.search.batch_qa(questions, k=3)

        return OutcomeContext(
            outcome_variable_name=outcome_variable_name,
            measurement_method=self._extract_answer(results[0]),
            instrument=self._extract_answer(results[1]),
            scale=self._extract_answer(results[2]),
            measurement_timing=self._extract_answer(results[3]),
            data_collection_method=self._extract_answer(results[4]),
            source_sections=self._collect_source_sections(results),
            confidence=self._average_confidence(results),
        )

    def _extract_answer(self, qa_result: dict[str, Any]) -> str | None:
        """Extract clean answer from QA result."""
        answer = qa_result.get("answer")

        if not answer or answer.lower() in [
            "information not found",
            "not found",
            "unknown",
        ]:
            return None

        return answer.strip()

    def _collect_source_sections(self, qa_results: list[dict]) -> list[str]:
        """Collect unique source sections."""
        sections = set()

        for result in qa_results:
            for chunk in result.get("source_chunks", []):
                page = chunk.get("page")
                if page:
                    sections.add(f"page {page}")

        return sorted(sections)

    def _average_confidence(self, qa_results: list[dict]) -> float:
        """Calculate average confidence."""
        confidences = [
            r.get("confidence", 0.0) for r in qa_results if r.get("confidence", 0) > 0
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0
