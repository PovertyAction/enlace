# Research Analyst Literature Review Skill

A comprehensive skill for systematic literature reviews and meticulous extraction of information from research papers.

## Overview

This skill provides structured templates and workflows for conducting thorough literature reviews, particularly focused on impact evaluations, randomized controlled trials, and econometric studies. It ensures consistent, detailed documentation of study characteristics, methodologies, and findings.

## Purpose

Extract and document comprehensive information from research papers including:

- Study design and methodology
- Sample characteristics and data collection
- Variables and measures
- Analytical approaches
- Treatment effects and results
- Quality assessment
- Implications and limitations

## Contents

### Main Documentation

- **SKILL.md**: Complete methodology for systematic literature review and paper extraction

### Templates

Located in `templates/`:

- **rct_template.md**: Comprehensive template for randomized controlled trials
- **observational_template.md**: Template for observational studies with causal inference

### Helper Scripts

Located in `scripts/`:

- **extract_paper.py**: Interactive assistant for paper extraction

### Reference Materials

Located in `references/`:

- **extraction_checklist.md**: Quality control checklist
- **quality_assessment_guide.md**: Guidelines for risk of bias assessment
- **effect_size_guide.md**: Guide for documenting and interpreting effect sizes

## Quick Start

### Using with Docling

First, convert your PDF to markdown:

```bash
# Using docling
uv run docling paper.pdf
```

Then extract information using this skill:

```bash
python scripts/extract_paper.py --paper output/paper.md --type rct
```

### Manual Extraction

1. Choose appropriate template from `templates/`
2. Copy template to your extraction directory
3. Work through sections systematically
4. Reference paper while filling in each section

## Template Overview

### RCT Template Sections

1. **Bibliographic Information**: Full citation, DOI, keywords
2. **Research Context**: Questions, hypotheses, theory
3. **Study Design**: Randomization, treatment arms, power analysis
4. **Data Collection**: Methods, timeline, quality control
5. **Sample Characteristics**: Size, demographics, balance, attrition
6. **Variables and Measures**: Outcomes, treatment, controls
7. **Analytical Methods**: Models, standard errors, robustness
8. **Results**: Treatment effects, heterogeneity, tables
9. **Quality Assessment**: Internal/external validity, risk of bias
10. **Discussion**: Interpretation, limitations, implications
11. **Synthesis**: Key takeaways, relevance to your research

### Observational Study Template

Adapted for non-experimental studies with focus on:

- Identification strategy (IV/DiD/RDD/Matching)
- Causal assumptions and validation
- Endogeneity concerns
- Selection bias
- Threats to identification

## Key Features

### Systematic Documentation

- Standardized structure across all papers
- Ensures no critical information missed
- Facilitates comparison across studies
- Supports meta-analysis preparation

### Quality Assessment

Includes frameworks for:

- Cochrane Risk of Bias assessment
- GRADE evidence quality rating
- Internal and external validity evaluation
- Statistical conclusion validity

### Critical Analysis

Prompts for:

- Methodological strengths and weaknesses
- Credibility of causal claims
- Generalizability assessment
- Comparison to related literature

### Research Synthesis

Supports:

- Cross-study comparisons
- Effect size databases
- Evidence synthesis tables
- Gap identification

## Workflow

### Individual Paper Extraction

```text
1. Convert PDF → Markdown (docling)
   ↓
2. Initialize extraction (extract_paper.py)
   ↓
3. Systematic extraction (follow template)
   ↓
4. Quality check (extraction_checklist.md)
   ↓
5. Save with standardized filename
```

### Systematic Review

```text
1. Define inclusion criteria
   ↓
2. Search and screen papers
   ↓
3. Extract each paper (templates)
   ↓
4. Quality assessment (all papers)
   ↓
5. Create synthesis tables
   ↓
6. Meta-analysis (if applicable)
```

## File Organization

Recommended structure:

```text
literature_review/
├── papers/              # Original PDFs
│   ├── rct/
│   └── observational/
├── extraction/          # Completed extractions
│   ├── 2023_Author_Title.md
│   └── ...
├── synthesis/           # Cross-study analysis
│   ├── evidence_table.csv
│   ├── quality_summary.md
│   └── meta_analysis/
└── references.bib       # Bibliography
```

### File Naming Convention

```json
[Year]_[FirstAuthorLastName]_[ShortTitle].md
```

Examples:

- `2023_Dupas_HealthInsurance.md`
- `2022_Banerjee_UniversalBasicIncome.md`

## Integration with Other Skills

### With Docling Skill

Convert PDFs to markdown before extraction:

```bash
# High-quality conversion
uv run docling paper.pdf

# Then extract
python scripts/extract_paper.py --paper papers/paper.md
```

### With PyFixest Skill

When documenting regression results:

- Use PyFixest terminology for models
- Note which PyFixest functions would replicate analysis
- Extract information useful for replication

### With Stata Skill

When reviewing Stata-based studies:

- Document Stata commands used
- Note packages required
- Map to equivalent PyFixest approaches

