#!/usr/bin/env python3
"""Generate a new Stata .do file with IPA conventions and standard headers.

Usage:
    python create_do_template.py output.do --project "My Project" --purpose "Data cleaning"
"""

import argparse
from datetime import datetime
from pathlib import Path

DO_FILE_TEMPLATE = """* ==============================================================================
* Project: {project}
* Purpose: {purpose}
* Author:  {author}
* Date:    {date}
* ==============================================================================

* Set up environment
clear all
set more off
version {stata_version}

* Set working directory
cd "{working_dir}"

* ==============================================================================
* Section 1: Load Data
* ==============================================================================

* Load dataset
use "{dataset}", clear

* Quick check of data
describe
summarize

* ==============================================================================
* Section 2: Data Cleaning
* ==============================================================================

* Check for duplicates
duplicates report {id_var}

* Check for missing values
misstable summarize

* ==============================================================================
* Section 3: Variable Creation
* ==============================================================================

* Create new variables here

* ==============================================================================
* Section 4: Data Analysis
* ==============================================================================

* Analysis code here

* ==============================================================================
* Section 5: Save Output
* ==============================================================================

* Save cleaned dataset
save "{output_dataset}", replace

* Export results
* export delimited using "{output_csv}", replace

* ==============================================================================
* End of do-file
* ==============================================================================
"""


def create_do_file(
    output_path: str,
    project: str = "Project Name",
    purpose: str = "Purpose of this script",
    author: str = "Your Name",
    stata_version: str = "18",
    working_dir: str = ".",
    dataset: str = "data.dta",
    output_dataset: str = "data_cleaned.dta",
    output_csv: str = "results.csv",
    id_var: str = "id",
):
    """Create a .do file from template with specified parameters."""
    output = Path(output_path)

    # Check if file already exists
    if output.exists():
        print(f"Warning: File already exists: {output_path}")
        response = input("Overwrite? (y/n): ").lower()
        if response != "y":
            print("Aborted.")
            return False

    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Fill in template
    content = DO_FILE_TEMPLATE.format(
        project=project,
        purpose=purpose,
        author=author,
        date=current_date,
        stata_version=stata_version,
        working_dir=working_dir,
        dataset=dataset,
        output_dataset=output_dataset,
        output_csv=output_csv,
        id_var=id_var,
    )

    # Write file
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"✓ Created .do file: {output_path}")
        return True
    except Exception as e:
        print(f"Error creating .do file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Stata .do file from IPA template"
    )

    parser.add_argument("output", help="Output path for .do file")
    parser.add_argument("--project", default="Project Name", help="Project name")
    parser.add_argument(
        "--purpose", default="Purpose of this script", help="Purpose of the script"
    )
    parser.add_argument("--author", default="Your Name", help="Author name")
    parser.add_argument(
        "--stata-version", default="18", help="Stata version (default: 18)"
    )
    parser.add_argument("--working-dir", default=".", help="Working directory path")
    parser.add_argument("--dataset", default="data.dta", help="Input dataset filename")
    parser.add_argument(
        "--output-dataset", default="data_cleaned.dta", help="Output dataset filename"
    )
    parser.add_argument(
        "--output-csv", default="results.csv", help="Output CSV filename"
    )
    parser.add_argument("--id-var", default="id", help="ID variable name")

    args = parser.parse_args()

    success = create_do_file(
        output_path=args.output,
        project=args.project,
        purpose=args.purpose,
        author=args.author,
        stata_version=args.stata_version,
        working_dir=args.working_dir,
        dataset=args.dataset,
        output_dataset=args.output_dataset,
        output_csv=args.output_csv,
        id_var=args.id_var,
    )

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
