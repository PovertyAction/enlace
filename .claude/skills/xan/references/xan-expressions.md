# Xan Expression Language Reference (Moonblade)

Comprehensive guide to xan's built-in expression language for CSV data transformation and analysis.

## Overview

Moonblade is a dynamically typed expression language designed specifically for CSV processing. It provides Python/JavaScript-like syntax optimized for speed and memory efficiency when working with tabular data.

### Key Features

- **High Performance**: Faster than Python, Lua, or JavaScript for CSV operations
- **Constant Folding**: Static expressions evaluated once during parsing, not per row
- **Type-Aware**: Designed around CSV's string-based nature with explicit numeric conversions
- **Pipeline Support**: Chain operations using `|` operator
- **Higher-Order Functions**: Support for anonymous functions and functional programming

## Data Types and Literals

### Basic Types

```python
# Integers (underscores allowed for readability)
1, 42, 10_000, -5

# Floats
0.5, 3.14, -2.7

# Booleans
true, false

# Null
null
```

### Strings

```python
# Multiple quote styles
"double quotes"
'single quotes'
`backticks`

# Escape sequences
"line\nbreak"
"tab\there"
"backslash\\"
"quote\""

# Binary strings
b"binary data"
```

### Regular Expressions

```python
# Basic regex
/pattern/

# Case-insensitive flag
/pattern/i

# Example usage
match(text, /\d{3}-\d{4}/)
```

### Collections

```python
# Lists
[1, 2, 3]
["apple", "banana", "cherry"]
[true, 42, "mixed"]

# Maps (objects/dictionaries)
{"name": "Alice", "age": 30}
{key: value, another: 123}  # Shorthand syntax
```

## Column References

### Simple Column Names

For alphanumeric column names, use them directly:

```python
# Direct reference
price * quantity
tweet_count / retweet_count
```

### Complex Column Names

Use `col()` function for names with spaces or special characters:

```python
# By name
col("Name of Movie")
col("Price ($)")

# By index (0-based)
col(0)      # First column
col(2)      # Third column
col(-1)     # Last column

# Handle duplicate column names
col("text", 0)  # First occurrence
col("text", 1)  # Second occurrence
```

### Safe Column Access

Use `?` operator for columns that may not exist:

```python
# Returns first found column or null
text? || content? || body?

# Check if column exists
name? != null
```

## Operators

### Unary Operators

```python
-count          # Negation
!has_value      # Logical NOT
```

### Arithmetic Operators

```python
a + b           # Addition
a - b           # Subtraction
a * b           # Multiplication
a / b           # Division
a % b           # Modulo
a // b          # Integer division
a ** b          # Exponentiation
```

### Comparison Operators (Numeric)

```python
age == 25       # Equal
age != 25       # Not equal
age < 18        # Less than
age <= 18       # Less than or equal
age > 65        # Greater than
age >= 65       # Greater than or equal
```

### String Comparison Operators

```python
name eq "Alice"     # String equality
name ne "Bob"       # String not equal
name lt "M"         # Lexicographic less than
name le "M"         # Lexicographic less than or equal
name gt "M"         # Lexicographic greater than
name ge "M"         # Lexicographic greater than or equal
```

### String Operators

```python
"Hello" ++ " " ++ "World"    # Concatenation
"apple" in "pineapple"       # Contains check
```

### Logical Operators

```python
age > 18 && status eq "active"     # AND
age < 18 || age > 65               # OR
!(age > 65)                         # NOT
```

### Pipeline Operator

```python
# Pass left result to _ identifier on right
price | _ * 1.1           # Add 10% to price
text | trim(_) | upper(_) # Chain transformations
```

## Indexing and Slicing

### List Indexing

```python
# Zero-based indexing
list[0]         # First element
list[1]         # Second element
list[-1]        # Last element
list[-2]        # Second to last
```

### Slicing

```python
list[1:4]       # Elements 1, 2, 3 (exclusive end)
list[:4]        # First 4 elements
list[1:]        # All except first
list[:]         # Copy entire list
```

### Map Access

```python
# Bracket notation
map["name"]
map["nested"]["key"]

# Dot notation
map.name
map.nested.key
```

## Function Calls

### Standard Syntax

```python
# Basic function call
trim(name)
upper(text)

# Multiple arguments
concat(first_name, " ", last_name)

# Nested calls
trim(upper(name))
```

### Method Notation

```python
# Method style (equivalent to function style)
name.trim()              # Same as trim(name)
text.upper()             # Same as upper(text)
name.split(" ")          # Same as split(name, " ")
```

