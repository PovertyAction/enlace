---
name: pyfixest
description: This skill should be used when users need to perform econometric analysis in Python using pyfixest for fixed effects regression, polars for data transformation, and altair for data visualization. Use this skill for RCT analysis, panel data, difference-in-differences, IV estimation, and creating publication-quality tables and figures.
---

# PyFixest Econometric Analysis Skill

## Purpose

This skill provides comprehensive guidance for econometric analysis in Python, focusing on fixed effects regression, causal inference, and data visualization. It complements the Stata skill by offering modern Python-based workflows for RCT analysis, panel data, and advanced econometric methods.

## When to Use This Skill

Use this skill when:

- Performing fixed effects regression analysis in Python
- Analyzing randomized controlled trials (RCTs)
- Working with panel data or difference-in-differences designs
- Running instrumental variables (IV) regressions
- Creating publication-quality regression tables and coefficient plots
- Transforming and cleaning data for econometric analysis
- Visualizing regression results and diagnostic plots
- Need faster performance than Stata on large datasets

## Core Libraries

This skill integrates three powerful Python libraries:

### PyFixest - Fixed Effects Regression

High-performance Python package for estimating linear models with multiple fixed effects. Inspired by R's `fixest` package.

**Key capabilities:**

- OLS with high-dimensional fixed effects
- Poisson, logit, and probit models
- Instrumental variables (IV/2SLS)
- Quantile regression
- Difference-in-differences (DiD) estimators
- Multiple hypothesis testing corrections
- Wild bootstrap and randomization inference
- Cluster-robust standard errors (one-way and two-way)

### Polars - Data Transformation

Lightning-fast DataFrame library with an expression-based API for data manipulation.

**Key capabilities:**

- Fast CSV, Parquet, and JSON I/O
- Lazy evaluation with query optimization
- Memory-efficient processing of large datasets
- Expression-based transformations
- Group-by operations and aggregations
- Joins and concatenation

### Altair - Data Visualization

Declarative statistical visualization library based on Vega-Lite.

**Key capabilities:**

- Statistical visualizations with concise syntax
- Interactive plots
- Coefficient plots and effect visualizations
- Export to PNG, SVG, PDF, HTML
- Publication-quality graphics

## Installation and Setup

The project's `pyproject.toml` already includes the required dependencies:

```toml
dependencies = [
    "pyfixest>=0.30.2",
    "polars>=1.0.0",
    "altair>=5.5.0",
    "pandas>=2.2.3",
]
```

For visualization export, install `vl-convert`:

```bash
uv add vl-convert-python
```

## PyFixest Usage

### Basic Regression Syntax

PyFixest uses a formula-based interface similar to Stata:

```python
import pyfixest as pf
import polars as pl

# Load data
data = pl.read_csv("data.csv")

# Basic OLS regression
fit = pf.feols("outcome ~ treatment", data=data)
fit.summary()

# With control variables
fit = pf.feols("outcome ~ treatment + age + gender", data=data)

# With fixed effects
fit = pf.feols("outcome ~ treatment | region_id", data=data)

# Multiple fixed effects
fit = pf.feols("outcome ~ treatment | region_id + time_period", data=data)
```

### Standard Errors and Clustering

```python
# Heteroskedasticity-robust standard errors (default)
fit = pf.feols("outcome ~ treatment", data=data, vcov="HC1")

# Cluster-robust standard errors (one-way)
fit = pf.feols("outcome ~ treatment", data=data,
               vcov={"CRV1": "cluster_id"})

# Two-way clustering
fit = pf.feols("outcome ~ treatment", data=data,
               vcov={"CRV1": "cluster_id + time_period"})

# Change standard errors after estimation
fit.vcov("HC3")
fit.summary()
```

### RCT Analysis Patterns

#### Individual Randomization

```python
# Simple treatment effect
fit = pf.feols("outcome ~ treatment", data=data, vcov="HC1")

# ANCOVA specification (with baseline covariate)
fit = pf.feols("outcome ~ treatment + baseline_outcome",
               data=data, vcov="HC1")

# With stratification fixed effects
fit = pf.feols("outcome ~ treatment + baseline_outcome | strata",
               data=data, vcov="HC1")
```

#### Cluster Randomization

