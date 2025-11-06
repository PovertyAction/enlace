#!/usr/bin/env python3
"""Complete RCT analysis template using pyfixest.

This template provides a full workflow for analyzing randomized controlled trials,
from data loading through final tables and figures.

Modify the configuration section to match your data and analysis requirements.
"""

from pathlib import Path

import altair as alt
import polars as pl
import pyfixest as pf

# =============================================================================
# CONFIGURATION
# =============================================================================

# Data paths
DATA_PATH = "data/trial_data.csv"
OUTPUT_DIR = "results/"

# Variable names
OUTCOME_VAR = "outcome"
TREATMENT_VAR = "treatment"
BASELINE_OUTCOME = "baseline_outcome"
CLUSTER_VAR = "cluster_id"  # Set to None if no clustering
STRATA_VAR = "strata"  # Set to None if no stratification

# Control variables for ANCOVA
CONTROL_VARS = ["age", "gender", "education"]

# Variables for balance check
BALANCE_VARS = ["age", "gender", "education", "income", "baseline_outcome"]

# Analysis settings
ALPHA = 0.05  # Significance level
RANDOM_SEED = 42  # For reproducibility

# =============================================================================
# SETUP
# =============================================================================

# Create output directory
output_dir = Path(OUTPUT_DIR)
output_dir.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("RCT ANALYSIS")
print("=" * 80)
print(f"\nOutput directory: {output_dir}")


# =============================================================================
# LOAD AND PREPARE DATA
# =============================================================================

print("\n" + "=" * 80)
print("LOADING DATA")
print("=" * 80)

data = pl.read_csv(DATA_PATH)
print(f"Loaded {len(data)} observations")
print(f"Columns: {', '.join(data.columns)}")

# Create analysis sample
analysis_data = (
    data
    # Remove missing outcomes
    .filter(~pl.col(OUTCOME_VAR).is_null())
    # Remove missing treatment
    .filter(~pl.col(TREATMENT_VAR).is_null())
)

print(f"\nAnalysis sample: {len(analysis_data)} observations")
print(f"Treatment group: {analysis_data.filter(pl.col(TREATMENT_VAR) == 1).height}")
print(f"Control group: {analysis_data.filter(pl.col(TREATMENT_VAR) == 0).height}")


# =============================================================================
# BALANCE CHECK
# =============================================================================

print("\n" + "=" * 80)
print("BALANCE CHECK")
print("=" * 80)

balance_results = []

for var in BALANCE_VARS:
    if var not in analysis_data.columns:
        print(f"Warning: {var} not found, skipping")
        continue

    # Summary by treatment group
    summary = (
        analysis_data.filter(~pl.col(var).is_null())
        .group_by(TREATMENT_VAR)
        .agg(
            [
                pl.col(var).mean().alias("mean"),
                pl.col(var).std().alias("sd"),
                pl.count().alias("n"),
            ]
        )
        .sort(TREATMENT_VAR)
    )

    # Test for difference
    fit = pf.feols(f"{var} ~ {TREATMENT_VAR}", data=analysis_data, vcov="HC1")
    results = fit.tidy()
    treatment_row = results.filter(pl.col("Coefficient") == TREATMENT_VAR)

    balance_results.append(
        {
            "Variable": var,
            "Control_Mean": summary.filter(pl.col(TREATMENT_VAR) == 0)["mean"][0],
            "Treatment_Mean": summary.filter(pl.col(TREATMENT_VAR) == 1)["mean"][0],
            "Difference": treatment_row["Estimate"][0],
            "P_Value": treatment_row["Pr(>|t|)"][0],
        }
    )

balance_df = pl.DataFrame(balance_results)
print("\n", balance_df)

# Save balance table
balance_df.write_csv(output_dir / "balance_table.csv")
print(f"\nBalance table saved to: {output_dir / 'balance_table.csv'}")


# =============================================================================
# ATTRITION ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("ATTRITION ANALYSIS")
print("=" * 80)

# Create attrition indicator
data_with_attrition = data.with_columns(pl.col(OUTCOME_VAR).is_null().alias("attrited"))

# Overall attrition by treatment
attrition_by_treatment = (
    data_with_attrition.group_by(TREATMENT_VAR)
    .agg([pl.col("attrited").mean().alias("attrition_rate"), pl.count().alias("n")])
    .sort(TREATMENT_VAR)
)

print("\nAttrition rates by treatment:")
print(attrition_by_treatment)

# Test for differential attrition
attrition_fit = pf.feols(
    f"attrited ~ {TREATMENT_VAR}", data=data_with_attrition, vcov="HC1"
)
print("\nTest for differential attrition:")
attrition_fit.summary()


# =============================================================================
# PRIMARY ANALYSIS
# =============================================================================

print("\n" + "=" * 80)
print("PRIMARY ANALYSIS")
print("=" * 80)

# Determine standard error specification
if CLUSTER_VAR:
    vcov = {"CRV1": CLUSTER_VAR}
    print(f"Using cluster-robust SE (cluster: {CLUSTER_VAR})")
else:
    vcov = "HC1"
    print("Using heteroskedasticity-robust SE")

# Model 1: Simple treatment effect
print("\n--- Model 1: Simple treatment effect ---")
fml1 = f"{OUTCOME_VAR} ~ {TREATMENT_VAR}"
if STRATA_VAR:
    fml1 += f" | {STRATA_VAR}"
model1 = pf.feols(fml1, data=analysis_data, vcov=vcov)
model1.summary()

