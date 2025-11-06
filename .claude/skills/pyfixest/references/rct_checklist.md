# RCT Analysis Checklist

## Pre-Analysis

- [ ] Review pre-analysis plan (PAP) if available
- [ ] Identify primary and secondary outcomes
- [ ] Document all planned specifications
- [ ] List pre-specified control variables
- [ ] Define subgroups for heterogeneity analysis
- [ ] Plan multiple testing correction strategy

## Data Preparation

- [ ] Load raw data
- [ ] Check data structure and variable types
- [ ] Verify treatment assignment variable (binary 0/1)
- [ ] Identify stratification variables
- [ ] Identify cluster variables (if applicable)
- [ ] Check for missing data patterns
- [ ] Create analysis sample inclusion criteria
- [ ] Generate derived variables (if needed)
- [ ] Save cleaned dataset

## Balance Checks

- [ ] List baseline covariates for balance table
- [ ] Calculate means by treatment arm
- [ ] Calculate standard deviations by treatment arm
- [ ] Test for differences using regression
- [ ] Create formatted balance table
- [ ] Check joint F-test for overall balance
- [ ] Document any significant imbalances
- [ ] Consider including imbalanced variables as controls

## Attrition Analysis

- [ ] Create indicator for missing outcome data
- [ ] Test overall attrition rates by treatment
- [ ] Test differential attrition (treatment × baseline characteristics)
- [ ] Calculate attrition bounds (Lee bounds) if needed
- [ ] Consider inverse probability weighting if attrition is differential
- [ ] Document attrition patterns in results

## Primary Analysis

### Model Specification

- [ ] Specify outcome variable
- [ ] Specify treatment variable
- [ ] Choose standard error type (robust or clustered)
- [ ] Include stratification fixed effects (if applicable)
- [ ] Decide on baseline covariates (ANCOVA recommended)

### Individual Randomization

- [ ] Model 1: Simple treatment effect (`y ~ treatment`)
- [ ] Model 2: With baseline outcome (`y ~ treatment + baseline_y`)
- [ ] Model 3: With all pre-specified controls
- [ ] Model 4: With stratification FE (`y ~ treatment | strata`)
- [ ] Use heteroskedasticity-robust SE (`vcov="HC1"`)

### Cluster Randomization

- [ ] Model 1: Simple with cluster SE
- [ ] Model 2: With baseline outcome and cluster SE
- [ ] Model 3: With controls and stratification FE
- [ ] Use cluster-robust SE (`vcov={"CRV1": "cluster_id"}`)
- [ ] Check number of clusters (>40 preferred)
- [ ] Consider wild bootstrap if few clusters (<40)
- [ ] Consider randomization inference if very few clusters (<20)

## Robustness Checks

- [ ] Alternative standard error specifications
- [ ] Different sets of control variables
- [ ] Trimming extreme outliers
- [ ] Winsorizing outcome variables
- [ ] Alternative functional forms
- [ ] Include/exclude specific observations
- [ ] Cluster at different levels (if applicable)

## Secondary Outcomes

- [ ] Estimate effects on all pre-specified secondary outcomes
- [ ] Apply multiple testing correction:
  - [ ] Romano-Wolf stepdown p-values
  - [ ] Bonferroni correction
  - [ ] FDR correction (Benjamini-Hochberg)
- [ ] Consider creating summary indices
- [ ] Report corrected p-values in tables

## Heterogeneous Effects

- [ ] Test interactions with pre-specified subgroups only
- [ ] Use proper interaction syntax: `treatment*subgroup`
- [ ] Report interaction p-values
- [ ] Apply multiple testing correction for multiple subgroups
- [ ] Visualize heterogeneous effects
- [ ] Avoid data-driven subgroup selection

## Tables and Figures

### Required Tables

- [ ] Balance table (baseline characteristics by treatment)
- [ ] Attrition table (if applicable)
- [ ] Main results table (primary outcome with multiple specs)
- [ ] Secondary outcomes table
- [ ] Heterogeneity table (if applicable)
- [ ] Robustness checks table

### Required Figures

- [ ] Coefficient plot for main results
- [ ] Distribution of outcomes by treatment arm
- [ ] Event study plot (if panel data)
- [ ] Heterogeneity visualization (if applicable)

### Table Requirements

