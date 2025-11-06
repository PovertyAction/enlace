---
name: research-analyst
description: This skill should be used when conducting systematic literature reviews and analyzing research papers. Use this skill to extract and document key information from academic papers including study design, methodology, data characteristics, analytical approaches, results, and implications. Produces structured, comprehensive notes suitable for research synthesis and meta-analysis.
---

# Research Analyst Literature Review Skill

## Purpose

This skill provides systematic guidance for conducting thorough literature reviews and extracting detailed information from research papers. It enables meticulous documentation of study characteristics, methodologies, and findings in a structured format suitable for research synthesis, meta-analysis, and evidence assessment.

## When to Use This Skill

Use this skill when:

- Conducting systematic literature reviews
- Extracting information from research papers
- Analyzing RCT studies and impact evaluations
- Documenting study methodologies and results
- Preparing evidence synthesis reports
- Building literature databases
- Reviewing papers for research proposals
- Comparing methodologies across studies
- Extracting effect sizes for meta-analysis
- Assessing study quality and risk of bias

## Core Methodology

### Systematic Documentation Framework

This skill follows a comprehensive framework for documenting research papers:

1. **Bibliographic Information**: Authors, publication details, citation
2. **Research Context**: Background, research questions, hypotheses
3. **Study Design**: Type of study, experimental design, timeline
4. **Data Collection**: Sources, methods, instruments, procedures
5. **Sample Characteristics**: Size, demographics, selection, location
6. **Variables and Measures**: Outcomes, treatments, controls, instruments
7. **Analytical Methods**: Statistical approaches, models, software
8. **Results**: Effect sizes, statistical significance, robustness
9. **Quality Assessment**: Internal validity, external validity, bias
10. **Implications**: Interpretation, limitations, contributions

## Paper Analysis Workflow

### Step 1: Initial Document Processing

When provided with a research paper (PDF converted to markdown via marker or docling):

```markdown
# Initial Assessment

**Document received**: [filename]
**Conversion method**: [marker/docling]
**Initial scan**: [page count, sections identified]
**Paper type**: [RCT/Observational/Review/Meta-analysis]
```

### Step 2: Bibliographic Extraction

Extract complete citation information:

```markdown
## Bibliographic Information

**Authors**: [Full list with affiliations]
**Title**: [Complete title]
**Journal/Publisher**: [Name, volume, issue]
**Publication Year**: [Year]
**DOI/URL**: [Persistent identifier]
**Keywords**: [Author keywords]
**JEL Codes**: [If applicable]

**Citation (APA)**:
[Formatted citation]

**Citation (BibTeX)**:
```bibtex
@article{key,
    author = {},
    title = {},
    journal = {},
    year = {},
    volume = {},
    pages = {},
    doi = {}
}
```text

```

### Step 3: Research Context Documentation

```markdown
## Research Context

### Background
[Summarize the research problem, gap in literature, and motivation]

### Research Questions
1. [Primary research question]
2. [Secondary research questions]

### Hypotheses
- H1: [If explicitly stated]
- H2: [...]

### Theoretical Framework
[Economic theory, conceptual model, or theoretical approach]

### Contribution
[Stated contribution to literature]
```

### Step 4: Study Design Documentation

```markdown
## Study Design

### Study Type
- **Design**: [RCT/Quasi-experimental/Observational/etc.]
- **Setting**: [Lab/Field/Natural experiment]
- **Unit of Analysis**: [Individual/Household/Cluster]
- **Timeline**: [Cross-sectional/Panel/Longitudinal]

### Experimental Design (if RCT)

#### Randomization
- **Randomization level**: [Individual/Cluster]
- **Randomization method**: [Simple/Stratified/Block]
- **Stratification variables**: [List variables]
- **Timing**: [When randomization occurred]
- **Assignment ratio**: [e.g., 1:1, 2:1]

#### Treatment Arms
1. **Treatment Group**: [Description]
2. **Control Group**: [Description]
3. **Additional Arms**: [If applicable]

#### Implementation
- **Treatment delivery**: [How intervention was delivered]
- **Duration**: [Length of treatment period]
- **Compliance**: [Adherence mechanisms]
- **Contamination controls**: [Spillover prevention]

### Power Analysis
- **Conducted**: [Yes/No]
- **Target power**: [e.g., 0.80]
- **Minimum detectable effect (MDE)**: [Size]
- **Assumptions**: [Key assumptions used]
- **Sample size determination**: [Method]

### Pre-registration
- **Pre-analysis plan**: [Yes/No, registry]
- **Registration ID**: [If available]
- **Deviations**: [Noted deviations from PAP]
```

