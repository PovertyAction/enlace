#!/usr/bin/env python3
"""Create balance tables for RCT analysis.

This script creates comprehensive balance tables comparing baseline characteristics
across treatment arms, including mean differences and statistical tests.

Usage:
    python create_balance_table.py --data data.csv --treatment treatment \
        --covariates age gender income --output balance_table.csv
"""

import argparse
from pathlib import Path

import polars as pl
import pyfixest as pf


def create_balance_table(
    data: pl.DataFrame, treatment_var: str, covariates: list[str]
) -> pl.DataFrame:
    """Create detailed balance table with tests for differences.

    Args:
        data: Input DataFrame
        treatment_var: Name of binary treatment variable
        covariates: List of baseline covariate names

    Returns:
        DataFrame with balance statistics

    """
    balance_rows = []

    for covar in covariates:
        # Skip if variable not in data
        if covar not in data.columns:
            print(f"Warning: {covar} not found in data, skipping")
            continue

        # Calculate summary statistics by treatment group
        try:
            summary = (
                data.filter(~pl.col(covar).is_null())
                .group_by(treatment_var)
                .agg(
                    [
                        pl.col(covar).mean().alias("mean"),
                        pl.col(covar).std().alias("sd"),
                        pl.count().alias("n"),
                    ]
                )
                .sort(treatment_var)
            )

            # Extract control and treatment statistics
            control_stats = summary.filter(pl.col(treatment_var) == 0)
            treatment_stats = summary.filter(pl.col(treatment_var) == 1)

            if len(control_stats) == 0 or len(treatment_stats) == 0:
                print(f"Warning: Missing treatment or control group for {covar}")
                continue

            # Test for mean difference
            fit = pf.feols(f"{covar} ~ {treatment_var}", data=data, vcov="HC1")
            results = fit.tidy()
            treatment_row = results.filter(pl.col("Coefficient") == treatment_var)

            balance_rows.append(
                {
                    "Variable": covar,
                    "Control_Mean": round(control_stats["mean"][0], 3),
                    "Control_SD": round(control_stats["sd"][0], 3),
                    "Control_N": control_stats["n"][0],
                    "Treatment_Mean": round(treatment_stats["mean"][0], 3),
                    "Treatment_SD": round(treatment_stats["sd"][0], 3),
                    "Treatment_N": treatment_stats["n"][0],
                    "Difference": round(treatment_row["Estimate"][0], 3),
                    "SE": round(treatment_row["Std. Error"][0], 3),
                    "T_Stat": round(treatment_row["t value"][0], 3),
                    "P_Value": round(treatment_row["Pr(>|t|)"][0], 4),
                    "Significant": "***"
                    if treatment_row["Pr(>|t|)"][0] < 0.01
                    else "**"
                    if treatment_row["Pr(>|t|)"][0] < 0.05
                    else "*"
                    if treatment_row["Pr(>|t|)"][0] < 0.1
                    else "",
                }
            )

        except Exception as e:
            print(f"Error processing {covar}: {e}")
            continue

    return pl.DataFrame(balance_rows)


def format_balance_table_latex(balance_df: pl.DataFrame) -> str:
    """Format balance table for LaTeX output."""
    latex = "\\begin{table}[htbp]\n"
    latex += "\\centering\n"
    latex += "\\caption{Balance Table}\n"
    latex += "\\label{tab:balance}\n"
    latex += "\\begin{tabular}{lcccccc}\n"
    latex += "\\hline\\hline\n"
    latex += (
        "Variable & Control & Treatment & Difference & SE & t-stat & p-value \\\\\n"
    )
    latex += "\\hline\n"

    for row in balance_df.iter_rows(named=True):
        latex += (
            f"{row['Variable']} & "
            f"{row['Control_Mean']:.3f} & "
            f"{row['Treatment_Mean']:.3f} & "
            f"{row['Difference']:.3f}{row['Significant']} & "
            f"({row['SE']:.3f}) & "
            f"{row['T_Stat']:.3f} & "
            f"{row['P_Value']:.4f} \\\\\n"
        )

    latex += "\\hline\\hline\n"
    latex += "\\multicolumn{7}{l}{\\footnotesize Notes: *** p<0.01, ** p<0.05, * p<0.1} \\\\\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"

    return latex


def main():
    """Create balance table from command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create balance table for RCT analysis"
    )

    parser.add_argument("--data", required=True, help="Path to input data file")
    parser.add_argument(
        "--treatment", required=True, help="Name of treatment variable (binary 0/1)"
    )
    parser.add_argument(
        "--covariates",
        nargs="+",
        required=True,
        help="List of baseline covariates to include",
    )
    parser.add_argument(
        "--output", default="balance_table.csv", help="Output file path"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "latex", "both"],
        default="csv",
        help="Output format (csv, latex, or both)",
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.data}")
    data_path = Path(args.data)
    if data_path.suffix == ".csv":
        data = pl.read_csv(args.data)
    elif data_path.suffix == ".parquet":
        data = pl.read_parquet(args.data)
    else:
        msg = f"Unsupported file format: {data_path.suffix}"
        raise ValueError(msg)

    # Create balance table
    print(f"\nCreating balance table for {len(args.covariates)} variables")
    balance_df = create_balance_table(data, args.treatment, args.covariates)

    # Print to console
    print("\n" + "=" * 80)
    print("BALANCE TABLE")
    print("=" * 80 + "\n")
    print(balance_df)

    # Save output
    output_path = Path(args.output)
    if args.format in ["csv", "both"]:
        csv_path = output_path.with_suffix(".csv")
        balance_df.write_csv(csv_path)
        print(f"\nBalance table saved to: {csv_path}")

    if args.format in ["latex", "both"]:
        latex_path = output_path.with_suffix(".tex")
        latex_table = format_balance_table_latex(balance_df)
        with open(latex_path, "w") as f:
            f.write(latex_table)
        print(f"LaTeX table saved to: {latex_path}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    n_imbalanced = len(balance_df.filter(pl.col("P_Value") < 0.05))
    print(f"Variables tested: {len(balance_df)}")
    print(f"Significantly different (p<0.05): {n_imbalanced}")
    if n_imbalanced > 0:
        print(
            "\nWarning: Some baseline characteristics differ significantly by treatment."
        )
        print("Consider including these as control variables in your analysis.\n")
    else:
        print("\nBalance check passed: No significant baseline differences detected.\n")


if __name__ == "__main__":
    main()
