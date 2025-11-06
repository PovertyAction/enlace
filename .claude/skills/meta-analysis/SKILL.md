---
name: meta-analysis
description: Perform meta-analysis of extracted research results, calculate effect sizes, generate forest plots, test for heterogeneity, and assess publication bias. Use after extracting treatment effects from multiple studies.
---

# Meta-Analysis for Research Synthesis

Synthesize results across multiple studies using meta-analytic techniques.

## When to Use This Skill

Use this skill when you need to:

- Calculate pooled effect sizes across studies
- Generate forest plots
- Test for heterogeneity (I², τ², Q-test)
- Assess publication bias (funnel plots, Egger's test)
- Perform subgroup analysis
- Calculate meta-regression

## Quick Start

### Calculate Effect Sizes

```python
import numpy as np
import pandas as pd

def calculate_cohens_d(mean1, mean2, sd1, sd2, n1, n2):
    """Calculate Cohen's d effect size."""
    # Pooled SD
    pooled_sd = np.sqrt(((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2))

    # Cohen's d
    d = (mean1 - mean2) / pooled_sd

    # Variance of d
    var_d = ((n1 + n2) / (n1 * n2)) + (d**2 / (2 * (n1 + n2)))

    # Standard error
    se_d = np.sqrt(var_d)

    return d, se_d

# Example: Convert extracted summary stats to effect sizes
studies = pd.DataFrame({
    "study": ["Smith 2020", "Jones 2021", "Lee 2022"],
    "treatment_mean": [5.2, 4.8, 5.5],
    "treatment_sd": [1.2, 1.5, 1.1],
    "treatment_n": [100, 120, 95],
    "control_mean": [4.1, 3.9, 4.3],
    "control_sd": [1.1, 1.4, 1.2],
    "control_n": [100, 115, 90]
})

# Calculate effect sizes
effect_sizes = []
for _, row in studies.iterrows():
    d, se = calculate_cohens_d(
        row["treatment_mean"], row["control_mean"],
        row["treatment_sd"], row["control_sd"],
        row["treatment_n"], row["control_n"]
    )
    effect_sizes.append({"study": row["study"], "d": d, "se": se})

effect_df = pd.DataFrame(effect_sizes)
print(effect_df)
```

### Fixed Effects Meta-Analysis

```python
def fixed_effects_meta_analysis(effects, se):
    """Calculate pooled effect using fixed effects model."""
    # Weights (inverse variance)
    weights = 1 / (se ** 2)

    # Pooled effect
    pooled_effect = np.sum(effects * weights) / np.sum(weights)

    # Standard error of pooled effect
    se_pooled = np.sqrt(1 / np.sum(weights))

    # 95% CI
    ci_lower = pooled_effect - 1.96 * se_pooled
    ci_upper = pooled_effect + 1.96 * se_pooled

    # Z-test
    z = pooled_effect / se_pooled
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    return {
        "pooled_effect": pooled_effect,
        "se": se_pooled,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "z": z,
        "p_value": p_value
    }

# Run meta-analysis
from scipy import stats
result = fixed_effects_meta_analysis(effect_df["d"].values, effect_df["se"].values)

print(f"Pooled Effect: {result['pooled_effect']:.3f}")
print(f"95% CI: [{result['ci_lower']:.3f}, {result['ci_upper']:.3f}]")
print(f"p-value: {result['p_value']:.4f}")
```

### Test Heterogeneity

```python
def test_heterogeneity(effects, se):
    """Calculate I² and Q-statistic."""
    weights = 1 / (se ** 2)
    pooled = np.sum(effects * weights) / np.sum(weights)

    # Q statistic
    Q = np.sum(weights * (effects - pooled) ** 2)
    df = len(effects) - 1
    p_Q = 1 - stats.chi2.cdf(Q, df)

    # I² statistic
    I2 = max(0, ((Q - df) / Q) * 100)

    # Tau² (between-study variance)
    C = np.sum(weights) - (np.sum(weights**2) / np.sum(weights))
    tau2 = max(0, (Q - df) / C)

    return {
        "Q": Q,
        "df": df,
        "p_Q": p_Q,
        "I2": I2,
        "tau2": tau2
    }

# Test heterogeneity
het = test_heterogeneity(effect_df["d"].values, effect_df["se"].values)

print(f"Q = {het['Q']:.2f} (df={het['df']}, p={het['p_Q']:.4f})")
print(f"I² = {het['I2']:.1f}%")
print(f"τ² = {het['tau2']:.4f}")

if het["I2"] > 75:
    print("⚠ High heterogeneity - consider random effects model")
```

### Forest Plot (Text-Based)

```python
def text_forest_plot(studies_df):
    """Create text-based forest plot."""
    print("\nForest Plot")
    print("=" * 70)
    print(f"{'Study':<20} {'Effect':<10} {'95% CI':<20} {'Weight':<10}")
    print("-" * 70)

    weights = 1 / (studies_df["se"] ** 2)
    weights_pct = (weights / weights.sum()) * 100

    for _, row in studies_df.iterrows():
        ci_lower = row["d"] - 1.96 * row["se"]
        ci_upper = row["d"] + 1.96 * row["se"]
        weight = weights_pct[row.name]

        # Visual representation
        scale_pos = int((row["d"] + 2) * 10)  # Scale: -2 to 2
        visual = " " * max(0, scale_pos) + "■"

        print(f"{row['study']:<20} {row['d']:>6.3f}    [{ci_lower:>6.3f}, {ci_upper:>6.3f}] {weight:>6.1f}%")
        print(f"{'':20} {visual}")

    print("-" * 70)

    # Pooled effect
    result = fixed_effects_meta_analysis(studies_df["d"].values, studies_df["se"].values)
    print(f"{'Pooled':<20} {result['pooled_effect']:>6.3f}    [{result['ci_lower']:>6.3f}, {result['ci_upper']:>6.3f}] {'':>6}")
    print("=" * 70)

text_forest_plot(effect_df)
```

### Publication Bias - Egger's Test

```python
def eggers_test(effects, se):
    """Test for publication bias using Egger's test."""
    from scipy import stats

    # Precision (1/SE)
    precision = 1 / se

    # Standard normal deviate
    sndev = effects / se

    # Regression: SNDEV ~ precision
    slope, intercept, r_value, p_value, std_err = stats.linregress(precision, sndev)

    # Intercept test
    t_stat = intercept / std_err
    df = len(effects) - 2
    p_intercept = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    return {
        "intercept": intercept,
        "se_intercept": std_err,
        "t": t_stat,
        "p_value": p_intercept
    }

# Test publication bias
egger = eggers_test(effect_df["d"].values, effect_df["se"].values)

print(f"\nEgger's Test for Publication Bias")
print(f"Intercept: {egger['intercept']:.3f} (SE={egger['se_intercept']:.3f})")
print(f"t = {egger['t']:.2f}, p = {egger['p_value']:.4f}")

if egger["p_value"] < 0.05:
    print("⚠ Evidence of publication bias (p < 0.05)")
else:
    print("✓ No significant publication bias detected")
```

## Complete Meta-Analysis Pipeline

```python
def run_meta_analysis(studies_df):
    """Complete meta-analysis workflow."""

    print("=" * 70)
    print("META-ANALYSIS REPORT")
    print("=" * 70)

    # 1. Calculate effect sizes (if needed)
    if "d" not in studies_df.columns:
        print("\n1. Calculating effect sizes...")
        # Calculate Cohen's d for each study
        # (assuming you have mean/SD/N data)

    # 2. Fixed effects model
    print("\n2. Fixed Effects Meta-Analysis")
    fe_result = fixed_effects_meta_analysis(studies_df["d"].values, studies_df["se"].values)
    print(f"   Pooled Effect: {fe_result['pooled_effect']:.3f} (SE={fe_result['se']:.3f})")
    print(f"   95% CI: [{fe_result['ci_lower']:.3f}, {fe_result['ci_upper']:.3f}]")
    print(f"   Z = {fe_result['z']:.2f}, p = {fe_result['p_value']:.4f}")

    # 3. Heterogeneity
    print("\n3. Heterogeneity Assessment")
    het = test_heterogeneity(studies_df["d"].values, studies_df["se"].values)
    print(f"   Q = {het['Q']:.2f} (df={het['df']}, p={het['p_Q']:.4f})")
    print(f"   I² = {het['I2']:.1f}%")
    print(f"   τ² = {het['tau2']:.4f}")

    # 4. Publication bias
    print("\n4. Publication Bias Assessment")
    egger = eggers_test(studies_df["d"].values, studies_df["se"].values)
    print(f"   Egger's test: t = {egger['t']:.2f}, p = {egger['p_value']:.4f}")

    # 5. Forest plot
    text_forest_plot(studies_df)

    return {
        "fixed_effects": fe_result,
        "heterogeneity": het,
        "publication_bias": egger
    }

# Run complete analysis
results = run_meta_analysis(effect_df)
```

## Integration with Research Workflow

```text
Extracted Data (multiple studies)
    │
    ▼
Calculate effect sizes
    │
    ▼
meta-analysis skill
    │
    ├─→ Fixed/Random effects
    ├─→ Heterogeneity tests
    ├─→ Publication bias
    └─→ Forest plots
    │
    ▼
Meta-analysis results
    │
    ▼
quarto (Report with visualizations)
```

## Best Practices

1. **Check heterogeneity first** - Use random effects if I² > 50%
2. **Always test publication bias** - Especially with < 10 studies
3. **Report both models** - Fixed and random effects
4. **Conduct sensitivity analysis** - Leave-one-out analysis
5. **Visualize results** - Forest plots essential for interpretation

## See Also

- **research-analyst** - Extract data for meta-analysis
- **data-validator** - Ensure data quality before meta-analysis
- **quarto** - Create publication-ready meta-analysis reports
