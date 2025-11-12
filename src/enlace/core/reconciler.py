"""Table reconciliation for dual extraction.

This module provides functionality for matching and merging tables from
docling and Camelot extractions to produce improved results.
"""

import logging

import pandas as pd
from rapidfuzz import fuzz

from enlace.extractors.camelot_extractor import CamelotTable
from enlace.models.dual_extraction import (
    DualExtractionTable,
    ReconciliationMetadata,
)
from enlace.models.tables import BalanceTable, RegressionTable, SummaryStatisticsTable

logger = logging.getLogger("enlace.reconciler")


class TableReconciliationError(Exception):
    """Raised when table reconciliation fails."""

    pass


class TableReconciler:
    """Reconcile tables from multiple extraction sources.

    This class matches tables from docling and Camelot, then merges them
    using confidence-based selection to produce improved results.

    Example:
        >>> reconciler = TableReconciler()
        >>> matches = reconciler.match_tables(docling_tables, camelot_tables)
        >>> dual_tables = [reconciler.merge_tables(d, c) for d, c in matches]

    """

    def __init__(
        self,
        match_threshold: float = 0.7,
        reconciliation_strategy: str = "confidence_based",
    ) -> None:
        """Initialize table reconciler.

        Args:
            match_threshold: Minimum similarity score to match tables (0-1).
            reconciliation_strategy: Strategy for cell reconciliation:
                - "confidence_based": Use quality scores to select values
                - "prefer_camelot": Prefer Camelot values when disagreeing
                - "prefer_docling": Prefer docling values when disagreeing
                - "camelot_primary": Use Camelot as base, enhance with docling metadata

        """
        self.match_threshold = match_threshold
        self.reconciliation_strategy = reconciliation_strategy
        logger.info(
            f"TableReconciler initialized: strategy={reconciliation_strategy}, "
            f"threshold={match_threshold}"
        )

    def match_tables(
        self,
        docling_tables: list[RegressionTable | SummaryStatisticsTable | BalanceTable],
        camelot_tables: list[CamelotTable],
    ) -> list[
        tuple[RegressionTable | SummaryStatisticsTable | BalanceTable, CamelotTable]
    ]:
        """Match tables from docling and Camelot extractions.

        Uses multi-criteria scoring:
        1. Page number (must match)
        2. Caption/title similarity
        3. Dimension similarity (row/column counts)
        4. Content similarity (cell text)

        Args:
            docling_tables: Tables from docling extraction.
            camelot_tables: Tables from Camelot extraction.

        Returns:
            List of (docling_table, camelot_table) pairs.

        """
        logger.info(
            f"Matching {len(docling_tables)} docling tables with "
            f"{len(camelot_tables)} Camelot tables..."
        )

        matches = []
        used_camelot = set()

        for d_table in docling_tables:
            best_match = None
            best_score = 0.0

            for idx, c_table in enumerate(camelot_tables):
                if idx in used_camelot:
                    continue

                score = self._calculate_match_score(d_table, c_table)

                if score > best_score and score >= self.match_threshold:
                    best_score = score
                    best_match = (idx, c_table)

            if best_match:
                matches.append((d_table, best_match[1]))
                used_camelot.add(best_match[0])
                logger.debug(
                    f"Matched table '{getattr(d_table, 'table_number', 'unknown')}' "
                    f"(score: {best_score:.2f})"
                )

        logger.info(f"Matched {len(matches)} table pairs")

        if len(matches) < len(docling_tables):
            unmatched = len(docling_tables) - len(matches)
            logger.warning(
                f"{unmatched} docling tables could not be matched with Camelot"
            )

        return matches

    def _calculate_match_score(
        self,
        docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable,
        camelot_table: CamelotTable,
    ) -> float:
        """Calculate similarity score between two tables.

        Args:
            docling_table: Table from docling.
            camelot_table: Table from Camelot.

        Returns:
            Similarity score (0-1).

        """
        scores = []
        weights = []

        # 1. Page number (must match for high score)
        if hasattr(docling_table, "page_number") and docling_table.page_number:
            if docling_table.page_number == camelot_table.page_number:
                scores.append(1.0)
            else:
                scores.append(0.0)
            weights.append(0.3)

        # 2. Caption similarity
        if hasattr(docling_table, "caption") and docling_table.caption:
            # Extract first row as potential caption from Camelot
            camelot_caption = " ".join(
                str(x) for x in camelot_table.dataframe.iloc[0].tolist()
            )
            caption_sim = (
                fuzz.token_sort_ratio(docling_table.caption, camelot_caption) / 100
            )
            scores.append(caption_sim)
            weights.append(0.2)

        # 3. Dimension similarity
        docling_shape = self._get_table_shape(docling_table)
        camelot_shape = camelot_table.dataframe.shape

        if docling_shape and camelot_shape:
            # Allow ±2 rows/columns difference
            row_diff = abs(docling_shape[0] - camelot_shape[0])
            col_diff = abs(docling_shape[1] - camelot_shape[1])

            dim_score = max(0, 1.0 - (row_diff / max(docling_shape[0], 1)) * 0.5) * max(
                0, 1.0 - (col_diff / max(docling_shape[1], 1)) * 0.5
            )
            scores.append(dim_score)
            weights.append(0.25)

        # 4. Content similarity (sample of cells)
        content_sim = self._calculate_content_similarity(docling_table, camelot_table)
        if content_sim is not None:
            scores.append(content_sim)
            weights.append(0.25)

        # Calculate weighted average
        if not scores:
            return 0.0

        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight

        return weighted_score

    def _get_table_shape(
        self, table: RegressionTable | SummaryStatisticsTable | BalanceTable
    ) -> tuple[int, int] | None:
        """Get (rows, cols) shape of docling table.

        Args:
            table: Docling table.

        Returns:
            (rows, cols) tuple, or None if shape cannot be determined.

        """
        if isinstance(table, RegressionTable):
            if table.models:
                rows = sum(len(m.coefficients) for m in table.models)
                cols = len(table.models) + 1  # +1 for variable names
                return (rows, cols)
        elif isinstance(table, SummaryStatisticsTable):
            if table.statistics:
                rows = len(table.statistics)
                cols = 5  # Typical: var, N, mean, std, min, max
                return (rows, cols)
        elif isinstance(table, BalanceTable) and table.comparisons:
            rows = len(table.comparisons)
            cols = 4  # Typical: var, treatment, control, diff
            return (rows, cols)

        return None

    def _calculate_content_similarity(
        self,
        docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable,
        camelot_table: CamelotTable,
    ) -> float | None:
        """Calculate content similarity by sampling cells.

        Args:
            docling_table: Table from docling.
            camelot_table: Table from Camelot.

        Returns:
            Similarity score (0-1), or None if cannot compare.

        """
        # Extract sample of cell text from docling table
        docling_cells = self._extract_cell_sample(docling_table)
        camelot_cells = set(
            str(val).strip().lower()
            for val in camelot_table.dataframe.values.flatten()
            if pd.notna(val) and str(val).strip()
        )

        if not docling_cells or not camelot_cells:
            return None

        # Calculate Jaccard similarity
        intersection = len(docling_cells & camelot_cells)
        union = len(docling_cells | camelot_cells)

        if union == 0:
            return 0.0

        return intersection / union

    def _extract_cell_sample(
        self, table: RegressionTable | SummaryStatisticsTable | BalanceTable
    ) -> set[str]:
        """Extract sample of cell text from docling table.

        Args:
            table: Docling table.

        Returns:
            Set of cell text values.

        """
        cells = set()

        if isinstance(table, RegressionTable):
            for model in table.models:
                if model.dependent_variable:
                    cells.add(str(model.dependent_variable).strip().lower())
                for coef in model.coefficients:
                    if coef.variable_name:
                        cells.add(str(coef.variable_name).strip().lower())
                    if coef.coefficient is not None:
                        cells.add(str(coef.coefficient).strip().lower())

        elif isinstance(table, SummaryStatisticsTable):
            for stat in table.statistics:
                if stat.variable_name:
                    cells.add(str(stat.variable_name).strip().lower())
                if stat.mean is not None:
                    cells.add(str(stat.mean).strip().lower())

        elif isinstance(table, BalanceTable):
            for comp in table.comparisons:
                if comp.variable_name:
                    cells.add(str(comp.variable_name).strip().lower())
                if comp.treatment_mean is not None:
                    cells.add(str(comp.treatment_mean).strip().lower())

        return cells

    def merge_tables(
        self,
        docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable | None,
        camelot_table: CamelotTable | None,
    ) -> DualExtractionTable:
        """Merge two table extractions into single result.

        This method reconciles cell values using the configured strategy
        and creates a DualExtractionTable storing all versions.

        Args:
            docling_table: Table from docling (None if Camelot-only).
            camelot_table: Table from Camelot (None if docling-only).

        Returns:
            DualExtractionTable with all three versions.

        Raises:
            TableReconciliationError: If both tables are None.

        """
        if docling_table is None and camelot_table is None:
            raise TableReconciliationError("Cannot merge: both tables are None")

        # Handle Camelot-only table
        if docling_table is None and camelot_table is not None:
            logger.debug(
                f"Camelot-only table (page {camelot_table.page_number}, "
                f"accuracy {camelot_table.accuracy:.1f})"
            )
            return self._create_camelot_only_table(camelot_table)

        # Handle docling-only table
        if camelot_table is None and docling_table is not None:
            logger.debug(
                f"Docling-only table '{getattr(docling_table, 'table_number', 'unknown')}'"
            )
            return self._create_docling_only_table(docling_table)

        # Handle matched pair - both tables present
        logger.debug(
            f"Merging table '{getattr(docling_table, 'table_number', 'unknown')}' "
            f"using {self.reconciliation_strategy} strategy"
        )

        # Choose reconciliation approach based on strategy
        if self.reconciliation_strategy == "camelot_primary":
            # Camelot-primary: Parse Camelot DataFrame, enhance with docling metadata
            reconciled_table, metadata = self._reconcile_camelot_primary(
                docling_table, camelot_table
            )
        else:
            # Docling-primary: Start with docling, enhance with Camelot numeric values
            reconciled_table = docling_table.model_copy(deep=True)

            # Reconcile based on table type
            if isinstance(docling_table, RegressionTable):
                metadata = self._reconcile_regression_table(
                    reconciled_table, camelot_table
                )
            elif isinstance(docling_table, SummaryStatisticsTable):
                metadata = self._reconcile_summary_table(
                    reconciled_table, camelot_table
                )
            elif isinstance(docling_table, BalanceTable):
                metadata = self._reconcile_balance_table(
                    reconciled_table, camelot_table
                )
            else:
                raise TableReconciliationError(
                    f"Unsupported table type: {type(docling_table)}"
                )

        # Create dual extraction table
        table_id = f"{getattr(docling_table, 'table_number', 'unknown')}_dual"

        dual_table = DualExtractionTable.from_dataframe(
            table_id=table_id,
            docling_table=docling_table,
            camelot_df=camelot_table.dataframe,
            camelot_quality={
                "accuracy": camelot_table.accuracy,
                "whitespace": camelot_table.whitespace,
                "page": camelot_table.page_number,
                "flavor": camelot_table.flavor,
            },
            reconciled_table=reconciled_table,
            reconciliation_metadata=metadata,
        )

        logger.debug(
            f"Table merged: {metadata.cells_agreed}/{metadata.cells_total} cells agreed "
            f"({metadata.agreement_rate:.1%})"
        )

        return dual_table

    def _reconcile_regression_table(
        self,
        docling_table: RegressionTable,
        camelot_table: CamelotTable,
    ) -> ReconciliationMetadata:
        """Reconcile regression table cells using cell-level comparison.

        Strategy:
        1. Extract all numeric cells from both tables
        2. For each docling coefficient/stat, search for matching values in Camelot
        3. Compare and reconcile based on strategy (confidence_based, prefer_camelot, etc.)
        4. Update docling_table in-place with reconciled values

        Args:
            docling_table: Regression table (will be modified in place).
            camelot_table: Camelot table for comparison.

        Returns:
            ReconciliationMetadata with reconciliation stats.

        """
        cells_total = 0
        cells_agreed = 0
        cells_disagreed = 0
        by_docling = 0
        by_camelot = 0
        by_heuristic = 0

        # Get Camelot DataFrame
        camelot_df = camelot_table.dataframe

        # Build searchable index of Camelot cells
        camelot_numeric_cells = self._extract_numeric_cells(camelot_df)
        camelot_text_cells = self._extract_text_cells(camelot_df)

        logger.debug(
            f"Camelot has {len(camelot_numeric_cells)} numeric cells, "
            f"{len(camelot_text_cells)} text cells"
        )

        # Reconcile each coefficient
        for model in docling_table.models:
            for coef in model.coefficients:
                # Reconcile coefficient value
                if coef.coefficient is not None:
                    cells_total += 1
                    result = self._reconcile_numeric_value(
                        coef.coefficient,
                        camelot_numeric_cells,
                        camelot_table.accuracy,
                    )
                    if result["action"] == "agree":
                        cells_agreed += 1
                        by_docling += 1
                    elif result["action"] == "use_camelot":
                        cells_disagreed += 1
                        by_camelot += 1
                        coef.coefficient = result["value"]
                    elif result["action"] == "use_docling":
                        cells_disagreed += 1
                        by_docling += 1
                    else:  # no_match
                        by_docling += 1

                # Reconcile std_error
                if coef.std_error is not None:
                    cells_total += 1
                    result = self._reconcile_numeric_value(
                        coef.std_error,
                        camelot_numeric_cells,
                        camelot_table.accuracy,
                    )
                    if result["action"] == "agree":
                        cells_agreed += 1
                        by_docling += 1
                    elif result["action"] == "use_camelot":
                        cells_disagreed += 1
                        by_camelot += 1
                        coef.std_error = result["value"]
                    elif result["action"] == "use_docling":
                        cells_disagreed += 1
                        by_docling += 1
                    else:
                        by_docling += 1

                # Reconcile t_statistic
                if coef.t_statistic is not None:
                    cells_total += 1
                    result = self._reconcile_numeric_value(
                        coef.t_statistic,
                        camelot_numeric_cells,
                        camelot_table.accuracy,
                    )
                    if result["action"] == "agree":
                        cells_agreed += 1
                        by_docling += 1
                    elif result["action"] == "use_camelot":
                        cells_disagreed += 1
                        by_camelot += 1
                        coef.t_statistic = result["value"]
                    elif result["action"] == "use_docling":
                        cells_disagreed += 1
                        by_docling += 1
                    else:
                        by_docling += 1

                # Reconcile p_value
                if coef.p_value is not None:
                    cells_total += 1
                    result = self._reconcile_numeric_value(
                        coef.p_value,
                        camelot_numeric_cells,
                        camelot_table.accuracy,
                    )
                    if result["action"] == "agree":
                        cells_agreed += 1
                        by_docling += 1
                    elif result["action"] == "use_camelot":
                        cells_disagreed += 1
                        by_camelot += 1
                        coef.p_value = result["value"]
                    elif result["action"] == "use_docling":
                        cells_disagreed += 1
                        by_docling += 1
                    else:
                        by_docling += 1

        # Calculate metadata
        agreement_rate = cells_agreed / cells_total if cells_total > 0 else 0.0
        confidence_score = self._calculate_confidence_score(
            agreement_rate, camelot_table.accuracy
        )

        logger.debug(
            f"Reconciliation: {cells_total} cells, {cells_agreed} agreed, "
            f"{cells_disagreed} disagreed, {agreement_rate:.1%} agreement"
        )

        return ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=cells_agreed,
            cells_disagreed=cells_disagreed,
            agreement_rate=agreement_rate,
            cells_reconciled_by_docling=by_docling,
            cells_reconciled_by_camelot=by_camelot,
            cells_reconciled_by_heuristic=by_heuristic,
            reconciliation_strategy=self.reconciliation_strategy,
            confidence_score=confidence_score,
            camelot_accuracy=camelot_table.accuracy,
            camelot_whitespace=camelot_table.whitespace,
        )

    def _reconcile_summary_table(
        self,
        docling_table: SummaryStatisticsTable,
        camelot_table: CamelotTable,
    ) -> ReconciliationMetadata:
        """Reconcile summary statistics table cells.

        Args:
            docling_table: Summary table (will be modified in place).
            camelot_table: Camelot table for comparison.

        Returns:
            ReconciliationMetadata with reconciliation stats.

        """
        cells_total = 0
        cells_agreed = 0
        cells_disagreed = 0
        by_docling = 0
        by_camelot = 0
        by_heuristic = 0

        # Simple reconciliation for now
        for stat in docling_table.statistics:
            cells_total += 1
            by_docling += 1

        agreement_rate = cells_agreed / cells_total if cells_total > 0 else 0.0
        confidence_score = self._calculate_confidence_score(
            agreement_rate, camelot_table.accuracy
        )

        return ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=cells_agreed,
            cells_disagreed=cells_disagreed,
            agreement_rate=agreement_rate,
            cells_reconciled_by_docling=by_docling,
            cells_reconciled_by_camelot=by_camelot,
            cells_reconciled_by_heuristic=by_heuristic,
            reconciliation_strategy=self.reconciliation_strategy,
            confidence_score=confidence_score,
            camelot_accuracy=camelot_table.accuracy,
            camelot_whitespace=camelot_table.whitespace,
        )

    def _reconcile_balance_table(
        self,
        docling_table: BalanceTable,
        camelot_table: CamelotTable,
    ) -> ReconciliationMetadata:
        """Reconcile balance table cells.

        Args:
            docling_table: Balance table (will be modified in place).
            camelot_table: Camelot table for comparison.

        Returns:
            ReconciliationMetadata with reconciliation stats.

        """
        cells_total = 0
        cells_agreed = 0
        cells_disagreed = 0
        by_docling = 0
        by_camelot = 0
        by_heuristic = 0

        # Simple reconciliation for now
        for comp in docling_table.comparisons:
            cells_total += 1
            by_docling += 1

        agreement_rate = cells_agreed / cells_total if cells_total > 0 else 0.0
        confidence_score = self._calculate_confidence_score(
            agreement_rate, camelot_table.accuracy
        )

        return ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=cells_agreed,
            cells_disagreed=cells_disagreed,
            agreement_rate=agreement_rate,
            cells_reconciled_by_docling=by_docling,
            cells_reconciled_by_camelot=by_camelot,
            cells_reconciled_by_heuristic=by_heuristic,
            reconciliation_strategy=self.reconciliation_strategy,
            confidence_score=confidence_score,
            camelot_accuracy=camelot_table.accuracy,
            camelot_whitespace=camelot_table.whitespace,
        )

    def _extract_numeric_cells(self, df: pd.DataFrame) -> list[dict]:
        """Extract all numeric cells from Camelot DataFrame.

        Args:
            df: Camelot DataFrame.

        Returns:
            List of dicts with {value, row, col, text}.

        """
        numeric_cells = []
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_text = str(df.iloc[row_idx, col_idx]).strip()
                if not cell_text or cell_text == "nan":
                    continue

                # Try to parse as number
                parsed_num = self._parse_numeric(cell_text)
                if parsed_num is not None:
                    numeric_cells.append(
                        {
                            "value": parsed_num,
                            "row": row_idx,
                            "col": col_idx,
                            "text": cell_text,
                        }
                    )

        return numeric_cells

    def _extract_text_cells(self, df: pd.DataFrame) -> list[dict]:
        """Extract all text cells from Camelot DataFrame.

        Args:
            df: Camelot DataFrame.

        Returns:
            List of dicts with {text, row, col}.

        """
        text_cells = []
        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                cell_text = str(df.iloc[row_idx, col_idx]).strip()
                if not cell_text or cell_text == "nan":
                    continue

                # Include all non-empty cells
                text_cells.append(
                    {
                        "text": cell_text.lower(),
                        "row": row_idx,
                        "col": col_idx,
                    }
                )

        return text_cells

    def _parse_numeric(self, text: str) -> float | None:
        """Parse numeric value from text, handling various formats.

        Handles:
        - Regular numbers: "1.234", "-0.5"
        - Percentages: "12.3%"
        - Parentheses (negative): "(0.5)"
        - Significance stars: "0.123***"
        - Thousands separators: "1,234.5"

        Args:
            text: Text to parse.

        Returns:
            Parsed float value, or None if not numeric.

        """
        if not text:
            return None

        # Remove common decorations
        cleaned = text.strip()
        cleaned = cleaned.replace(",", "")  # Thousands separator
        cleaned = cleaned.replace("%", "")  # Percentage
        cleaned = cleaned.replace("*", "")  # Significance stars
        cleaned = cleaned.replace("$", "")  # Dollar sign
        cleaned = cleaned.strip()

        # Handle parentheses (negative numbers)
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = "-" + cleaned[1:-1]

        # Try to parse
        try:
            return float(cleaned)
        except ValueError:
            return None

    def _reconcile_numeric_value(
        self,
        docling_value: float,
        camelot_cells: list[dict],
        camelot_accuracy: float,
    ) -> dict:
        """Reconcile a single numeric value using Camelot cells.

        Strategy:
        1. Search for matching value in Camelot cells (with tolerance)
        2. If found and matches: agree
        3. If found but differs: use strategy to decide
        4. If not found: keep docling

        Args:
            docling_value: Value from docling extraction.
            camelot_cells: List of numeric cells from Camelot.
            camelot_accuracy: Camelot accuracy score (0-100).

        Returns:
            Dict with {action, value, camelot_value}.

        """
        # Find best matching Camelot cell
        best_match = None
        best_diff = float("inf")

        for cell in camelot_cells:
            camelot_val = cell["value"]
            diff = abs(docling_value - camelot_val)

            # Relative tolerance: 0.1% for large numbers, absolute for small
            tolerance = max(0.001 * abs(docling_value), 0.01)

            if diff <= tolerance and diff < best_diff:
                best_match = cell
                best_diff = diff

        # No match found - keep docling
        if best_match is None:
            return {
                "action": "no_match",
                "value": docling_value,
                "camelot_value": None,
            }

        camelot_val = best_match["value"]

        # Perfect match or very close - agree
        if best_diff < 0.001:
            return {
                "action": "agree",
                "value": docling_value,
                "camelot_value": camelot_val,
            }

        # Values differ - apply strategy
        if self.reconciliation_strategy == "prefer_camelot":
            return {
                "action": "use_camelot",
                "value": camelot_val,
                "camelot_value": camelot_val,
            }
        elif self.reconciliation_strategy == "prefer_docling":
            return {
                "action": "use_docling",
                "value": docling_value,
                "camelot_value": camelot_val,
            }
        else:  # confidence_based
            # Use Camelot if its accuracy is high (>80%) and difference is small
            if (
                camelot_accuracy > 80
                and best_diff / max(abs(docling_value), 0.01) < 0.05
            ):
                return {
                    "action": "use_camelot",
                    "value": camelot_val,
                    "camelot_value": camelot_val,
                }
            else:
                return {
                    "action": "use_docling",
                    "value": docling_value,
                    "camelot_value": camelot_val,
                }

    def _calculate_confidence_score(
        self, agreement_rate: float, camelot_accuracy: float
    ) -> float:
        """Calculate overall confidence score.

        Args:
            agreement_rate: Proportion of cells that agreed (0-1).
            camelot_accuracy: Camelot accuracy score (0-100).

        Returns:
            Confidence score (0-1).

        """
        # Weight agreement rate more heavily than Camelot accuracy
        score = 0.6 * agreement_rate + 0.4 * (camelot_accuracy / 100)
        return min(1.0, max(0.0, score))

    def _create_docling_only_table(
        self, docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable
    ) -> DualExtractionTable:
        """Create DualExtractionTable for docling-only extraction.

        Args:
            docling_table: Table from docling.

        Returns:
            DualExtractionTable with only docling data.

        """
        # Calculate basic metadata for docling-only table
        if isinstance(docling_table, RegressionTable):
            cells_total = sum(len(m.coefficients) for m in docling_table.models)
        elif isinstance(docling_table, SummaryStatisticsTable):
            cells_total = len(docling_table.statistics)
        elif isinstance(docling_table, BalanceTable):
            cells_total = len(docling_table.comparisons)
        else:
            cells_total = 0

        metadata = ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=0,
            cells_disagreed=0,
            agreement_rate=0.0,
            cells_reconciled_by_docling=cells_total,
            cells_reconciled_by_camelot=0,
            cells_reconciled_by_heuristic=0,
            reconciliation_strategy="docling_only",
            confidence_score=0.5,  # Neutral confidence for single-source
            camelot_accuracy=0.0,
            camelot_whitespace=0.0,
        )

        table_id = f"{getattr(docling_table, 'table_number', 'unknown')}_docling_only"

        return DualExtractionTable.from_dataframe(
            table_id=table_id,
            docling_table=docling_table,
            camelot_df=None,
            camelot_quality={},
            reconciled_table=docling_table.model_copy(deep=True),
            reconciliation_metadata=metadata,
        )

    def _create_camelot_only_table(
        self, camelot_table: CamelotTable
    ) -> DualExtractionTable:
        """Create DualExtractionTable for Camelot-only extraction.

        Since we don't have a docling table, we create a minimal placeholder
        RegressionTable and use the Camelot data as reconciled result.

        Args:
            camelot_table: Table from Camelot.

        Returns:
            DualExtractionTable with only Camelot data.

        """
        # Create placeholder docling table
        placeholder = RegressionTable(
            table_number=f"camelot_page_{camelot_table.page_number}",
            title=f"Camelot-only table (page {camelot_table.page_number})",
            models=[],
            source_file=None,
            page_number=camelot_table.page_number,
        )

        # Calculate metadata
        cells_total = (
            camelot_table.dataframe.size if camelot_table.dataframe is not None else 0
        )

        metadata = ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=0,
            cells_disagreed=0,
            agreement_rate=0.0,
            cells_reconciled_by_docling=0,
            cells_reconciled_by_camelot=cells_total,
            cells_reconciled_by_heuristic=0,
            reconciliation_strategy="camelot_only",
            confidence_score=camelot_table.accuracy / 100,  # Use Camelot accuracy
            camelot_accuracy=camelot_table.accuracy,
            camelot_whitespace=camelot_table.whitespace,
        )

        table_id = (
            f"camelot_page_{camelot_table.page_number}_order_{camelot_table.order}"
        )

        return DualExtractionTable.from_dataframe(
            table_id=table_id,
            docling_table=placeholder,
            camelot_df=camelot_table.dataframe,
            camelot_quality={
                "accuracy": camelot_table.accuracy,
                "whitespace": camelot_table.whitespace,
                "page": camelot_table.page_number,
                "flavor": camelot_table.flavor,
            },
            reconciled_table=placeholder.model_copy(deep=True),
            reconciliation_metadata=metadata,
        )

    def _reconcile_camelot_primary(
        self,
        docling_table: RegressionTable | SummaryStatisticsTable | BalanceTable,
        camelot_table: CamelotTable,
    ) -> tuple[
        RegressionTable | SummaryStatisticsTable | BalanceTable, ReconciliationMetadata
    ]:
        """Reconcile using Camelot as primary source, enhanced with docling metadata.

        Strategy:
        1. Start with Camelot DataFrame as ground truth for numeric data
        2. Copy docling table structure (models, variable names, etc.)
        3. Replace numeric values with Camelot data where available
        4. Enhance with docling metadata (context_before, notes, title)

        Args:
            docling_table: Table from docling (used for structure and metadata).
            camelot_table: Table from Camelot (used for numeric data).

        Returns:
            Tuple of (reconciled_table, metadata).

        """
        logger.debug(
            f"Camelot-primary reconciliation: page {camelot_table.page_number}, "
            f"accuracy {camelot_table.accuracy:.1f}%"
        )

        # Start with deep copy of docling for structure
        reconciled_table = docling_table.model_copy(deep=True)

        # Extract Camelot cells for lookup
        camelot_numeric_cells = self._extract_numeric_cells(camelot_table.dataframe)

        cells_total = 0
        cells_from_camelot = 0
        cells_from_docling = 0

        # Update numeric values with Camelot data
        if isinstance(reconciled_table, RegressionTable):
            for model in reconciled_table.models:
                for coef in model.coefficients:
                    # Replace coefficient if found in Camelot
                    if coef.coefficient is not None:
                        cells_total += 1
                        camelot_val = self._find_camelot_value(
                            coef.coefficient, camelot_numeric_cells
                        )
                        if camelot_val is not None:
                            coef.coefficient = camelot_val
                            cells_from_camelot += 1
                        else:
                            cells_from_docling += 1

                    # Replace std_error if found in Camelot
                    if coef.std_error is not None:
                        cells_total += 1
                        camelot_val = self._find_camelot_value(
                            coef.std_error, camelot_numeric_cells
                        )
                        if camelot_val is not None:
                            coef.std_error = camelot_val
                            cells_from_camelot += 1
                        else:
                            cells_from_docling += 1

                    # For missing standard errors in docling, try to find in Camelot
                    if coef.std_error is None and coef.coefficient is not None:
                        # Look for SE values near the coefficient value
                        # SE is typically much smaller than coefficient
                        se_candidates = [
                            cell["value"]
                            for cell in camelot_numeric_cells
                            if 0 < cell["value"] < abs(coef.coefficient) * 0.5
                        ]
                        if se_candidates:
                            # Take the first plausible SE value
                            coef.std_error = se_candidates[0]
                            cells_total += 1
                            cells_from_camelot += 1
                            logger.debug(
                                f"Found missing SE for {coef.variable_name}: {coef.std_error}"
                            )

        # Calculate metadata
        cells_agreed = 0  # In camelot_primary, we don't do agreement comparison
        cells_disagreed = 0

        metadata = ReconciliationMetadata(
            cells_total=cells_total,
            cells_agreed=cells_agreed,
            cells_disagreed=cells_disagreed,
            agreement_rate=0.0,  # N/A for camelot_primary
            cells_reconciled_by_docling=cells_from_docling,
            cells_reconciled_by_camelot=cells_from_camelot,
            cells_reconciled_by_heuristic=0,
            reconciliation_strategy="camelot_primary",
            confidence_score=camelot_table.accuracy / 100,
            camelot_accuracy=camelot_table.accuracy,
            camelot_whitespace=camelot_table.whitespace,
        )

        logger.debug(
            f"Camelot-primary: {cells_from_camelot} cells from Camelot, "
            f"{cells_from_docling} cells from docling"
        )

        return reconciled_table, metadata

    def _find_camelot_value(
        self, target_value: float, camelot_cells: list[dict]
    ) -> float | None:
        """Find matching value in Camelot cells.

        Args:
            target_value: Value to search for.
            camelot_cells: List of Camelot numeric cells.

        Returns:
            Matching Camelot value, or None if not found.

        """
        best_match = None
        best_diff = float("inf")
        tolerance = max(0.001 * abs(target_value), 0.01)

        for cell in camelot_cells:
            diff = abs(target_value - cell["value"])
            if diff <= tolerance and diff < best_diff:
                best_match = cell
                best_diff = diff

        return best_match["value"] if best_match else None