### Named Arguments

```python
# Specify arguments by name
read(path, encoding="utf8")
replace(text, pattern="old", replacement="new")
```

### Higher-Order Functions

```python
# Anonymous functions with =>
map(numbers, x => x * 2)
filter(users, user => user.age > 18)
map(items, item => item.price * item.quantity)

# Multiple parameters
reduce(list, (acc, x) => acc + x, 0)
```

## Control Flow

### Conditional Expressions

```python
# if-then-else
if(age >= 18, "adult", "minor")

# unless (inverse if)
unless(empty, value, "default")

# try (error handling)
try(parse_int(value), 0)  # Returns 0 if parse fails
```

### Short-Circuit Evaluation

```python
# OR returns first truthy value
name || "Unknown"
col1? || col2? || "default"

# AND returns last value if all truthy
has_value && process(value)
```

## Named Expressions

Used in commands like `xan map`, `xan agg`:

```python
# Simple expressions (comma-separated)
sum(sales), mean(price), count()

# With aliases
sum(sales) as total_sales
mean(price) as avg_price

# Destructuring assignments
split(full_name, " ") as (first_name, last_name)
```

## Built-in Functions

### String Functions

```python
# Case conversion
upper(text)                    # "HELLO"
lower(text)                    # "hello"

# Trimming
trim(text)                     # Remove whitespace
trim_start(text)               # Remove leading whitespace
trim_end(text)                 # Remove trailing whitespace

# Splitting and joining
split(text, delimiter)         # Split into list
join(list, separator)          # Join list into string

# Pattern matching
match(text, /pattern/)         # Check if pattern matches
replace(text, pattern, repl)   # Replace matches
count(text, pattern)           # Count occurrences

# Checking
startswith(text, prefix)       # Check prefix
endswith(text, suffix)         # Check suffix
contains(text, substring)      # Check if contains

# Formatting
fmt(template, ...args)         # Format string
concat(str1, str2, ...)        # Concatenate strings

# Other operations
len(text)                      # String length
substr(text, start, length)    # Substring
```

### Numeric Functions

```python
# Basic math
abs(number)                    # Absolute value
round(number, decimals)        # Round to decimals
floor(number)                  # Round down
ceil(number)                   # Round up
sqrt(number)                   # Square root
pow(base, exponent)            # Exponentiation

# Parsing
parse_int(string)              # Parse integer
parse_float(string)            # Parse float
number(string)                 # Parse number (int or float)

# Checking
is_number(value)               # Check if numeric
is_int(value)                  # Check if integer
is_finite(value)               # Check if finite
```

### List Functions

```python
# Transformations
map(list, fn)                  # Apply function to each element
filter(list, fn)               # Keep elements matching predicate
find(list, fn)                 # Find first matching element

# Aggregations
sum(list)                      # Sum all elements
mean(list)                     # Average
min(list)                      # Minimum value
max(list)                      # Maximum value
len(list)                      # Number of elements

# Checks
all(list, fn)                  # True if all match
any(list, fn)                  # True if any match
contains(list, value)          # Check membership

# Other operations
join(list, separator)          # Join into string
sort(list)                     # Sort ascending
reverse(list)                  # Reverse order
unique(list)                   # Remove duplicates
```

### Date and Time Functions

```python
# Parsing
datetime(string, format?)      # Parse datetime
timestamp(datetime)            # Convert to Unix timestamp

# Formatting
strftime(datetime, format)     # Format datetime
date(datetime)                 # Extract date part
time(datetime)                 # Extract time part

# Components
year(datetime)                 # Extract year
month(datetime)                # Extract month
day(datetime)                  # Extract day
hour(datetime)                 # Extract hour
minute(datetime)               # Extract minute
second(datetime)               # Extract second
weekday(datetime)              # Day of week (0-6)

# Arithmetic
add_days(datetime, n)          # Add n days
add_months(datetime, n)        # Add n months
add_years(datetime, n)         # Add n years

# Timezone
to_timezone(datetime, tz)      # Convert timezone
```

### Type Functions

```python
# Type checking
is_null(value)                 # Check if null
is_string(value)               # Check if string
is_number(value)               # Check if number
is_bool(value)                 # Check if boolean
is_list(value)                 # Check if list
is_map(value)                  # Check if map

# Type conversion
string(value)                  # Convert to string
number(value)                  # Convert to number
bool(value)                    # Convert to boolean
```

### Path and File I/O Functions

