# Xan Practical Examples

Real-world examples demonstrating common CSV processing workflows with xan.

## Quick Reference Patterns

### Data Exploration Workflow

```bash
# Start with basic inspection
xan headers data.csv        # See column names
xan count data.csv          # Count rows
xan view data.csv | head    # Preview first rows
xan stats data.csv          # Get statistics

# Check data quality
xan frequency -s status data.csv     # Value distribution
xan stats -s price data.csv          # Column-specific stats
```

## Common Use Cases

### 1. Data Cleaning

**Remove duplicates:**

```bash
xan dedup data.csv > clean.csv
xan dedup -s email data.csv > unique_emails.csv
```

**Fill missing values:**

```bash
xan fill "N/A" data.csv
xan fill -s column "0" data.csv
```

**Standardize text:**

```bash
xan map 'trim(upper(name)) as name' data.csv
xan transform 'lower(email)' -c email data.csv
```

**Remove empty rows:**

```bash
xan filter 'len(trim(col(0))) > 0' data.csv
```

### 2. Filtering and Selection

**Select specific columns:**

```bash
xan select name,email,age data.csv
xan select '1,3-5,8' data.csv          # By index
xan drop unnecessary,columns data.csv   # Remove columns
```

**Filter by conditions:**

```bash
# Numeric conditions
xan filter 'age >= 18' users.csv
xan filter 'price > 100 && price < 500' products.csv

# String conditions
xan filter 'status eq "active"' data.csv
xan filter '"@example.com" in email' users.csv

# Date conditions
xan filter 'year(datetime(date)) == 2024' events.csv
```

**Sample data:**

```bash
xan sample 1000 data.csv               # Random 1000 rows
xan sample 0.1 data.csv                # 10% sample
xan sample --seed 42 100 data.csv      # Reproducible sample
```

### 3. Transformations

**Create calculated columns:**

```bash
# Simple calculations
xan map 'price * quantity as total' sales.csv

# String manipulation
xan map 'concat(first_name, " ", last_name) as full_name' users.csv

# Conditional logic
xan map 'if(score >= 90, "A", if(score >= 80, "B", "C")) as grade' scores.csv

# Type conversions
xan map 'number(text_amount) * 1.1 as adjusted' data.csv
```

**Multiple transformations:**

```bash
xan map 'upper(name) as NAME, price * 1.1 as new_price, category' data.csv
```

**Split columns:**

```bash
xan map 'split(full_name, " ") as (first, last)' users.csv
```

### 4. Aggregation and Statistics

**Basic aggregations:**

```bash
xan agg 'sum(sales), mean(price), count()' data.csv
xan agg 'min(date) as start, max(date) as end' events.csv
```

**Group by aggregations:**

```bash
# Simple grouping
xan groupby category data.csv

# With aggregations
xan groupby category --agg 'sum(sales) as total, count() as n' data.csv
xan groupby 'region,product' --agg 'mean(price), stddev(price)' data.csv
```

**Frequency analysis:**

```bash
xan frequency -s category data.csv
xan freq -s status data.csv | xan sort -s count -R  # Sorted by count
xan frequency -s category --limit 10 data.csv       # Top 10
```

### 5. Sorting

```bash
# Single column
xan sort -s name data.csv
xan sort -s date -R data.csv           # Reverse order

# Numeric sort
xan sort -N -s amount data.csv

# Multiple columns
xan sort -s 'last_name,first_name' data.csv
```

### 6. Joining Data

**Join two files:**

```bash
# Inner join
xan join id users.csv user_id orders.csv

# Left join
xan join --left email users.csv email addresses.csv

# Outer join
xan join --outer id file1.csv id file2.csv
```

**Concatenate files:**

```bash
# Stack rows (union)
xan cat rows file1.csv file2.csv file3.csv

# Side by side (columns)
xan cat cols file1.csv file2.csv
```

### 7. Reshaping Data

**Wide to long:**

```bash
xan unpivot data.csv
xan unpivot --keep id,name --columns 'q1,q2,q3,q4' survey.csv
```

**Long to wide:**

```bash
xan pivot --index id --columns category --values amount data.csv
```

**Transpose:**

```bash
xan transpose data.csv
xan stats data.csv | xan transpose  # Transposed stats
```

### 8. Time Series Analysis

**Extract date components:**

```bash
xan map 'year(datetime(date)) as year, month(datetime(date)) as month' data.csv
```

**Window functions:**

