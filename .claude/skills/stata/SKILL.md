---
name: stata
description: This skill should be used when users need to develop, test, or debug Stata code. Use this skill for working with .do files, running Stata commands via Python's stata_setup, creating Stata materials, or troubleshooting Stata code.
---

# Stata Development and Testing Skill

## Purpose

This skill provides guidance for developing and testing Stata code. It enables Claude to help users write, execute, and debug Stata .do files, create Stata materials, and run Stata commands programmatically through Python.

## When to Use This Skill

Use this skill when:

- Developing or editing Stata .do files
- Testing Stata code execution
- Debugging Stata code or syntax errors
- Running Stata commands from the command line via Python

## Stata Command-Line Execution

To execute Stata code from the command line, use the project's uv Python environment with the stata_setup package:

### Setup Process

1. Ensure the uv virtual environment is activated
2. Import and configure stata_setup in Python:

```python
import stata_setup
stata_setup.config('C:\\Program Files\\Stata18/', 'se')
```

**Important Notes:**

- The Stata version (e.g., Stata18) and path may vary depending on the user's installation
- The second parameter specifies the Stata edition: 'se' (Standard Edition), 'mp' (Multiprocessor), or 'ic' (Intercooled)
- Always ask the user about their Stata version and installation path if uncertain

### Running Stata Commands

After configuration, execute Stata commands using:

```python
from pystata import stata

# Run a single command
stata.run('summarize variable_name')

# Run a .do file
stata.run('do "path/to/file.do"')

# Run multiple commands
stata.run('''
    use "dataset.dta", clear
    summarize
    describe
''')
```

### Stata .do File Conventions

Follow these conventions when creating or editing .do files:

1. **File Headers**: Include descriptive comments at the top

   ```stata
   * Project: [Project Name]
   * Purpose: [Brief description]
   * Author: [Name]
   * Date: [Date]
   ```

2. **Section Organization**: Use clear section headers

   ```stata
   *===============================================================================
   * Section: Data Import
   *===============================================================================
   ```

3. **Commenting**: Add inline comments for complex operations

   ```stata
   gen age_group = cond(age < 18, 1, cond(age < 65, 2, 3))  // 1=youth, 2=adult, 3=senior
   ```

4. **Best Practices**:
   - Use descriptive variable names
   - Label variables and values appropriately
   - Include data validation checks
   - Document data transformations
   - Save intermediate files with clear naming

## Using Bundled Resources

### Scripts

- **`scripts/run_stata.py`**: Helper script to execute Stata code from Python with proper error handling and output capture
- **`scripts/create_do_template.py`**: Generate a new .do file with conventions and standard headers

### References

- **`references/stata_quick_reference.md`**: Common Stata commands and syntax patterns

### Assets

- **`assets/template.do`**: Template .do file following IPA coding standards
- **`assets/example_dataset.dta`**: Sample dataset for testing code

## Workflow for Testing Stata Code

1. **Activate Environment**: Ensure uv virtual environment is active
2. **Configure Stata**: Run stata_setup configuration with user's Stata path
3. **Execute Code**: Use pystata to run commands or .do files
4. **Capture Output**: Review output for errors or warnings
5. **Iterate**: Debug and refine code as needed

## Common Tasks

### Creating a New Stata Code

1. Review existing code and information for structure
2. Use assets/template.do as starting point
3. Add documentation to README.md

### Debugging Stata Code

1. Run code through pystata to capture error messages
2. Check syntax against references/stata_quick_reference.md
3. Verify variable names and types
4. Test with small dataset first
5. Add diagnostic commands (describe, summarize, list)

### Running Stata Code

1. Navigate to appropriate directory
2. Check for data file dependencies
3. Execute .do file using scripts/run_stata.py
4. Verify output matches expected results
5. Document any environment-specific adjustments needed

## Best Practices for RCT Regression Analysis

### Overview

Randomized controlled trials (RCTs) require careful statistical analysis to properly estimate treatment effects. The appropriate regression specification depends on the randomization design, the presence of stratification, and whether clustering was used.

### Individual-Level Randomization

For individually randomized trials without clustering:

#### Basic Specification

```stata
* Simple difference in means (OLS regression)
reg outcome treatment, robust

* With baseline covariates (ANCOVA specification)
reg outcome treatment baseline_outcome baseline_covariate1 baseline_covariate2, robust

* With stratification variables (always include strata fixed effects)
reg outcome treatment i.strata, robust
```

