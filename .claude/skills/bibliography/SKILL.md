---
name: bibliography
description: Extract citations from research papers, generate BibTeX entries, manage references, and deduplicate bibliographies. Use for citation extraction, reference management, and building literature databases for meta-analysis.
---

# Bibliography Management for Research

Manage citations, extract references, and build literature databases for systematic reviews and meta-analysis.

## When to Use This Skill

Use this skill when you need to:

- Extract citations from PDF research papers
- Generate BibTeX entries for papers
- Create structured reference databases
- Deduplicate references across multiple papers
- Build citation networks
- Manage references for systematic reviews
- Export citations to Zotero/Mendeley format

## Quick Start

### Extract Citations from PDF

```python
import re
from pathlib import Path

def extract_citations_simple(markdown_text):
    """Extract citations from markdown converted paper."""
    # Common patterns for citations
    patterns = [
        r'\(([A-Z][a-z]+(?:\s+et\s+al\.?)?\s+\d{4}[a-z]?)\)',  # (Author 2020)
        r'\[(\d+)\]',  # [1], [2], etc.
        r'([A-Z][a-z]+\s+and\s+[A-Z][a-z]+\s+\(\d{4}\))',  # Author and Author (2020)
    ]

    citations = []
    for pattern in patterns:
        citations.extend(re.findall(pattern, markdown_text))

    return list(set(citations))

# Use with pdf-processor output
paper_md = Path("paper.md").read_text()
citations = extract_citations_simple(paper_md)
print(f"Found {len(citations)} citations")
```

### Generate BibTeX Entry

```python
from dataclasses import dataclass
import re

@dataclass
class Paper:
    """Research paper metadata."""
    title: str
    authors: list[str]
    year: int
    journal: str = ""
    volume: str = ""
    pages: str = ""
    doi: str = ""

    def to_bibtex(self) -> str:
        """Generate BibTeX entry."""
        # Create citation key
        first_author = self.authors[0].split()[-1].lower()
        key = f"{first_author}{self.year}"

        # Format authors
        author_str = " and ".join(self.authors)

        bibtex = f"""@article{{{key},
    title = {{{self.title}}},
    author = {{{author_str}}},
    year = {{{self.year}}},
"""

        if self.journal:
            bibtex += f"    journal = {{{self.journal}}},\n"
        if self.volume:
            bibtex += f"    volume = {{{self.volume}}},\n"
        if self.pages:
            bibtex += f"    pages = {{{self.pages}}},\n"
        if self.doi:
            bibtex += f"    doi = {{{self.doi}}},\n"

        bibtex += "}\n"
        return bibtex

# Example usage
paper = Paper(
    title="The Effect of Cash Transfers on Child Health",
    authors=["Smith, John", "Doe, Jane"],
    year=2020,
    journal="Journal of Development Economics",
    volume="145",
    pages="102468",
    doi="10.1016/j.jdeveco.2020.102468"
)

print(paper.to_bibtex())
```

### Extract DOI from PDF Text

```python
import re

def extract_doi(text):
    """Extract DOI from paper text."""
    # DOI pattern
    doi_pattern = r'10\.\d{4,}(?:\.\d+)*\/(?:(?!["&\'<>])\S)+'

    match = re.search(doi_pattern, text)
    if match:
        return match.group(0)
    return None

# Use with pdf-processor output
paper_text = Path("paper.md").read_text()
doi = extract_doi(paper_text)
if doi:
    print(f"DOI: {doi}")
    print(f"URL: https://doi.org/{doi}")
```

## Advanced Workflows

### Workflow 1: Build Reference Database from PDFs

