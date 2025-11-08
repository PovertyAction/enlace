"""Metadata extraction from research papers.

This module provides functions for extracting metadata such as title, authors,
year, DOI, and journal information from research papers.
"""

import logging
import re
from pathlib import Path

from enlace.models.extraction import PaperMetadata

logger = logging.getLogger("enlace.core.metadata")


def extract_metadata(
    markdown_path: Path, pdf_path: Path | None = None
) -> PaperMetadata:
    """Extract paper metadata from markdown text.

    Args:
        markdown_path: Path to markdown file
        pdf_path: Optional path to original PDF (for additional metadata)

    Returns:
        PaperMetadata object with extracted metadata

    """
    metadata = PaperMetadata()

    if not markdown_path.exists():
        logger.warning(f"Markdown file not found: {markdown_path}")
        return metadata

    try:
        # Read first 2000 characters for metadata extraction
        text = markdown_path.read_text(encoding="utf-8")[:2000]

        # Extract title (usually first heading)
        title = _extract_title(text)
        if title:
            metadata.title = title

        # Extract DOI
        doi = _extract_doi(text)
        if doi:
            metadata.doi = doi

        # Extract year
        year = _extract_year(text)
        if year:
            metadata.year = year

        # Extract authors
        authors = _extract_authors(text)
        if authors:
            metadata.authors = authors

        # Extract journal
        journal = _extract_journal(text)
        if journal:
            metadata.journal = journal

        # Extract abstract
        abstract = _extract_abstract(markdown_path.read_text(encoding="utf-8"))
        if abstract:
            metadata.abstract = abstract

        logger.debug(
            f"Extracted metadata: title={metadata.title}, year={metadata.year}"
        )

    except Exception as e:
        logger.warning(f"Metadata extraction error: {e}")

    return metadata


def extract_citations(markdown_path: Path) -> list[dict]:
    """Extract citations from the paper.

    Args:
        markdown_path: Path to markdown file

    Returns:
        List of citation dictionaries

    """
    citations = []

    if not markdown_path.exists():
        return citations

    try:
        text = markdown_path.read_text(encoding="utf-8")

        # Pattern 1: (Author Year) or (Author et al. Year)
        pattern1 = r"\(([A-Z][a-z]+(?:\s+et\s+al\.?)?\s+\d{4}[a-z]?)\)"
        matches1 = re.findall(pattern1, text)
        for match in matches1:
            citations.append(
                {
                    "citation_id": f"ref_{len(citations) + 1}",
                    "text": match,
                    "context": "extracted",
                    "type": "author-year",
                }
            )

        # Pattern 2: [Number] style citations
        pattern2 = r"\[(\d+)\]"
        matches2 = re.findall(pattern2, text)
        for match in matches2:
            citations.append(
                {
                    "citation_id": f"ref_{len(citations) + 1}",
                    "text": match,
                    "context": "extracted",
                    "type": "numbered",
                }
            )

        logger.debug(f"Extracted {len(citations)} citations")

    except Exception as e:
        logger.warning(f"Citation extraction error: {e}")

    return citations


def extract_methodology(markdown_path: Path) -> dict:
    """Extract methodology details from the paper.

    Args:
        markdown_path: Path to markdown file

    Returns:
        Dictionary with methodology information

    """
    methodology = {
        "study_design": None,
        "sample_size": None,
        "treatment_arms": None,
        "randomization_level": None,
        "outcome_primary": None,
        "outcomes_secondary": [],
        "treatment_description": None,
        "control_description": None,
        "location": None,
        "duration": None,
    }

    if not markdown_path.exists():
        return methodology

    try:
        text = markdown_path.read_text(encoding="utf-8")

        # Study design
        if "randomized controlled trial" in text.lower() or "rct" in text.lower():
            methodology["study_design"] = "Randomized Controlled Trial"
        elif "quasi-experimental" in text.lower():
            methodology["study_design"] = "Quasi-experimental"
        elif (
            "difference-in-differences" in text.lower()
            or "diff-in-diff" in text.lower()
        ):
            methodology["study_design"] = "Difference-in-Differences"
        elif "regression discontinuity" in text.lower() or "rdd" in text.lower():
            methodology["study_design"] = "Regression Discontinuity"

        # Sample size - look for patterns like "N = 1,234" or "n=1234"
        n_match = re.search(r"[Nn]\s*=\s*([0-9,]+)", text)
        if n_match:
            sample_size_str = n_match.group(1).replace(",", "")
            try:
                methodology["sample_size"] = int(sample_size_str)
            except ValueError:
                logger.debug(f"Could not parse sample size: {sample_size_str}")

        # Treatment arms - look for "two-arm", "three-arm", etc.
        arms_match = re.search(r"(\w+)-arm", text.lower())
        if arms_match:
            arm_word = arms_match.group(1)
            if arm_word in ["two", "2"]:
                methodology["treatment_arms"] = 2
            elif arm_word in ["three", "3"]:
                methodology["treatment_arms"] = 3
            elif arm_word in ["four", "4"]:
                methodology["treatment_arms"] = 4

        logger.debug(
            f"Extracted methodology: design={methodology['study_design']}, n={methodology['sample_size']}"
        )

    except Exception as e:
        logger.warning(f"Methodology extraction error: {e}")

    return methodology


# ============================================================================
# PRIVATE HELPER FUNCTIONS
# ============================================================================


def _extract_title(text: str) -> str | None:
    """Extract paper title from text."""
    # Look for first markdown heading
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        # Clean up common artifacts
        title = re.sub(r"\s+", " ", title)
        return title
    return None


def _extract_doi(text: str) -> str | None:
    """Extract DOI from text."""
    # DOI pattern: 10.xxxx/xxxxx
    doi_match = re.search(r'10\.\d{4,}(?:\.\d+)*/(?:(?!["&\'<>])\S)+', text)
    if doi_match:
        return doi_match.group(0)
    return None


def _extract_year(text: str) -> int | None:
    """Extract publication year from text."""
    # Look for 4-digit year (19xx or 20xx)
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        try:
            return int(year_match.group(0))
        except ValueError:
            pass
    return None


def _extract_authors(text: str) -> list[str]:
    """Extract author names from text."""
    # This is a simple heuristic - looking for capitalized names
    # in the first few lines after the title
    authors = []

    # Look for patterns like "FirstName LastName" after title
    # This is challenging without structured metadata
    # For now, return empty list - can be enhanced with NLP

    return authors


def _extract_journal(text: str) -> str | None:
    """Extract journal name from text."""
    # Look for common journal name patterns
    # This is difficult without structured metadata
    # For now, return None - can be enhanced

    return None


def _extract_abstract(text: str) -> str | None:
    """Extract abstract from full text."""
    # Look for abstract section
    abstract_pattern = r"(?i)##?\s*abstract\s*\n+(.*?)(?:\n##|\n\n##|$)"
    abstract_match = re.search(abstract_pattern, text, re.DOTALL)

    if abstract_match:
        abstract = abstract_match.group(1).strip()
        # Limit to reasonable length (first 1000 chars)
        if len(abstract) > 1000:
            abstract = abstract[:1000] + "..."
        return abstract

    return None
