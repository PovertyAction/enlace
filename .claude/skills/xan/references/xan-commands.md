# Xan Command Reference

Complete reference for all xan commands, organized by category.

## File Exploration & Visualization

### count (c)

Count the number of rows in a CSV file.

```bash
xan count data.csv
xan c data.csv  # Short alias
```

### headers (h)

Display column names with their indices.

```bash
xan headers data.csv
xan h data.csv  # Short alias
```

### view (v)

Preview a CSV file in a human-friendly formatted way.

```bash
xan view data.csv
xan v data.csv  # Short alias
xan view -l 50 data.csv  # Limit to 50 rows
```

### flatten

Show a flattened, row-by-row display of the CSV data.

```bash
xan flatten data.csv
xan flatten -n 1 data.csv  # Show only first row
```

### hist

Print a histogram with frequency bars.

```bash
xan hist -s column data.csv
xan frequency column data.csv | xan hist  # From frequency table
```

### plot

Generate scatter plots or line charts in the terminal.

```bash
xan plot -x column1 -y column2 data.csv
xan plot --scatter -x age -y income data.csv
xan plot --line -x date -y value data.csv
```

### heatmap

Visualize a CSV matrix as a heatmap.

```bash
xan heatmap matrix.csv
```

### progress

Display a progress bar while reading data.

```bash
xan progress data.csv | xan some-command
```

## Search & Filter

### search

Find or replace patterns in CSV data.

```bash
xan search 'pattern' data.csv
xan search -s column 'pattern' data.csv  # Search in specific column
xan search --replace 'old' 'new' data.csv
```

### grep

Fast, coarse filtering (faster than filter but less precise).

```bash
xan grep 'pattern' data.csv
xan grep -v 'pattern' data.csv  # Invert match
```

### filter

Keep rows where evaluated expression is true.

```bash
xan filter 'age > 25' data.csv
xan filter 'status == "active"' data.csv
xan filter 'revenue > 1000 && category == "A"' data.csv
```

### head

Extract the first N rows.

```bash
xan head data.csv           # Default: 10 rows
xan head -n 100 data.csv    # First 100 rows
```

### tail

Extract the last N rows.

```bash
xan tail data.csv           # Default: 10 rows
xan tail -n 50 data.csv     # Last 50 rows
```

### slice

Extract a range of rows by index.

```bash
xan slice --start 10 --end 20 data.csv
xan slice -s 100 -e 200 data.csv
xan slice --len 50 data.csv  # First 50 rows
```

### top

Find the highest-ranking rows by column value.

```bash
xan top -s sales -n 10 data.csv     # Top 10 by sales
xan top --bottom -s price data.csv  # Bottom values
```

### sample

Random sampling of rows.

```bash
xan sample 100 data.csv          # Sample 100 rows
xan sample 0.1 data.csv          # Sample 10% of rows
xan sample --seed 42 100 data.csv  # Reproducible sampling
```

## Sort & Deduplicate

### sort

Arrange rows by one or more columns.

```bash
xan sort -s column data.csv
xan sort -s col1,col2 data.csv        # Multi-column sort
xan sort -s col1 -R data.csv          # Reverse order
xan sort -N -s numeric_col data.csv   # Numeric sort
```

### dedup

Remove duplicate rows.

```bash
xan dedup data.csv
xan dedup -s column data.csv  # Deduplicate by specific column
```

### shuffle

Randomize the order of rows.

```bash
xan shuffle data.csv
xan shuffle --seed 42 data.csv  # Reproducible shuffle
```

## Aggregate

### frequency (freq)

Generate frequency tables showing counts of unique values.

```bash
xan frequency -s category data.csv
xan freq -s col1,col2 data.csv  # Multi-column frequency
xan frequency --limit 10 -s column data.csv  # Top 10 values
```

### groupby

Perform group-based aggregation.

```bash
xan groupby category data.csv
xan groupby category --agg 'sum(sales) as total' data.csv
```

### stats

Compute descriptive statistics (count, mean, stddev, min, max, etc.).

```bash
xan stats data.csv              # Stats for all columns
xan stats -s column data.csv    # Stats for specific column
xan stats data.csv | xan transpose  # Transposed view
```

### agg

Custom aggregation expressions.

```bash
xan agg 'sum(sales) as total_sales' data.csv
xan agg 'mean(price), max(quantity)' data.csv
```

### bins

Distribute numeric values into bins.

```bash
xan bins -s age --bins 10 data.csv
xan bins -s income --bins 5 --min 0 --max 100000 data.csv
```

### window

Compute window functions like cumulative sums, rolling means, lag/lead.

```bash
xan window 'cumsum(sales) as running_total' data.csv
xan window 'lag(value, 1) as prev_value' data.csv
xan window 'rolling_mean(price, 7) as ma7' data.csv
```

## Combine Multiple Files

### cat

Concatenate CSV files by rows or columns.

```bash
xan cat rows file1.csv file2.csv file3.csv
xan cat cols file1.csv file2.csv  # Side-by-side concatenation
```

### join

Merge files on matching column values.

```bash
xan join key file1.csv key file2.csv
xan join --left key file1.csv key file2.csv  # Left join
xan join --outer key file1.csv key file2.csv  # Outer join
```

### fuzzy-join

Pattern-based joining with regular expressions.

```bash
xan fuzzy-join --pattern 'regex' col1 file1.csv col2 file2.csv
```

### merge

Combine pre-sorted similar files.

```bash
xan merge file1.csv file2.csv
```

## Column Operations

### select

Choose specific columns to keep.

```bash
xan select column1,column3 data.csv
xan select 'col1,col2 as renamed' data.csv  # With renaming
xan select '1-5,8' data.csv  # By index range
```

