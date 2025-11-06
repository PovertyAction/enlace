#!/usr/bin/env python3
"""Create coefficient plots from regression results.

This script creates publication-quality coefficient plots with confidence intervals
using Altair for visualization.

Usage:
    python make_coefplot.py --models model1.pkl model2.pkl --output coefplot.png
"""

import argparse
import pickle
from pathlib import Path

import altair as alt
import polars as pl


def load_model_results(model_path: str) -> dict:
    """Load saved model results from pickle file."""
    with open(model_path, "rb") as f:
        return pickle.load(f)


def create_coefplot_data(
    models: list, model_names: list[str] = None, keep_vars: list[str] = None
) -> pl.DataFrame:
    """Extract coefficient data from multiple models.

    Args:
        models: List of fitted pyfixest models
        model_names: Optional names for models (default: Model 1, Model 2, ...)
        keep_vars: Optional list of variables to include (default: all)

    Returns:
        DataFrame with coefficients, standard errors, and confidence intervals

    """
    if model_names is None:
        model_names = [f"Model {i + 1}" for i in range(len(models))]

    coef_data = []

    for model, name in zip(models, model_names, strict=False):
        # Get tidy results
        tidy_df = model.tidy()

        # Filter variables if specified
        if keep_vars:
            tidy_df = tidy_df.filter(pl.col("Coefficient").is_in(keep_vars))

        # Add model name
        tidy_df = tidy_df.with_columns(pl.lit(name).alias("model"))

        # Calculate confidence intervals if not present
        if "CI_Lower" not in tidy_df.columns:
            tidy_df = tidy_df.with_columns(
                [
                    (pl.col("Estimate") - 1.96 * pl.col("Std. Error")).alias(
                        "CI_Lower"
                    ),
                    (pl.col("Estimate") + 1.96 * pl.col("Std. Error")).alias(
                        "CI_Upper"
                    ),
                ]
            )

        coef_data.append(tidy_df)

    return pl.concat(coef_data)


def create_coefplot(
    coef_data: pl.DataFrame,
    title: str = "Coefficient Plot",
    width: int = 600,
    height: int = 400,
    color_by: str = "significance",
    show_zero_line: bool = True,
) -> alt.Chart:
    """Create coefficient plot with confidence intervals.

    Args:
        coef_data: DataFrame with coefficient estimates
        title: Plot title
        width: Plot width in pixels
        height: Plot height in pixels
        color_by: Color scheme ('significance', 'model', or 'none')
        show_zero_line: Whether to show reference line at zero

    Returns:
        Altair Chart object

    """
    # Base chart
    base = alt.Chart(coef_data)

    # Y-axis encoding (coefficient names)
    y_encoding = alt.Y("Coefficient:N", title="Variable", sort="-x")

    # Color encoding based on selection
    if color_by == "significance":
        color = alt.condition(
            alt.datum["Pr(>|t|)"] < 0.05, alt.value("steelblue"), alt.value("gray")
        )
    elif color_by == "model":
        color = alt.Color("model:N", title="Model")
    else:
        color = alt.value("steelblue")

    # Point estimates
    points = base.mark_point(size=100, filled=True).encode(
        x=alt.X("Estimate:Q", title="Coefficient Estimate"), y=y_encoding, color=color
    )

    # Confidence intervals
    error_bars = base.mark_rule().encode(x="CI_Lower:Q", x2="CI_Upper:Q", y=y_encoding)

    # Combine points and error bars
    chart = error_bars + points

    # Add zero reference line
    if show_zero_line:
        zero_line = (
            alt.Chart(pl.DataFrame({"zero": [0]}))
            .mark_rule(strokeDash=[5, 5], color="red", opacity=0.5)
            .encode(x="zero:Q")
        )
        chart = chart + zero_line

    # Set properties
    chart = chart.properties(width=width, height=height, title=title)

    return chart


