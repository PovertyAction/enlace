* ==============================================================================
* Project: [Project Name]
* Purpose: [Brief description of what this script does]
* Author:  [Your Name]
* Date:    [YYYY-MM-DD]
* ==============================================================================

* ------------------------------------------------------------------------------
* Setup
* ------------------------------------------------------------------------------

* Clear environment
clear all
set more off
version 18  // Specify Stata version for reproducibility

* Set working directory
* cd "C:/path/to/working/directory"

* Define paths (using macros for flexibility)
local datadir   "data"
local rawdir    "`datadir'/raw"
local cleandir  "`datadir'/clean"
local outputdir "output"

* Create directories if they don't exist
* mkdir "`cleandir'", public
* mkdir "`outputdir'", public

* ------------------------------------------------------------------------------
* Section 1: Load Data
* ------------------------------------------------------------------------------

* Load dataset
use "`rawdir'/dataset.dta", clear

* Quick check of data structure
describe
summarize

* Display first few observations
list in 1/5

* ------------------------------------------------------------------------------
* Section 2: Data Cleaning
* ------------------------------------------------------------------------------

* Check for duplicates on ID variable
duplicates report id
assert r(unique_value) == r(N)  // Assert no duplicates

* Check for missing values
misstable summarize
* Note: Document any expected missing values

* Check ID variable
* Ensure ID is unique and non-missing
assert !missing(id)
isid id, sort

* ------------------------------------------------------------------------------
* Section 3: Variable Creation and Transformation
* ------------------------------------------------------------------------------

* Create new variables
* Example: Age groups
generate age_group = .
replace age_group = 1 if age < 18
replace age_group = 2 if age >= 18 & age < 65
replace age_group = 3 if age >= 65 & !missing(age)

* Label variables
label variable age_group "Age category"

* Define and apply value labels
label define age_group_lbl 1 "Under 18" 2 "18-64" 3 "65+"
label values age_group age_group_lbl

* Validate new variables
tab age_group, missing
assert !missing(age_group) if !missing(age)

* ------------------------------------------------------------------------------
* Section 4: Data Quality Checks
* ------------------------------------------------------------------------------

* Check logical consistency
* Example: Ensure response is consistent with eligibility
assert response == 1 if eligible == 1
* Note: Add specific validation checks for your data

* Check value ranges
* Example: Age should be between 0 and 120
assert age >= 0 & age <= 120 if !missing(age)

* Check skip patterns
* Example: If answered "No" to question 1, question 2 should be missing
assert missing(q2) if q1 == 0

* Flag potential issues for review
generate flag_review = 0
replace flag_review = 1 if [condition indicating potential issue]

* List flagged observations
list id flag_review [relevant_vars] if flag_review == 1

* ------------------------------------------------------------------------------
* Section 5: Variable Recoding
* ------------------------------------------------------------------------------

* Recode variables as needed
* Example: Binary yes/no
recode response (1 2 = 1 "Yes") (0 = 0 "No") (else = .), gen(response_binary)

* String cleaning (if applicable)
* Example: Trim whitespace and convert to lowercase
replace string_var = lower(strtrim(string_var))

* ------------------------------------------------------------------------------
* Section 6: Analysis
* ------------------------------------------------------------------------------

* Descriptive statistics
summarize [variables], detail

* Frequency tables
tabulate var1
tabulate var1 var2, row col

* By-group analysis
bysort group: summarize outcome_var
tabstat outcome_var, by(group) statistics(mean sd min max)

* Store results for later use
* Example: Store mean for each group
bysort group: egen group_mean = mean(outcome_var)

* ------------------------------------------------------------------------------
* Section 7: Save Output
* ------------------------------------------------------------------------------

* Save cleaned dataset
save "`cleandir'/dataset_clean.dta", replace

* Export to other formats (if needed)
* export delimited using "`outputdir'/dataset_clean.csv", replace

* Export summary statistics or tables
* Example: Export descriptive table
* tabout var1 var2 using "`outputdir'/crosstab.xls", replace

* Log key results
display "Data cleaning complete"
display "Total observations: " _N
display "Flagged for review: " sum(flag_review)

* ------------------------------------------------------------------------------
* End of Do-File
* ------------------------------------------------------------------------------

* Note: Always review output for any unexpected results or warnings
* Next steps: [Document what should be done after running this script]