### Step 5: Data Collection Documentation

```markdown
## Data Collection

### Data Sources
1. **Primary data**: [Survey/Administrative/Experimental]
2. **Secondary data**: [If used]
3. **Additional sources**: [Qualitative/Mixed methods]

### Collection Methods
- **Instruments**: [Surveys, tests, observations]
- **Survey mode**: [In-person/Phone/Online/Mixed]
- **Language**: [Survey language(s)]
- **Duration**: [Time to complete]

### Data Collection Timeline
- **Baseline**: [Date/Period]
- **Endline**: [Date/Period]
- **Midline**: [If applicable]
- **Follow-up**: [Additional waves]

### Quality Control
- **Enumerator training**: [Details]
- **Pilot testing**: [Yes/No]
- **Data validation**: [Real-time checks, back-checks]
- **Supervision**: [Field supervision methods]

### Ethical Considerations
- **IRB approval**: [Institution, ID number]
- **Informed consent**: [Process]
- **Data protection**: [Privacy measures]
```

### Step 6: Sample Characteristics

```markdown
## Sample Characteristics

### Target Population
- **Definition**: [Who the study targets]
- **Geographic location**: [Country, region, sites]
- **Setting**: [Urban/Rural/Mixed]
- **Context**: [Relevant contextual factors]

### Sampling Strategy
- **Sampling frame**: [Population list/database]
- **Sampling method**: [Random/Stratified/Convenience/etc.]
- **Selection criteria**: [Inclusion/exclusion criteria]

### Sample Size
- **Target sample**: [Planned N]
- **Achieved sample**: [Actual N]
- **By treatment arm**:
  - Control: N = [number]
  - Treatment: N = [number]
- **Clusters**: [If cluster design]
  - Number of clusters: [N]
  - Average cluster size: [N]

### Attrition
- **Overall attrition rate**: [%]
- **By treatment arm**:
  - Control: [%]
  - Treatment: [%]
- **Differential attrition**: [Test results]
- **Reasons for attrition**: [If documented]

### Baseline Characteristics

| Variable | Control Mean (SD) | Treatment Mean (SD) | Difference | P-value |
|----------|-------------------|---------------------|------------|---------|
| Age | [mean (sd)] | [mean (sd)] | [diff] | [p] |
| Gender (% female) | [%] | [%] | [diff] | [p] |
| [Variable] | [...] | [...] | [...] | [...] |

**Balance test**: [Result of joint F-test or chi-square test]

### Demographics
- **Age**: [Range, mean, distribution]
- **Gender**: [Breakdown]
- **Education**: [Levels, years]
- **Income/SES**: [Measures]
- **Other relevant characteristics**: [Ethnicity, occupation, etc.]
```

### Step 7: Variables and Measures

```markdown
## Variables and Measures

### Primary Outcomes
1. **[Outcome name]**
   - Definition: [How measured]
   - Type: [Continuous/Binary/Count/Ordinal]
   - Scale/Units: [Measurement scale]
   - Source: [Survey item, administrative data]
   - Timing: [When measured]
   - Pre-specified: [Yes/No]

### Secondary Outcomes
[Same structure as primary outcomes]

### Treatment Variable
- **Name**: [Variable name]
- **Definition**: [Description]
- **Coding**: [0/1 or other]
- **Intensity**: [Dose, duration]

### Control Variables
- **Pre-specified controls**: [List]
- **Baseline covariates**: [List]
- **Fixed effects**: [List]
- **Rationale**: [Why included]

### Instrumental Variables (if IV design)
- **Instrument(s)**: [Name(s)]
- **Relevance**: [Correlation with endogenous variable]
- **Validity**: [Exclusion restriction argument]
- **Test statistics**: [F-stat, etc.]

### Mediating Variables
[If mediation analysis conducted]

### Moderating Variables
[If heterogeneity analysis conducted]

### Data Quality
- **Missing data**: [Extent by variable]
- **Outliers**: [Treatment of outliers]
- **Measurement error**: [Discussion]
- **Variable transformations**: [Logs, standardization, etc.]
```