```python
# Cluster-robust standard errors
fit = pf.feols("outcome ~ treatment + baseline_outcome | strata",
               data=data, vcov={"CRV1": "cluster_id"})

# Extract results
fit.tidy()  # Returns DataFrame with coefficients, SE, p-values
fit.coef()  # Coefficient vector
fit.se()    # Standard errors
fit.confint()  # Confidence intervals
```

### Instrumental Variables (IV)

```python
# IV regression with one endogenous variable
# Syntax: "Y ~ exog_vars | fixed_effects | endog_var ~ instruments"
fit = pf.feols("outcome ~ age + gender | region_id | treatment ~ instrument",
               data=data, vcov={"CRV1": "cluster_id"})

# Access first-stage statistics
fit._f_stat_1st_stage  # First-stage F-statistic
fit._model_1st_stage   # First-stage model

# Multiple instruments
fit = pf.feols("outcome ~ controls | fe | X1 ~ Z1 + Z2 + Z3",
               data=data)
```

### Multiple Estimation and Specification Testing

PyFixest supports running multiple specifications efficiently:

```python
# Sequential replacement with sw()
# Tests multiple combinations of covariates
fit = pf.feols("outcome ~ sw(treatment, age, gender)", data=data)

# Cumulative stepwise with csw()
# Progressively adds controls
fit = pf.feols("outcome ~ treatment + csw(age, gender, education)",
               data=data, vcov="HC1")

# Multiple dependent variables
fit = pf.feols("sw(outcome1, outcome2, outcome3) ~ treatment",
               data=data, vcov={"CRV1": "cluster_id"})

# Results is a FixestMulti object
fit.summary()  # Show all models
```

### Advanced Inference

#### Wild Bootstrap

For few clusters, use wild cluster bootstrap:

```python
fit = pf.feols("outcome ~ treatment", data=data,
               vcov={"CRV1": "cluster_id"})

# Wild bootstrap test
boot_result = fit.wildboottest(param="treatment", reps=9999)
```

#### Randomization Inference

```python
# Permutation-based inference
ri_result = fit.ritest(resampvar="treatment", reps=5000)
```

#### Multiple Hypothesis Testing

```python
# Fit multiple models
fits = pf.feols("sw(outcome1, outcome2, outcome3) ~ treatment",
                data=data, vcov={"CRV1": "cluster_id"})

# Romano-Wolf correction
from pyfixest.multcomp import rwolf
rwolf_result = rwolf(fits, param="treatment", reps=1000)

# Bonferroni correction
from pyfixest.multcomp import bonferroni
bonf_result = bonferroni(fits, param="treatment")
```

### Difference-in-Differences

```python
# Standard DiD with two-way fixed effects
fit = pf.feols("outcome ~ treatment_post | unit_id + time_period",
               data=data, vcov={"CRV1": "unit_id"})

# Gardner's two-stage DiD (robust to dynamic treatment effects)
from pyfixest import did2s

fit = pf.did2s(
    data=data,
    yname="outcome",
    idname="unit_id",
    tname="time_period",
    gname="treatment_group",
    estimator="feols",
    cluster="unit_id"
)

# Event study specification
fit = pf.feols("outcome ~ i(time_to_treatment, ref=-1) | unit_id + time_period",
               data=data, vcov={"CRV1": "unit_id"})
```

### Poisson and GLM

```python
# Poisson regression (for count outcomes)
fit = pf.fepois("count_outcome ~ treatment | fixed_effects",
                data=data, vcov={"CRV1": "cluster_id"})

# Logit
fit = pf.feglm("binary_outcome ~ treatment + controls",
               family="logit", data=data, vcov="HC1")

# Probit
fit = pf.feglm("binary_outcome ~ treatment + controls",
               family="probit", data=data, vcov="HC1")
```

### Quantile Regression

```python
# Median regression (50th percentile)
fit = pf.quantreg("outcome ~ treatment + controls",
                  q=0.5, data=data)

# Multiple quantiles
for q in [0.25, 0.5, 0.75]:
    fit = pf.quantreg("outcome ~ treatment", q=q, data=data)
    print(f"Quantile {q}: {fit.coef()['treatment']:.3f}")
```

### Creating Publication Tables

