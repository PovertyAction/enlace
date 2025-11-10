"""Table augmentation engine for semantic context extraction.

This module provides the main orchestrator for augmenting parsed tables
with rich semantic context extracted from research paper text via RAG.
"""

import logging
from pathlib import Path
from typing import Any

from enlace.augmentation_config import AugmentationConfig
from enlace.context_extractors import (
    MethodsContextExtractor,
    OutcomeContextExtractor,
    StudyContextExtractor,
    TreatmentContextExtractor,
    VariableContextExtractor,
)
from enlace.context_models import TableContext
from enlace.semantic_search import SemanticSearchPipeline

logger = logging.getLogger(__name__)


class TableAugmenter:
    """Main orchestrator for semantic table augmentation.

    Coordinates all context extractors to enrich parsed tables with
    semantic information from paper text, enabling better validation,
    harmonization, and replication.
    """

    def __init__(self, config: AugmentationConfig | None = None):
        """Initialize table augmenter.

        Args:
            config: Augmentation configuration. Uses defaults if None.

        """
        self.config = config or AugmentationConfig()

        # Initialize semantic search pipeline
        self.search = SemanticSearchPipeline(config=self.config)

        # Initialize all extractors (lazy - share search pipeline)
        self.variable_extractor = VariableContextExtractor(self.search)
        self.treatment_extractor = TreatmentContextExtractor(self.search)
        self.study_extractor = StudyContextExtractor(self.search)
        self.methods_extractor = MethodsContextExtractor(self.search)
        self.outcome_extractor = OutcomeContextExtractor(self.search)

        # Cache study context (same for all tables in a paper)
        self._study_context_cache: dict[str, Any] = {}
        self._treatment_contexts_cache: dict[str, list] = {}

        logger.info(
            f"TableAugmenter initialized with config: "
            f"augment_variables={self.config.augment_variables}, "
            f"augment_treatments={self.config.augment_treatments}, "
            f"augment_methods={self.config.augment_methods}"
        )

    async def process_document(self, pdf_path: str) -> None:
        """Process PDF document for semantic search.

        Must be called before augmenting tables from this document.

        Args:
            pdf_path: Path to PDF file

        """
        await self.search.process_document(pdf_path)
        logger.info(f"Document processed for augmentation: {Path(pdf_path).name}")

    async def augment_regression_table(
        self,
        table_data: dict[str, Any],
        table_id: str,
        pdf_path: str | None = None,
    ) -> TableContext:
        """Augment regression table with semantic context.

        Args:
            table_data: Parsed regression table data (from parse.py)
            table_id: Table identifier (e.g., "table_3")
            pdf_path: Optional PDF path (if not already processed)

        Returns:
            TableContext with all extracted semantic information

        """
        logger.info(f"Augmenting regression table: {table_id}")

        # Process document if needed
        if pdf_path and self.search.current_document_path != str(Path(pdf_path)):
            await self.process_document(pdf_path)

        # Extract study context (cached per document)
        study_context = await self._get_study_context()

        # Extract treatment contexts (cached per document)
        treatment_contexts = await self._get_treatment_contexts()

        # Extract methods context for this specific table
        methods_context = None
        if self.config.augment_methods:
            methods_context = await self.methods_extractor.extract_methods_for_table(
                table_caption="", table_number=table_id
            )
            logger.debug(
                f"Methods context extracted with confidence: "
                f"{methods_context.confidence:.2f}"
            )

        # Extract variable contexts for coefficients
        variable_contexts = {}
        if self.config.augment_variables:
            variable_names = self._extract_variable_names_from_table(table_data)
            logger.info(f"Extracting context for {len(variable_names)} variables")

            for var_name in variable_names:
                var_context = await self.variable_extractor.extract_context(var_name)

                # Only include if confidence meets threshold
                if (
                    var_context.confidence is not None
                    and var_context.confidence >= self.config.min_confidence_to_include
                ):
                    variable_contexts[var_name] = var_context
                    logger.debug(
                        f"Variable '{var_name}' context: "
                        f"confidence={var_context.confidence:.2f}"
                    )
                else:
                    logger.debug(
                        f"Variable '{var_name}' context excluded "
                        f"(confidence too low: {var_context.confidence:.2f})"
                    )

        # Extract outcome contexts
        outcome_contexts = {}
        outcome_names = self._extract_outcome_names_from_table(table_data)

        for outcome_name in outcome_names:
            outcome_context = await self.outcome_extractor.extract_context(outcome_name)

            # Only include if confidence meets threshold
            if (
                outcome_context.confidence is not None
                and outcome_context.confidence >= self.config.min_confidence_to_include
            ):
                outcome_contexts[outcome_name] = outcome_context
                logger.debug(
                    f"Outcome '{outcome_name}' context: "
                    f"confidence={outcome_context.confidence:.2f}"
                )

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            study_context,
            treatment_contexts,
            variable_contexts,
            outcome_contexts,
            methods_context,
        )

        # Build comprehensive TableContext
        # Get title from Pydantic model or dict
        caption = getattr(table_data, "title", None) or "Regression results"
        if isinstance(table_data, dict):
            caption = table_data.get(
                "title", table_data.get("caption", "Regression results")
            )

        table_context = TableContext(
            table_id=table_id,
            table_description=caption or "Regression results",
            study_context=study_context if self.config.augment_study_context else None,
            treatment_contexts=(
                treatment_contexts if self.config.augment_treatments else []
            ),
            variable_contexts=variable_contexts,
            outcome_contexts=outcome_contexts,
            methods_context=methods_context,
            overall_confidence=overall_confidence,
        )

        logger.info(
            f"Table {table_id} augmented: "
            f"{len(variable_contexts)} variables, "
            f"{len(outcome_contexts)} outcomes, "
            f"confidence={overall_confidence:.2f}"
        )

        return table_context

    async def augment_summary_stats_table(
        self,
        table_data: dict[str, Any],
        table_id: str,
        pdf_path: str | None = None,
    ) -> TableContext:
        """Augment summary statistics table with semantic context.

        Args:
            table_data: Parsed summary stats table data
            table_id: Table identifier
            pdf_path: Optional PDF path (if not already processed)

        Returns:
            TableContext with extracted semantic information

        """
        logger.info(f"Augmenting summary statistics table: {table_id}")

        # Process document if needed
        if pdf_path and self.search.current_document_path != str(Path(pdf_path)):
            await self.process_document(pdf_path)

        # Extract study context (cached)
        study_context = await self._get_study_context()

        # Extract treatment contexts (cached)
        treatment_contexts = await self._get_treatment_contexts()

        # Extract variable contexts for summary statistics
        variable_contexts = {}
        if self.config.augment_variables:
            variable_names = self._extract_variable_names_from_table(table_data)
            logger.debug(
                f"Extracting context for {len(variable_names)} summary stat variables"
            )

            for var_name in variable_names:
                var_context = await self.variable_extractor.extract_context(var_name)

                if (
                    var_context.confidence is not None
                    and var_context.confidence >= self.config.min_confidence_to_include
                ):
                    variable_contexts[var_name] = var_context

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            study_context, treatment_contexts, variable_contexts, {}, None
        )

        # Get title from Pydantic model or dict
        caption = getattr(table_data, "title", None) or "Summary statistics"
        if isinstance(table_data, dict):
            caption = table_data.get(
                "title", table_data.get("caption", "Summary statistics")
            )

        table_context = TableContext(
            table_id=table_id,
            table_description=caption or "Summary statistics",
            study_context=study_context if self.config.augment_study_context else None,
            treatment_contexts=(
                treatment_contexts if self.config.augment_treatments else []
            ),
            variable_contexts=variable_contexts,
            overall_confidence=overall_confidence,
        )

        logger.info(
            f"Summary stats table {table_id} augmented: "
            f"{len(variable_contexts)} variables, "
            f"confidence={overall_confidence:.2f}"
        )

        return table_context

    async def augment_balance_table(
        self,
        table_data: dict[str, Any],
        table_id: str,
        pdf_path: str | None = None,
    ) -> TableContext:
        """Augment balance table with semantic context.

        Args:
            table_data: Parsed balance table data
            table_id: Table identifier
            pdf_path: Optional PDF path (if not already processed)

        Returns:
            TableContext with extracted semantic information

        """
        logger.info(f"Augmenting balance table: {table_id}")

        # Process document if needed
        if pdf_path and self.search.current_document_path != str(Path(pdf_path)):
            await self.process_document(pdf_path)

        # Extract study context (cached)
        study_context = await self._get_study_context()

        # Extract treatment contexts (cached) - critical for balance tables
        treatment_contexts = await self._get_treatment_contexts()

        # Extract variable contexts for balance checks
        variable_contexts = {}
        if self.config.augment_variables:
            variable_names = self._extract_variable_names_from_table(table_data)
            logger.debug(
                f"Extracting context for {len(variable_names)} balance check variables"
            )

            for var_name in variable_names:
                var_context = await self.variable_extractor.extract_context(var_name)

                if (
                    var_context.confidence is not None
                    and var_context.confidence >= self.config.min_confidence_to_include
                ):
                    variable_contexts[var_name] = var_context

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            study_context, treatment_contexts, variable_contexts, {}, None
        )

        # Get title from Pydantic model or dict
        caption = getattr(table_data, "title", None) or "Balance table"
        if isinstance(table_data, dict):
            caption = table_data.get(
                "title", table_data.get("caption", "Balance table")
            )

        table_context = TableContext(
            table_id=table_id,
            table_description=caption or "Balance table",
            study_context=study_context if self.config.augment_study_context else None,
            treatment_contexts=(
                treatment_contexts if self.config.augment_treatments else []
            ),
            variable_contexts=variable_contexts,
            overall_confidence=overall_confidence,
        )

        logger.info(
            f"Balance table {table_id} augmented: "
            f"{len(variable_contexts)} variables, "
            f"{len(treatment_contexts)} treatment arms, "
            f"confidence={overall_confidence:.2f}"
        )

        return table_context

    async def _get_study_context(self):
        """Get study context (cached per document)."""
        doc_path = self.search.current_document_path

        if doc_path not in self._study_context_cache:
            if self.config.augment_study_context:
                study_context = await self.study_extractor.extract_study_context()
                self._study_context_cache[doc_path] = study_context
                logger.debug(
                    f"Study context cached: confidence={study_context.confidence:.2f}"
                )
            else:
                self._study_context_cache[doc_path] = None

        return self._study_context_cache[doc_path]

    async def _get_treatment_contexts(self):
        """Get treatment contexts (cached per document)."""
        doc_path = self.search.current_document_path

        if doc_path not in self._treatment_contexts_cache:
            if self.config.augment_treatments:
                treatment_contexts = (
                    await self.treatment_extractor.extract_treatment_arms()
                )
                self._treatment_contexts_cache[doc_path] = treatment_contexts
                logger.info(f"Cached {len(treatment_contexts)} treatment contexts")
            else:
                self._treatment_contexts_cache[doc_path] = []

        return self._treatment_contexts_cache[doc_path]

    def _extract_variable_names_from_table(
        self, table_data: dict[str, Any]
    ) -> list[str]:
        """Extract variable names from parsed table data.

        Args:
            table_data: Parsed table from parse.py

        Returns:
            List of variable names to extract context for

        """
        variables = set()

        # Handle regression table structure (Pydantic or dict)
        models = getattr(table_data, "models", None)
        if models is None and isinstance(table_data, dict):
            models = table_data.get("models", [])

        if models:
            for model in models:
                coefficients = getattr(model, "coefficients", None)
                if coefficients is None and isinstance(model, dict):
                    coefficients = model.get("coefficients", [])

                for coef in coefficients:
                    var_name = getattr(coef, "variable_name", None)
                    if var_name is None and isinstance(coef, dict):
                        var_name = coef.get("variable", coef.get("variable_name"))
                    if var_name:
                        variables.add(var_name)

        # Handle summary stats / balance table structure
        else:
            table_variables = getattr(table_data, "variables", None)
            if table_variables is None and isinstance(table_data, dict):
                table_variables = table_data.get("variables", [])
            if table_variables:
                for var in table_variables:
                    if hasattr(var, "name") and var.name:
                        variables.add(var.name)
                    elif isinstance(var, dict) and "name" in var:
                        variables.add(var["name"])
                    elif isinstance(var, str):
                        variables.add(var)

            # Fallback: try to extract from any row/column data
            else:
                rows = getattr(table_data, "rows", None)
                if rows is None and isinstance(table_data, dict):
                    rows = table_data.get("rows", [])
                for row in rows:
                    var_name = (
                        row.variable
                        if hasattr(row, "variable")
                        else (row.get("variable") if isinstance(row, dict) else None)
                    )
                    if var_name:
                        variables.add(var_name)

        logger.info(f"Extracted {len(variables)} variable names from table")
        return sorted(variables)

    def _extract_outcome_names_from_table(
        self, table_data: dict[str, Any]
    ) -> list[str]:
        """Extract outcome variable names from parsed table data.

        Args:
            table_data: Parsed table from parse.py

        Returns:
            List of outcome variable names

        """
        outcomes = set()

        # Regression tables: outcome is often in model metadata
        # Handle both Pydantic models and dicts
        models = getattr(table_data, "models", None)
        if models is None and isinstance(table_data, dict):
            models = table_data.get("models", [])
        if models:
            for model in models:
                # Handle both Pydantic and dict models
                if hasattr(model, "outcome") and model.outcome:
                    outcomes.add(model.outcome)
                elif hasattr(model, "dependent_variable") and model.dependent_variable:
                    outcomes.add(model.dependent_variable)
                elif isinstance(model, dict):
                    if "outcome" in model:
                        outcomes.add(model["outcome"])
                    elif "dependent_variable" in model:
                        outcomes.add(model["dependent_variable"])

        # Try to get from title or description
        caption = getattr(table_data, "title", None) or ""
        if not caption and isinstance(table_data, dict):
            caption = table_data.get("title", table_data.get("caption", ""))
        if caption and "outcome:" in caption.lower():
            # Simple extraction - could be improved with regex
            pass

        # If no outcomes found, return empty list
        # (most tables don't explicitly name outcomes separately)
        logger.info(f"Extracted {len(outcomes)} outcome names from table")
        return sorted(outcomes)

    def _calculate_overall_confidence(
        self,
        study_context,
        treatment_contexts,
        variable_contexts,
        outcome_contexts,
        methods_context,
    ) -> float:
        """Calculate overall confidence score for table augmentation.

        Args:
            study_context: StudyContext or None
            treatment_contexts: List of TreatmentContext
            variable_contexts: Dict of VariableContext
            outcome_contexts: Dict of OutcomeContext
            methods_context: MethodsContext or None

        Returns:
            Overall confidence score (0-1)

        """
        confidences = []

        # Study context confidence
        if study_context and study_context.confidence is not None:
            confidences.append(study_context.confidence)

        # Treatment contexts confidence (average)
        treatment_confs = [
            tc.confidence for tc in treatment_contexts if tc.confidence is not None
        ]
        if treatment_confs:
            confidences.append(sum(treatment_confs) / len(treatment_confs))

        # Variable contexts confidence (average)
        var_confs = [
            vc.confidence for vc in variable_contexts.values() if vc.confidence
        ]
        if var_confs:
            confidences.append(sum(var_confs) / len(var_confs))

        # Outcome contexts confidence (average)
        outcome_confs = [
            oc.confidence for oc in outcome_contexts.values() if oc.confidence
        ]
        if outcome_confs:
            confidences.append(sum(outcome_confs) / len(outcome_confs))

        # Methods context confidence
        if methods_context and methods_context.confidence is not None:
            confidences.append(methods_context.confidence)

        # Return average of all available confidences
        if confidences:
            overall = sum(confidences) / len(confidences)
            logger.debug(
                f"Overall confidence calculated from {len(confidences)} components: "
                f"{overall:.2f}"
            )
            return overall

        # No confidence scores available
        return 0.0

    def reset(self) -> None:
        """Reset augmenter state and clear caches."""
        self.search.reset()
        self._study_context_cache.clear()
        self._treatment_contexts_cache.clear()
        logger.info("TableAugmenter reset")