### Step 8: Analytical Methods

```markdown
## Analytical Methods

### Software
- **Primary software**: [Stata/R/Python/etc.]
- **Version**: [If specified]
- **Packages**: [Key packages used]

### Statistical Approach

#### Primary Analysis
- **Model type**: [OLS/Probit/Poisson/IV/DiD/etc.]
- **Specification**: [Equation or description]
- **Estimation method**: [Method details]

**Primary specification**:
```

[Write out regression equation]

```text

#### Standard Errors
- **Type**: [Robust/Clustered/Bootstrap]
- **Clustering level**: [If clustered]
- **Justification**: [Why this SE type]

#### Fixed Effects
- **Included**: [List of FE]
- **Purpose**: [Control for what]

### Robustness Checks
1. **[Check 1]**: [Alternative specification]
2. **[Check 2]**: [Different SE]
3. **[Check 3]**: [Sample restrictions]
4. **[Check 4]**: [Alternative measures]

### Heterogeneity Analysis
- **Subgroups**: [Pre-specified subgroups]
- **Interaction terms**: [Tested interactions]
- **Multiple testing**: [Correction method]

### Sensitivity Analysis
- **Attrition**: [Lee bounds, IPW]
- **Outliers**: [Trimming, winsorizing]
- **Missing data**: [Imputation, MI]
- **Specification**: [Model variations]

### Additional Tests
- **Balance tests**: [Method, results]
- **Parallel trends**: [If DiD]
- **First stage**: [If IV]
- **Overidentification**: [If IV with multiple instruments]
- **Placebo tests**: [If conducted]
```

### Step 9: Results Documentation

```markdown
## Results

### Main Treatment Effects

#### Primary Outcome: [Outcome name]

**Table location**: [Table number in paper]

| Specification | Coefficient | SE | t-stat | p-value | 95% CI | N |
|---------------|-------------|-----|--------|---------|---------|---|
| (1) Simple | [β] | [se] | [t] | [p] | [ci] | [n] |
| (2) With controls | [β] | [se] | [t] | [p] | [ci] | [n] |
| (3) Preferred spec | [β] | [se] | [t] | [p] | [ci] | [n] |

**Effect size interpretation**:
- Coefficient: [β value and units]
- Control mean: [baseline level]
- Effect size: [% of control mean or standardized effect]
- Statistical significance: [*** p<0.01, ** p<0.05, * p<0.1]
- Economic significance: [Interpretation]

**Authors' interpretation**: [Quote or paraphrase key interpretation]

#### Secondary Outcomes

[Same table structure for each secondary outcome]

**Multiple testing correction**: [Method, adjusted p-values if applicable]

### Heterogeneous Effects

#### By [Subgroup variable]

| Subgroup | Coefficient | SE | p-value | N |
|----------|-------------|-----|---------|---|
| [Group 1] | [β] | [se] | [p] | [n] |
| [Group 2] | [β] | [se] | [p] | [n] |

**Interaction p-value**: [p-value for interaction test]

**Interpretation**: [Authors' interpretation of heterogeneity]

### Robustness Results

| Specification | Primary outcome β | SE | p-value |
|---------------|-------------------|-----|---------|
| Baseline | [β] | [se] | [p] |
| [Robustness 1] | [β] | [se] | [p] |
| [Robustness 2] | [β] | [se] | [p] |

**Robustness interpretation**: [Are results stable?]

### Mechanism Analysis

[If authors test mechanisms]

**Proposed mechanism**: [Theory]

**Mediating variable**: [Variable name]

**Results**: [Findings on mechanism]

### Additional Findings
- [Other notable results]
- [Unexpected findings]
- [Null results]
```