```python
# Estimate multiple specifications
fit1 = pf.feols("outcome ~ treatment", data=data, vcov="HC1")
fit2 = pf.feols("outcome ~ treatment + controls", data=data, vcov="HC1")
fit3 = pf.feols("outcome ~ treatment + controls | strata",
                data=data, vcov={"CRV1": "cluster_id"})

# Create publication table
pf.etable([fit1, fit2, fit3],
          labels={"treatment": "Treatment Effect"},
          coef_fmt="b (se)",  # Show coefficient with SE in parentheses
          signif_code=[0.01, 0.05, 0.1],  # Significance levels
          keep="treatment")  # Only show treatment coefficient

# Export to file
pf.etable([fit1, fit2, fit3],
          labels={"treatment": "Treatment"},
          output="results/table1.tex")  # LaTeX format
```

## Polars for Data Transformation

Polars provides fast, memory-efficient data manipulation with an expression-based API.

### Reading Data

```python
import polars as pl

# CSV files
data = pl.read_csv("data.csv")

# Parquet (recommended for large datasets)
data = pl.read_parquet("data.parquet")

# JSON
data = pl.read_json("data.json")

# Excel
data = pl.read_excel("data.xlsx", sheet_name="Sheet1")

# Multiple files
data = pl.read_csv("data/*.csv")
```

### Basic Operations

```python
# Select columns
data.select(["outcome", "treatment", "age"])

# Filter rows
data.filter(pl.col("age") > 25)

# Create new columns
data.with_columns([
    (pl.col("price") * pl.col("quantity")).alias("total"),
    pl.col("name").str.to_uppercase().alias("name_upper")
])

# Sort
data.sort("age", descending=True)

# Remove duplicates
data.unique()
```

### Expression-Based Transformations

```python
# Multiple operations in one expression
result = (
    data
    .filter(pl.col("treatment") == 1)
    .with_columns([
        (pl.col("outcome") - pl.col("baseline")).alias("change"),
        pl.col("age").cast(pl.Int32)
    ])
    .select(["id", "outcome", "change"])
)

# Conditional logic
data.with_columns(
    pl.when(pl.col("age") < 18)
    .then(pl.lit("minor"))
    .when(pl.col("age") < 65)
    .then(pl.lit("adult"))
    .otherwise(pl.lit("senior"))
    .alias("age_group")
)
```

### Aggregations and Group By

```python
# Group by and aggregate
data.group_by("treatment").agg([
    pl.col("outcome").mean().alias("mean_outcome"),
    pl.col("outcome").std().alias("sd_outcome"),
    pl.col("outcome").count().alias("n")
])

# Multiple grouping variables
data.group_by(["treatment", "region"]).agg([
    pl.col("outcome").mean(),
    pl.col("age").median()
])

# Window functions
data.with_columns([
    pl.col("outcome").mean().over("treatment").alias("treatment_mean"),
    pl.col("outcome").rank().over("treatment").alias("rank_in_treatment")
])
```

### Joins

```python
# Inner join
result = data1.join(data2, on="id", how="inner")

# Left join
result = data1.join(data2, on="id", how="left")

# Multiple keys
result = data1.join(data2, on=["id", "time"], how="inner")

# Different column names
result = data1.join(data2, left_on="user_id", right_on="id", how="left")
```

### String Operations

```python
# String manipulation
data.with_columns([
    pl.col("name").str.to_lowercase().alias("name_lower"),
    pl.col("name").str.strip().alias("name_trimmed"),
    pl.col("email").str.contains("@example.com").alias("is_example"),
    pl.col("text").str.replace("old", "new").alias("text_updated")
])
```

### Handling Missing Data

```python
# Check for nulls
data.null_count()

# Drop rows with any null
data.drop_nulls()

# Drop rows with null in specific columns
data.drop_nulls(subset=["outcome", "treatment"])

# Fill nulls
data.fill_null(0)  # Fill with constant
data.fill_null(strategy="mean")  # Fill with column mean
data.fill_null(strategy="forward")  # Forward fill
```

### Exporting Data

```python
# CSV
data.write_csv("output.csv")

# Parquet (recommended for large data)
data.write_parquet("output.parquet")

# JSON
data.write_json("output.json")

# Excel
data.write_excel("output.xlsx")
```

### Converting to/from Pandas