**Key Considerations:**

1. **Robust Standard Errors**: Always use `robust` (Huber-White) standard errors for heteroskedasticity-robust inference
2. **Baseline Covariates**: Including baseline outcome improves precision (reduces standard errors)
3. **Stratification Variables**: Must include strata fixed effects when randomization was stratified
4. **Pre-specified Controls**: Only include covariates specified in pre-analysis plan

#### Balance Checks

```stata
* Check balance on baseline covariates
foreach var of varlist baseline_age baseline_gender baseline_income {
    reg `var' treatment, robust
}

* Joint F-test for balance
reg treatment baseline_age baseline_gender baseline_income
test baseline_age baseline_gender baseline_income

* Create balance table
iebaltab baseline_age baseline_gender baseline_income, ///
    grpvar(treatment) ///
    save("output/balance_table.xlsx") replace
```

### Cluster-Randomized Trials

When randomization occurs at the cluster level (e.g., villages, schools, clinics):

#### Standard Approach: Cluster-Robust Standard Errors

```stata
* Cluster-robust standard errors
reg outcome treatment, vce(cluster cluster_id)

* With baseline covariates
reg outcome treatment baseline_outcome baseline_covariate1, ///
    vce(cluster cluster_id)

* With stratification
reg outcome treatment i.strata, vce(cluster cluster_id)

* With cluster-level covariates
reg outcome treatment cluster_size cluster_baseline, ///
    vce(cluster cluster_id)
```

**Key Considerations:**

1. **Cluster-Robust SE**: Use `vce(cluster cluster_id)` to account for within-cluster correlation
2. **Degrees of Freedom**: Effective sample size is number of clusters, not individuals
3. **Small Sample Adjustments**: With few clusters (<40), consider alternative methods
4. **Cluster-Level Analysis**: Can aggregate to cluster level and analyze cluster means

#### Cluster-Level Analysis (Alternative)

```stata
* Collapse to cluster level
collapse (mean) outcome treatment baseline_outcome ///
    (first) strata cluster_size, by(cluster_id)

* Analyze at cluster level
reg outcome treatment baseline_outcome [aweight=cluster_size], robust

* With stratification
reg outcome treatment i.strata [aweight=cluster_size], robust
```

**When to Use:**

- Few clusters (typically <20 clusters)
- Severe imbalance in cluster sizes
- All variables are cluster-invariant or properly aggregated

#### Small-Cluster Adjustments

With few clusters, use wild cluster bootstrap or randomization inference:

```stata
* Install boottest command
ssc install boottest

* Wild cluster bootstrap with Webb weights
reg outcome treatment baseline_outcome, vce(cluster cluster_id)
boottest treatment, cluster(cluster_id) boottype(wild) reps(9999)

* Randomization inference (requires ritest)
ssc install ritest
ritest treatment _b[treatment], reps(5000) cluster(cluster_id): ///
    reg outcome treatment baseline_outcome, vce(cluster cluster_id)
```

### Stratified Randomization

When randomization was stratified (blocked):

#### Include Strata Fixed Effects

```stata
* Individual randomization with stratification
reg outcome treatment i.strata, robust

* Cluster randomization with stratification
reg outcome treatment i.strata, vce(cluster cluster_id)

* With baseline covariates
reg outcome treatment baseline_outcome i.strata, vce(cluster cluster_id)
```

**Why Include Strata Fixed Effects:**

1. Correct standard errors (accounts for correlation within strata)
2. Improves precision (reduces residual variance)
3. Makes analysis consistent with randomization design
4. Required for unbiased inference when strata are few

#### Alternative: Absorb Fixed Effects

For many strata, use `reghdfe` for computational efficiency:

```stata
* Install reghdfe
ssc install reghdfe

* Absorb strata fixed effects
reghdfe outcome treatment baseline_outcome, ///
    absorb(strata) vce(cluster cluster_id)

* With multiple fixed effects
reghdfe outcome treatment baseline_outcome, ///
    absorb(strata time_period) vce(cluster cluster_id)
```

### Covariate Adjustment

#### ANCOVA Specification (Recommended)

```stata
* Include baseline outcome as covariate
reg outcome treatment baseline_outcome, robust

