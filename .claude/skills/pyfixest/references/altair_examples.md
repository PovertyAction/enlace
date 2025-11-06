# Altair Visualization Examples

## Basic Chart Types

### Scatter Plot

```python
import altair as alt
import polars as pl

chart = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color='treatment:N'
).properties(
    width=600,
    height=400,
    title='Outcome by Age and Treatment'
)

chart.save('scatter.png')
```

### Line Plot

```python
chart = alt.Chart(data).mark_line(point=True).encode(
    x='time:Q',
    y='outcome:Q',
    color='treatment:N'
).properties(title='Outcome Over Time')
```

### Bar Chart

```python
chart = alt.Chart(data).mark_bar().encode(
    x='category:N',
    y='mean(outcome):Q',
    color='treatment:N'
)
```

### Histogram

```python
chart = alt.Chart(data).mark_bar().encode(
    x=alt.X('outcome:Q', bin=alt.Bin(maxbins=30)),
    y='count()',
    color='treatment:N'
)
```

### Box Plot

```python
chart = alt.Chart(data).mark_boxplot().encode(
    x='treatment:N',
    y='outcome:Q'
)
```

## Econometric Visualizations

### Coefficient Plot

```python
# From regression results
results_df = fit.tidy()

# Add confidence intervals if not present
results_df = results_df.with_columns([
    (pl.col("Estimate") - 1.96 * pl.col("Std. Error")).alias("CI_Lower"),
    (pl.col("Estimate") + 1.96 * pl.col("Std. Error")).alias("CI_Upper")
])

# Create base chart
base = alt.Chart(results_df).encode(
    y=alt.Y('Coefficient:N', sort='-x', title='Variable')
)

# Points
points = base.mark_point(size=100, filled=True).encode(
    x=alt.X('Estimate:Q', title='Coefficient Estimate'),
    color=alt.condition(
        alt.datum['Pr(>|t|)'] < 0.05,
        alt.value('steelblue'),
        alt.value('gray')
    )
)

# Error bars
error_bars = base.mark_rule().encode(
    x='CI_Lower:Q',
    x2='CI_Upper:Q'
)

# Zero line
zero_line = alt.Chart(pl.DataFrame({'zero': [0]})).mark_rule(
    strokeDash=[5, 5],
    color='red'
).encode(x='zero:Q')

chart = (error_bars + points + zero_line).properties(
    width=600,
    height=400,
    title='Regression Coefficients'
)
```

### Event Study Plot

```python
# From event study regression
event_data = fit.tidy()

# Main line
line = alt.Chart(event_data).mark_line(point=True).encode(
    x=alt.X('time_to_treatment:Q', title='Time to Treatment'),
    y=alt.Y('Estimate:Q', title='Treatment Effect'),
    color=alt.value('steelblue')
)

# Confidence interval band
band = alt.Chart(event_data).mark_area(opacity=0.3).encode(
    x='time_to_treatment:Q',
    y='CI_Lower:Q',
    y2='CI_Upper:Q',
    color=alt.value('steelblue')
)

# Zero line
zero = alt.Chart(pl.DataFrame({'y': [0]})).mark_rule(
    strokeDash=[5, 5],
    color='red'
).encode(y='y:Q')

chart = (band + line + zero).properties(
    width=700,
    height=400,
    title='Event Study: Treatment Effects Over Time'
)
```

### Balance Plot

```python
# Compare means across treatment groups
balance_data = data.group_by('treatment').agg([
    pl.col('age').mean().alias('age'),
    pl.col('income').mean().alias('income'),
    pl.col('education').mean().alias('education')
])

# Reshape to long format
balance_long = balance_data.unpivot(
    on=['age', 'income', 'education'],
    index='treatment'
)

# Create plot
chart = alt.Chart(balance_long).mark_bar().encode(
    x='treatment:N',
    y='value:Q',
    color='treatment:N',
    column='variable:N'
).properties(
    width=200,
    height=300
)
```

### Distribution Comparison

```python
# Overlapping histograms
chart = alt.Chart(data).mark_bar(opacity=0.7).encode(
    x=alt.X('outcome:Q', bin=alt.Bin(maxbins=30)),
    y='count()',
    color='treatment:N'
)

# Or density plots
chart = alt.Chart(data).transform_density(
    'outcome',
    as_=['outcome', 'density'],
    groupby=['treatment']
).mark_area(opacity=0.5).encode(
    x='outcome:Q',
    y='density:Q',
    color='treatment:N'
)
```

### Heterogeneity Plot

```python
# Treatment effects by subgroup
subgroup_results = pl.DataFrame({
    'subgroup': ['Male', 'Female', 'Young', 'Old'],
    'estimate': [0.15, 0.22, 0.18, 0.19],
    'se': [0.03, 0.04, 0.035, 0.038]
})

subgroup_results = subgroup_results.with_columns([
    (pl.col('estimate') - 1.96 * pl.col('se')).alias('ci_lower'),
    (pl.col('estimate') + 1.96 * pl.col('se')).alias('ci_upper')
])

base = alt.Chart(subgroup_results)

points = base.mark_point(size=100).encode(
    x='estimate:Q',
    y='subgroup:N',
    color='subgroup:N'
)

errors = base.mark_rule().encode(
    x='ci_lower:Q',
    x2='ci_upper:Q',
    y='subgroup:N'
)

zero = alt.Chart(pl.DataFrame({'x': [0]})).mark_rule(
    strokeDash=[5, 5],
    color='red'
).encode(x='x:Q')

chart = (errors + points + zero).properties(
    width=600,
    height=300,
    title='Treatment Effects by Subgroup'
)
```