def create_faceted_coefplot(
    coef_data: pl.DataFrame,
    facet_by: str = "model",
    title: str = "Coefficient Plot",
    width: int = 300,
    height: int = 400,
) -> alt.Chart:
    """Create coefficient plot with facets for multiple models.

    Args:
        coef_data: DataFrame with coefficient estimates
        facet_by: Variable to facet by (typically 'model')
        title: Plot title
        width: Width of each facet
        height: Height of each facet

    Returns:
        Altair Chart object with facets

    """
    # Base chart
    base = alt.Chart(coef_data)

    # Point estimates
    points = base.mark_point(size=80, filled=True).encode(
        x=alt.X("Estimate:Q", title="Coefficient"),
        y=alt.Y("Coefficient:N", title="Variable", sort="-x"),
        color=alt.condition(
            alt.datum["Pr(>|t|)"] < 0.05, alt.value("steelblue"), alt.value("gray")
        ),
    )

    # Confidence intervals
    error_bars = base.mark_rule().encode(
        x="CI_Lower:Q", x2="CI_Upper:Q", y=alt.Y("Coefficient:N", sort="-x")
    )

    # Zero line
    zero_line = (
        alt.Chart(pl.DataFrame({"zero": [0]}))
        .mark_rule(strokeDash=[5, 5], color="red", opacity=0.5)
        .encode(x="zero:Q")
    )

    # Combine and facet
    chart = (
        (error_bars + points + zero_line)
        .properties(width=width, height=height)
        .facet(column=alt.Column(f"{facet_by}:N", title=None))
    )

    return chart.properties(title=title)


def create_comparison_plot(
    coef_data: pl.DataFrame,
    variable: str,
    title: str = None,
    width: int = 500,
    height: int = 300,
) -> alt.Chart:
    """Create plot comparing estimates of single variable across models.

    Args:
        coef_data: DataFrame with coefficient estimates
        variable: Variable name to plot
        title: Plot title (default: "Estimates of {variable}")
        width: Plot width
        height: Plot height

    Returns:
        Altair Chart object

    """
    if title is None:
        title = f"Estimates of {variable}"

    # Filter to single variable
    plot_data = coef_data.filter(pl.col("Coefficient") == variable)

    base = alt.Chart(plot_data)

    points = base.mark_point(size=100, filled=True).encode(
        x=alt.X("Estimate:Q", title="Coefficient Estimate"),
        y=alt.Y("model:N", title="Specification"),
        color=alt.condition(
            alt.datum["Pr(>|t|)"] < 0.05, alt.value("steelblue"), alt.value("gray")
        ),
    )

    error_bars = base.mark_rule().encode(x="CI_Lower:Q", x2="CI_Upper:Q", y="model:N")

    zero_line = (
        alt.Chart(pl.DataFrame({"zero": [0]}))
        .mark_rule(strokeDash=[5, 5], color="red")
        .encode(x="zero:Q")
    )

    return (error_bars + points + zero_line).properties(
        width=width, height=height, title=title
    )


def main():
    """Create coefficient plots from command line."""
    parser = argparse.ArgumentParser(description="Create coefficient plots")

    parser.add_argument(
        "--models", nargs="+", help="Path(s) to saved model pickle files"
    )
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--model-names", nargs="+", help="Custom names for models (optional)"
    )
    parser.add_argument(
        "--keep-vars", nargs="+", help="Variables to include (optional, default: all)"
    )
    parser.add_argument("--title", default="Coefficient Plot", help="Plot title")
    parser.add_argument("--width", type=int, default=600, help="Plot width")
    parser.add_argument("--height", type=int, default=400, help="Plot height")
    parser.add_argument(
        "--style",
        choices=["standard", "faceted", "comparison"],
        default="standard",
        help="Plot style",
    )
    parser.add_argument(
        "--variable",
        help="Variable name for comparison plot (required if style=comparison)",
    )

    args = parser.parse_args()

    # Load models
    print(f"Loading {len(args.models)} model(s)")
    models = [load_model_results(path) for path in args.models]

    # Create coefficient data
    coef_data = create_coefplot_data(models, args.model_names, args.keep_vars)

    print(f"\nCreating {args.style} coefficient plot")

    # Create appropriate plot
    if args.style == "standard":
        chart = create_coefplot(
            coef_data, title=args.title, width=args.width, height=args.height
        )
    elif args.style == "faceted":
        chart = create_faceted_coefplot(
            coef_data, title=args.title, width=args.width // 2, height=args.height
        )
    elif args.style == "comparison":
        if not args.variable:
            print("Error: --variable required for comparison plot")
            return
        chart = create_comparison_plot(
            coef_data,
            args.variable,
            title=args.title,
            width=args.width,
            height=args.height,
        )

    # Save plot
    output_path = Path(args.output)
    chart.save(str(output_path))
    print(f"Plot saved to: {output_path}")


if __name__ == "__main__":
    main()