* Gains:
* - Reduced standard errors (improved precision)
* - Accounts for baseline imbalance
* - More powerful test of treatment effect
```

#### Pre-specified Covariates

```stata
* Only include covariates from pre-analysis plan
reg outcome treatment baseline_outcome age gender education i.strata, ///
    vce(cluster cluster_id)

* Avoid data-driven covariate selection
* Document all covariates in pre-analysis plan
```

#### Missing Baseline Data

```stata
* Create missing indicators
gen baseline_outcome_missing = missing(baseline_outcome)
replace baseline_outcome = 0 if missing(baseline_outcome)

* Include missing indicator as covariate
reg outcome treatment baseline_outcome baseline_outcome_missing, robust

* Alternative: Multiple imputation
mi set wide
mi register imputed baseline_outcome
mi impute chained (regress) baseline_outcome = age gender, add(20)
mi estimate: reg outcome treatment baseline_outcome
```

### Multiple Outcomes and Hypotheses

#### Family-Wise Error Rate (FWER) Correction

```stata
* Install wyoung command for multiple hypothesis testing
ssc install wyoung

* Control FWER across multiple outcomes
wyoung outcome1 outcome2 outcome3 outcome4, ///
    cmd(reg OUTCOMEVAR treatment baseline_outcome, vce(cluster cluster_id)) ///
    familyp(treatment) cluster(cluster_id) bootstraps(1000)
```

#### False Discovery Rate (FDR) Correction

```stata
* Store p-values from multiple tests
local outcomes "outcome1 outcome2 outcome3 outcome4"
local i = 1
foreach outcome of local outcomes {
    reg `outcome' treatment, vce(cluster cluster_id)
    local pval`i' = 2*ttail(e(df_r), abs(_b[treatment]/_se[treatment]))
    local i = `i' + 1
}

* Apply Benjamini-Hochberg FDR correction
* (requires manual calculation or qqvalue command)
```

#### Index Construction

```stata
* Standardize outcomes and average (Anderson 2008)
local outcomes "outcome1 outcome2 outcome3"
foreach var of local outcomes {
    egen std_`var' = std(`var')
}

* Create index as simple average
egen outcome_index = rowmean(std_outcome1 std_outcome2 std_outcome3)

* Analyze index
reg outcome_index treatment, vce(cluster cluster_id)

* Alternative: Use covariance-weighted average
* (requires seemreg or PCA approach)
```

### Heterogeneous Treatment Effects

#### Pre-specified Subgroup Analysis

```stata
* Interaction with binary subgroup
reg outcome i.treatment##i.subgroup baseline_outcome, ///
    vce(cluster cluster_id)

* Test for heterogeneity
test 1.treatment#1.subgroup

* Interactions with continuous variables
gen treatment_x_age = treatment * age
reg outcome treatment age treatment_x_age baseline_outcome, ///
    vce(cluster cluster_id)
test treatment_x_age
```

#### Multiple Subgroups (Adjust for Multiple Testing)

```stata
* Test interactions with multiple subgroups
local subgroups "gender age_above_median urban"
foreach subgroup of local subgroups {
    reg outcome i.treatment##i.`subgroup' baseline_outcome, ///
        vce(cluster cluster_id)
    test 1.treatment#1.`subgroup'
}

* Apply multiple testing correction to interaction p-values
```

### Attrition and Missing Data

#### Attrition Balance Check

```stata
* Create attrition indicator
gen attrited = missing(outcome)

* Test if attrition differs by treatment
reg attrited treatment, vce(cluster cluster_id)

* Test if attrition is differential by baseline characteristics
reg attrited i.treatment##c.baseline_outcome, vce(cluster cluster_id)
test 1.treatment#c.baseline_outcome
```

#### Bounds for Attrition Bias (Lee 2009)

```stata
* Install leebounds command
ssc install leebounds

* Calculate Lee bounds
leebounds outcome treatment, select(not_attrited) cieffect
```

#### Inverse Probability Weighting (IPW)

```stata
* Model probability of non-attrition
logit not_attrited treatment baseline_outcome age gender, ///
    vce(cluster cluster_id)
predict prob_respond

* Create IPW weights
gen ipw_weight = 1 / prob_respond

* Weighted regression
reg outcome treatment baseline_outcome [pweight=ipw_weight], ///
    vce(cluster cluster_id)
