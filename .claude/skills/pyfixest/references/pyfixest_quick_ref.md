# PyFixest Quick Reference

## Model Estimation

### Basic Syntax

```python
import pyfixest as pf

# OLS regression
fit = pf.feols("y ~ x1 + x2", data=df)

# With fixed effects
fit = pf.feols("y ~ x1 | group_id", data=df)

# Multiple fixed effects
fit = pf.feols("y ~ x1 | fe1 + fe2", data=df)

# With cluster-robust SE
fit = pf.feols("y ~ x1", data=df, vcov={"CRV1": "cluster_id"})
```

### Standard Errors

```python
# Heteroskedasticity-robust (default)
vcov="HC1"

# Cluster-robust (one-way)
vcov={"CRV1": "cluster_var"}

# Two-way clustering
vcov={"CRV1": "cluster1 + cluster2"}

# Change SE after estimation
fit.vcov("HC3")
```

### Other Model Types

```python
# Poisson regression
fit = pf.fepois("count ~ x1 | fe", data=df)

# Logit
fit = pf.feglm("binary ~ x1", family="logit", data=df)

# Probit
fit = pf.feglm("binary ~ x1", family="probit", data=df)

# Quantile regression
fit = pf.quantreg("y ~ x1", q=0.5, data=df)
```

## Instrumental Variables

```python
# IV regression
# Syntax: "Y ~ exog | FE | endog ~ instruments"
fit = pf.feols("y ~ x1 | fe | x2 ~ z1 + z2", data=df)

# Access first-stage statistics
fit._f_stat_1st_stage
fit._model_1st_stage
```

## Multiple Estimation

```python
# Sequential replacement
pf.feols("y ~ sw(x1, x2, x3)", data=df)

# Cumulative stepwise
pf.feols("y ~ x1 + csw(x2, x3)", data=df)

# Multiple outcomes
pf.feols("sw(y1, y2, y3) ~ x1", data=df)

# Sample splits
pf.feols("y ~ x1", data=df, split="group_var")
```

## Results and Inference

### Accessing Results

```python
# Print summary
fit.summary()

# Get coefficients as DataFrame
fit.tidy()

# Extract components
fit.coef()          # Coefficients
fit.se()            # Standard errors
fit.confint()       # Confidence intervals
fit.tstat()         # t-statistics
fit.pvalue()        # p-values
fit.resid()         # Residuals
fit.predict()       # Fitted values
```

### Hypothesis Testing

```python
# Wald test
fit.wald_test(R=constraint_matrix)

# Joint confidence intervals
fit.confint(joint=True)
```

### Advanced Inference

```python
# Wild bootstrap
fit.wildboottest(param="x1", reps=9999)

# Randomization inference
fit.ritest(resampvar="treatment", reps=5000)

# Causal cluster variance
fit.ccv()
```

### Multiple Testing Corrections

```python
from pyfixest.multcomp import rwolf, bonferroni

# Romano-Wolf
fits = pf.feols("sw(y1, y2, y3) ~ treatment", data=df)
rwolf(fits, param="treatment", reps=1000)

# Bonferroni
bonferroni(fits, param="treatment")
```

## Visualization

```python
# Coefficient plot
fit.coefplot()

# Event study plot
pf.iplot([fit])

# Publication tables
pf.etable([fit1, fit2, fit3])
pf.etable([fit1, fit2], output="table.tex")
```

## Difference-in-Differences

```python
# Two-way fixed effects
pf.feols("y ~ treatment_post | unit_id + time", data=df)

# Gardner's two-stage DiD
from pyfixest import did2s
pf.did2s(data=df, yname="y", idname="id", tname="time",
         gname="treatment_group", estimator="feols")

# Event study
pf.feols("y ~ i(time_to_treatment, ref=-1) | unit + time", data=df)
```

## Formula Syntax

### Basic Operators

- `+`: Add variables
- `-`: Remove variables (e.g., `y ~ . - x1` for all except x1)
- `:`: Interaction
- `*`: Full factorial (e.g., `x1*x2` = `x1 + x2 + x1:x2`)
- `|`: Separate formula parts (covariates | FE | IV)

### Special Functions

- `C()`: Treat as categorical/factor
- `I()`: Arithmetic operations (e.g., `I(x**2)`)
- `i()`: Categorical interactions with reference level
- `sw()`: Sequential replacement
- `csw()`: Cumulative stepwise
- `sw0()`, `csw0()`: Same but starting with empty specification

### Examples

```python
# Categorical variable
"y ~ C(group)"

# Polynomial
"y ~ x + I(x**2) + I(x**3)"

# Interactions
"y ~ x1*x2"  # x1 + x2 + x1:x2
"y ~ x1:x2"  # Only interaction term

# Event study with categorical time
"y ~ i(time_to_treatment, ref=-1)"

# Multiple FE
"y ~ x1 | fe1 + fe2 + fe3"

# IV with multiple instruments
"y ~ x1 | fe | endog ~ z1 + z2 + z3"
```

## Common Patterns

### RCT Analysis

```python
# Simple treatment effect
pf.feols("outcome ~ treatment", data=df, vcov="HC1")

# ANCOVA (with baseline)
pf.feols("outcome ~ treatment + baseline_outcome", data=df, vcov="HC1")

# With stratification
pf.feols("outcome ~ treatment | strata", data=df, vcov="HC1")

# Cluster randomization
pf.feols("outcome ~ treatment | strata",
         data=df, vcov={"CRV1": "cluster_id"})
```

### Panel Data

```python
# Two-way fixed effects
pf.feols("y ~ x1 | unit_id + time_period", data=panel)

# With lagged variables (create first)
panel = panel.with_columns(
    pl.col("x1").shift(1).over("unit_id").alias("x1_lag")
)
pf.feols("y ~ x1 + x1_lag | unit_id + time", data=panel)
```

### Heterogeneous Effects

```python
# Subgroup interactions
pf.feols("y ~ treatment*subgroup", data=df)

# Extract interaction coefficient
fit.tidy().filter(pl.col("Coefficient") == "treatment:subgroup")
```

## Tips and Best Practices

1. **Use appropriate SE**: Always specify `vcov` parameter
2. **Cluster when needed**: Use CRV1 for cluster randomization
3. **Include stratification FE**: Always include strata as fixed effects
4. **Check convergence**: Review fit.summary() for warnings
5. **Save models**: Use pickle to save fitted models for later
6. **Multiple specifications**: Use `csw()` for robustness checks
7. **Document choices**: Comment your code with justifications
8. **Pre-specify models**: Define analysis before seeing results

## Common Errors and Solutions

### "Collinearity detected"

- Check for perfectly correlated variables
- Fixed effects may absorb some variables
- Use `.vif()` to check variance inflation factors

### "Convergence not achieved"

- Scale variables with large magnitudes
- Check data quality (outliers, missing values)
- Try different starting values or algorithms

### "Insufficient degrees of freedom"

- Too many fixed effects relative to sample size
- Reduce number of fixed effects
- Check for singleton observations

### Memory errors

- Use polars instead of pandas for large data
- Process data in chunks
- Reduce number of fixed effects categories