```python
# Reading
read(path, encoding?)          # Read file contents
parse_json(string)             # Parse JSON string

# Writing
write(path, content)           # Write to file

# Path operations
pathjoin(parts...)             # Join path components
pathext(path)                  # Get file extension
pathstem(path)                 # Get filename without extension
pathparent(path)               # Get parent directory

# File info
filesize(path)                 # Get file size
exists(path)                   # Check if file exists

# Operations
copy(source, dest)             # Copy file
move(source, dest)             # Move file
```

### Utility Functions

```python
# Hashing
md5(value)                     # MD5 hash
sha1(value)                    # SHA1 hash
sha256(value)                  # SHA256 hash

# Random
random()                       # Random float [0, 1)
randint(min, max)              # Random integer
uuid()                         # Generate UUID

# Execution
cmd(command, args...)          # Execute command
shell(command)                 # Execute shell command

# JSON
parse_json(string)             # Parse JSON
to_json(value)                 # Convert to JSON

# Encoding
urlencode(string)              # URL encode
urldecode(string)              # URL decode
base64_encode(string)          # Base64 encode
base64_decode(string)          # Base64 decode
```

## Aggregation Functions

Used in `xan agg`, `xan groupby`, `xan stats`:

### Statistical Aggregations

```python
# Basic statistics
count()                        # Count rows
count(expr)                    # Count non-empty values
sum(expr)                      # Sum values
mean(expr) or avg(expr)        # Average
median(expr)                   # Median value
median_low(expr)               # Lower median
median_high(expr)              # Upper median
mode(expr)                     # Most frequent value

# Extremes
min(expr)                      # Minimum value
max(expr)                      # Maximum value
argmin(expr)                   # Index of minimum
argmax(expr)                   # Index of maximum

# Spread
stddev(expr)                   # Standard deviation (population)
stddev_sample(expr)            # Standard deviation (sample)
var(expr)                      # Variance (population)
var_sample(expr)               # Variance (sample)
rms(expr)                      # Root mean square

# Quantiles
q1(expr)                       # First quartile (25%)
q3(expr)                       # Third quartile (75%)
quantile(expr, q)              # Specific quantile
approx_quantile(expr, q)       # Approximate quantile
```

### Cardinality Functions

```python
cardinality(expr)              # Count distinct values
approx_cardinality(expr)       # Approximate distinct count (HyperLogLog)
```

### Correlation Functions

```python
correlation(expr1, expr2)      # Correlation coefficient
covariance(expr1, expr2)       # Covariance (population)
covariance_sample(expr1, expr2) # Covariance (sample)
```

### Boolean Aggregations

```python
all(expr)                      # True if all values truthy
any(expr)                      # True if any value truthy
percentage(expr, decimals?)    # Percent of truthy values
ratio(expr, decimals?)         # Ratio of truthy values
```

### Ranking Functions

```python
top(k, expr, sep?)             # Top k values
argtop(k, expr, expr?, sep?)   # Indices of top k values
most_common(k, expr, sep?)     # Most frequent k values
most_common_counts(k, expr, sep?) # Counts of most frequent k values
```

### Temporal Aggregations

```python
earliest(expr)                 # Earliest datetime
latest(expr)                   # Latest datetime
count_seconds(expr)            # Time span in seconds
count_hours(expr)              # Time span in hours
count_days(expr)               # Time span in days
count_years(expr)              # Time span in years
```

### Collection Aggregations

```python
first(expr)                    # First non-empty value
last(expr)                     # Last non-empty value
lex_first(expr)                # Lexicographically first
lex_last(expr)                 # Lexicographically last
distinct_values(expr, sep?)    # Unique values (sorted)
values(expr, sep?)             # All values concatenated
```

### Type Reporting

```python
type(expr)                     # Predominant type
types(expr)                    # All observed types
```

## Window Functions

Used in `xan window`:

```python
# Cumulative aggregations
cumsum(expr)                   # Running total
cumcount()                     # Running count
cummin(expr)                   # Running minimum
cummax(expr)                   # Running maximum

# Moving windows
rolling_sum(expr, n)           # Sum of last n values
rolling_mean(expr, n)          # Mean of last n values
rolling_min(expr, n)           # Min of last n values
rolling_max(expr, n)           # Max of last n values

# Row shifting
lag(expr, n)                   # Value from n rows before
lead(expr, n)                  # Value from n rows after

# Ranking
row_number()                   # Sequential row number
rank()                         # Rank with gaps
dense_rank()                   # Rank without gaps
```

## Common Patterns and Examples