```bash
# Cumulative sum
xan window 'cumsum(amount) as running_total' transactions.csv

# Moving average
xan window 'rolling_mean(value, 7) as ma7' timeseries.csv

# Previous value
xan window 'lag(price, 1) as prev_price' stocks.csv

# Calculate change
xan window 'lag(value, 1) as prev' data.csv |
xan map 'value - prev as change'
```

**Time-based filtering:**

```bash
xan filter 'year(datetime(date)) >= 2023' events.csv
xan filter 'month(datetime(timestamp)) in [1, 2, 3]' data.csv  # Q1
```

### 9. Text Analysis

**Tokenization:**

```bash
xan tokenize -s text data.csv
xan tokenize --ngrams 2 -s content data.csv
```

**Build vocabulary:**

```bash
xan vocab -s text data.csv
```

**Search and replace:**

```bash
# Search
xan search -s column 'pattern' data.csv
xan grep 'pattern' data.csv

# Replace
xan search --replace 'old' 'new' data.csv
```

### 10. Format Conversion

**CSV to other formats:**

```bash
xan to json data.csv > data.json
xan to xlsx data.csv -o output.xlsx
xan to parquet data.csv -o data.parquet
xan to npy data.csv  # NumPy format
```

**Other formats to CSV:**

```bash
xan from json data.json > data.csv
xan from excel data.xlsx > data.csv
xan from ndjson stream.ndjson > data.csv
```

**Change delimiter:**

```bash
xan fmt -t '|' data.csv  # Pipe-separated
xan fmt -t '\t' data.csv # Tab-separated
xan -d ';' view data.csv # Read semicolon-separated
```

### 11. Advanced Pipelines

**Complex data workflow:**

```bash
# Clean, filter, aggregate, and sort
xan dedup data.csv |
xan filter 'year(datetime(date)) == 2024' |
xan groupby category --agg 'sum(sales) as total, count() as n' |
xan sort -N -s total -R |
xan head -n 10
```

**Data quality report:**

```bash
# Count nulls per column
xan map 'if(trim(col(0)) eq "", 1, 0) as empty' data.csv |
xan agg 'sum(empty) as null_count'

# Get stats for multiple columns
xan select price,quantity,discount data.csv |
xan stats |
xan transpose
```

**Split and process:**

```bash
# Split by category
xan partition -s category data.csv --outdir ./by_category/

# Split into chunks
xan split -n 1000 large.csv --outdir ./chunks/
```

### 12. Visualization

**Terminal visualizations:**

```bash
# Histogram
xan hist -s age users.csv
xan frequency -s category data.csv | xan hist

# Scatter plot
xan plot -x age -y income --scatter users.csv

# Line chart
xan plot -x date -y value --line timeseries.csv

# Heatmap
xan heatmap correlation_matrix.csv
```

### 13. Working with Large Files

**Progress monitoring:**

```bash
xan progress large.csv | xan filter 'score > 90'
```

**Parallel processing:**

```bash
xan parallel -t 4 data.csv | xan agg 'sum(amount)'
```

**Memory-efficient processing:**

```bash
# Stream processing with pipes
cat large.csv | xan filter 'active' | xan select id,name | xan head -n 1000
```

### 14. Data Validation

**Check for required fields:**

```bash
xan filter 'len(trim(email)) == 0 || len(trim(name)) == 0' users.csv
```

**Validate email format:**

```bash
xan filter '!match(email, /^[\w.+-]+@[\w.-]+\.[a-z]{2,}$/i)' users.csv
```

**Find outliers:**

```bash
# Values outside 2 standard deviations
xan stats -s price data.csv > stats.csv
# Then use the mean and stddev to filter
xan filter 'abs(price - 100) > 2 * 15' data.csv  # Example values
```

**Duplicate detection:**

```bash
xan frequency -s email users.csv |
xan filter 'count > 1' |
xan sort -N -s count -R
```

## Real-World Workflows

### E-commerce Analysis

```bash
# Top products by revenue
xan map 'price * quantity as revenue' sales.csv |
xan groupby product --agg 'sum(revenue) as total_rev, count() as orders' |
xan sort -N -s total_rev -R |
xan head -n 20
```

### Customer Segmentation

```bash
# Segment customers by purchase behavior
xan groupby customer_id --agg 'sum(amount) as total, count() as orders, mean(amount) as avg' orders.csv |
xan map 'if(total > 1000, "high", if(total > 500, "medium", "low")) as segment' |
xan frequency -s segment
```

### Log Analysis

```bash
# Parse and analyze web logs
xan map 'split(request, " ") as (method, path, protocol)' access.log |
xan filter 'status >= 400' |
xan frequency -s path --limit 20 |
xan sort -N -s count -R
```

