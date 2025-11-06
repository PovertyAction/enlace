#!/usr/bin/env python3
"""Interactive paper extraction assistant.

This script guides the user through extracting key information from a research
paper following the research-analyst skill templates.

Usage:
    python extract_paper.py --paper paper.md --type rct
    python extract_paper.py --paper paper.md --type observational
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def detect_study_type(paper_content: str) -> str:
    """Attempt to detect study type from paper content."""
    content_lower = paper_content.lower()

    # Keywords for RCT
    rct_keywords = [
        "randomized",
        "randomised",
        "rct",
        "random assignment",
        "treatment arm",
    ]
    # Keywords for observational
    obs_keywords = [
        "observational",
        "cohort",
        "cross-sectional",
        "instrumental variable",
    ]

    rct_score = sum(1 for kw in rct_keywords if kw in content_lower)
    obs_score = sum(1 for kw in obs_keywords if kw in content_lower)

    if rct_score > obs_score:
        return "rct"
    elif obs_score > rct_score:
        return "observational"
    else:
        return "unknown"


def extract_title(paper_content: str) -> str:
    """Extract paper title from markdown."""
    lines = paper_content.split("\n")
    for line in lines[:50]:  # Check first 50 lines
        if line.startswith("# ") and len(line) > 3:
            return line[2:].strip()
    return "[Title Not Found]"


def extract_authors(paper_content: str) -> str:
    """Attempt to extract authors from paper."""
    lines = paper_content.split("\n")
    for i, line in enumerate(lines[:100]):
        if "author" in line.lower() and i + 1 < len(lines):
            potential_authors = lines[i + 1].strip()
            if len(potential_authors) < 200:  # Reasonable length
                return potential_authors
    return "[Authors Not Found]"


def load_template(study_type: str, template_dir: Path) -> str:
    """Load the appropriate template."""
    template_path = template_dir / f"{study_type}_template.md"

    if not template_path.exists():
        print(f"Warning: Template not found at {template_path}")
        return ""

    with open(template_path) as f:
        return f.read()


def initialize_extraction(paper_path: str, study_type: str, template_dir: Path) -> dict:
    """Initialize extraction with detected information."""
    # Load paper
    paper_path_obj = Path(paper_path)
    if not paper_path_obj.exists():
        msg = f"Paper not found: {paper_path}"
        raise FileNotFoundError(msg)

    with open(paper_path_obj) as f:
        paper_content = f.read()

    # Detect study type if not specified
    if study_type == "auto":
        study_type = detect_study_type(paper_content)
        print(f"Detected study type: {study_type}")

    # Extract basic info
    title = extract_title(paper_content)
    authors = extract_authors(paper_content)

    return {
        "paper_content": paper_content,
        "study_type": study_type,
        "title": title,
        "authors": authors,
        "paper_file": paper_path_obj.name,
    }


def create_extraction_file(info: dict, template: str, output_path: Path) -> None:
    """Create extraction file with template filled in."""
    # Replace template placeholders
    content = template

    # Basic replacements
    content = content.replace("[Paper Title]", info["title"])
    content = content.replace("[YYYY-MM-DD]", datetime.now().strftime("%Y-%m-%d"))
    content = content.replace("[Full list]", info["authors"])
    content = content.replace("[Full list with affiliations]", info["authors"])

    # Add paper source info
    content = f"<!-- Source: {info['paper_file']} -->\n\n" + content

    # Write to output
    with open(output_path, "w") as f:
        f.write(content)

    print(f"Created extraction file: {output_path}")


def print_extraction_guide(study_type: str) -> None:
    """Print guidance for completing extraction."""
    print("\n" + "=" * 80)
    print("EXTRACTION GUIDE")
    print("=" * 80)

    guide = {
        "rct": """
Follow these steps for RCT extraction:

1. Bibliographic Information (10 min)
   - Complete citation with DOI
   - Format BibTeX entry

2. Research Context (15 min)
   - Research questions and hypotheses
   - Theoretical framework

3. Study Design (30 min)
   - Randomization details
   - Treatment arms
   - Power analysis
   - Pre-registration

4. Data Collection (20 min)
   - Methods and instruments
   - Timeline
   - Quality control

5. Sample (20 min)
   - Sample size and attrition
   - Baseline characteristics
   - Balance table

6. Variables (20 min)
   - Outcomes (primary and secondary)
   - Treatment variable
   - Controls and covariates

7. Analysis (30 min)
   - Statistical methods
   - Standard errors
   - Robustness checks

8. Results (45 min)
   - Main treatment effects
   - Heterogeneity
   - Robustness

9. Quality Assessment (30 min)
   - Internal validity
   - External validity
   - Risk of bias

10. Discussion (20 min)
    - Interpretation
    - Limitations
    - Implications

Estimated total time: 4-5 hours for thorough extraction
        """,
        "observational": """
Follow these steps for observational study extraction:

1. Bibliographic Information (10 min)

2. Research Context (15 min)

3. Study Design (30 min)
   - Identification strategy
   - Causal assumptions
   - Validation tests

4. Data (20 min)
   - Sources and sample

5. Variables (20 min)

6. Analysis (30 min)
   - Empirical strategy
   - Threats to identification

7. Results (30 min)

8. Quality Assessment (30 min)
   - Internal validity
   - Identification credibility

9. Discussion (20 min)

Estimated total time: 3-4 hours
        """,
    }

    print(guide.get(study_type, "Follow template structure."))


def main():
    """Run extraction assistant."""
    parser = argparse.ArgumentParser(description="Research paper extraction assistant")

    parser.add_argument(
        "--paper", required=True, help="Path to paper (markdown format)"
    )
    parser.add_argument(
        "--type",
        choices=["rct", "observational", "auto"],
        default="auto",
        help="Study type (default: auto-detect)",
    )
    parser.add_argument("--output", help="Output file path (default: auto-generated)")
    parser.add_argument(
        "--template-dir",
        help="Directory containing templates (default: ../templates/)",
    )

    args = parser.parse_args()

    # Determine template directory
    if args.template_dir:
        template_dir = Path(args.template_dir)
    else:
        template_dir = Path(__file__).parent.parent / "templates"

    print("=" * 80)
    print("RESEARCH PAPER EXTRACTION ASSISTANT")
    print("=" * 80)

    # Initialize
    print("\nInitializing extraction...")
    info = initialize_extraction(args.paper, args.type, template_dir)

    print(f"Paper: {info['title']}")
    print(f"Authors: {info['authors']}")
    print(f"Study type: {info['study_type']}")

    # Load template
    print(f"\nLoading {info['study_type']} template...")
    template = load_template(info["study_type"], template_dir)

    if not template:
        print("Error: Could not load template")
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Auto-generate filename from title
        clean_title = "".join(c if c.isalnum() else "_" for c in info["title"][:50])
        output_path = Path(f"extraction_{clean_title}.md")

    # Create extraction file
    print("\nCreating extraction file...")
    create_extraction_file(info, template, output_path)

    # Print guide
    print_extraction_guide(info["study_type"])

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print(f"1. Open extraction file: {output_path}")
    print("2. Fill in template sections systematically")
    print("3. Reference paper content for each section")
    print("4. Be thorough - document everything")
    print("5. Add critical commentary in reviewer sections")
    print("\nGood luck with your extraction!")


if __name__ == "__main__":
    main()