# Model 2: With baseline outcome (ANCOVA)
if BASELINE_OUTCOME in analysis_data.columns:
    print("\n--- Model 2: ANCOVA (with baseline outcome) ---")
    fml2 = f"{OUTCOME_VAR} ~ {TREATMENT_VAR} + {BASELINE_OUTCOME}"
    if STRATA_VAR:
        fml2 += f" | {STRATA_VAR}"
    model2 = pf.feols(fml2, data=analysis_data, vcov=vcov)
    model2.summary()
else:
    model2 = None
    print("\nWarning: Baseline outcome not found, skipping ANCOVA")

# Model 3: With all controls
if CONTROL_VARS:
    print("\n--- Model 3: With control variables ---")
    controls = " + ".join(CONTROL_VARS)
    fml3 = f"{OUTCOME_VAR} ~ {TREATMENT_VAR}"
    if model2:
        fml3 += f" + {BASELINE_OUTCOME}"
    fml3 += f" + {controls}"
    if STRATA_VAR:
        fml3 += f" | {STRATA_VAR}"
    model3 = pf.feols(fml3, data=analysis_data, vcov=vcov)
    model3.summary()
else:
    model3 = None
    print("\nNo control variables specified")


# =============================================================================
# RESULTS SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("TREATMENT EFFECT SUMMARY")
print("=" * 80)

# Calculate control mean
control_mean = (
    analysis_data.filter(pl.col(TREATMENT_VAR) == 0)
    .select(pl.col(OUTCOME_VAR).mean())
    .item()
)

# Extract results from each model
models = {"Model 1": model1}
if model2:
    models["Model 2"] = model2
if model3:
    models["Model 3"] = model3

for name, model in models.items():
    results = model.tidy()
    treatment_row = results.filter(pl.col("Coefficient") == TREATMENT_VAR)

    if len(treatment_row) > 0:
        est = treatment_row["Estimate"][0]
        se = treatment_row["Std. Error"][0]
        pval = treatment_row["Pr(>|t|)"][0]

        print(f"\n{name}:")
        print(f"  Coefficient: {est:.4f}")
        print(f"  Std. Error: {se:.4f}")
        print(f"  P-value: {pval:.4f}")
        print(f"  95% CI: [{est - 1.96 * se:.4f}, {est + 1.96 * se:.4f}]")
        print(f"  Effect size: {100 * est / control_mean:.2f}% of control mean")


# =============================================================================
# TABLES
# =============================================================================

print("\n" + "=" * 80)
print("CREATING TABLES")
print("=" * 80)

# Regression table
model_list = [m for m in [model1, model2, model3] if m is not None]
table_path = output_dir / "regression_table.tex"

pf.etable(
    model_list,
    coef_fmt="b (se)",
    signif_code=[0.01, 0.05, 0.1],
    output=str(table_path),
)

print(f"Regression table saved to: {table_path}")


# =============================================================================
# FIGURES
# =============================================================================

print("\n" + "=" * 80)
print("CREATING FIGURES")
print("=" * 80)

# Coefficient plot
coef_data = []
for i, model in enumerate(model_list, 1):
    tidy_df = model.tidy()
    treatment_row = tidy_df.filter(pl.col("Coefficient") == TREATMENT_VAR)
    if len(treatment_row) > 0:
        # Calculate CI if not present
        if "CI_Lower" not in treatment_row.columns:
            treatment_row = treatment_row.with_columns(
                [
                    (pl.col("Estimate") - 1.96 * pl.col("Std. Error")).alias(
                        "CI_Lower"
                    ),
                    (pl.col("Estimate") + 1.96 * pl.col("Std. Error")).alias(
                        "CI_Upper"
                    ),
                ]
            )
        coef_data.append(
            treatment_row.with_columns(pl.lit(f"Model {i}").alias("model"))
        )

if coef_data:
    plot_data = pl.concat(coef_data)

    base = alt.Chart(plot_data).encode(y=alt.Y("model:N", title="Specification"))

    points = base.mark_point(size=100, filled=True).encode(
        x=alt.X("Estimate:Q", title="Treatment Effect"),
        color=alt.condition(
            alt.datum["Pr(>|t|)"] < 0.05, alt.value("steelblue"), alt.value("gray")
        ),
    )

    error_bars = base.mark_rule().encode(x="CI_Lower:Q", x2="CI_Upper:Q")

    zero_line = (
        alt.Chart(pl.DataFrame({"zero": [0]}))
        .mark_rule(strokeDash=[5, 5], color="red")
        .encode(x="zero:Q")
    )

    coef_plot = (error_bars + points + zero_line).properties(
        width=600, height=300, title="Treatment Effect Estimates"
    )

    coef_plot_path = output_dir / "coefficient_plot.png"
    coef_plot.save(str(coef_plot_path))
    print(f"Coefficient plot saved to: {coef_plot_path}")

# Distribution comparison
dist_plot = (
    alt.Chart(analysis_data)
    .mark_bar(opacity=0.7)
    .encode(
        x=alt.X(f"{OUTCOME_VAR}:Q", bin=alt.Bin(maxbins=30), title=OUTCOME_VAR.title()),
        y=alt.Y("count()", title="Count"),
        color=alt.Color(
            f"{TREATMENT_VAR}:N",
            title="Treatment",
            scale=alt.Scale(domain=[0, 1], range=["gray", "steelblue"]),
        ),
    )
    .properties(width=600, height=400, title="Outcome Distribution by Treatment Group")
)

dist_plot_path = output_dir / "distribution_plot.png"
dist_plot.save(str(dist_plot_path))
print(f"Distribution plot saved to: {dist_plot_path}")


# =============================================================================
# COMPLETION
# =============================================================================

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print(f"\nAll results saved to: {output_dir}")
print("\nGenerated files:")
print("  - balance_table.csv")
print("  - regression_table.tex")
print("  - coefficient_plot.png")
print("  - distribution_plot.png")