```python
# PyFixest works with both polars and pandas
import pandas as pd

# Polars to pandas
df_pandas = data.to_pandas()

# Pandas to polars
data_polars = pl.from_pandas(df_pandas)

# Use either with pyfixest
fit = pf.feols("outcome ~ treatment", data=data_polars)  # Polars
fit = pf.feols("outcome ~ treatment", data=df_pandas)    # Pandas
```

## Altair for Visualization

Altair provides declarative visualization with a concise, intuitive API.

### Basic Plotting Patterns

```python
import altair as alt

# Scatter plot
chart = alt.Chart(data).mark_point().encode(
    x='age',
    y='outcome',
    color='treatment'
).properties(
    width=600,
    height=400,
    title='Outcome by Age and Treatment'
)

# Save to file
chart.save('figures/scatter.png')
chart.save('figures/scatter.svg')
chart.save('figures/scatter.html')
```

### Coefficient Plots

```python
# Create coefficient plot from pyfixest results
fit = pf.feols("outcome ~ treatment + age + gender", data=data)

# Built-in coefficient plot
fit.coefplot()

# Custom coefficient plot with Altair
coef_df = fit.tidy()

chart = alt.Chart(coef_df).mark_point(filled=True, size=100).encode(
    y=alt.Y('Coefficient:N', sort='-x'),
    x='Estimate:Q',
    color=alt.condition(
        alt.datum.pvalue < 0.05,
        alt.value('steelblue'),
        alt.value('gray')
    )
).properties(
    title='Regression Coefficients',
    width=600,
    height=400
)

# Add confidence intervals
error_bars = alt.Chart(coef_df).mark_rule().encode(
    y='Coefficient:N',
    x='CI_Lower:Q',
    x2='CI_Upper:Q'
)

(chart + error_bars).save('figures/coefplot.png')
```

### Event Study Plots

```python
# Event study visualization
event_data = fit.tidy()  # From event study regression

chart = (
    alt.Chart(event_data)
    .mark_line(point=True)
    .encode(
        x=alt.X('time_to_treatment:Q', title='Time to Treatment'),
        y=alt.Y('Estimate:Q', title='Treatment Effect'),
        color=alt.value('steelblue')
    )
)

# Add confidence interval band
band = (
    alt.Chart(event_data)
    .mark_area(opacity=0.3)
    .encode(
        x='time_to_treatment:Q',
        y='CI_Lower:Q',
        y2='CI_Upper:Q',
        color=alt.value('steelblue')
    )
)

# Add zero line
zero_line = (
    alt.Chart(pl.DataFrame({'y': [0]}))
    .mark_rule(strokeDash=[5, 5], color='red')
    .encode(y='y:Q')
)

(band + chart + zero_line).save('figures/event_study.png')
```

### Distribution Plots

```python
# Histogram
alt.Chart(data).mark_bar().encode(
    x=alt.X('outcome:Q', bin=alt.Bin(maxbins=30)),
    y='count()',
    color='treatment:N'
).save('figures/histogram.png')

# Density plot (smoothed histogram)
alt.Chart(data).transform_density(
    'outcome',
    as_=['outcome', 'density'],
    groupby=['treatment']
).mark_area(opacity=0.5).encode(
    x='outcome:Q',
    y='density:Q',
    color='treatment:N'
).save('figures/density.png')

# Box plot
alt.Chart(data).mark_boxplot().encode(
    x='treatment:N',
    y='outcome:Q'
).save('figures/boxplot.png')
```

### Balance Tables and Summary Statistics

```python
# Create balance table with polars
balance = (
    data
    .group_by("treatment")
    .agg([
        pl.col("age").mean().alias("age_mean"),
        pl.col("age").std().alias("age_sd"),
        pl.col("female").mean().alias("female_prop"),
        pl.col("income").mean().alias("income_mean"),
        pl.col("income").std().alias("income_sd"),
        pl.count().alias("n")
    ])
)

# Visualize balance
balance_long = balance.melt(
    id_vars=["treatment"],
    value_vars=["age_mean", "female_prop", "income_mean"]
)

alt.Chart(balance_long).mark_bar().encode(
    x='treatment:N',
    y='value:Q',
    color='treatment:N',
    column='variable:N'
).save('figures/balance.png')
```

### Interactive Visualizations

