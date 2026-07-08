"""Camelot-based table extraction from PDF files.

This module provides a wrapper around the Camelot library for extracting
tables from text-based PDF documents using line detection and text flow analysis.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

logger = logging.getLogger("enlace.camelot_extractor")


class CamelotError(Exception):
    """Raised when Camelot extraction fails."""

    pass


class CamelotNotInstalledError(CamelotError):
    """Raised when Camelot is not installed."""

    pass


@dataclass
class CamelotTable:
    """Represents a table extracted by Camelot.

    Attributes:
        dataframe: Pandas DataFrame with table data
        page_number: Page number where table was found
        accuracy: Camelot accuracy score (0-100)
        whitespace: Camelot whitespace score (0-100)
        order: Table order on the page (0-indexed)
        flavor: Extraction method used ('lattice' or 'stream')
        table_region: Bounding box coordinates (x1, y1, x2, y2)

    """

    dataframe: pd.DataFrame
    page_number: int
    accuracy: float
    whitespace: float
    order: int
    flavor: str
    table_region: tuple[float, float, float, float] | None = None


class CamelotExtractor:
    """Extract tables from PDF files using Camelot.

    Camelot provides two extraction modes:
    - Lattice: Detects tables with visible borders using line detection
    - Stream: Detects borderless tables using text positioning

    Example:
        >>> extractor = CamelotExtractor()
        >>> tables = extractor.extract_tables(Path("paper.pdf"))
        >>> for table in tables:
        ...     print(f"Page {table.page_number}: {table.accuracy:.1f}% accuracy")

    """

    def __init__(
        self,
        lattice_line_scale: int = 40,
        stream_edge_tol: int = 50,
        quality_threshold: float = 60.0,  # Lowered from 70 to catch more tables
        min_table_size: int = 3,
        min_content_density: float = 0.30,  # Lowered from 0.35 for sparse tables
    ) -> None:
        """Initialize Camelot extractor.

        Args:
            lattice_line_scale: Scale factor for line detection (1-150).
                Higher values detect smaller lines.
            stream_edge_tol: Tolerance for text edge detection.
                Increase to detect tables with vertically-spaced text.
            quality_threshold: Minimum accuracy score to accept (0-100).
            min_table_size: Minimum table dimensions (NxN, default 3x3).
            min_content_density: Minimum filled cell ratio (0-1, default 0.30).

        Raises:
            CamelotNotInstalledError: If Camelot is not installed.

        """
        self.lattice_line_scale = lattice_line_scale
        self.stream_edge_tol = stream_edge_tol
        self.quality_threshold = quality_threshold
        self.min_table_size = min_table_size
        self.min_content_density = min_content_density

        # Try to import Camelot
        try:
            import camelot

            self.camelot = camelot
            logger.info("Camelot extractor initialized")
        except ImportError as e:
            raise CamelotNotInstalledError(
                "Camelot is not installed. Install with: pip install camelot-py[base]"
            ) from e

    def extract_tables(
        self,
        pdf_path: Path,
        pages: str = "all",
        prefer_flavor: str | None = None,
    ) -> list[CamelotTable]:
        """Extract tables from PDF using Camelot.

        This method tries both lattice and stream modes and selects the best
        results based on quality scores, unless a specific flavor is requested.

        Args:
            pdf_path: Path to PDF file (must be text-based, not scanned).
            pages: Page range to extract ('all', '1', '1,2,3', '1-5').
            prefer_flavor: Force specific extraction mode ('lattice' or 'stream').
                If None, tries both and selects best.

        Returns:
            List of CamelotTable objects.

        Raises:
            CamelotError: If extraction fails.
            FileNotFoundError: If pdf_path does not exist.

        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if pdf_path.suffix.lower() != ".pdf":
            raise CamelotError(f"Not a PDF file: {pdf_path}")

        # Check if PDF is text-based
        if not self._is_text_based_pdf(pdf_path):
            logger.warning(
                f"{pdf_path.name} appears to be scanned/image-based. "
                "Camelot works best on text-based PDFs."
            )

        logger.info(f"Extracting tables from {pdf_path.name} with Camelot...")

        try:
            if prefer_flavor:
                # Use specific flavor
                tables = self._extract_with_flavor(pdf_path, pages, prefer_flavor)
            else:
                # Try both flavors and select best
                lattice_tables = self._extract_with_flavor(pdf_path, pages, "lattice")
                stream_tables = self._extract_with_flavor(pdf_path, pages, "stream")
                tables = self._select_best_tables(lattice_tables, stream_tables)

            logger.info(
                f"Extracted {len(tables)} raw tables from {pdf_path.name} with Camelot"
            )

            # Filter out false positives (equations, small fragments, etc.)
            filtered_tables = self._filter_false_positives(tables)

            logger.info(
                f"After filtering: {len(filtered_tables)} tables "
                f"({len(tables) - len(filtered_tables)} false positives removed)"
            )

            # Sort by page number and order to preserve logical table sequence
            filtered_tables.sort(key=lambda t: (t.page_number, t.order))

            logger.info(
                f"Tables sorted by page number: {[f'p{t.page_number}' for t in filtered_tables]}"
            )

            return filtered_tables

        except Exception as e:
            raise CamelotError(f"Camelot extraction failed: {e}") from e

    def _extract_with_flavor(
        self, pdf_path: Path, pages: str, flavor: str
    ) -> list[CamelotTable]:
        """Extract tables using specific Camelot flavor.

        Args:
            pdf_path: Path to PDF file.
            pages: Page range string.
            flavor: 'lattice' or 'stream'.

        Returns:
            List of CamelotTable objects.

        """
        logger.debug(f"Trying {flavor} mode on {pdf_path.name}...")

        # Build Camelot kwargs - more aggressive to capture all tables
        kwargs = {"flavor": flavor, "pages": pages}

        if flavor == "lattice":
            kwargs["line_scale"] = self.lattice_line_scale
            # Enable morphological operations for better line detection
            kwargs["iterations"] = 1  # Enable morphological operations
            kwargs["process_background"] = True  # Process background lines
        elif flavor == "stream":
            kwargs["edge_tol"] = self.stream_edge_tol
            # More permissive stream mode to catch varied table formats
            kwargs["row_tol"] = 3  # More permissive row alignment (was 2)
            kwargs["column_tol"] = 2  # More permissive column alignment (was 0)

        # Run Camelot
        tables_list = self.camelot.read_pdf(str(pdf_path), **kwargs)

        # Wrap results
        wrapped_tables = []
        for table in tables_list:
            # Get quality metrics
            report = table.parsing_report

            # Filter by quality threshold
            if report["accuracy"] < self.quality_threshold:
                logger.debug(
                    f"Skipping low-quality table on page {table.page}: "
                    f"{report['accuracy']:.1f}% accuracy"
                )
                continue

            wrapped = CamelotTable(
                dataframe=table.df,
                page_number=table.page,
                accuracy=report["accuracy"],
                whitespace=report["whitespace"],
                order=report["order"],
                flavor=flavor,
            )
            wrapped_tables.append(wrapped)

        logger.debug(
            f"{flavor} mode found {len(wrapped_tables)} tables "
            f"(quality threshold: {self.quality_threshold}%)"
        )

        return wrapped_tables

    def _select_best_tables(
        self,
        lattice_tables: list[CamelotTable],
        stream_tables: list[CamelotTable],
    ) -> list[CamelotTable]:
        """Select best tables from lattice and stream extractions.

        For each page, selects the extraction with higher average quality.

        Args:
            lattice_tables: Tables from lattice mode.
            stream_tables: Tables from stream mode.

        Returns:
            Best tables from both modes.

        """
        # Group by page
        lattice_by_page = {}
        for table in lattice_tables:
            if table.page_number not in lattice_by_page:
                lattice_by_page[table.page_number] = []
            lattice_by_page[table.page_number].append(table)

        stream_by_page = {}
        for table in stream_tables:
            if table.page_number not in stream_by_page:
                stream_by_page[table.page_number] = []
            stream_by_page[table.page_number].append(table)

        # Select best for each page
        all_pages = set(lattice_by_page.keys()) | set(stream_by_page.keys())
        best_tables = []

        for page in sorted(all_pages):
            lattice_page_tables = lattice_by_page.get(page, [])
            stream_page_tables = stream_by_page.get(page, [])

            # Calculate average quality for each mode
            if lattice_page_tables:
                lattice_avg_quality = sum(
                    t.accuracy for t in lattice_page_tables
                ) / len(lattice_page_tables)
            else:
                lattice_avg_quality = 0

            if stream_page_tables:
                stream_avg_quality = sum(t.accuracy for t in stream_page_tables) / len(
                    stream_page_tables
                )
            else:
                stream_avg_quality = 0

            # Select better mode for this page
            if lattice_avg_quality >= stream_avg_quality:
                best_tables.extend(lattice_page_tables)
                if lattice_page_tables:
                    logger.debug(
                        f"Page {page}: Using lattice mode "
                        f"({lattice_avg_quality:.1f}% avg quality)"
                    )
            else:
                best_tables.extend(stream_page_tables)
                if stream_page_tables:
                    logger.debug(
                        f"Page {page}: Using stream mode "
                        f"({stream_avg_quality:.1f}% avg quality)"
                    )

        return best_tables

    def _filter_false_positives(self, tables: list[CamelotTable]) -> list[CamelotTable]:
        """Filter out false positive tables (equations, fragments, etc.).

        Uses multiple heuristics to identify real tables vs. extracted equations,
        figure captions, or other non-table grid structures.

        Research papers typically have:
        - Larger tables (at least 4x4)
        - Row/column headers with descriptive text
        - Mixed text/numeric content
        - Reasonable cell density

        Args:
            tables: List of extracted tables.

        Returns:
            Filtered list with false positives removed.

        """
        filtered = []

        for table in tables:
            df = table.dataframe

            # Criterion 1: Minimum size - configurable threshold
            min_size = self.min_table_size
            if df.shape[0] < min_size or df.shape[1] < min_size:
                logger.debug(
                    f"Filtered table (page {table.page_number}): too small "
                    f"({df.shape[0]}x{df.shape[1]}, need at least {min_size}x{min_size})"
                )
                continue

            # Criterion 2: Minimum cells
            min_cells = min_size * min_size
            if df.size < min_cells:
                logger.debug(
                    f"Filtered table (page {table.page_number}): too few cells "
                    f"({df.size}, need at least {min_cells})"
                )
                continue

            # Criterion 3: Content density - configurable threshold
            non_empty = df.map(lambda x: bool(str(x).strip())).sum().sum()
            fill_rate = non_empty / df.size
            if fill_rate < self.min_content_density:
                logger.debug(
                    f"Filtered table (page {table.page_number}): too sparse "
                    f"({fill_rate:.1%} filled, need {self.min_content_density:.0%}+)"
                )
                continue

            # Criterion 4: Check for table-like text content
            # Real tables have descriptive headers, not just pure numbers
            text_cells = 0
            numeric_cells = 0
            word_count = 0  # Track multi-word cells (typical of headers)

            for val in df.values.flatten():
                val_str = str(val).strip()
                if not val_str or val_str == "nan":
                    continue

                # Check if cell is purely numeric (including percentages, decimals)
                if self._is_numeric_like(val_str):
                    numeric_cells += 1
                else:
                    text_cells += 1
                    # Count words in text cells
                    words = val_str.split()
                    if len(words) >= 2:  # Multi-word cells are strong signal of headers
                        word_count += 1

            total_content_cells = text_cells + numeric_cells
            if total_content_cells == 0:
                logger.debug(f"Filtered table (page {table.page_number}): no content")
                continue

            # Real tables should have at least some text (headers, labels)
            text_ratio = text_cells / total_content_cells
            if text_ratio < 0.15:  # At least 15% text (increased from 10%)
                logger.debug(
                    f"Filtered table (page {table.page_number}): "
                    f"no text headers ({text_ratio:.1%} text, need 15%+)"
                )
                continue

            # Criterion 5: Check for descriptive headers (multi-word cells)
            # Research tables typically have descriptive column/row names
            # But some tables use abbreviations, so be permissive
            if text_cells > 0:
                descriptive_ratio = word_count / text_cells
                if descriptive_ratio < 0.1:  # At least 10% of text cells are multi-word
                    # Relaxed from 20% to avoid missing tables with abbreviated headers
                    logger.debug(
                        f"Filtered table (page {table.page_number}): "
                        f"no descriptive headers ({descriptive_ratio:.1%} multi-word)"
                    )
                    continue

            # Passed all filters - keep this table
            logger.debug(
                f"Kept table (page {table.page_number}): "
                f"{df.shape[0]}x{df.shape[1]}, {fill_rate:.1%} filled, "
                f"{text_ratio:.1%} text"
            )
            filtered.append(table)

        return filtered

    @staticmethod
    def _is_numeric_like(val: str) -> bool:
        """Check if string is numeric-like (number, percentage, etc.).

        Args:
            val: String value to check.

        Returns:
            True if value looks numeric.

        """
        # Remove common numeric decorations
        cleaned = val.replace(",", "").replace("%", "").replace("$", "").strip()
        # Check for negative sign, decimals, scientific notation
        cleaned = (
            cleaned.replace("-", "").replace(".", "").replace("e", "").replace("E", "")
        )
        # Also handle parentheses for negative numbers
        cleaned = cleaned.replace("(", "").replace(")", "")
        # Check for stars (significance markers)
        cleaned = cleaned.replace("*", "")

        return cleaned.replace("+", "").isdigit() if cleaned else False

    def _is_text_based_pdf(self, pdf_path: Path) -> bool:
        """Check if PDF contains extractable text.

        Args:
            pdf_path: Path to PDF file.

        Returns:
            True if PDF has extractable text, False if image-based/scanned.

        """
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages for text
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:
                        return True
                return False
        except ImportError:
            # If pdfplumber not available, assume it's text-based
            logger.debug("pdfplumber not installed, cannot check if PDF is text-based")
            return True
        except Exception as e:
            logger.warning(f"Could not check PDF type: {e}")
            return True  # Assume text-based and let Camelot try


def is_text_based_pdf(pdf_path: Path) -> bool:
    """Check if PDF contains extractable text (not scanned).

    This is a convenience function that can be used without instantiating
    a CamelotExtractor.

    Args:
        pdf_path: Path to PDF file.

    Returns:
        True if PDF has extractable text, False if image-based/scanned.

    """
    try:
        import pdfplumber

        with pdfplumber.open(pdf_path) as pdf:
            # Check first 3 pages for text
            for page in pdf.pages[:3]:
                text = page.extract_text()
                if text and len(text.strip()) > 100:
                    return True
            return False
    except ImportError:
        # If pdfplumber not available, check with simpler method
        try:
            import PyPDF2

            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_num in range(min(3, len(reader.pages))):
                    text = reader.pages[page_num].extract_text()
                    if text and len(text.strip()) > 100:
                        return True
                return False
        except ImportError:
            # No PDF libraries available, assume text-based
            return True
    except Exception:
        # Any error, assume text-based
        return True