### Financial Reporting

```bash
# Monthly revenue summary
xan map 'year(datetime(date)) as year, month(datetime(date)) as month, amount' transactions.csv |
xan groupby 'year,month' --agg 'sum(amount) as revenue, count() as txn_count' |
xan sort -s 'year,month'
```

### Data Quality Audit

```bash
# Generate data quality report
echo "column,total_rows,null_count,null_percentage,unique_count" > report.csv

for col in $(xan headers data.csv | cut -f2); do
  xan select "$col" data.csv |
  xan stats |
  xan select column,count,cardinality |
  xan map 'count as total' |
  # Add null count calculation
  xan map 'cardinality as unique'
done >> report.csv
```

## Performance Tips

### 1. Use Appropriate Commands

```bash
# Fast coarse filtering
xan grep 'pattern' large.csv  # Faster than filter for simple patterns

# Precise filtering
xan filter 'complex && expression' data.csv  # When logic is needed
```

### 2. Pipeline Optimization

```bash
# Good: Filter early in pipeline
xan filter 'active' large.csv | xan groupby category

# Bad: Process unnecessary data
xan groupby category large.csv | xan filter 'active'
```

### 3. Column Selection

```bash
# Good: Select needed columns first
xan select id,amount,date large.csv | xan filter 'amount > 100'

# Less efficient: Work with all columns
xan filter 'amount > 100' large.csv | xan select id,amount,date
```

### 4. Use Compression

```bash
# Xan handles compression transparently
xan view data.csv.gz
xan filter 'condition' data.csv.zst | xan to json
```

### 5. Sampling for Development

```bash
# Test on sample before processing full file
xan sample 1000 huge.csv | xan filter 'complex' | xan agg 'stats'

# Then run on full file when ready
xan filter 'complex' huge.csv | xan agg 'stats'
```

## Debugging Expressions

**Test expressions with `eval`:**

```bash
xan eval '2 + 2'
xan eval 'upper("hello world")'
xan eval 'if(10 > 5, "yes", "no")'
xan eval 'split("a,b,c", ",")'
```

**Incremental development:**

```bash
# Build complex expressions step by step
xan map 'price' data.csv  # Step 1: Check column
xan map 'price * 1.1' data.csv  # Step 2: Add calculation
xan map 'round(price * 1.1, 2) as new_price' data.csv  # Step 3: Format
```

**Use view to inspect:**

```bash
xan map 'expression' data.csv | xan view
xan filter 'condition' data.csv | xan count  # Check result count
```

## Integration Examples

### With Other Unix Tools

```bash
# Count lines matching condition
xan filter 'status eq "active"' data.csv | wc -l

# Combine with grep
xan to json data.csv | grep "pattern"

# Use with sort (on CSV)
xan select name,score data.csv | sort

# Pipe to head/tail
xan sort -s date data.csv | head -n 10
```

### With Database Tools

```bash
# Export to SQLite-compatible format
xan select id,name,value data.csv > import.csv
sqlite3 db.sqlite3 ".import import.csv table_name"

# Import from database export
sqlite3 db.sqlite3 "SELECT * FROM table" | xan view
```

### With Python/R

```bash
# Process with xan, analyze with Python
xan filter 'condition' data.csv > filtered.csv
python analyze.py filtered.csv

# Pre-process for R
xan select col1,col2,col3 data.csv | xan dedup > for_r.csv
Rscript analysis.R for_r.csv
```

## Quick Solutions Index

- **Remove duplicates**: `xan dedup`
- **Get row count**: `xan count`
- **View first N rows**: `xan head -n N`
- **Filter rows**: `xan filter 'condition'`
- **Select columns**: `xan select col1,col2`
- **Calculate statistics**: `xan stats`
- **Group and aggregate**: `xan groupby col --agg 'sum(x)'`
- **Join files**: `xan join key file1.csv key file2.csv`
- **Sort**: `xan sort -s column`
- **Convert format**: `xan to json`
- **Sample data**: `xan sample N`
- **Find unique values**: `xan frequency -s col`
- **Create new columns**: `xan map 'expr as name'`
- **Wide to long**: `xan unpivot`
- **Long to wide**: `xan pivot`

## Getting Help

```bash
xan --help                    # General help
xan <command> --help          # Command-specific help
xan help cheatsheet           # Expression language cheatsheet
xan help functions            # Function reference
xan help aggs                 # Aggregation functions
xan eval '<expression>'       # Test expressions
```