```python
# Add interactivity
chart = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color='treatment:N',
    tooltip=['id', 'age', 'outcome', 'treatment']
).interactive()  # Adds pan, zoom

# Selection highlighting
brush = alt.selection_interval()

points = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color=alt.condition(brush, 'treatment:N', alt.value('lightgray'))
).add_selection(brush)

points.save('figures/interactive.html')
```

## Common Workflows

### RCT Analysis Workflow

```python
import polars as pl
import pyfixest as pf
import altair as alt

# 1. Load and prepare data
data = pl.read_csv("trial_data.csv")

# 2. Create analysis dataset
analysis_data = (
    data
    .filter(~pl.col("outcome").is_null())
    .with_columns([
        (pl.col("outcome") - pl.col("baseline_outcome")).alias("change"),
        pl.col("treatment").cast(pl.Int8)
    ])
)

# 3. Check balance
balance = (
    analysis_data
    .group_by("treatment")
    .agg([
        pl.col("baseline_outcome").mean().alias("baseline_mean"),
        pl.col("age").mean().alias("age_mean"),
        pl.col("female").mean().alias("female_mean"),
        pl.count().alias("n")
    ])
)
print(balance)

# 4. Estimate treatment effects
fit1 = pf.feols("outcome ~ treatment",
                data=analysis_data, vcov="HC1")
fit2 = pf.feols("outcome ~ treatment + baseline_outcome",
                data=analysis_data, vcov="HC1")
fit3 = pf.feols("outcome ~ treatment + baseline_outcome | strata",
                data=analysis_data, vcov="HC1")

# 5. Create results table
pf.etable([fit1, fit2, fit3],
          labels={"treatment": "Treatment Effect"},
          keep="treatment",
          output="results/table1.tex")

# 6. Coefficient plot
coef_data = pl.concat([
    fit1.tidy().with_columns(pl.lit("Model 1").alias("model")),
    fit2.tidy().with_columns(pl.lit("Model 2").alias("model")),
    fit3.tidy().with_columns(pl.lit("Model 3").alias("model"))
]).filter(pl.col("Coefficient") == "treatment")

alt.Chart(coef_data).mark_point(size=100).encode(
    x='Estimate:Q',
    y='model:N',
    color='model:N'
).save('figures/treatment_effects.png')
```

### Panel Data Analysis

```python
# 1. Load panel data
panel = pl.read_parquet("panel_data.parquet")

# 2. Create lagged variables
panel_clean = (
    panel
    .sort(["unit_id", "time"])
    .with_columns([
        pl.col("outcome").shift(1).over("unit_id").alias("outcome_lag"),
        pl.col("treatment").cum_sum().over("unit_id").alias("treated_ever")
    ])
)

# 3. Two-way fixed effects
fit = pf.feols("outcome ~ treatment | unit_id + time",
               data=panel_clean, vcov={"CRV1": "unit_id"})

# 4. Event study
# Create time relative to treatment
panel_event = panel_clean.with_columns(
    (pl.col("time") - pl.col("treatment_time")).alias("time_to_treat")
)

fit_event = pf.feols("outcome ~ i(time_to_treat, ref=-1) | unit_id + time",
                     data=panel_event, vcov={"CRV1": "unit_id"})

# 5. Plot event study
pf.iplot([fit_event])  # Built-in event study plot
```

### Data Cleaning and Preparation

```python
# Comprehensive cleaning workflow
cleaned = (
    pl.read_csv("raw_data.csv")

    # Remove duplicates
    .unique(subset=["id", "time"])

    # Filter valid observations
    .filter(
        (pl.col("age") >= 0) & (pl.col("age") <= 120) &
        (pl.col("outcome") > 0)
    )

    # Create derived variables
    .with_columns([
        # Age groups
        pl.when(pl.col("age") < 18).then(pl.lit("youth"))
        .when(pl.col("age") < 65).then(pl.lit("adult"))
        .otherwise(pl.lit("senior")).alias("age_group"),

        # Log transformations
        pl.col("income").log().alias("log_income"),

        # Standardize
        ((pl.col("test_score") - pl.col("test_score").mean()) /
         pl.col("test_score").std()).alias("test_score_std"),

        # Missing indicators
        pl.col("baseline_outcome").is_null().alias("baseline_missing")
    ])

    # Handle missing values
    .with_columns([
        pl.col("baseline_outcome").fill_null(0),
    ])

    # Select final variables
    .select([
        "id", "time", "treatment", "outcome",
        "baseline_outcome", "baseline_missing",
        "age", "age_group", "log_income", "test_score_std"
    ])
)

# Save cleaned data
cleaned.write_parquet("data/cleaned_data.parquet")
```