### Step 10: Quality Assessment

```markdown
## Quality Assessment

### Internal Validity

#### Randomization Quality
- **Balance achieved**: [Yes/No, evidence]
- **Baseline equivalence**: [Statistical tests]
- **Randomization integrity**: [Concerns if any]

#### Attrition
- **Overall level**: [Low/Moderate/High]
- **Differential attrition**: [Tested, results]
- **Attrition bias**: [Likely direction, magnitude]

#### Compliance
- **Take-up rate**: [%]
- **Treatment group compliance**: [%]
- **Control group contamination**: [%]
- **ITT vs TOT**: [Both estimated?]

#### Spillovers
- **Risk of spillovers**: [Low/Medium/High]
- **Evidence of spillovers**: [If tested]
- **Impact on estimates**: [Direction of bias]

#### Hawthorne/John Henry Effects
- **Risk**: [Assessment]
- **Evidence**: [If discussed]

### External Validity

#### Population
- **Representativeness**: [Of what population]
- **Selection bias**: [In enrollment]
- **Generalizability**: [To whom]

#### Setting
- **Context specificity**: [How specific]
- **Transportability**: [To other settings]

#### Intervention
- **Scalability**: [Can it be scaled]
- **Implementation fidelity**: [Adherence to protocol]
- **Cost-effectiveness**: [If discussed]

### Statistical Power
- **Adequately powered**: [Yes/No]
- **Achieved power**: [If calculable]
- **Precision**: [Width of confidence intervals]

### Risk of Bias Assessment

Use Cochrane Risk of Bias tool or similar:

| Domain | Risk Level | Justification |
|--------|------------|---------------|
| Selection bias | [Low/Some/High] | [Reason] |
| Performance bias | [Low/Some/High] | [Reason] |
| Detection bias | [Low/Some/High] | [Reason] |
| Attrition bias | [Low/Some/High] | [Reason] |
| Reporting bias | [Low/Some/High] | [Reason] |

**Overall risk of bias**: [Low/Moderate/High]

### Transparency and Replicability
- **Pre-analysis plan**: [Public, followed]
- **Data availability**: [Public/Restricted/Not available]
- **Code availability**: [Public/Available on request/Not available]
- **Replication package**: [Complete/Partial/None]
- **Clear documentation**: [Yes/No]
```

### Step 11: Implications and Discussion

```markdown
## Discussion and Implications

### Authors' Interpretation
[Summarize how authors interpret their findings]

### Contribution to Literature
- **Novel contribution**: [What's new]
- **Confirmation/Contradiction**: [With prior work]
- **Literature gap addressed**: [What gap filled]

### Theoretical Implications
[What the results mean for theory]

### Policy Implications
- **Actionable recommendations**: [List]
- **Cost-benefit**: [If discussed]
- **Implementation considerations**: [Practical concerns]

### Limitations

#### Acknowledged by Authors
1. [Limitation 1]
2. [Limitation 2]
3. [...]

#### Additional Concerns
[Reviewer-identified limitations not discussed by authors]

### Future Research
- **Suggested by authors**: [Directions]
- **Gaps remaining**: [What's still unknown]
- **Needed replications**: [In other contexts]

### Reviewer Comments
[Critical analysis, concerns, strengths]
```

### Step 12: Research Summary

```markdown
## Executive Summary

**Study in one sentence**: [Concise description]

**Key finding**: [Main result in plain language]

**Effect size**: [Magnitude in interpretable units]

**Quality rating**: [High/Medium/Low]

**Relevance to [your research]**: [How it relates to your work]

**Critical takeaway**: [Most important lesson]
```

## Templates for Different Study Types

### RCT Template

See sections above - this is the primary template structure.

### Observational Study Template

For non-experimental studies, adapt the template to focus on:

