# Research Paper Extraction: [Paper Title]

**Extraction Date**: [YYYY-MM-DD]
**Extracted By**: [Your name]
**Paper Type**: Observational Study

---

## Bibliographic Information

**Authors**: [Full list]
**Title**: [Complete title]
**Journal**: [Name]
**Year**: [Year]
**Volume/Issue/Pages**: [Details]
**DOI**: [DOI]

**Citation (APA)**: [Formatted citation]

**Keywords**: [Keywords]

---

## Research Context

### Background

[Research problem and motivation]

### Research Questions

1. [Primary question]
2. [Secondary questions]

### Theoretical Framework

[Theory underlying the study]

---

## Study Design

### Study Type

- **Design**: [Cross-sectional/Cohort/Case-control/Panel/Time series]
- **Observational Type**: [Prospective/Retrospective]
- **Unit of Analysis**: [Individual/Household/Firm/etc.]
- **Time Period**: [Start - End dates]

### Identification Strategy

- **Causal Inference Method**: [Natural experiment/IV/DiD/RDD/Matching/Synthetic control/Other]
- **Identification Assumption**: [Key assumption for causal identification]
- **Validation of Assumption**: [How tested? Results?]

#### If Instrumental Variables

- **Instrument**: [Name]
- **Relevance**: [First-stage F-stat]
- **Exclusion Restriction**: [Argument for validity]
- **Overidentification Test**: [If multiple instruments]

#### If Difference-in-Differences

- **Treatment Group**: [Who/what]
- **Control Group**: [Who/what]
- **Treatment Timing**: [When]
- **Parallel Trends**: [Tested? Result?]
- **Event Study**: [Conducted? Results?]

#### If Regression Discontinuity

- **Running Variable**: [Variable]
- **Cutoff**: [Threshold value]
- **Bandwidth**: [Selection method, value]
- **Manipulation Test**: [Result]
- **Continuity of Covariates**: [Tested? Result?]

#### If Matching/Propensity Score

- **Matching Method**: [PSM/CEM/Mahalanobis/etc.]
- **Matching Variables**: [List]
- **Balance Assessment**: [Achieved? Metrics?]
- **Common Support**: [Checked? % on/off support]

---

## Data

### Data Sources

1. **Primary Source**: [Name, type]
   - Years available: [Range]
   - Geographic coverage: [Coverage]
   - Unit of observation: [Unit]

2. **Secondary Sources**: [If additional data]

### Sample Selection

- **Target Population**: [Who]
- **Sampling Frame**: [Source]
- **Selection Criteria**: [Inclusion/exclusion]
- **Final Sample**: N = [number]

### Sample Characteristics

| Variable | Mean (SD) or % | N |
|----------|----------------|---|
| [Variable 1] | [value] | [n] |
| [Variable 2] | [value] | [n] |

### Data Quality

- **Missing Data**: [% by key variables]
- **Attrition** (if panel): [%]
- **Measurement Issues**: [Concerns]

---

## Variables

### Outcome Variables

1. **[Outcome 1]**:
   - Definition: [How measured]
   - Type: [Continuous/Binary/etc.]
   - Mean (SD): [value]

### Key Explanatory Variable(s)

- **[Variable]**: [Definition, coding]
- **Variation**: [Source of variation]

### Control Variables

[List with justifications]

### Fixed Effects

[List unit, time, or other FE]

---

## Analytical Methods

### Empirical Strategy

**Primary Specification**:

```json
[Equation]
```

**Identification**: [How causal effect identified]

### Statistical Methods

- **Estimation**: [OLS/IV/2SLS/Panel/etc.]
- **Standard Errors**: [Type, clustering]
- **Software**: [Stata/R/Python]

### Robustness Checks

1. [Check 1]
2. [Check 2]

### Threats to Identification

[Key threats and how addressed]

---

## Results

### Main Findings

**Table Location**: [Table X]

| Specification | Coefficient | SE | p-value | N |
|---------------|-------------|-----|---------|---|
| (1) [Spec] | [β] | [se] | [p] | [n] |
| (2) [Spec] | [β] | [se] | [p] | [n] |

**Interpretation**:
[Effect size, magnitude, significance]

### Robustness

[Results from robustness checks]

### Heterogeneity

[Subgroup results if tested]

---

## Quality Assessment

### Internal Validity

- **Endogeneity Concerns**: [Assessment]
- **Selection Bias**: [Concern level]
- **Confounding**: [Addressed? How?]
- **Reverse Causality**: [Possible? Addressed?]

### Identification Credibility

- **Assumption Plausibility**: [High/Medium/Low]
- **Validation Tests**: [Passed/Failed/Mixed]
- **Alternative Explanations**: [Ruled out?]

### External Validity

- **Population**: [Generalizable to whom?]
- **Setting**: [How specific?]
- **Time Period**: [Time-specific factors?]

**Overall Quality**: [High/Moderate/Low]

---

## Discussion

### Authors' Interpretation

[Key interpretations]

### Contribution

[What's new? How advances literature?]

### Limitations

1. [Limitation 1]
2. [Limitation 2]

### Policy Implications

[If discussed]

---

## Reviewer Assessment

### Strengths

1. [Strength 1]
2. [Strength 2]

### Weaknesses

1. [Weakness 1]
2. [Weakness 2]

### Credibility

**Causal Interpretation**: [Credible/Questionable/Not credible]

**Reasoning**: [Why]

---

## Key Takeaways

1. **Main Finding**: [One sentence]
2. **Identification Strategy**: [Method used]
3. **Credibility**: [How believable]
4. **Relevance**: [To your work]

---

## Notes

[Additional notes, questions, ideas]
