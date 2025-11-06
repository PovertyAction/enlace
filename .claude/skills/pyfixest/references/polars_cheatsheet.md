# Polars Cheatsheet

## Reading Data

```python
import polars as pl

# CSV
df = pl.read_csv("file.csv")
df = pl.read_csv("file.csv", separator="\t")

# Parquet
df = pl.read_parquet("file.parquet")

# JSON
df = pl.read_json("file.json")

# Excel
df = pl.read_excel("file.xlsx", sheet_name="Sheet1")

# Multiple files with glob pattern
df = pl.read_csv("data/*.csv")
df = pl.read_parquet("data/year=*/month=*/*.parquet")

# From pandas
df = pl.from_pandas(pandas_df)
```

## Writing Data

```python
# CSV
df.write_csv("output.csv")

# Parquet
df.write_parquet("output.parquet")

# JSON
df.write_json("output.json")

# Excel
df.write_excel("output.xlsx")

# To pandas
pandas_df = df.to_pandas()
```

## Basic Operations

```python
# View data
df.head(10)
df.tail(5)
df.glimpse()  # Overview of data types and values
df.describe()  # Summary statistics

# Shape and info
df.shape  # (rows, cols)
df.columns  # Column names
df.dtypes  # Column types
df.schema  # Full schema

# Select columns
df.select(["col1", "col2"])
df.select(pl.col("col1", "col2"))
df.select(pl.all())  # All columns
df.select(pl.col("*"))  # All columns

# Drop columns
df.drop(["col1", "col2"])

# Filter rows
df.filter(pl.col("age") > 25)
df.filter((pl.col("age") > 25) & (pl.col("city") == "NYC"))
df.filter(pl.col("name").is_in(["Alice", "Bob"]))

# Sort
df.sort("age")
df.sort("age", descending=True)
df.sort(["age", "name"])

# Limit
df.head(100)
df.tail(50)
df.slice(offset=10, length=20)
```

## Column Operations

```python
# Create new columns
df.with_columns([
    (pl.col("price") * pl.col("quantity")).alias("total"),
    pl.col("name").str.to_uppercase().alias("name_upper")
])

# Rename columns
df.rename({"old_name": "new_name"})

# Cast types
df.with_columns(pl.col("age").cast(pl.Int32))

# Replace values
df.with_columns(
    pl.col("status").replace({"old": "new"})
)
```

## Expressions

### Conditional Logic

```python
# When-then-otherwise
df.with_columns(
    pl.when(pl.col("age") < 18)
    .then(pl.lit("minor"))
    .when(pl.col("age") < 65)
    .then(pl.lit("adult"))
    .otherwise(pl.lit("senior"))
    .alias("age_group")
)
```

### String Operations

```python
# String methods
pl.col("name").str.to_lowercase()
pl.col("name").str.to_uppercase()
pl.col("name").str.strip()
pl.col("name").str.replace("old", "new")
pl.col("name").str.contains("pattern")
pl.col("name").str.starts_with("A")
pl.col("name").str.ends_with("Z")
pl.col("name").str.slice(0, 3)  # First 3 characters
pl.col("name").str.len_chars()  # Length

# Concatenate strings
pl.concat_str([pl.col("first_name"), pl.lit(" "), pl.col("last_name")])
```

### Numeric Operations

```python
# Math operations
pl.col("x") + 10
pl.col("x") - pl.col("y")
pl.col("x") * 2
pl.col("x") / pl.col("y")
pl.col("x") ** 2  # Power
pl.col("x").abs()
pl.col("x").sqrt()
pl.col("x").log()
pl.col("x").exp()

# Rounding
pl.col("x").round(2)
pl.col("x").floor()
pl.col("x").ceil()

# Clipping
pl.col("x").clip(lower=0, upper=100)
```

### Date Operations

```python
# Date components
pl.col("date").dt.year()
pl.col("date").dt.month()
pl.col("date").dt.day()
pl.col("date").dt.hour()
pl.col("date").dt.weekday()

# Date arithmetic
pl.col("date") + pl.duration(days=7)
pl.col("end_date") - pl.col("start_date")

# Date formatting
pl.col("date").dt.strftime("%Y-%m-%d")
```

## Aggregations

```python
# Basic aggregations
df.select([
    pl.col("value").mean(),
    pl.col("value").median(),
    pl.col("value").std(),
    pl.col("value").var(),
    pl.col("value").min(),
    pl.col("value").max(),
    pl.col("value").sum(),
    pl.count()
])

# Quantiles
pl.col("value").quantile(0.25)
pl.col("value").quantile(0.5)  # Median
pl.col("value").quantile(0.75)
```

## Group By

```python
# Basic group by
df.group_by("category").agg([
    pl.col("value").mean().alias("mean_value"),
    pl.col("value").std().alias("sd_value"),
    pl.count().alias("n")
])

# Multiple grouping variables
df.group_by(["category", "region"]).agg([
    pl.col("sales").sum(),
    pl.col("sales").mean()
])

# Group by with expressions
df.group_by(
    pl.col("date").dt.year().alias("year")
).agg(pl.col("sales").sum())
```

## Window Functions