### Data Validation

```python
# Check for missing values
if(col("value")? != null, col("value"), "N/A")

# Validate numeric ranges
if(age >= 0 && age <= 120, age, null)

# Check string patterns
if(match(email, /^[\w.]+@[\w.]+$/), email, "invalid")
```

### String Manipulation

```python
# Normalize names
trim(upper(name))

# Extract parts
split(full_name, " ") as (first, last)

# Build descriptions
concat(product, " (", category, ")")

# Clean whitespace
replace(text, /\s+/, " ")
```

### Numeric Calculations

```python
# Percentage calculation
round(value / total * 100, 2)

# Currency formatting
concat("$", round(price, 2))

# Conditional math
if(quantity > 0, total / quantity, 0)
```

### Date Processing

```python
# Age calculation
year(today()) - year(birthdate)

# Format for display
strftime(datetime, "%Y-%m-%d")

# Business logic
if(weekday(date) >= 5, "weekend", "weekday")
```

### List Processing

```python
# Average of values
mean(map(split(values, ","), x => number(x)))

# Filter and count
len(filter(split(tags, ","), tag => tag eq "important"))

# Transform and join
join(map(split(text, " "), word => upper(word)), " ")
```

### Null Handling

```python
# Provide defaults
value? || 0
name? || "Unknown"

# Safe chaining
col("data")?.value? || "missing"

# Conditional processing
if(col("value")? != null, process(col("value")), null)
```

## Comments and Formatting

```python
# Single-line comments
price * 1.1  # Add 10% markup

# Multi-line expressions (newlines ignored in expressions)
if(
  age >= 18 && status eq "active",
  "eligible",
  "not eligible"
)

# Complex calculations
sum(price * quantity) +
  tax_amount -
  discount
```

## Best Practices

### 1. Type Awareness

```python
# Good: Use string operators for strings
name eq "Alice"

# Bad: Using numeric equality on strings
name == "Alice"  # May not work as expected

# Good: Parse numbers explicitly
number(age) > 18

# Good: Provide defaults for parsing
number(value) || 0
```

### 2. Performance Optimization

```python
# Good: Use constant folding
if(1 + 1 == 2, value, 0)  # Condition evaluated once

# Good: Avoid repeated computation
let total = price * quantity; total * 1.1

# Good: Use appropriate aggregations
cardinality(id)  # Better than len(unique(id))
```

### 3. Safe Column Access

```python
# Good: Handle missing columns
col("optional")? || "default"

# Good: Check before use
if(col("data")? != null, process(col("data")), null)

# Good: Use index for position-based access
col(0)  # First column regardless of name
```

### 4. Testing Expressions

Use `xan eval` to test expressions before using them:

```bash
xan eval '2 + 2'
xan eval 'upper("hello")'
xan eval 'if(10 > 5, "yes", "no")'
```

### 5. Complex Transformations

```python
# Break into steps with intermediate columns
xan map 'split(full_name, " ") as (first, last)' data.csv |
xan map 'upper(first) as first_upper' |
xan select first_upper,last
```

## Error Handling

Most functions ignore empty/null values by default:

```python
# These skip empty values
mean(value)      # Ignores empty cells
sum(amount)      # Skips nulls

# Force inclusion with defaults
mean(number(value) || 0)  # Treats empty as 0

# Use try for error-prone operations
try(number(text), 0)      # Returns 0 on parse error
try(col("maybe"), "N/A")  # Returns "N/A" if column missing
```

## Command Integration

### With `xan map`

Create or transform columns:

```bash
xan map 'price * quantity as total' data.csv
xan map 'upper(name), lower(category)' data.csv
```

### With `xan filter`

Keep rows matching conditions:

```bash
xan filter 'age > 18' data.csv
xan filter 'status eq "active" && score >= 80' data.csv
```

### With `xan agg`

Compute aggregations:

```bash
xan agg 'sum(sales) as total, mean(price) as avg_price' data.csv
```

### With `xan groupby`

Group and aggregate:

```bash
xan groupby category data.csv
xan groupby category --agg 'sum(sales), count()' data.csv
```

### With `xan window`

Compute window functions:

```bash
xan window 'cumsum(amount) as running_total' data.csv
xan window 'lag(value, 1) as previous' data.csv
```

## Additional Resources

- Run `xan help cheatsheet` for quick reference
- Run `xan help functions` for complete function list
- Run `xan help aggs` for aggregation functions
- Use `xan eval '<expression>'` to test expressions
- GitHub: <https://github.com/medialab/xan>
