# PyFixest Econometric Analysis Skill

A comprehensive skill for econometric analysis in Python using pyfixest, polars, and altair.

## Overview

This skill provides a complete workflow for analyzing randomized controlled trials (RCTs) and other econometric applications in Python. It complements the Stata skill with modern, open-source alternatives that offer superior performance on large datasets and excellent visualization capabilities.

## Core Libraries

- **PyFixest**: Fixed effects regression with support for OLS, IV, Poisson, GLM, and DiD
- **Polars**: Lightning-fast DataFrame library for data transformation
- **Altair**: Declarative statistical visualization

## Contents

### Main Documentation

- **SKILL.md**: Complete skill documentation with usage examples and best practices

### Helper Scripts

Located in `scripts/`:

- **run_analysis.py**: Complete RCT analysis workflow from data to results
- **create_balance_table.py**: Generate balance tables with statistical tests
- **make_coefplot.py**: Create publication-quality coefficient plots

### Reference Documentation

Located in `references/`:

- **pyfixest_quick_ref.md**: Quick reference for PyFixest syntax and commands
- **polars_cheatsheet.md**: Comprehensive guide to Polars operations
- **rct_checklist.md**: Detailed checklist for RCT analysis

### Example Assets

Located in `assets/`:

- **analysis_template.py**: Complete analysis template ready to customize

## Quick Start

### Using the Analysis Template

1. Copy `assets/analysis_template.py` to your project
2. Edit the configuration section with your variable names
3. Run the script to generate tables and figures

```bash
python analysis_template.py
```

### Using Helper Scripts

Run a complete analysis:

```bash
python scripts/run_analysis.py \
    --data data/trial.csv \
    --outcome outcome \
    --treatment treatment \
    --covariates age gender education \
    --cluster cluster_id \
    --strata strata \
    --output results/
```

Create a balance table:

```bash
python scripts/create_balance_table.py \
    --data data/trial.csv \
    --treatment treatment \
    --covariates age gender income education \
    --output results/balance_table.csv
```

## Key Features

### Advantages Over Stata

- **Performance**: Faster on large datasets (>1GB)
- **Memory efficiency**: Polars handles data larger than RAM
- **Visualization**: Publication-quality plots with Altair
- **Free and open source**: No licensing costs
- **Modern ecosystem**: Integration with Python data science tools
- **Reproducibility**: Jupyter notebooks for interactive analysis

### When to Use This Skill vs Stata Skill

**Use PyFixest skill when:**

- Working with large datasets
- Need advanced visualizations
- Want faster data manipulation
- Prefer open-source tools
- Working in Jupyter notebooks

**Use Stata skill when:**

- Have existing .do files
- Team uses Stata exclusively
- Need Stata-specific commands
- Working on Windows with Stata license

## Example Workflow

```python
import polars as pl
import pyfixest as pf
import altair as alt

# Load data
data = pl.read_csv("trial_data.csv")

# Check balance
balance = data.group_by("treatment").agg([
    pl.col("age").mean(),
    pl.col("female").mean(),
    pl.count()
])

# Estimate treatment effect
fit = pf.feols("outcome ~ treatment + baseline_outcome | strata",
               data=data, vcov={"CRV1": "cluster_id"})
fit.summary()

# Create results table
pf.etable([fit], output="results/table1.tex")

# Visualize
fit.coefplot()
```

## Common Patterns

### RCT Analysis

```python
# Simple treatment effect
pf.feols("outcome ~ treatment", data=df, vcov="HC1")

# ANCOVA specification
pf.feols("outcome ~ treatment + baseline_outcome", data=df, vcov="HC1")

# With stratification
pf.feols("outcome ~ treatment | strata", data=df, vcov="HC1")

# Cluster randomization
pf.feols("outcome ~ treatment | strata",
         data=df, vcov={"CRV1": "cluster_id"})
```

### Data Transformation with Polars

```python
# Clean and prepare data
cleaned = (
    pl.read_csv("raw.csv")
    .filter(pl.col("age") > 0)
    .with_columns([
        (pl.col("outcome") - pl.col("baseline")).alias("change"),
        pl.col("name").str.to_uppercase()
    ])
    .group_by("treatment")
    .agg(pl.col("outcome").mean())
)
```

### Visualization with Altair

```python
# Coefficient plot
alt.Chart(results).mark_point().encode(
    x='estimate:Q',
    y='variable:N',
    color=alt.condition(
        alt.datum.pvalue < 0.05,
        alt.value('steelblue'),
        alt.value('gray')
    )
).save('coefplot.png')
```

## Best Practices

1. **Always pre-specify analyses**: Follow your pre-analysis plan
2. **Use appropriate standard errors**: Cluster when randomization is clustered
3. **Include stratification FE**: Always include strata as fixed effects
4. **Correct for multiple testing**: Use Romano-Wolf or Bonferroni
5. **Check balance**: Verify baseline characteristics are balanced
6. **Test for attrition**: Check differential attrition by treatment
7. **Document everything**: Comment code and save analysis logs
8. **Version control**: Use git to track changes
9. **Reproducibility**: Make code runnable from scratch

## Resources

### Documentation

- PyFixest: <https://py-econometrics.github.io/pyfixest/>
- Polars: <https://docs.pola.rs/>
- Altair: <https://altair-viz.github.io/>

### Key Papers

- Cameron & Miller (2015): "A practitioner's guide to cluster-robust inference"
- Athey & Imbens (2017): "The econometrics of randomized experiments"
- Correia (2017): "Linear Models with High-Dimensional Fixed Effects"

## Installation

The required packages are already included in `pyproject.toml`:

```toml
dependencies = [
    "pyfixest>=0.30.2",
    "polars>=1.0.0",
    "altair>=5.5.0",
]
```

For visualization export, also install:

```bash
uv add vl-convert-python
```

## Contributing

To improve this skill:

1. Add new helper scripts for common workflows
2. Expand reference documentation
3. Add more example assets
4. Document new PyFixest features
5. Share useful code patterns

## License

This skill documentation is part of the project and follows the project's license.

## Support

For questions about:

- **PyFixest**: Check the [official documentation](https://py-econometrics.github.io/pyfixest/)
- **Polars**: See the [user guide](https://docs.pola.rs/user-guide/)
- **Altair**: Visit the [documentation](https://altair-viz.github.io/)
- **This skill**: Review SKILL.md or the reference documentation