```python
from pathlib import Path
import json
from dataclasses import asdict

def extract_paper_metadata(pdf_path):
    """Extract metadata from PDF using pdf-processor."""
    # Assuming you've already converted with pdf-processor
    md_path = pdf_path.with_suffix(".md")

    if not md_path.exists():
        return None

    text = md_path.read_text()

    # Extract title (usually first heading)
    title_match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
    title = title_match.group(1) if title_match else pdf_path.stem

    # Extract DOI
    doi = extract_doi(text)

    # Extract year from text or filename
    year_match = re.search(r'\b(19|20)\d{2}\b', text[:1000])
    year = int(year_match.group()) if year_match else None

    return {
        "source_file": pdf_path.name,
        "title": title,
        "doi": doi,
        "year": year,
        "citations": extract_citations_simple(text)
    }

# Process all papers
papers_dir = Path("papers")
reference_db = []

for pdf_file in papers_dir.glob("*.pdf"):
    metadata = extract_paper_metadata(pdf_file)
    if metadata:
        reference_db.append(metadata)

# Save database
with open("reference_database.json", "w") as f:
    json.dump(reference_db, f, indent=2)

print(f"Processed {len(reference_db)} papers")
```

### Workflow 2: Deduplicate References

```python
import difflib

def deduplicate_references(references):
    """Deduplicate references by title similarity."""
    unique_refs = []
    seen_titles = []

    for ref in references:
        title = ref.get("title", "").lower()

        # Check similarity with existing titles
        is_duplicate = False
        for seen_title in seen_titles:
            similarity = difflib.SequenceMatcher(None, title, seen_title).ratio()
            if similarity > 0.9:  # 90% similarity threshold
                is_duplicate = True
                break

        if not is_duplicate:
            unique_refs.append(ref)
            seen_titles.append(title)

    return unique_refs

# Use with reference database
with open("reference_database.json") as f:
    all_refs = json.load(f)

unique_refs = deduplicate_references(all_refs)
print(f"Reduced {len(all_refs)} to {len(unique_refs)} unique references")
```

### Workflow 3: Create Citation Network

```python
import json
from collections import defaultdict

def build_citation_network(reference_db):
    """Build citation network from reference database."""
    network = defaultdict(list)

    for paper in reference_db:
        source = paper["title"]
        cited_papers = paper.get("citations", [])

        for citation in cited_papers:
            network[source].append(citation)

    return dict(network)

# Build network
with open("reference_database.json") as f:
    refs = json.load(f)

network = build_citation_network(refs)

# Find most cited papers
citation_counts = defaultdict(int)
for paper, citations in network.items():
    for cited in citations:
        citation_counts[cited] += 1

top_cited = sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)[:10]

print("Top 10 most cited:")
for paper, count in top_cited:
    print(f"  {count:3d} - {paper}")
```

### Workflow 4: Export to BibTeX File

```python
def create_bibtex_file(papers, output_path="references.bib"):
    """Create BibTeX file from paper metadata."""
    with open(output_path, "w") as f:
        for i, paper in enumerate(papers, 1):
            # Create entry key
            first_author = paper.get("authors", ["Unknown"])[0].split()[-1].lower()
            year = paper.get("year", "n.d.")
            key = f"{first_author}{year}"

            # Write entry
            f.write(f"@article{{{key},\n")
            f.write(f"    title = {{{paper.get('title', 'Unknown')}}},\n")

            if "authors" in paper:
                authors = " and ".join(paper["authors"])
                f.write(f"    author = {{{authors}}},\n")

            f.write(f"    year = {{{year}}},\n")

            if "journal" in paper:
                f.write(f"    journal = {{{paper['journal']}}},\n")

            if "doi" in paper:
                f.write(f"    doi = {{{paper['doi']}}},\n")

            f.write("}\n\n")

    print(f"Created {output_path} with {len(papers)} entries")

# Use with reference database
with open("reference_database.json") as f:
    papers = json.load(f)

create_bibtex_file(papers)
```

## Integration with External Tools

### DOI Lookup via CrossRef API