### drop

Remove specific columns.

```bash
xan drop column2,column4 data.csv
xan drop '3-5' data.csv  # Drop columns by index
```

### map

Create new columns using expressions.

```bash
xan map 'price * quantity as total' data.csv
xan map 'upper(name) as NAME' data.csv
xan map 'if(age > 18, "adult", "minor") as category' data.csv
```

### transform

Modify existing column values using expressions.

```bash
xan transform 'upper(name)' -c name data.csv
xan transform 'round(price, 2)' -c price data.csv
```

### enum

Add a sequential index column.

```bash
xan enum data.csv
xan enum --start 1 data.csv        # Start from 1
xan enum -c id data.csv            # Name the index column
```

### flatmap

Generate multiple rows from a single row using expressions.

```bash
xan flatmap 'split(tags, ",")' data.csv
```

### fill

Replace empty cells with a specified value.

```bash
xan fill 0 data.csv              # Fill with 0
xan fill -s column N/A data.csv  # Fill specific column
```

### blank

Remove duplicate consecutive values in a column.

```bash
xan blank -s column data.csv
```

## Format & Convert

### behead

Remove the header row.

```bash
xan behead data.csv
```

### rename

Change column names.

```bash
xan rename old_name new_name data.csv
xan rename 'col1 name1, col2 name2' data.csv  # Multiple renames
```

### input

Parse non-standard CSV formats.

```bash
xan input --delimiter ';' --quote '"' data.txt
```

### fixlengths

Standardize row lengths by padding or truncating.

```bash
xan fixlengths data.csv
xan fixlengths --length 10 data.csv
```

### fmt

Change field delimiters and formatting.

```bash
xan fmt -t '|' data.csv    # Output as pipe-separated
xan fmt -t '\t' data.csv   # Output as tab-separated
```

### explode

Split column values by a separator into multiple rows.

```bash
xan explode -s tags -c ',' data.csv
```

### implode

Collapse identical consecutive rows.

```bash
xan implode data.csv
```

### from

Convert various formats to CSV.

```bash
xan from json data.json
xan from excel data.xlsx
xan from ndjson data.ndjson
```

### to

Export CSV to other formats.

```bash
xan to json data.csv
xan to xlsx data.csv
xan to npy data.csv      # NumPy format
xan to parquet data.csv
```

### scrape

Extract HTML tables into CSV.

```bash
xan scrape --select 'table.data' page.html
```

### reverse

Flip the order of rows.

```bash
xan reverse data.csv
```

### transpose (t)

Swap rows and columns.

```bash
xan transpose data.csv
xan t data.csv  # Short alias
```

### pivot

Restructure data from long to wide format.

```bash
xan pivot --index id --columns category --values value data.csv
```

### unpivot

Convert from wide to long format.

```bash
xan unpivot data.csv
xan unpivot --keep id --columns 'col1,col2' data.csv
```

## File Splitting

### split

Divide a CSV file into chunks.

```bash
xan split -n 1000 data.csv           # 1000 rows per file
xan split -c 5 data.csv              # Split into 5 files
xan split --outdir ./chunks data.csv
```

### partition

Separate rows into different files by column value.

```bash
xan partition -s category data.csv
xan partition --outdir ./parts -s type data.csv
```

## Parallelization

### parallel (p)

Map-reduce style distributed processing.

```bash
xan parallel -t 4 data.csv  # Use 4 threads
xan p data.csv  # Short alias
```

## Generate

### range

Create CSV from numeric ranges.

```bash
xan range 1 100              # Numbers 1 to 100
xan range --step 5 0 100     # 0, 5, 10, ..., 100
xan range --column value 1 10
```

## Text Analysis

### tokenize

Break text into tokens.

```bash
xan tokenize -s text data.csv
xan tokenize --ngrams 2 -s content data.csv
```

### vocab

Build a token vocabulary with frequencies.

```bash
xan vocab -s text data.csv
```

### cluster

Find near-duplicate rows using similarity measures.

```bash
xan cluster -s text --threshold 0.8 data.csv
```

## Matrix & Network

### matrix

Convert CSV to matrix format.

```bash
xan matrix data.csv
```

### network

Convert CSV to network format (edge list).

```bash
xan network --source src --target dst data.csv
```

## Debugging

### eval

Test and evaluate single expressions.

```bash
xan eval '2 + 2'
xan eval 'upper("hello")'
xan eval 'if(10 > 5, "yes", "no")'
```

## Global Options

These options work with most commands:

- `-d, --delimiter <char>`: Field delimiter (default: auto-detect)
- `-n, --no-headers`: Input has no header row
- `-o, --output <file>`: Write output to file
- `--color <when>`: Color output (auto|always|never)
- `-h, --help`: Show help for command
- `--version`: Show version information

## Environment Variables

- `NO_COLOR`: Disable colored output
- `CLICOLOR`: Enable colored output (0/1)
- `CLICOLOR_FORCE`: Force colored output

## File Format Support

Xan automatically detects these formats:

- `.csv` - Comma-separated values
- `.tsv`, `.tab` - Tab-separated values
- `.psv` - Pipe-separated values
- `.ssv` - Semicolon-separated values
- `.scsv` - Semicolon-separated values
- `.vcf` - Variant Call Format (bioinformatics)
- `.gtf` - Gene Transfer Format (bioinformatics)
- `.sam` - Sequence Alignment Map (bioinformatics)
- `.bed` - Browser Extensible Data (bioinformatics)
- `.cdx` - Web archival format

## Compression Support

Xan transparently handles:

- `.gz` - Gzip compression
- `.zst` - Zstandard compression
- `.gzi` - Gzip index for efficient seeking