- [ ] Include all specifications (not just preferred)
- [ ] Report standard errors in parentheses
- [ ] Indicate significance levels (*** p<0.01, ** p<0.05, * p<0.1)
- [ ] Report sample size (N)
- [ ] Report number of clusters (if applicable)
- [ ] Include control mean (outcome mean in control group)
- [ ] Document standard error type in notes
- [ ] List included controls in notes
- [ ] Specify fixed effects in notes

### Figure Requirements

- [ ] Include confidence intervals
- [ ] Show reference lines (zero line for effects)
- [ ] Use informative titles
- [ ] Label axes clearly
- [ ] Use consistent color scheme
- [ ] Make colorblind-friendly
- [ ] Export in multiple formats (PNG, SVG, PDF)

## Code Quality

- [ ] Use version control (git)
- [ ] Write reproducible code
- [ ] Comment code extensively
- [ ] Use relative paths (not absolute)
- [ ] Set random seeds for bootstrap/permutation tests
- [ ] Separate scripts by purpose (clean, analyze, visualize)
- [ ] Document package versions
- [ ] Save intermediate results
- [ ] Clear variable names

## Reporting Standards

### Coefficient Reporting

- [ ] Report point estimate
- [ ] Report standard error
- [ ] Report t-statistic or p-value
- [ ] Report 95% confidence interval
- [ ] Report control group mean
- [ ] Calculate and report effect size (% of control mean)

### Sample Reporting

- [ ] Report total sample size
- [ ] Report N by treatment arm
- [ ] Report N of clusters (if applicable)
- [ ] Report attrition rates
- [ ] Document sample restrictions

### Method Reporting

- [ ] Describe randomization procedure
- [ ] Document stratification variables
- [ ] Document clustering structure
- [ ] Justify choice of control variables
- [ ] Explain standard error choice
- [ ] Document any deviations from PAP

## Common Mistakes to Avoid

- [ ] NOT clustering when randomization was clustered
- [ ] NOT including stratification fixed effects
- [ ] NOT correcting for multiple hypothesis testing
- [ ] Including post-treatment variables as controls
- [ ] Using wrong standard errors
- [ ] P-hacking (data-driven specification search)
- [ ] Not reporting all pre-specified outcomes
- [ ] Cherry-picking favorable specifications
- [ ] Ignoring differential attrition
- [ ] Not pre-specifying heterogeneity analysis

## Documentation

- [ ] Write analysis log/README
- [ ] Document data sources
- [ ] List all variable definitions
- [ ] Explain all data transformations
- [ ] Document sample restrictions
- [ ] Note any data quality issues
- [ ] Keep audit trail of analysis decisions
- [ ] Compare results to PAP (if applicable)

## Final Checks

- [ ] Verify all results are reproducible
- [ ] Check all numbers match across tables/text
- [ ] Verify sample sizes are consistent
- [ ] Check for typos in variable labels
- [ ] Ensure all figures have proper labels
- [ ] Test code runs from scratch
- [ ] Archive final dataset
- [ ] Save final analysis script
- [ ] Document computational environment

## PyFixest-Specific Checks

- [ ] Verify formula syntax is correct
- [ ] Check convergence messages
- [ ] Verify correct vcov specification
- [ ] Check fixed effects are absorbed correctly
- [ ] Ensure cluster variable matches randomization
- [ ] Verify interaction terms are specified correctly
- [ ] Check that tidy() output has expected coefficients
- [ ] Save fitted models for later reference

## Reporting Template

```python
# Example reporting code
fit = pf.feols("outcome ~ treatment + baseline_outcome | strata",
               data=data, vcov={"CRV1": "cluster_id"})

# Extract key statistics
results = fit.tidy()
treatment_row = results.filter(pl.col("Coefficient") == "treatment")

print(f"Treatment effect: {treatment_row['Estimate'][0]:.3f}")
print(f"Standard error: {treatment_row['Std. Error'][0]:.3f}")
print(f"P-value: {treatment_row['Pr(>|t|)'][0]:.4f}")
print(f"95% CI: [{treatment_row['Estimate'][0] - 1.96*treatment_row['Std. Error'][0]:.3f}, "
      f"{treatment_row['Estimate'][0] + 1.96*treatment_row['Std. Error'][0]:.3f}]")

# Control mean
control_mean = data.filter(pl.col("treatment") == 0).select(
    pl.col("outcome").mean()
).item()
print(f"Control mean: {control_mean:.3f}")
print(f"Effect size: {100 * treatment_row['Estimate'][0] / control_mean:.1f}%")
```