```python
import requests

def get_metadata_from_doi(doi):
    """Fetch paper metadata from CrossRef using DOI."""
    url = f"https://api.crossref.org/works/{doi}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["message"]

        return {
            "title": data.get("title", [""])[0],
            "authors": [
                f"{author.get('family', '')}, {author.get('given', '')}"
                for author in data.get("author", [])
            ],
            "year": data.get("published-print", {}).get("date-parts", [[None]])[0][0],
            "journal": data.get("container-title", [""])[0],
            "volume": data.get("volume", ""),
            "pages": data.get("page", ""),
            "doi": doi
        }
    except Exception as e:
        print(f"Error fetching DOI {doi}: {e}")
        return None

# Example usage
metadata = get_metadata_from_doi("10.1016/j.jdeveco.2020.102468")
if metadata:
    paper = Paper(**metadata)
    print(paper.to_bibtex())
```

### Export to Zotero CSV Format

```python
import csv

def export_to_zotero_csv(papers, output_path="zotero_import.csv"):
    """Export to Zotero CSV format."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "Item Type", "Title", "Author", "Year", "Publication Title",
            "Volume", "Pages", "DOI", "URL"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for paper in papers:
            writer.writerow({
                "Item Type": "journalArticle",
                "Title": paper.get("title", ""),
                "Author": "; ".join(paper.get("authors", [])),
                "Year": paper.get("year", ""),
                "Publication Title": paper.get("journal", ""),
                "Volume": paper.get("volume", ""),
                "Pages": paper.get("pages", ""),
                "DOI": paper.get("doi", ""),
                "URL": f"https://doi.org/{paper['doi']}" if paper.get("doi") else ""
            })

    print(f"Exported {len(papers)} papers to {output_path}")
```

## Common Patterns

### Pattern 1: Extract→Validate→Export

```python
# 1. Extract from PDFs
papers = []
for pdf in Path("papers").glob("*.pdf"):
    metadata = extract_paper_metadata(pdf)
    if metadata:
        papers.append(metadata)

# 2. Validate and enrich with DOI lookup
enriched = []
for paper in papers:
    if paper.get("doi"):
        # Enrich with CrossRef data
        metadata = get_metadata_from_doi(paper["doi"])
        if metadata:
            enriched.append(metadata)
    else:
        enriched.append(paper)

# 3. Deduplicate
unique_papers = deduplicate_references(enriched)

# 4. Export to BibTeX
create_bibtex_file(unique_papers, "library.bib")
```

### Pattern 2: Build Systematic Review Database

```python
# Create structured database for systematic review
review_db = []

for paper_metadata in papers:
    entry = {
        "id": len(review_db) + 1,
        "title": paper_metadata["title"],
        "authors": paper_metadata.get("authors", []),
        "year": paper_metadata.get("year"),
        "doi": paper_metadata.get("doi"),
        "inclusion_status": "pending",  # pending, included, excluded
        "exclusion_reason": None,
        "quality_score": None,
        "extracted_data": {},
        "notes": ""
    }
    review_db.append(entry)

# Save for screening
with open("systematic_review.json", "w") as f:
    json.dump(review_db, f, indent=2)
```

## Integration with Research Workflow

```text
PDF Papers
    │
    ▼
pdf-processor skill
    │
    ▼
Markdown + metadata
    │
    ▼
bibliography skill
    │
    ├─→ Extract citations
    ├─→ Build reference database
    ├─→ Deduplicate
    └─→ Generate BibTeX
    │
    ▼
references.bib / database.json
    │
    ▼
research-analyst (systematic review)
```

## Best Practices

1. **Always extract DOI** - Enables automatic metadata enrichment
2. **Deduplicate early** - Prevents duplicate entries in database
3. **Validate metadata** - Check against CrossRef/DOI lookup
4. **Use consistent formats** - Stick to BibTeX or structured JSON
5. **Track source files** - Link references back to original PDFs

## Resources

- CrossRef API: <https://api.crossref.org/>
- BibTeX format: <http://www.bibtex.org/Format/>
- Zotero import: <https://www.zotero.org/support/kb/importing_standardized_formats>

## See Also

- **pdf-processor** - Extract text from papers for citation mining
- **research-analyst** - Systematic review and meta-analysis workflow