```python
# Window operations
df.with_columns([
    # Mean by group
    pl.col("value").mean().over("category").alias("category_mean"),

    # Rank within group
    pl.col("value").rank().over("category").alias("rank"),

    # Cumulative sum by group
    pl.col("value").cum_sum().over("category").alias("cumsum"),

    # Lag/lead
    pl.col("value").shift(1).over("id").alias("value_lag"),
    pl.col("value").shift(-1).over("id").alias("value_lead"),

    # Row number
    pl.col("id").cum_count().over("category").alias("row_num")
])
```

## Joins

```python
# Inner join
df1.join(df2, on="id", how="inner")

# Left join
df1.join(df2, on="id", how="left")

# Outer join
df1.join(df2, on="id", how="outer")

# Multiple keys
df1.join(df2, on=["id", "date"], how="inner")

# Different column names
df1.join(df2, left_on="user_id", right_on="id", how="left")
```

## Concatenation

```python
# Vertical (stack rows)
pl.concat([df1, df2])
pl.concat([df1, df2], how="vertical")

# Horizontal (add columns)
pl.concat([df1, df2], how="horizontal")

# Diagonal (union with different columns)
pl.concat([df1, df2], how="diagonal")
```

## Reshaping

```python
# Pivot (long to wide)
df.pivot(
    values="value",
    index="id",
    columns="category"
)

# Melt (wide to long)
df.melt(
    id_vars=["id", "name"],
    value_vars=["col1", "col2", "col3"],
    variable_name="variable",
    value_name="value"
)

# Unpivot (same as melt)
df.unpivot(
    on=["col1", "col2"],
    index="id"
)
```

## Missing Data

```python
# Check for nulls
df.null_count()
df.select(pl.all().is_null().sum())

# Filter nulls
df.filter(pl.col("value").is_null())
df.filter(~pl.col("value").is_null())

# Drop nulls
df.drop_nulls()  # Drop if any null
df.drop_nulls(subset=["col1", "col2"])  # Drop if null in specific cols

# Fill nulls
df.fill_null(0)  # Fill with constant
df.fill_null(strategy="forward")  # Forward fill
df.fill_null(strategy="backward")  # Backward fill
df.fill_null(strategy="mean")  # Fill with mean

# Replace with expression
df.with_columns(
    pl.col("value").fill_null(pl.col("value").mean())
)
```

## Advanced Patterns

### Chaining Operations

```python
result = (
    df
    .filter(pl.col("year") == 2024)
    .with_columns([
        (pl.col("price") * 1.1).alias("price_adjusted"),
        pl.col("name").str.to_uppercase()
    ])
    .group_by("category")
    .agg([
        pl.col("price_adjusted").mean(),
        pl.count()
    ])
    .sort("price_adjusted", descending=True)
    .head(10)
)
```

### Lazy Evaluation

```python
# Start lazy computation
lazy_df = pl.scan_csv("large_file.csv")

# Build query
result = (
    lazy_df
    .filter(pl.col("year") == 2024)
    .group_by("category")
    .agg(pl.col("sales").sum())
    .collect()  # Execute query
)

# Show query plan
lazy_df.show_graph()
```

### Custom Functions

```python
# Apply function to column
df.with_columns(
    pl.col("value").map_elements(lambda x: x * 2).alias("doubled")
)

# Apply to multiple columns
df.with_columns(
    pl.struct(["col1", "col2"])
    .map_elements(lambda x: x["col1"] + x["col2"])
    .alias("sum")
)
```

## Performance Tips

1. **Use expressions over apply**: Vectorized operations are faster
2. **Use lazy evaluation**: `scan_csv()` instead of `read_csv()` for large files
3. **Use Parquet**: Faster I/O than CSV
4. **Filter early**: Reduce data size before expensive operations
5. **Use proper types**: Cast to appropriate types (Int32 vs Int64)
6. **Avoid pandas conversion**: Work in Polars when possible
7. **Use `select` over `with_columns`**: When you only need subset of columns

## Common Patterns for Econometrics

### Creating Lagged Variables

```python
# Sort by id and time first
df = df.sort(["id", "time"])

# Create lags
df = df.with_columns([
    pl.col("x").shift(1).over("id").alias("x_lag1"),
    pl.col("x").shift(2).over("id").alias("x_lag2"),
])
```

### Creating Treatment Indicators

```python
# Post-treatment indicator
df = df.with_columns(
    (pl.col("time") >= pl.col("treatment_time")).alias("post")
)

# Treatment × Post
df = df.with_columns(
    (pl.col("treatment") * pl.col("post")).alias("treatment_post")
)
```

### Creating Summary Statistics by Group

```python
# Balance table
balance = (
    df
    .group_by("treatment")
    .agg([
        pl.col("age").mean().alias("age_mean"),
        pl.col("age").std().alias("age_sd"),
        pl.col("female").mean().alias("female_prop"),
        pl.count().alias("n")
    ])
)
```

### Winsorizing

```python
# Winsorize at 1st and 99th percentiles
p01 = df.select(pl.col("value").quantile(0.01)).item()
p99 = df.select(pl.col("value").quantile(0.99)).item()

df = df.with_columns(
    pl.col("value").clip(p01, p99).alias("value_winsorized")
)
```

### Standardizing Variables

```python
# Z-score standardization
df = df.with_columns(
    ((pl.col("value") - pl.col("value").mean()) /
     pl.col("value").std()).alias("value_std")
)
```
