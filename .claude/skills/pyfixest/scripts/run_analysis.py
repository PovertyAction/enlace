#!/usr/bin/env python3
"""Template script for RCT analysis using pyfixest.

This script provides a complete workflow for analyzing randomized controlled trials,
including balance checks, treatment effect estimation, and result visualization.

Usage:
    python run_analysis.py --data data/trial_data.csv --output results/
"""

import argparse
from pathlib import Path

import altair as alt
import polars as pl
import pyfixest as pf


def load_and_prepare_data(data_path: str) -> pl.DataFrame:
    """Load and perform basic data preparation."""
    print(f"Loading data from {data_path}")

    # Determine file type and load accordingly
    path = Path(data_path)
    if path.suffix == ".csv":
        data = pl.read_csv(data_path)
    elif path.suffix == ".parquet":
        data = pl.read_parquet(data_path)
    elif path.suffix == ".xlsx":
        data = pl.read_excel(data_path)
    else:
        msg = f"Unsupported file format: {path.suffix}"
        raise ValueError(msg)

    print(f"Loaded {len(data)} observations")
    return data


def check_balance(
    data: pl.DataFrame, treatment_var: str, covariates: list[str]
) -> pl.DataFrame:
    """Create balance table comparing treatment and control groups."""
    print("\n" + "=" * 80)
    print("BALANCE CHECK")
    print("=" * 80 + "\n")

    balance_stats = []

    for covar in covariates:
        # Calculate means by treatment group
        group_means = (
            data.group_by(treatment_var)
            .agg(
                [
                    pl.col(covar).mean().alias("mean"),
                    pl.col(covar).std().alias("sd"),
                    pl.count().alias("n"),
                ]
            )
            .sort(treatment_var)
        )

        # Test for differences
        fit = pf.feols(f"{covar} ~ {treatment_var}", data=data, vcov="HC1")
        results = fit.tidy()

        balance_stats.append(
            {
                "variable": covar,
                "control_mean": group_means.filter(pl.col(treatment_var) == 0)["mean"][
                    0
                ],
                "treatment_mean": group_means.filter(pl.col(treatment_var) == 1)[
                    "mean"
                ][0],
                "difference": results.filter(pl.col("Coefficient") == treatment_var)[
                    "Estimate"
                ][0],
                "pvalue": results.filter(pl.col("Coefficient") == treatment_var)[
                    "Pr(>|t|)"
                ][0],
            }
        )

    balance_df = pl.DataFrame(balance_stats)
    print(balance_df)
    return balance_df


def estimate_treatment_effects(
    data: pl.DataFrame,
    outcome: str,
    treatment: str,
    covariates: list[str] = None,
    cluster: str = None,
    strata: str = None,
) -> dict:
    """Estimate treatment effects with multiple specifications."""
    print("\n" + "=" * 80)
    print("TREATMENT EFFECT ESTIMATION")
    print("=" * 80 + "\n")

    # Determine standard error type
    if cluster:
        vcov = {"CRV1": cluster}
        print(f"Using cluster-robust standard errors (cluster: {cluster})")
    else:
        vcov = "HC1"
        print("Using heteroskedasticity-robust standard errors")

    models = {}

    # Model 1: Simple treatment effect
    print("\nModel 1: Simple treatment effect")
    fml1 = f"{outcome} ~ {treatment}"
    if strata:
        fml1 += f" | {strata}"
    models["model1"] = pf.feols(fml1, data=data, vcov=vcov)
    models["model1"].summary()

    # Model 2: With covariates
    if covariates:
        print("\nModel 2: With control variables")
        controls = " + ".join(covariates)
        fml2 = f"{outcome} ~ {treatment} + {controls}"
        if strata:
            fml2 += f" | {strata}"
        models["model2"] = pf.feols(fml2, data=data, vcov=vcov)
        models["model2"].summary()

    # Model 3: With baseline outcome (if available)
    baseline_outcome = f"baseline_{outcome}"
    if baseline_outcome in data.columns:
        print("\nModel 3: ANCOVA specification (with baseline outcome)")
        fml3 = f"{outcome} ~ {treatment} + {baseline_outcome}"
        if covariates:
            fml3 += " + " + " + ".join(covariates)
        if strata:
            fml3 += f" | {strata}"
        models["model3"] = pf.feols(fml3, data=data, vcov=vcov)
        models["model3"].summary()

    return models


