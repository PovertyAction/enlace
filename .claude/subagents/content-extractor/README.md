# Content Extractor Subagent

Comprehensive extraction of structured content from research papers.

## Quick Start

### Single Paper

```bash
# Extract all content from a paper
python extractor.py single papers/smith2020.pdf --output-dir extracted

# Extract only tables
python extractor.py single papers/smith2020.pdf --no-figures --no-citations
```

### Batch Processing

```bash
# Extract from multiple papers in catalog
python extractor.py batch papers_catalog.json --parallel --workers 4
```

## What It Extracts

1. **Tables** - All tables with classification (regression, summary, balance)
2. **Figures** - All figures with captions and metadata
3. **Citations** - Complete citation list with references
4. **Metadata** - Title, authors, year, DOI, journal
5. **Methodology** - Study design, sample size, treatment details

## Output Structure

```text
extracted/
└── smith2020/
    ├── extraction.json          # Complete extraction output
    ├── smith2020.md            # Converted markdown
    ├── tables/
    │   ├── table_1.json
    │   ├── table_1.csv
    │   └── table_1.html
    └── figures/
        ├── figure_1.png
        └── figure_2.png
```

## Integration

### As a Subagent

```python
from extractor import ContentExtractor

extractor = ContentExtractor(output_dir="extracted")

# Process single paper
result = await extractor.process_paper(
    paper_path="papers/smith2020.pdf",
    extract_tables=True,
    extract_figures=True
)

print(f"Extracted {len(result['tables'])} tables")
print(f"Quality score: {result['extraction_quality']:.2f}")
```

### Batch Processing

```python
# Process multiple papers
papers = [
    {"paper_id": "smith2020", "path": "papers/smith2020.pdf"},
    {"paper_id": "jones2021", "path": "papers/jones2021.pdf"}
]

result = await extractor.process_batch(
    papers=papers,
    parallel=True,
    workers=4
)

print(f"Processed {result['papers_successful']}/{result['papers_processed']} papers")
```

## Quality Assurance

Each extraction receives a quality score (0-1):

- **≥ 0.90** - Excellent, proceed with confidence
- **0.75-0.89** - Good, minor review recommended
- **0.60-0.74** - Fair, significant review needed
- **< 0.60** - Poor, manual extraction recommended

## Dependencies

- pdf-processor skill (marker/docling)
- table-validator skill
- bibliography skill
- research-analyst skill

## Next Steps

After extraction, use:

- **data-quality-checker** - Validate extractions
- **data-harmonizer** - Merge across studies
- **meta-synthesizer** - Perform meta-analysis

## Documentation

See `SUBAGENT.md` for complete specification and examples.