- **Identification strategy**: [IV/DiD/RDD/Matching/etc.]
- **Causal assumptions**: [Required assumptions]
- **Validation of assumptions**: [Tests conducted]
- **Endogeneity concerns**: [Potential confounding]
- **Selection bias**: [Magnitude and direction]

### Systematic Review/Meta-Analysis Template

Focus on:

- **Search strategy**: [Databases, keywords, dates]
- **Inclusion criteria**: [PICOS framework]
- **Studies included**: [Number, characteristics]
- **Effect size measures**: [Standardized measures used]
- **Heterogeneity**: [I², τ², Q-statistic]
- **Publication bias**: [Funnel plot, Egger's test]
- **Pooled estimates**: [Fixed/random effects results]

### Qualitative Study Template

Focus on:

- **Research design**: [Ethnography/Case study/etc.]
- **Data collection**: [Interviews/Focus groups/Observations]
- **Sample**: [Purposive sampling strategy]
- **Analysis method**: [Thematic/Content/Discourse analysis]
- **Findings**: [Key themes]
- **Trustworthiness**: [Credibility, transferability]

## Note Organization System

### File Naming Convention

```json
[Year]_[FirstAuthorLastName]_[ShortTitle].md
```

Example: `2023_Dupas_HealthInsurance.md`

### Folder Structure

```text
literature_review/
├── papers/
│   ├── rct/
│   ├── observational/
│   ├── reviews/
│   └── methods/
├── extraction/
│   └── [Individual paper notes]
├── synthesis/
│   ├── by_topic/
│   ├── by_method/
│   └── by_outcome/
└── meta_analysis/
    └── effect_size_database.csv
```

### Linking Papers

Create cross-references between related papers:

```markdown
**Related papers**:
- Similar intervention: [Author Year]
- Different context: [Author Year]
- Methodological comparison: [Author Year]
- Contradictory findings: [Author Year]
```

## Extraction Best Practices

### Accuracy

1. **Quote directly** for key claims and results
2. **Page numbers** for all extracted information
3. **Verify numbers** - check tables match text
4. **Note discrepancies** if inconsistencies found

### Completeness

1. **Extract all relevant tables** - copy key tables
2. **Document appendices** - note supplementary materials
3. **Capture footnotes** - often contain critical details
4. **Include limitations** - even minor ones

### Consistency

1. **Use templates** - same structure for all papers
2. **Standardize units** - convert to common metrics
3. **Consistent coding** - use same category labels
4. **Date stamping** - note when extracted

### Critical Analysis

1. **Question assumptions** - are they reasonable?
2. **Assess methods** - appropriate for question?
3. **Evaluate evidence** - how strong?
4. **Note concerns** - what's missing or unclear?

## Common Paper Sections and What to Extract

### Abstract

- Main research question
- Sample size
- Key finding
- Effect size

### Introduction

- Research gap
- Contribution
- Research questions

### Literature Review

- Prior findings
- Theoretical framework
- Hypothesis development

### Methods

- ALL methodological details (see templates above)
- Data collection procedures
- Analytical strategy

### Results

- ALL numerical results
- Tables and figures
- Statistical tests

### Discussion

- Interpretation
- Limitations
- Implications

### Appendices

- Additional results
- Robustness checks
- Survey instruments
- Balance tables

## Integration with Other Skills

### Using with Marker/Docling Skills

```bash
# Convert PDF to markdown first
marker_single paper.pdf --output_dir output/

# Or with docling
docling convert paper.pdf

# Then analyze with this skill
# Claude will systematically extract information
```

### Using with PyFixest Skill

When documenting regression results:

- Note model specifications
- Extract coefficients and SEs
- Document standard error type
- Note fixed effects

Can verify or replicate results if data available.

### Using with Stata Skill

When documenting Stata-based studies:

- Note Stata commands used
- Extract do-file information
- Document packages required
- Note Stata version

### Creating Effect Size Database

Extract for meta-analysis:

```csv
study,year,outcome,treatment_coef,se,n_treatment,n_control,effect_size_d
Dupas2023,2023,enrollment,0.15,0.03,500,500,0.42
```

## Quality Control Checklist

Before considering a paper extraction complete:

- [ ] Full citation captured with DOI
- [ ] Research question clearly stated
- [ ] Sample size documented (all arms)
- [ ] Outcome variables defined with units
- [ ] Treatment effect sizes extracted
- [ ] Standard errors and p-values noted
- [ ] Sample characteristics documented
- [ ] Analytical method described
- [ ] Robustness checks summarized
- [ ] Limitations documented
- [ ] Page numbers noted for key information
- [ ] Tables referenced or copied
- [ ] Quality assessment completed
- [ ] Reviewer comments added
- [ ] File named properly and saved

## Reporting Standards

### For Evidence Synthesis

When synthesizing across papers:

1. **Study characteristics table**
   - All included studies
   - Key design features
   - Sample sizes
   - Quality ratings

2. **Results synthesis**
   - Direction of effects
   - Magnitude of effects
   - Consistency across studies
   - Heterogeneity exploration

3. **Quality summary**
   - Risk of bias assessment
   - Internal validity threats
   - External validity concerns

### For Research Proposals

Extract to inform your own study:

- Sample size justifications
- Power calculations from similar studies
- Outcome measure options
- Data collection methods
- Analytical approaches
- Expected effect sizes

## Advanced Features

### Comparative Analysis

When comparing multiple papers on same topic:

```markdown
## Comparative Analysis: [Topic]

| Study | Design | N | Outcome | Effect Size | Quality |
|-------|--------|---|---------|-------------|---------|
| Study 1 | RCT | 1000 | Y | 0.25*** | High |
| Study 2 | Quasi | 500 | Y | 0.18* | Med |
| Study 3 | RCT | 2000 | Y | 0.30*** | High |

**Pattern**: [What emerges across studies]
**Heterogeneity**: [Why effects differ]
**Conclusion**: [Synthesis]
```

### Evidence Grading

Use GRADE or similar system:

- **High quality**: RCT with low risk of bias
- **Moderate quality**: RCT with some concerns or strong quasi
- **Low quality**: Observational with limitations
- **Very low quality**: Serious methodological flaws

### Meta-Analytic Preparation

For quantitative synthesis:

```python
import polars as pl

# Effect size database
effects = pl.DataFrame({
    'study': ['Study1', 'Study2', 'Study3'],
    'yi': [0.25, 0.18, 0.30],  # Effect sizes
    'vi': [0.01, 0.02, 0.015],  # Variances
    'n_total': [1000, 500, 2000],
    'quality': ['high', 'medium', 'high']
})
```

## Tips for Efficient Review

1. **Skim first**: Read abstract, intro, results, conclusion
2. **Identify relevance**: Is it worth full extraction?
3. **Systematic extraction**: Use template every time
4. **Immediate notes**: Don't delay documentation
5. **Critical lens**: Question everything
6. **Cross-reference**: Link to related papers
7. **Version control**: Track extraction dates
8. **Regular synthesis**: Don't just extract, synthesize

## Common Pitfalls to Avoid

1. **Incomplete extraction**: Missing key details
2. **Uncritical acceptance**: Taking claims at face value
3. **Selective extraction**: Only positive results
4. **Inconsistent coding**: Different standards per paper
5. **Lost context**: Not noting limitations
6. **Ignoring appendices**: Supplementary materials matter
7. **No synthesis**: Just extracting without integrating
8. **Unclear notes**: Future you needs to understand

## Resources

### Research Quality Assessment Tools

- Cochrane Risk of Bias tool (RCTs)
- ROBINS-I tool (observational studies)
- GRADE system (evidence quality)
- Newcastle-Ottawa Scale (case-control/cohort)
- CASP checklists (various designs)

### Citation Management

- Use with Zotero/Mendeley for bibliography
- Extract BibTeX for LaTeX documents
- Maintain consistent citation keys

### Recommended Reading

- Cochrane Handbook for Systematic Reviews
- Campbell Collaboration guidelines
- PRISMA guidelines for reporting
- CONSORT statement for RCTs
- STROBE statement for observational studies