## Advanced Techniques

### Faceted Plots

```python
# Multiple panels
chart = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color='treatment:N',
    facet=alt.Facet('region:N', columns=3)
).properties(
    width=200,
    height=200
)
```

### Layered Charts

```python
# Combine multiple marks
scatter = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q'
)

regression = scatter.transform_regression(
    'age', 'outcome'
).mark_line(color='red')

chart = scatter + regression
```

### Interactive Plots

```python
# Add zoom and pan
chart = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color='treatment:N',
    tooltip=['id', 'age', 'outcome', 'treatment']
).interactive()

# Selection highlighting
brush = alt.selection_interval()

points = alt.Chart(data).mark_point().encode(
    x='age:Q',
    y='outcome:Q',
    color=alt.condition(brush, 'treatment:N', alt.value('lightgray'))
).add_selection(brush)
```

### Customizing Appearance

```python
chart = alt.Chart(data).mark_point(
    size=100,
    filled=True,
    opacity=0.8
).encode(
    x=alt.X('age:Q',
            scale=alt.Scale(zero=False),
            axis=alt.Axis(title='Age (years)', titleFontSize=14)),
    y=alt.Y('outcome:Q',
            axis=alt.Axis(title='Outcome Score', titleFontSize=14)),
    color=alt.Color('treatment:N',
                    scale=alt.Scale(scheme='set2'),
                    legend=alt.Legend(title='Treatment Group'))
).properties(
    width=700,
    height=500,
    title=alt.TitleParams(
        'Treatment Effects on Outcome',
        fontSize=16,
        anchor='start'
    )
)
```

## Saving Charts

```python
# PNG
chart.save('figure.png')
chart.save('figure.png', ppi=300)  # High resolution

# SVG (vector graphics)
chart.save('figure.svg')

# PDF
chart.save('figure.pdf')

# HTML (interactive)
chart.save('figure.html')
chart.save('figure.html', inline=True)  # Standalone HTML
```

## Publication-Quality Defaults

```python
# Define custom theme
def publication_theme():
    return {
        'config': {
            'view': {'width': 600, 'height': 400},
            'mark': {'size': 80, 'opacity': 0.8},
            'axis': {
                'labelFontSize': 12,
                'titleFontSize': 14,
                'labelFont': 'Arial',
                'titleFont': 'Arial'
            },
            'legend': {
                'labelFontSize': 12,
                'titleFontSize': 13,
                'labelFont': 'Arial',
                'titleFont': 'Arial'
            },
            'title': {
                'fontSize': 16,
                'font': 'Arial',
                'anchor': 'start'
            }
        }
    }

# Register theme
alt.themes.register('publication', publication_theme)
alt.themes.enable('publication')

# Now all charts use this theme
chart = alt.Chart(data).mark_point().encode(x='x:Q', y='y:Q')
```

## Common Patterns for RCT Visualization

### Treatment vs Control Comparison

```python
# Side-by-side means
summary = data.group_by('treatment').agg([
    pl.col('outcome').mean().alias('mean'),
    pl.col('outcome').std().alias('se')
]).with_columns([
    (pl.col('mean') - 1.96 * pl.col('se')).alias('ci_lower'),
    (pl.col('mean') + 1.96 * pl.col('se')).alias('ci_upper')
])

base = alt.Chart(summary)

bars = base.mark_bar().encode(
    x='treatment:N',
    y='mean:Q',
    color='treatment:N'
)

errors = base.mark_errorbar().encode(
    x='treatment:N',
    y='ci_lower:Q',
    y2='ci_upper:Q'
)

chart = (bars + errors).properties(title='Mean Outcome by Treatment')
```

### Before-After Plot

```python
# Reshape data
before_after = data.select([
    'id', 'treatment',
    pl.col('baseline_outcome').alias('Before'),
    pl.col('outcome').alias('After')
]).unpivot(
    on=['Before', 'After'],
    index=['id', 'treatment'],
    variable_name='period',
    value_name='score'
)

# Plot
chart = alt.Chart(before_after).mark_line(point=True).encode(
    x='period:N',
    y='mean(score):Q',
    color='treatment:N'
).properties(title='Outcome Before and After Treatment')
```

### Multiple Outcomes Plot

```python
# Multiple outcome variables
outcomes_long = data.select([
    'id', 'treatment',
    pl.col('outcome1').alias('Health'),
    pl.col('outcome2').alias('Income'),
    pl.col('outcome3').alias('Education')
]).unpivot(
    on=['Health', 'Income', 'Education'],
    index=['id', 'treatment']
)

chart = alt.Chart(outcomes_long).mark_bar().encode(
    x='variable:N',
    y='mean(value):Q',
    color='treatment:N',
    column='variable:N'
)
```

## Tips and Tricks

1. **Use proper data types**: Specify `:Q` (quantitative), `:N` (nominal), `:O` (ordinal), or `:T` (temporal)

2. **Save at high resolution**: Use `ppi=300` for publication-quality PNG

3. **Make figures self-contained**: Include clear titles and axis labels

4. **Use colorblind-friendly palettes**: `scheme='tableau10'` or `scheme='set2'`

5. **Show uncertainty**: Always include confidence intervals for estimates

6. **Keep it simple**: Don't overcomplicate visualizations

7. **Test interactivity**: Use `.interactive()` for exploratory analysis

8. **Consistent styling**: Define a theme for all project figures

9. **Export multiple formats**: Save both PNG (for presentations) and SVG (for papers)

10. **Document code**: Comment what each visualization shows
