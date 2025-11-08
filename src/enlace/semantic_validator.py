"""Semantic validation engine for cross-checking parsed table values.

This module provides validation functionality to cross-check numerically
parsed values against paper text using RAG, catching OCR errors and
ensuring data quality.
"""

import logging
import re
from typing import Any

from augmentation_config import AugmentationConfig
from context_models import ValidationResult
from semantic_search import SemanticSearchPipeline

logger = logging.getLogger(__name__)


class SemanticValidator:
    """Validates parsed numerical values against paper text using RAG.

    Cross-checks parsed table values with semantic search to catch
    OCR errors, parsing mistakes, and ensure data integrity.
    """

    def __init__(
        self,
        config: AugmentationConfig | None = None,
        search_pipeline: SemanticSearchPipeline | None = None,
    ):
        """Initialize semantic validator.

        Args:
            config: Augmentation configuration. Uses defaults if None.
            search_pipeline: Optional shared search pipeline. Creates new if None.

        """
        self.config = config or AugmentationConfig()
        self.search = search_pipeline or SemanticSearchPipeline(config=self.config)

        # Validation thresholds
        self.exact_match_threshold = 0.001  # For relative differences
        self.close_match_threshold = 0.05  # 5% tolerance
        self.warning_threshold = 0.10  # 10% tolerance

        logger.info("SemanticValidator initialized")

    async def validate_coefficient(
        self,
        variable_name: str,
        parsed_value: float,
        table_id: str | None = None,
        standard_error: float | None = None,
    ) -> ValidationResult:
        """Validate regression coefficient value against paper text.

        Args:
            variable_name: Name of variable (e.g., "treatment_effect")
            parsed_value: Coefficient value extracted by parser
            table_id: Optional table identifier for context
            standard_error: Optional SE value for additional validation

        Returns:
            ValidationResult with match status and confidence

        """
        logger.debug(
            f"Validating coefficient: {variable_name}={parsed_value} (table={table_id})"
        )

        # Build search query
        table_context = f" in {table_id}" if table_id else ""
        query = (
            f"What is the regression coefficient for '{variable_name}'{table_context}?"
        )

        # Perform semantic QA
        qa_result = await self.search.semantic_qa(query, k=5)
        answer_text = qa_result["answer"]
        base_confidence = qa_result["confidence"]

        # Extract numerical value from answer
        rag_value = self._extract_number_from_text(answer_text)

        # Calculate match metrics
        if rag_value is not None and parsed_value is not None:
            matches, discrepancy, relative_disc = self._compare_values(
                parsed_value, rag_value
            )

            logger.debug(
                f"Value comparison: parsed={parsed_value:.4f}, "
                f"rag={rag_value:.4f}, "
                f"relative_diff={relative_disc:.2%}"
            )
        else:
            matches = rag_value is None and parsed_value is None
            discrepancy = None
            relative_disc = None
            logger.debug("Could not extract numerical value from RAG answer")

        # Adjust confidence based on match quality
        final_confidence = self._adjust_confidence_for_match(
            base_confidence, matches, relative_disc
        )

        # Extract source info
        source_text, source_page = self._extract_source_info(qa_result)

        return ValidationResult(
            parsed_value=parsed_value,
            rag_extracted_value=rag_value,
            matches=matches,
            discrepancy_size=discrepancy,
            relative_discrepancy=relative_disc,
            confidence=final_confidence,
            source_text=source_text,
            source_page=source_page,
        )

    async def validate_summary_statistic(
        self,
        variable_name: str,
        statistic_type: str,
        parsed_value: float,
        group: str | None = None,
    ) -> ValidationResult:
        """Validate summary statistic against paper text.

        Args:
            variable_name: Name of variable
            statistic_type: Type of statistic (mean, std, min, max, etc.)
            parsed_value: Value extracted by parser
            group: Optional group identifier (treatment, control, etc.)

        Returns:
            ValidationResult with match status and confidence

        """
        logger.debug(
            f"Validating summary stat: {statistic_type}({variable_name})={parsed_value}"
        )

        # Build search query
        group_context = f" for {group}" if group else ""
        query = (
            f"What is the {statistic_type} of '{variable_name}'{group_context} "
            f"in the summary statistics?"
        )

        # Perform semantic QA
        qa_result = await self.search.semantic_qa(query, k=5)
        answer_text = qa_result["answer"]
        base_confidence = qa_result["confidence"]

        # Extract value
        rag_value = self._extract_number_from_text(answer_text)

        # Compare values
        if rag_value is not None and parsed_value is not None:
            matches, discrepancy, relative_disc = self._compare_values(
                parsed_value, rag_value
            )
        else:
            matches = rag_value is None and parsed_value is None
            discrepancy = None
            relative_disc = None

        final_confidence = self._adjust_confidence_for_match(
            base_confidence, matches, relative_disc
        )
        source_text, source_page = self._extract_source_info(qa_result)

        return ValidationResult(
            parsed_value=parsed_value,
            rag_extracted_value=rag_value,
            matches=matches,
            discrepancy_size=discrepancy,
            relative_discrepancy=relative_disc,
            confidence=final_confidence,
            source_text=source_text,
            source_page=source_page,
        )

    async def validate_sample_size(
        self, parsed_value: int, group: str | None = None
    ) -> ValidationResult:
        """Validate sample size against paper text.

        Args:
            parsed_value: Sample size extracted by parser
            group: Optional group identifier

        Returns:
            ValidationResult with match status and confidence

        """
        logger.debug(f"Validating sample size: {parsed_value} (group={group})")

        group_context = f" for {group}" if group else ""
        query = f"What is the sample size{group_context}?"

        qa_result = await self.search.semantic_qa(query, k=5)
        answer_text = qa_result["answer"]
        base_confidence = qa_result["confidence"]

        rag_value = self._extract_number_from_text(answer_text)

        if rag_value is not None and parsed_value is not None:
            matches, discrepancy, relative_disc = self._compare_values(
                float(parsed_value), rag_value
            )
        else:
            matches = rag_value is None and parsed_value is None
            discrepancy = None
            relative_disc = None

        final_confidence = self._adjust_confidence_for_match(
            base_confidence, matches, relative_disc
        )
        source_text, source_page = self._extract_source_info(qa_result)

        return ValidationResult(
            parsed_value=parsed_value,
            rag_extracted_value=int(rag_value) if rag_value else None,
            matches=matches,
            discrepancy_size=discrepancy,
            relative_discrepancy=relative_disc,
            confidence=final_confidence,
            source_text=source_text,
            source_page=source_page,
        )

    async def batch_validate_coefficients(
        self, coefficients: list[dict[str, Any]], table_id: str | None = None
    ) -> dict[str, ValidationResult]:
        """Validate multiple coefficients efficiently.

        Args:
            coefficients: List of coefficient dicts with 'variable' and 'value' keys
            table_id: Optional table identifier for context

        Returns:
            Dictionary mapping variable names to ValidationResults

        """
        logger.info(f"Batch validating {len(coefficients)} coefficients")

        results = {}
        for coef in coefficients:
            var_name = coef.get("variable")
            value = coef.get("value")
            se = coef.get("standard_error")

            if var_name and value is not None:
                result = await self.validate_coefficient(var_name, value, table_id, se)
                results[var_name] = result

        # Log summary
        match_count = sum(1 for r in results.values() if r.matches)
        logger.info(
            f"Validation complete: {match_count}/{len(results)} values match "
            f"({match_count / len(results) * 100:.1f}%)"
        )

        return results

    def _extract_number_from_text(self, text: str) -> float | None:
        """Extract numerical value from text.

        Args:
            text: Text containing a number

        Returns:
            Extracted float value or None if not found

        """
        if not text:
            return None

        # Remove common words that might interfere
        cleaned = text.lower().replace("approximately", "").replace("about", "")

        # Pattern for scientific notation and decimal numbers
        patterns = [
            r"[-+]?\d*\.?\d+[eE][-+]?\d+",  # Scientific notation
            r"[-+]?\d+\.\d+",  # Decimal number
            r"[-+]?\d+",  # Integer
        ]

        for pattern in patterns:
            matches = re.findall(pattern, cleaned)
            if matches:
                try:
                    # Return first valid number found
                    return float(matches[0])
                except ValueError:
                    continue

        return None

    def _compare_values(
        self, parsed: float, rag: float
    ) -> tuple[bool, float | None, float | None]:
        """Compare parsed and RAG-extracted values.

        Args:
            parsed: Value from parser
            rag: Value from RAG extraction

        Returns:
            Tuple of (matches, absolute_discrepancy, relative_discrepancy)

        """
        if parsed is None or rag is None:
            return False, None, None

        # Handle exact zeros
        if abs(parsed) < 1e-10 and abs(rag) < 1e-10:
            return True, 0.0, 0.0

        # Calculate discrepancies
        abs_discrepancy = abs(parsed - rag)

        # Use larger value as denominator for relative difference
        denominator = max(abs(parsed), abs(rag))
        relative_discrepancy = abs_discrepancy / denominator if denominator > 0 else 0.0

        # Determine match
        matches = relative_discrepancy <= self.close_match_threshold

        return matches, abs_discrepancy, relative_discrepancy

    def _adjust_confidence_for_match(
        self, base_confidence: float, matches: bool, relative_disc: float | None
    ) -> float:
        """Adjust confidence score based on match quality.

        Args:
            base_confidence: Base confidence from semantic QA
            matches: Whether values match within threshold
            relative_disc: Relative discrepancy if available

        Returns:
            Adjusted confidence score (0-1)

        """
        if not matches:
            # Penalize mismatches
            if relative_disc is not None:
                if relative_disc > self.warning_threshold:
                    # Major discrepancy
                    return base_confidence * 0.3
                # Minor discrepancy
                return base_confidence * 0.6

            # No RAG value found
            return base_confidence * 0.5

        # Boost confidence for good matches
        if relative_disc is not None and relative_disc <= self.exact_match_threshold:
            # Exact match
            return min(1.0, base_confidence * 1.2)

        # Close match
        return min(1.0, base_confidence * 1.1)

    def _extract_source_info(self, qa_result: dict) -> tuple[str | None, int | None]:
        """Extract source text and page number from QA result.

        Args:
            qa_result: Result dict from semantic_qa

        Returns:
            Tuple of (source_text, source_page)

        """
        source_chunks = qa_result.get("source_chunks", [])

        if source_chunks:
            # Use first source chunk
            first_chunk = source_chunks[0]
            return (
                first_chunk.get("text", None),
                first_chunk.get("page", None),
            )

        return None, None

    async def validate_table_summary(
        self, table_data: dict[str, Any], table_id: str
    ) -> dict[str, Any]:
        """Generate validation summary for entire table.

        Args:
            table_data: Parsed table data
            table_id: Table identifier

        Returns:
            Dictionary with validation statistics and flagged issues

        """
        logger.info(f"Generating validation summary for {table_id}")

        results = {
            "table_id": table_id,
            "total_values_checked": 0,
            "matches": 0,
            "mismatches": 0,
            "missing_validations": 0,
            "flagged_issues": [],
            "average_confidence": 0.0,
        }

        # Extract and validate coefficients if regression table
        if "models" in table_data:
            all_coefficients = []
            for model in table_data["models"]:
                if "coefficients" in model:
                    all_coefficients.extend(model["coefficients"])

            validation_results = await self.batch_validate_coefficients(
                all_coefficients, table_id
            )

            results["total_values_checked"] = len(validation_results)
            results["matches"] = sum(
                1 for r in validation_results.values() if r.matches
            )
            results["mismatches"] = results["total_values_checked"] - results["matches"]

            # Calculate average confidence
            confidences = [r.confidence for r in validation_results.values()]
            if confidences:
                results["average_confidence"] = sum(confidences) / len(confidences)

            # Flag issues
            for var_name, val_result in validation_results.items():
                if (
                    not val_result.matches
                    and val_result.relative_discrepancy
                    and val_result.relative_discrepancy > self.warning_threshold
                ):
                    results["flagged_issues"].append(
                        {
                            "variable": var_name,
                            "parsed_value": val_result.parsed_value,
                            "rag_value": val_result.rag_extracted_value,
                            "discrepancy": f"{val_result.relative_discrepancy:.1%}",
                            "severity": "high",
                        }
                    )

        logger.info(
            f"Validation summary: {results['matches']}/{results['total_values_checked']} "
            f"matches, {len(results['flagged_issues'])} issues flagged"
        )

        return results

    def reset(self) -> None:
        """Reset validator state."""
        self.search.reset()
        logger.info("SemanticValidator reset")