```

### Standard Error Considerations

#### Choosing the Right Standard Error Type

| Design | Standard Error Specification |
|--------|------------------------------|
| Individual randomization, no clustering | `robust` (HC1) |
| Individual randomization with stratification | `robust` + strata FE |
| Cluster randomization | `vce(cluster cluster_id)` |
| Cluster randomization with stratification | `vce(cluster cluster_id)` + strata FE |
| Panel data with clustering | `vce(cluster cluster_id)` or two-way clustering |
| Few clusters (<40) | Wild cluster bootstrap |
| Very few clusters (<20) | Randomization inference |

#### Two-Way Clustering

```stata
* Install reghdfe for two-way clustering
ssc install reghdfe

* Two-way clustering (e.g., cluster and time)
reghdfe outcome treatment baseline_outcome, ///
    absorb(strata) vce(cluster cluster_id time_period)

* Two-way clustering with ivreghdfe for IV
ssc install ivreghdfe
ivreghdfe outcome (endogenous = instrument) controls, ///
    absorb(strata) cluster(cluster_id time_period)
```

### Panel Data and Difference-in-Differences

For RCTs with panel data:

#### Fixed Effects Specification

```stata
* Individual fixed effects
xtreg outcome treatment time_post_treatment, fe vce(cluster cluster_id)

* Alternative with reghdfe (more flexible)
reghdfe outcome treatment time_dummies, ///
    absorb(individual_id) vce(cluster cluster_id)
```

#### Difference-in-Differences

```stata
* Standard DiD specification
reg outcome i.treatment##i.post baseline_controls, ///
    vce(cluster cluster_id)

* Extract treatment effect
lincom 1.treatment#1.post

* Event study specification
gen time_to_treatment = time_period - treatment_period
reg outcome ib-1.time_to_treatment i.individual_id i.time_period, ///
    vce(cluster cluster_id)
```

### Power Analysis and Sample Size

#### Ex-post Power Calculation

```stata
* Install powerreg
ssc install powerreg

* Calculate achieved power
powerreg, n(1000) alpha(0.05) beta(_b[treatment]) sd(e(rmse))

* For cluster randomization, adjust for ICC
powerreg, n(50) m(20) alpha(0.05) beta(_b[treatment]) ///
    sd(e(rmse)) icc(0.05)
```

#### Minimum Detectable Effect (MDE)

```stata
* Calculate MDE given sample and power
power twomeans 0, n(500) power(0.8) sd(10)

* For cluster-randomized trials
power twomeans 0, n(50) m(20) power(0.8) sd(10) rho(0.05)
```

### Reporting Standards

#### Essential Regression Output

Always report:

1. **Treatment effect estimate** (coefficient on treatment)
2. **Standard error** (and type: robust, clustered, etc.)
3. **P-value** (exact p-value, not just significance stars)
4. **Confidence interval** (typically 95%)
5. **Sample size** (observations and clusters if applicable)
6. **R-squared** (to show explanatory power)
7. **Control mean** (outcome mean in control group)

```stata
* Comprehensive output example
reg outcome treatment baseline_outcome i.strata, vce(cluster cluster_id)

* Calculate control mean
sum outcome if treatment == 0

* Calculate confidence interval
lincom treatment, level(95)

* Export results table
esttab using "output/main_results.tex", ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    b(3) se(3) ///
    scalars(r2 N N_clust) ///
    mtitles("Outcome") ///
    addnote("Cluster-robust standard errors in parentheses" ///
            "Stratification fixed effects included") ///
    replace
```

#### Pre-Analysis Plan Adherence

Document deviations from pre-analysis plan:

```stata
* Note in comments which specifications are exploratory
* ============================================================================
* PRIMARY SPECIFICATION (Pre-registered)
* ============================================================================
reg outcome treatment baseline_outcome i.strata, vce(cluster cluster_id)
est store primary

* ============================================================================
* ROBUSTNESS CHECK (Exploratory)
* ============================================================================
reg outcome treatment baseline_outcome age gender i.strata, ///
    vce(cluster cluster_id)