## Best Practices

### Data Management

1. **Use Parquet format**: Faster I/O and smaller file sizes than CSV
2. **Leverage polars for large datasets**: More memory-efficient than pandas
3. **Keep raw data separate**: Never overwrite original data files
4. **Document transformations**: Comment data cleaning steps clearly
5. **Save intermediate results**: Cache cleaned datasets to avoid reprocessing

### Regression Analysis

1. **Pre-specify models**: Define specifications before seeing results (pre-analysis plan)
2. **Always cluster**: Use cluster-robust SE when randomization is clustered
3. **Include stratification FE**: Always include strata fixed effects when applicable
4. **Report multiple specifications**: Show robustness with different controls
5. **Correct for multiple testing**: Use Romano-Wolf, Bonferroni, or FDR when testing multiple hypotheses
6. **Check balance**: Verify baseline covariate balance across treatment arms
7. **Test for attrition**: Check differential attrition by treatment status

### Visualization

1. **Export to multiple formats**: Save PNG for presentations, SVG for papers, HTML for sharing
2. **Use consistent styling**: Define color schemes and themes upfront
3. **Make plots self-contained**: Include informative titles and axis labels
4. **Show uncertainty**: Always include confidence intervals or standard errors
5. **Consider colorblind-friendly palettes**: Use accessible color schemes

### Code Organization

1. **Separate scripts by purpose**:
   - `01_clean.py`: Data cleaning
   - `02_analysis.py`: Main analysis
   - `03_figures.py`: Create visualizations
   - `04_tables.py`: Generate tables

2. **Use relative paths**: Make code portable across systems

3. **Comment liberally**: Explain the "why" not just the "what"

4. **Version control**: Use git to track changes

## Using Bundled Resources

### Scripts

- **`scripts/run_analysis.py`**: Template for RCT analysis workflow
- **`scripts/create_balance_table.py`**: Generate balance tables
- **`scripts/make_coefplot.py`**: Create coefficient plots with Altair
- **`scripts/export_results.py`**: Export regression results to LaTeX/HTML

### References

- **`references/pyfixest_quick_ref.md`**: Common pyfixest commands and syntax
- **`references/polars_cheatsheet.md`**: Polars operations reference
- **`references/altair_examples.md`**: Altair visualization examples
- **`references/rct_checklist.md`**: RCT analysis best practices checklist

### Assets

- **`assets/analysis_template.py`**: Complete RCT analysis template
- **`assets/example_data.csv`**: Sample dataset for testing
- **`assets/viz_theme.json`**: Altair theme for publication-quality plots

## Comparison with Stata

| Feature | Stata (via stata skill) | Python (via pyfixest skill) |
|---------|------------------------|----------------------------|
| Speed | Good for moderate data | Excellent for large data |
| Fixed Effects | reghdfe | pyfixest |
| Syntax | Do files | Python scripts |
| Reproducibility | .do files | .py files + notebooks |
| Visualization | Limited | Excellent (Altair) |
| Data manipulation | Stata commands | Polars (very fast) |
| Package ecosystem | Stata packages | Python ecosystem |
| Licensing | Commercial | Open source |
| Memory efficiency | Limited | Excellent (Polars) |
| Interactive analysis | Stata interface | Jupyter notebooks |

**When to use Stata skill:**

- Legacy code or .do files
- Team uses Stata exclusively
- Stata-specific commands needed
- Working on Windows with Stata license

**When to use pyfixest skill:**

- Large datasets (>1GB)
- Need data manipulation (cleaning, reshaping)
- Want publication-quality visualizations
- Prefer open-source tools
- Working in Jupyter notebooks
- Need integration with Python ecosystem

## Advanced Topics

### Custom Standard Errors

```python
# Implement custom variance-covariance matrix
import numpy as np

fit = pf.feols("outcome ~ treatment", data=data)

# Access model matrices
X = fit.X  # Design matrix
y = fit.Y  # Outcome vector
resid = fit.resid()  # Residuals

# Compute custom vcov (example: HC2)
# ... custom calculation ...
```

