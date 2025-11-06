# Stata Quick Reference

Common Stata commands and syntax patterns for development and testing.

## Data Management

### Loading and Saving Data

```stata
* Load Stata dataset
use "filename.dta", clear

* Save dataset
save "filename.dta", replace

* Import delimited file
import delimited "filename.csv", clear

* Export to CSV
export delimited using "filename.csv", replace
```

### Viewing Data

```stata
* Browse data in viewer
browse

* List first/last observations
list in 1/10
list in -10/L

* Describe dataset structure
describe
codebook varname

* Summary statistics
summarize
summarize varname, detail
```

## Variable Operations

### Creating Variables

```stata
* Generate new variable
generate newvar = expression

* Replace values
replace varname = newvalue if condition

* Rename variable
rename oldname newname

* Drop variables
drop varname1 varname2
```

### Variable Labels

```stata
* Label variable
label variable varname "Variable description"

* Define value labels
label define labelname 1 "Yes" 0 "No"
label values varname labelname

* View labels
label list
label list labelname
```

## Data Cleaning

### Missing Values

```stata
* Check missing values
misstable summarize
misstable patterns

* Recode missing
replace varname = . if varname == 99

* Count non-missing
count if !missing(varname)
```

### Duplicates

```stata
* Check for duplicates
duplicates report id
duplicates list id
duplicates tag id, gen(dup)

* Drop duplicates
duplicates drop id, force
```

### String Operations

```stata
* Convert to lowercase/uppercase
replace strvar = lower(strvar)
replace strvar = upper(strvar)

* Trim whitespace
replace strvar = strtrim(strvar)

* String to numeric
destring strvar, replace
generate numvar = real(strvar)

* Numeric to string
tostring numvar, replace
generate strvar = string(numvar)
```

## Conditional Logic

### If Conditions

```stata
* Simple if
generate flag = 1 if age > 18

* If-else with cond()
generate category = cond(age < 18, "minor", "adult")

* Multiple conditions
generate group = 1 if age < 18
replace group = 2 if age >= 18 & age < 65
replace group = 3 if age >= 65 & !missing(age)
```

### Logical Operators

```stata
* AND: &
if age > 18 & age < 65

* OR: |
if age < 18 | age > 65

* NOT: !
if !missing(age)

* Equal: ==
if status == "complete"

* Not equal: !=
if status != "complete"
```

## Loops and Macros

### Local Macros

```stata
* Define local macro
local varlist age income education

* Use local macro
summarize `varlist'

* Loop over local
foreach var of local varlist {
    summarize `var'
}
```

### Foreach Loops

```stata
* Loop over variables
foreach var of varlist age income education {
    summarize `var', detail
}

* Loop over values
foreach val in 1 2 3 {
    count if category == `val'
}

* Loop over variable list
foreach var in age income {
    replace `var' = 0 if missing(`var')
}
```

### Forvalues Loops

```stata
* Numeric loop
forvalues i = 1/10 {
    display "Iteration `i'"
}

* With step
forvalues i = 0(5)100 {
    count if age >= `i' & age < `i' + 5
}
```

## Data Manipulation

### Sorting

```stata
* Sort ascending
sort varname

* Sort descending
gsort -varname

* Sort by multiple variables
sort id date
```

### By Processing

```stata
* By group operations
bysort id: generate count = _N
bysort id (date): generate first = (_n == 1)
bysort id: egen mean_val = mean(value)
```

### Egen Functions

```stata
* Mean
egen mean_var = mean(varname)
bysort group: egen group_mean = mean(varname)

* Total
egen total = total(varname)

* Row operations
egen rowmean = rowmean(var1 var2 var3)
egen rowmax = rowmax(var1 var2 var3)
egen rowmin = rowmin(var1 var2 var3)

* Count non-missing
egen nonmiss = count(varname)
```

## Analysis

### Summary Statistics

```stata
* Basic summary
summarize
tabstat varname, statistics(mean sd min max)

* By group
bysort group: summarize varname
tabstat varname, by(group) statistics(mean sd)
```

### Tabulations

```stata
* One-way frequency
tabulate varname

* Two-way cross-tab
tabulate var1 var2

* With percentages
tabulate var1 var2, row col
```

### Regression

```stata
* Linear regression
regress y x1 x2 x3

* With robust standard errors
regress y x1 x2, robust

* Store results
estimates store model1

* Display stored results
estimates replay model1
```

## Special Variables

```stata
* _N: Total number of observations
display _N

* _n: Current observation number
generate obs_num = _n

* _merge: Merge indicator (after merge)
keep if _merge == 3
```

## Error Handling

```stata
* Capture errors
capture drop varname

* Assert conditions
assert age >= 0
assert !missing(id)

* Quietly suppress output
quietly summarize

* Noisily restore output
noisily display "Message"
```

## Working with Dates

```stata
* Convert string to date
generate date = date(datestring, "YMD")
format date %td

* Extract date components
generate year = year(date)
generate month = month(date)
generate day = day(date)

* Date arithmetic
generate days_diff = date2 - date1
```

## Matrix and Return Values

```stata
* Access r() results
summarize varname
return list
display r(mean)
display r(sd)

* Access e() results
regress y x
ereturn list
display e(N)
matrix b = e(b)
```

## Best Practices

1. **Always use `clear all` at the start** of scripts
2. **Comment extensively** with `*` or `//`
3. **Use meaningful variable names** that are descriptive
4. **Label all variables and values** for documentation
5. **Check for missing values** before analysis
6. **Use `assert` statements** to validate assumptions
7. **Save intermediate files** with descriptive names
8. **Use version control** (`version 18`) for reproducibility
9. **Avoid hard-coded paths** when possible
10. **Test code incrementally** rather than all at once