## Extraction Best Practices

### Accuracy

- Quote directly for key claims (with page numbers)
- Verify numbers match across tables and text
- Note any discrepancies
- Double-check effect sizes

### Completeness

- Extract all relevant tables
- Review appendices and supplementary materials
- Document all robustness checks
- Include limitations authors acknowledge

### Consistency

- Use same template for all similar studies
- Standardize units and metrics
- Consistent terminology
- Date stamp all extractions

### Critical Lens

- Question assumptions
- Assess appropriateness of methods
- Evaluate strength of evidence
- Note concerns or red flags

## Quality Control

Before considering extraction complete:

- [ ] Full citation with DOI
- [ ] Research questions clearly stated
- [ ] Sample size documented
- [ ] Treatment effects extracted with SEs
- [ ] Analytical method described
- [ ] Quality assessment completed
- [ ] Page numbers for key info
- [ ] Reviewer comments added

## Common Use Cases

### Research Proposal

- Identify effect sizes for power calculations
- Find appropriate outcome measures
- Review similar methodologies
- Identify gaps in literature

### Systematic Review

- Consistent extraction across papers
- Risk of bias assessment
- Effect size database
- Evidence synthesis

### Replication Study

- Detailed methodology documentation
- Identify data sources
- Note analytical choices
- Compare approaches

### Meta-Analysis

- Extract effect sizes and SEs
- Document sample sizes
- Note study characteristics
- Code moderators

## Output Examples

### Evidence Summary Table

| Study | Design | N | Outcome | Effect | SE | Quality |
|-------|--------|---|---------|--------|-----|---------|
| Dupas 2023 | RCT | 5000 | Enrollment | 0.15 | 0.03 | High |
| Banerjee 2022 | RCT | 2000 | Income | 120 | 35 | High |

### Effect Size Database

```csv
study,year,outcome,treatment_coef,se,n_total,n_treatment,n_control,quality
Dupas2023,2023,enrollment,0.15,0.03,5000,2500,2500,high
Banerjee2022,2022,income,120,35,2000,1000,1000,high
```

## Tips for Efficient Extraction

1. **Skim First**: Read abstract, intro, results, conclusion
2. **Assess Relevance**: Is full extraction needed?
3. **Systematic Approach**: Follow template every time
4. **Immediate Documentation**: Don't delay note-taking
5. **Critical Thinking**: Question everything
6. **Link Papers**: Cross-reference related studies
7. **Regular Breaks**: Complex extraction takes time
8. **Synthesize Ongoing**: Don't just extract, integrate

## Time Estimates

### Thorough RCT Extraction

- Simple paper: 3-4 hours
- Complex paper: 4-6 hours
- With appendices: 5-8 hours

### Quick Screening

- Relevance assessment: 15-30 minutes
- Key results extraction: 30-60 minutes

### Quality Assessment

- Risk of bias: 30-45 minutes
- Full quality review: 1-2 hours

## Quality Assessment Resources

### Risk of Bias Tools

- **Cochrane RoB 2**: For RCTs
- **ROBINS-I**: For observational studies
- **Newcastle-Ottawa Scale**: For case-control/cohort
- **GRADE**: Overall evidence quality

### Reporting Standards

- **CONSORT**: RCT reporting
- **STROBE**: Observational studies
- **PRISMA**: Systematic reviews
- **TREND**: Quasi-experimental designs

## Advanced Features

### Comparative Analysis

- Side-by-side study comparison
- Pattern identification across studies
- Heterogeneity exploration
- Synthesis of findings

### Evidence Grading

- GRADE quality assessment
- Strength of evidence
- Certainty in estimates
- Recommendation strength

### Meta-Analytic Preparation

- Effect size extraction
- Variance calculations
- Study weights
- Heterogeneity measures

## Resources

### Citation Management

- Integrate with Zotero/Mendeley
- Maintain BibTeX database
- Consistent citation keys

### Collaboration

- Share templates with team
- Standardize extraction
- Quality control procedures
- Inter-rater reliability

### Version Control

- Track extraction dates
- Note updates to papers
- Maintain audit trail

## Support

For questions about:

- **Templates**: See template documentation in files
- **Quality assessment**: See `references/quality_assessment_guide.md`
- **Effect sizes**: See `references/effect_size_guide.md`
- **Workflow**: See SKILL.md

## Contributing

To improve this skill:

- Add templates for other study types
- Expand quality assessment guidance
- Add examples of completed extractions
- Share best practices

## Example Workflow

```bash
# 1. Convert paper to markdown
uv run docling dupas2023_health.pdf

# 2. Initialize extraction
python scripts/extract_paper.py \
    --paper papers/dupas2023_health.md \
    --type rct \
    --output extraction/2023_Dupas_Health.md

# 3. Complete extraction systematically
# Open extraction/2023_Dupas_Health.md and work through template

# 4. Quality check
# Review against extraction_checklist.md

# 5. Add to synthesis
# Update evidence table and cross-references
```

## License

This skill documentation follows the project's license.