### Parallel Processing

```python
# Use polars lazy API for large datasets
lazy_data = pl.scan_csv("large_file.csv")

result = (
    lazy_data
    .filter(pl.col("year") == 2024)
    .with_columns([
        (pl.col("x") * 2).alias("x_doubled")
    ])
    .collect()  # Execute in parallel
)

# Run multiple regressions in parallel
from concurrent.futures import ProcessPoolExecutor

def run_regression(formula, data):
    return pf.feols(formula, data=data)

formulas = [
    "outcome1 ~ treatment",
    "outcome2 ~ treatment",
    "outcome3 ~ treatment"
]

with ProcessPoolExecutor() as executor:
    results = list(executor.map(run_regression, formulas, [data]*3))
```

### Integration with Jupyter Notebooks

```python
# In Jupyter notebook
import polars as pl
import pyfixest as pf
import altair as alt

# Set Altair to render inline
alt.data_transformers.enable('default')

# Load data
data = pl.read_csv("data.csv")

# Quick exploration
data.head()
data.describe()

# Run analysis
fit = pf.feols("outcome ~ treatment | strata", data=data)
fit.summary()  # Displays formatted table in notebook

# Show plot inline
chart = alt.Chart(data).mark_point().encode(x='x', y='y')
chart  # Automatically displays in notebook
```

## Troubleshooting

### Common Issues

**Import errors:**

- Ensure virtual environment is activated: `uv sync`
- Check package installation: `uv pip list | grep pyfixest`

**Memory errors with large datasets:**

- Use polars instead of pandas
- Use lazy evaluation: `pl.scan_csv()` then `.collect()`
- Process data in chunks
- Use Parquet format instead of CSV

**Convergence issues:**

- Check for multicollinearity with `.vif()`
- Scale large magnitude variables
- Check for perfect collinearity with fixed effects
- Try different optimization algorithms

**Visualization export errors:**

- Install vl-convert: `uv add vl-convert-python`
- For offline HTML: `chart.save('plot.html', inline=True)`
- Check file paths are valid

**Formula syntax errors:**

- Fixed effects come after first `|`
- IV specification uses two `|`: `Y ~ X1 | FE | endog ~ instruments`
- Use `C()` for categorical variables: `C(category)`
- Multiple variables: `+` not `,`

## Resources

### Official Documentation

- [PyFixest docs](https://py-econometrics.github.io/pyfixest/)
- [Polars docs](https://docs.pola.rs/)
- [Altair docs](https://altair-viz.github.io/)

### Tutorials

- PyFixest quickstart: <https://py-econometrics.github.io/pyfixest/quickstart.html>
- Polars user guide: <https://docs.pola.rs/user-guide/>
- Altair getting started: <https://altair-viz.github.io/getting_started/>

### Key Papers

- Correia, S. (2017). "Linear Models with High-Dimensional Fixed Effects" (reghdfe)
- Cameron, A. C., & Miller, D. L. (2015). "A practitioner's guide to cluster-robust inference"
- Athey, S., & Imbens, G. W. (2017). "The econometrics of randomized experiments"

## Quick Reference

```python
# Data loading
data = pl.read_csv("file.csv")
data = pl.read_parquet("file.parquet")

# Basic regression
fit = pf.feols("y ~ x1 + x2", data=data)
fit = pf.feols("y ~ x1 | fe", data=data)  # With FE
fit = pf.feols("y ~ x1", data=data, vcov={"CRV1": "cluster"})  # Clustered SE

# IV regression
fit = pf.feols("y ~ x1 | fe | endog ~ instrument", data=data)

# Multiple models
fits = pf.feols("y ~ csw(x1, x2, x3)", data=data)

# Results
fit.summary()
fit.tidy()  # DataFrame
fit.coef()  # Coefficients
fit.se()    # Standard errors
fit.confint()  # Confidence intervals

# Tables and plots
pf.etable([fit1, fit2, fit3])
fit.coefplot()

# Visualization
alt.Chart(data).mark_point().encode(x='x', y='y').save('plot.png')

# Data transformation
result = data.filter(pl.col("x") > 0).with_columns(
    (pl.col("y") * 2).alias("y_doubled")
)
```