def create_results_table(models: dict, output_path: str) -> None:
    """Create publication-quality results table."""
    print("\n" + "=" * 80)
    print("CREATING RESULTS TABLE")
    print("=" * 80 + "\n")

    model_list = list(models.values())

    # Create table
    pf.etable(
        model_list,
        coef_fmt="b (se)",
        signif_code=[0.01, 0.05, 0.1],
        output=output_path,
    )

    print(f"Table saved to: {output_path}")


def create_coefficient_plot(models: dict, treatment: str, output_path: str) -> None:
    """Create coefficient plot comparing treatment effects across specifications."""
    print("\n" + "=" * 80)
    print("CREATING COEFFICIENT PLOT")
    print("=" * 80 + "\n")

    # Combine results from all models
    coef_data = []
    for name, model in models.items():
        tidy_df = model.tidy()
        treatment_row = tidy_df.filter(pl.col("Coefficient") == treatment)
        if len(treatment_row) > 0:
            coef_data.append(
                treatment_row.with_columns(
                    [pl.lit(name.replace("model", "Model ")).alias("model")]
                )
            )

    if not coef_data:
        print("No treatment coefficients found to plot")
        return

    plot_data = pl.concat(coef_data)

    # Calculate confidence intervals if not present
    if "CI_Lower" not in plot_data.columns:
        plot_data = plot_data.with_columns(
            [
                (pl.col("Estimate") - 1.96 * pl.col("Std. Error")).alias("CI_Lower"),
                (pl.col("Estimate") + 1.96 * pl.col("Std. Error")).alias("CI_Upper"),
            ]
        )

    # Create plot
    base = alt.Chart(plot_data).encode(y=alt.Y("model:N", title="Specification"))

    points = base.mark_point(size=100, filled=True).encode(
        x=alt.X("Estimate:Q", title="Treatment Effect"),
        color=alt.condition(
            alt.datum["Pr(>|t|)"] < 0.05, alt.value("steelblue"), alt.value("gray")
        ),
    )

    error_bars = base.mark_rule().encode(x="CI_Lower:Q", x2="CI_Upper:Q")

    # Add zero line
    zero_line = (
        alt.Chart(pl.DataFrame({"zero": [0]}))
        .mark_rule(strokeDash=[5, 5], color="red")
        .encode(x="zero:Q")
    )

    chart = (error_bars + points + zero_line).properties(
        width=600, height=max(300, len(models) * 80), title="Treatment Effect Estimates"
    )

    # Save plot
    chart.save(output_path)
    print(f"Coefficient plot saved to: {output_path}")


def main():
    """Run complete RCT analysis workflow."""
    parser = argparse.ArgumentParser(description="Run RCT analysis with pyfixest")

    # Required arguments
    parser.add_argument("--data", required=True, help="Path to input data file")
    parser.add_argument("--outcome", required=True, help="Outcome variable name")
    parser.add_argument("--treatment", required=True, help="Treatment variable name")

    # Optional arguments
    parser.add_argument(
        "--covariates", nargs="+", help="Control variables (space-separated)"
    )
    parser.add_argument("--cluster", help="Cluster variable for standard errors")
    parser.add_argument("--strata", help="Stratification variable (fixed effects)")
    parser.add_argument(
        "--output",
        default="results/",
        help="Output directory for results (default: results/)",
    )
    parser.add_argument(
        "--balance-vars",
        nargs="+",
        help="Variables for balance check (space-separated)",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    data = load_and_prepare_data(args.data)

    # Balance check
    if args.balance_vars:
        balance_df = check_balance(data, args.treatment, args.balance_vars)
        balance_df.write_csv(output_dir / "balance_table.csv")

    # Estimate treatment effects
    models = estimate_treatment_effects(
        data=data,
        outcome=args.outcome,
        treatment=args.treatment,
        covariates=args.covariates,
        cluster=args.cluster,
        strata=args.strata,
    )

    # Create results table
    table_path = str(output_dir / "results_table.tex")
    create_results_table(models, table_path)

    # Create coefficient plot
    plot_path = str(output_dir / "coef_plot.png")
    create_coefficient_plot(models, args.treatment, plot_path)

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {output_dir}")


if __name__ == "__main__":
    main()