est store robustness
```

### Common Mistakes to Avoid

1. **Not clustering when randomization is clustered** → Too-small standard errors, inflated significance
2. **Omitting strata fixed effects** → Incorrect standard errors, loss of precision
3. **Not adjusting for multiple hypothesis testing** → Inflated Type I error rate
4. **Including post-treatment covariates** → Bias due to collider or mediator control
5. **Using individual-level standard errors with cluster randomization** → Invalid inference
6. **Ignoring differential attrition** → Potential bias in treatment effect estimates
7. **Data-driven covariate selection** → P-hacking, inflated significance
8. **Not weighting cluster-level analysis by cluster size** → Inefficient estimates

### Recommended Packages

```stata
* Core packages
ssc install reghdfe        // Fast fixed effects regression
ssc install boottest       // Wild cluster bootstrap
ssc install ritest         // Randomization inference
ssc install wyoung         // Multiple hypothesis testing
ssc install iebaltab       // Balance tables
ssc install estout         // Export regression tables
ssc install leebounds      // Lee bounds for attrition

* Additional useful packages
ssc install coefplot       // Coefficient plots
ssc install binscatter     // Binned scatter plots
ssc install rdrobust       // RD designs (if threshold assignment)
```

### Example Complete Analysis Script

```stata
*===============================================================================
* RCT Analysis Template
* Design: Cluster-randomized trial with stratification
*===============================================================================

* Setup
clear all
set more off
version 18

* Load data
use "data/analysis_dataset.dta", clear

* ============================================================================
* 1. BALANCE CHECKS
* ============================================================================

* Balance table
iebaltab baseline_age baseline_gender baseline_income, ///
    grpvar(treatment) ///
    save("output/balance_table.xlsx") replace

* ============================================================================
* 2. ATTRITION ANALYSIS
* ============================================================================

* Attrition by treatment
gen attrited = missing(outcome)
reg attrited treatment, vce(cluster cluster_id)

* Differential attrition by baseline characteristics
reg attrited i.treatment##c.baseline_outcome, vce(cluster cluster_id)

* ============================================================================
* 3. PRIMARY ANALYSIS (Pre-specified)
* ============================================================================

* Main specification with cluster-robust SE and strata FE
reg outcome treatment baseline_outcome i.strata, vce(cluster cluster_id)
est store main

* Calculate control mean
sum outcome if treatment == 0
estadd scalar control_mean = r(mean)

* Export results
esttab main using "output/main_results.tex", ///
    se star(* 0.10 ** 0.05 *** 0.01) ///
    b(3) se(3) ///
    scalars(control_mean r2 N N_clust) ///
    mtitles("Primary Outcome") ///
    addnote("Cluster-robust standard errors in parentheses" ///
            "Stratification fixed effects included" ///
            "Baseline outcome included as covariate") ///
    replace

* ============================================================================
* 4. HETEROGENEOUS EFFECTS (Pre-specified subgroups)
* ============================================================================

* Test for heterogeneity by pre-specified subgroup
reg outcome i.treatment##i.subgroup baseline_outcome i.strata, ///
    vce(cluster cluster_id)
test 1.treatment#1.subgroup

* ============================================================================
* 5. ROBUSTNESS CHECKS
* ============================================================================

* Without baseline covariate
reg outcome treatment i.strata, vce(cluster cluster_id)
est store robust1

* With additional controls
reg outcome treatment baseline_outcome age gender i.strata, ///
    vce(cluster cluster_id)
est store robust2

* Wild cluster bootstrap (small number of clusters)
reg outcome treatment baseline_outcome i.strata, vce(cluster cluster_id)
boottest treatment, cluster(cluster_id) boottype(wild) reps(9999)

* ============================================================================
* 6. MULTIPLE OUTCOMES (with FWER correction)
* ============================================================================

wyoung outcome1 outcome2 outcome3, ///
    cmd(reg OUTCOMEVAR treatment baseline_outcome i.strata, ///
        vce(cluster cluster_id)) ///
    familyp(treatment) cluster(cluster_id) bootstraps(1000)
```

### References

- Athey, S., & Imbens, G. W. (2017). "The econometrics of randomized experiments." *Handbook of Economic Field Experiments*, 1, 73-140.
- Cameron, A. C., & Miller, D. L. (2015). "A practitioner's guide to cluster-robust inference." *Journal of Human Resources*, 50(2), 317-372.
- McKenzie, D. (2012). "Beyond baseline and follow-up: The case for more T in experiments." *Journal of Development Economics*, 99(2), 210-221.
- Bruhn, M., & McKenzie, D. (2009). "In pursuit of balance: Randomization in practice in development field experiments." *American Economic Journal: Applied Economics*, 1(4), 200-232.
