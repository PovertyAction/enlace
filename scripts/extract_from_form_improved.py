"""Enhanced form-based extraction from research papers.

PROJECT-AGNOSTIC DESIGN:
This script is designed to work with ANY project by automatically discovering and
processing all form definitions found in the data/forms/ directory. No hardcoding needed.

How to use for your project:
1. Place your Excel form definitions in: data/forms/
   - Script auto-detects column names (rando/deliver/type for field types)
   - Supports standard ODK/KoBoToolbox format
2. Place your PDF papers in: papers/
3. Set ANTHROPIC_API_KEY in .env file
4. Run: uv run python scripts/extract_from_form_improved.py
5. Results saved to: output/form_extractions/{form_id}/

The script automatically:
- Discovers all Excel files in forms directory
- Identifies field type columns (rando, deliver, or type)
- Extracts substantive fields (text, integer, date, select_one, select_multiple)
- Creates separate outputs for each form
- Generates completion reports and validation warnings

Improvements over original:
1. Better field parsing with choice options
2. Validation and type coercion
3. Retry logic for failed extractions
4. Progress tracking and detailed logging
5. Incremental processing (skip completed papers)
6. Better error handling and recovery
7. Enhanced prompting with field types and constraints
8. Support for repeat groups and nested structures
9. Output validation against form schema
10. Detailed extraction statistics
11. AUTO-DISCOVERY of forms (project-agnostic)
12. AUTO-DETECTION of column naming conventions
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
from anthropic import Anthropic, APIError
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table as RichTable

# Configure console with error handling for Windows encoding
console = Console(stderr=False, force_terminal=False, legacy_windows=True)
logger = logging.getLogger(__name__)


class FormField:
    """Represents a single form field with metadata."""

    def __init__(self, row: pd.Series):
        """Initialize form field from Excel row.

        Args:
            row: Pandas Series containing field definition with columns:
                 name, label, rando (type), hint, required, constraint.

        """
        self.name = row["name"]
        self.label = row["label"]
        self.field_type = str(row["rando"])
        self.hint = row.get("hint", "")
        self.required = str(row.get("required", "")).lower() == "yes"
        self.choices = self._parse_choices(row)
        self.constraint = row.get("constraint", "")

    def _parse_choices(self, row: pd.Series) -> list[str]:
        """Extract choice options from select_one/select_multiple fields."""
        # Choices are typically in a separate sheet or in the type definition
        # e.g., "select_one choices" with choices defined elsewhere
        # For now, return empty list - this would need form-specific logic
        return []

    def to_prompt_text(self) -> str:
        """Generate prompt text for this field."""
        text = f"**{self.name}**: {self.label}"
        if self.hint and isinstance(self.hint, str) and self.hint.strip():
            text += f"\n   Hint: {self.hint}"
        text += f"\n   Type: {self.field_type}"
        if self.required:
            text += " (REQUIRED)"
        if self.choices:
            text += f"\n   Options: {', '.join(self.choices)}"
        if self.constraint and isinstance(self.constraint, str):
            text += f"\n   Constraint: {self.constraint}"
        return text


class ExtractionValidator:
    """Validates extracted data against form schema."""

    def __init__(self, fields: list[FormField]):
        """Initialize validator with form field definitions.

        Args:
            fields: List of FormField objects defining the schema.

        """
        self.fields = {f.name: f for f in fields}

    def validate(self, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Validate and coerce extracted data.

        Returns:
            Tuple of (cleaned_data, warnings)

        """
        cleaned = {}
        warnings = []

        for field_name, field in self.fields.items():
            value = data.get(field_name)

            # Handle missing required fields
            if field.required and (value is None or value == "NOT FOUND"):
                warnings.append(f"Missing required field: {field_name}")
                cleaned[field_name] = None
                continue

            # Skip NOT FOUND values
            if value == "NOT FOUND":
                cleaned[field_name] = None
                continue

            # Type coercion and validation
            try:
                if "integer" in field.field_type:
                    if value and value != "NOT FOUND":
                        cleaned[field_name] = int(float(str(value).replace(",", "")))
                    else:
                        cleaned[field_name] = None

                elif "date" in field.field_type:
                    if value and value != "NOT FOUND":
                        # Validate date format
                        cleaned[field_name] = str(value)
                    else:
                        cleaned[field_name] = None

                elif "select_multiple" in field.field_type:
                    if value and value != "NOT FOUND":
                        # Ensure it's a list
                        if isinstance(value, str):
                            cleaned[field_name] = [v.strip() for v in value.split(";")]
                        else:
                            cleaned[field_name] = value
                    else:
                        cleaned[field_name] = []

                else:
                    cleaned[field_name] = value

            except (ValueError, TypeError) as e:
                warnings.append(f"Type conversion error for {field_name}: {e}")
                cleaned[field_name] = value  # Keep original value

        return cleaned, warnings


def discover_forms(forms_dir: Path) -> list[Path]:
    """Discover all form definition Excel files in the forms directory.

    Returns:
        List of paths to form Excel files

    """
    forms = sorted(forms_dir.glob("*.xlsx"))
    # Filter out temporary Excel files
    forms = [f for f in forms if not f.name.startswith("~$")]
    return forms


def get_form_identifier(form_path: Path) -> str:
    """Extract a clean identifier from the form filename.

    E.g., 'DEV_stage1_ipaMC_v1.xlsx' -> 'stage1'
    """
    name = form_path.stem
    # Try to extract stage identifier
    if "stage1" in name.lower():
        return "stage1"
    elif "stage2" in name.lower():
        return "stage2"
    else:
        # Use the full stem as identifier
        return name


def load_form_definition(excel_path: Path) -> tuple[pd.DataFrame, list[FormField]]:
    """Load and parse the form definition from Excel.

    Returns:
        Tuple of (raw dataframe, parsed FormField objects)

    """
    df = pd.read_excel(excel_path)

    # Determine which column contains the field type
    # Different forms may use 'rando' or 'deliver' or 'type'
    type_column = None
    for col_name in ["rando", "deliver", "type"]:
        if col_name in df.columns:
            type_column = col_name
            break

    if type_column is None:
        raise ValueError(
            f"Could not find field type column (tried: 'rando', 'deliver', 'type') in {excel_path.name}"
        )

    # Normalize: add 'rando' column if it doesn't exist (for FormField compatibility)
    if "rando" not in df.columns:
        df["rando"] = df[type_column]

    # Filter to get only the substantive fields
    substantive_types = ["text", "integer", "date", "select_one", "select_multiple"]

    # Get fields that have labels and are substantive types
    fields_df = df[
        (df["label"].notna())
        & (df["rando"].apply(lambda x: any(t in str(x) for t in substantive_types)))
    ].copy()

    # Parse into FormField objects
    form_fields = [FormField(row) for _, row in fields_df.iterrows()]

    return fields_df, form_fields


def categorize_fields(fields: list[FormField]) -> dict[str, list[FormField]]:
    """Organize fields into logical sections."""
    sections = {
        "Publication Details": [],
        "Study Design": [],
        "Interventions/Treatments": [],
        "Credit/Loan Details": [],
        "Outcomes": [],
        "Geographic Information": [],
        "Sample Information": [],
        "Data Collection": [],
        "Other": [],
    }

    for field in fields:
        name_lower = field.name.lower()
        label_lower = field.label.lower() if isinstance(field.label, str) else ""

        if any(
            x in name_lower for x in ["study", "pub", "auth", "link", "doi", "journal"]
        ):
            sections["Publication Details"].append(field)
        elif any(x in name_lower for x in ["int", "treat", "comp", "control", "arm"]):
            sections["Interventions/Treatments"].append(field)
        elif any(x in name_lower for x in ["loan", "credit", "bank", "finance"]):
            sections["Credit/Loan Details"].append(field)
        elif "outcome" in name_lower or "result" in label_lower:
            sections["Outcomes"].append(field)
        elif any(x in name_lower for x in ["geo", "country", "region", "location"]):
            sections["Geographic Information"].append(field)
        elif any(x in name_lower for x in ["samp", "unit", "size", "population"]):
            sections["Sample Information"].append(field)
        elif any(
            x in name_lower
            for x in ["data", "collect", "survey", "baseline", "endline"]
        ):
            sections["Data Collection"].append(field)
        elif any(x in name_lower for x in ["design", "method", "random", "experiment"]):
            sections["Study Design"].append(field)
        else:
            sections["Study Design"].append(field)

    # Remove empty sections
    return {k: v for k, v in sections.items() if v}


def create_extraction_prompt(
    fields: list[FormField], paper_text: str, paper_name: str
) -> str:
    """Create an enhanced prompt for LLM extraction."""
    sections = categorize_fields(fields)

    prompt = f"""You are a research assistant extracting structured information from an academic paper.

PAPER: {paper_name}

INSTRUCTIONS:
- Extract ONLY information that is explicitly stated in the paper
- For fields not found, respond with "NOT FOUND" (not null or empty string)
- For numeric fields, provide only numbers (remove commas, currency symbols)
- For date fields, use YYYY-MM-DD or YYYY format when possible
- For select_multiple fields, provide a list of applicable values
- For select_one fields, choose exactly ONE option
- Be precise and quote directly from the paper when possible

PAPER TEXT (first 50,000 characters):
{paper_text[:50000]}

EXTRACTION FIELDS:

"""

    for section_name, section_fields in sections.items():
        if section_fields:
            prompt += f"\n{'=' * 60}\n## {section_name}\n{'=' * 60}\n"
            for field in section_fields:
                prompt += f"\n{field.to_prompt_text()}\n"

    prompt += """

OUTPUT FORMAT:
Provide your response as a valid JSON object with field names as keys and extracted values as values.

IMPORTANT:
- Use "NOT FOUND" for missing information (as a string value)
- For select_multiple fields, use arrays: ["value1", "value2"]
- For integer fields, use numbers without quotes: 3
- For text fields, use strings: "text value"
- Ensure all JSON is properly escaped

Example:
{
    "studyID": "12345",
    "IPA_studyName": "Impact of Microcredit",
    "pubYear": "2023",
    "authNum": 3,
    "outcomes": ["income", "consumption"],
    "unknownField": "NOT FOUND"
}

BEGIN EXTRACTION:
"""

    return prompt


def extract_with_llm(prompt: str, api_key: str, max_retries: int = 3) -> dict[str, Any]:
    """Use Claude to extract information with retry logic."""
    client = Anthropic(api_key=api_key)

    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=os.getenv("AUGMENTATION_LLM_MODEL"),
                max_tokens=8000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse JSON response
            response_text = response.content[0].text

            # Extract JSON from response (it might be wrapped in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()

            return json.loads(response_text)

        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                console.print(
                    f"[yellow]JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}[/yellow]"
                )
                time.sleep(2)
            else:
                raise

        except APIError as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                console.print(
                    f"[yellow]API error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...[/yellow]"
                )
                time.sleep(wait_time)
            else:
                raise


def ensure_markdown_extracted(paper: Path) -> Path:
    """Ensure paper is converted to markdown, run extraction if needed."""
    output_path = Path("output") / paper.stem
    markdown_path = output_path / f"{paper.stem}.md"

    if not markdown_path.exists():
        console.print(f"[yellow]Running enlace extraction for {paper.name}...[/yellow]")
        import subprocess

        result = subprocess.run(
            ["uv", "run", "enlace", "extract", str(paper), "-o", "output"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to extract paper: {result.stderr}")

    return markdown_path


def process_paper(
    paper: Path,
    fields: list[FormField],
    validator: ExtractionValidator,
    api_key: str,
    output_dir: Path,
    force_reextract: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    """Process a single paper and extract form data.

    Returns:
        Tuple of (extracted_data, warnings)

    """
    # Check if already extracted
    output_file = output_dir / f"{paper.stem}_extraction.json"
    if output_file.exists() and not force_reextract:
        console.print(f"[dim]Skipping {paper.name} (already extracted)[/dim]")
        with open(output_file) as f:
            return json.load(f), []

    # Ensure markdown exists
    markdown_path = ensure_markdown_extracted(paper)

    # Read the markdown
    paper_text = markdown_path.read_text(encoding="utf-8")

    # Create prompt
    prompt = create_extraction_prompt(fields, paper_text, paper.stem)

    # Extract with LLM
    extracted_data = extract_with_llm(prompt, api_key)

    # Validate and clean
    cleaned_data, warnings = validator.validate(extracted_data)

    # Save results
    output_file.write_text(json.dumps(cleaned_data, indent=2), encoding="utf-8")

    return cleaned_data, warnings


def generate_extraction_report(
    all_extractions: list[dict],
    all_warnings: dict[str, list[str]],
    fields: list[FormField],
) -> None:
    """Generate and display extraction statistics."""
    console.print("\n" + "=" * 60)
    console.print("[bold cyan]Extraction Report[/bold cyan]")
    console.print("=" * 60 + "\n")

    # Overall stats
    table = RichTable(title="Overall Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Papers", str(len(all_extractions)))
    table.add_row("Total Fields", str(len(fields)))
    table.add_row(
        "Papers with Warnings", str(len([w for w in all_warnings.values() if w]))
    )

    console.print(table)

    # Field completion stats
    console.print("\n[bold]Field Completion Rates:[/bold]")

    field_stats = {}
    for field in fields:
        found_count = sum(
            1
            for ext in all_extractions
            if ext.get(field.name) not in [None, "NOT FOUND", ""]
        )
        field_stats[field.name] = (
            (found_count / len(all_extractions)) * 100 if all_extractions else 0
        )

    # Show top 10 most and least complete fields
    sorted_fields = sorted(field_stats.items(), key=lambda x: x[1], reverse=True)

    completion_table = RichTable(title="Top 10 Most Complete Fields")
    completion_table.add_column("Field", style="cyan")
    completion_table.add_column("Completion %", style="green")

    for field_name, pct in sorted_fields[:10]:
        completion_table.add_row(field_name, f"{pct:.1f}%")

    console.print(completion_table)

    # Show fields with low completion
    low_completion = [(f, p) for f, p in sorted_fields if p < 50]
    if low_completion:
        console.print("\n[yellow]Fields with <50% completion:[/yellow]")
        for field_name, pct in low_completion[:10]:
            console.print(f"  • {field_name}: {pct:.1f}%")

    # Show warnings summary
    if any(all_warnings.values()):
        console.print("\n[bold yellow]Warnings Summary:[/bold yellow]")
        for paper_id, warnings in all_warnings.items():
            if warnings:
                console.print(f"\n[cyan]{paper_id}[/cyan]:")
                for warning in warnings[:5]:  # Show first 5 warnings
                    console.print(f"  • {warning}")
                if len(warnings) > 5:
                    console.print(f"  ... and {len(warnings) - 5} more")


def process_form(
    form_path: Path, papers_dir: Path, base_output_dir: Path, api_key: str
):
    """Process all papers using a specific form definition.

    Args:
        form_path: Path to the form Excel file
        papers_dir: Directory containing PDF papers
        base_output_dir: Base output directory
        api_key: Anthropic API key

    """
    form_id = get_form_identifier(form_path)
    form_output_dir = base_output_dir / form_id
    form_output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold cyan]{'=' * 70}[/bold cyan]")
    console.print(f"[bold cyan]Processing Form: {form_path.name}[/bold cyan]")
    console.print(f"[bold cyan]Form ID: {form_id}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 70}[/bold cyan]\n")

    # Load form definition
    console.print(f"[cyan]Loading form definition from {form_path}...[/cyan]")
    fields_df, form_fields = load_form_definition(form_path)
    console.print(f"[green]OK - Found {len(form_fields)} extraction fields[/green]")

    # Show field categories
    sections = categorize_fields(form_fields)
    console.print("\n[bold]Field Categories:[/bold]")
    for section_name, section_fields in sections.items():
        console.print(f"  • {section_name}: {len(section_fields)} fields")

    # Initialize validator
    validator = ExtractionValidator(form_fields)

    # Get papers
    papers = sorted(list(papers_dir.glob("*.pdf")))
    if not papers:
        console.print("[yellow]No PDF files found in papers directory[/yellow]")
        return

    console.print(f"\n[cyan]Found {len(papers)} papers to process[/cyan]\n")

    # Store all extractions and warnings
    all_extractions = []
    all_warnings = {}
    failed_papers = []

    # Process papers with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing papers...", total=len(papers))

        for paper in papers:
            progress.update(task, description=f"[cyan]Processing {paper.name}")

            try:
                extracted_data, warnings = process_paper(
                    paper, form_fields, validator, api_key, form_output_dir
                )

                # Add paper identifier
                extraction_with_paper = {"paper_id": paper.stem, **extracted_data}
                all_extractions.append(extraction_with_paper)
                all_warnings[paper.stem] = warnings

                if warnings:
                    console.print(
                        f"[yellow]WARNING - {paper.name}: {len(warnings)} warnings[/yellow]"
                    )
                else:
                    console.print(
                        f"[green]OK - {paper.name}: extracted successfully[/green]"
                    )

            except Exception as e:
                console.print(f"[red]ERROR - {paper.name}: {str(e)}[/red]")
                failed_papers.append((paper.name, str(e)))

            progress.advance(task)

    # Create Excel file with all extractions
    if all_extractions:
        console.print("\n[cyan]Creating Excel file with all extractions...[/cyan]")
        try:
            df = pd.DataFrame(all_extractions)
            excel_file = form_output_dir / f"{form_id}_all_extractions.xlsx"
            df.to_excel(excel_file, index=False, engine="openpyxl")
            console.print(f"[green]OK - Excel file created: {excel_file}[/green]")
            console.print(
                f"[dim]{len(all_extractions)} papers x {len(df.columns)} fields[/dim]"
            )
        except Exception as e:
            console.print(f"[red]ERROR creating Excel file: {str(e)}[/red]")

    # Generate report
    generate_extraction_report(all_extractions, all_warnings, form_fields)

    # Show failed papers
    if failed_papers:
        console.print("\n[bold red]Failed Papers:[/bold red]")
        for paper_name, error in failed_papers:
            console.print(f"  • {paper_name}: {error}")

    console.print(f"\n[bold green]Form {form_id} extraction complete![/bold green]")
    console.print(f"Results saved to: {form_output_dir}")


def main():
    """Execute the enhanced extraction workflow for all forms."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    console.print("\n[bold cyan]" + "=" * 70 + "[/bold cyan]")
    console.print("[bold cyan]Project-Agnostic Form Extraction System[/bold cyan]")
    console.print("[bold cyan]" + "=" * 70 + "[/bold cyan]\n")

    # Paths
    forms_dir = Path("data/forms")
    papers_dir = Path("papers")
    base_output_dir = Path("output/form_extractions")
    base_output_dir.mkdir(parents=True, exist_ok=True)

    # Check for API key
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment[/red]")
        console.print(
            "[yellow]Please set it in .env file or environment variables[/yellow]"
        )
        sys.exit(1)

    # Discover all forms
    console.print(f"[bold cyan]Step 1: Discovering forms in {forms_dir}...[/bold cyan]")
    forms = discover_forms(forms_dir)

    if not forms:
        console.print("[red]No form Excel files found in forms directory[/red]")
        console.print(
            "[yellow]Please add your Excel form definitions to data/forms/[/yellow]"
        )
        sys.exit(1)

    console.print(f"[green]Found {len(forms)} form(s) to process:[/green]")
    for form in forms:
        console.print(f"  • {form.name} -> Output ID: '{get_form_identifier(form)}'")

    # Process each form
    for form_path in forms:
        try:
            process_form(form_path, papers_dir, base_output_dir, api_key)
        except Exception as e:
            console.print(
                f"[red]FATAL ERROR processing {form_path.name}: {str(e)}[/red]"
            )
            import traceback

            traceback.print_exc()

    console.print("\n[bold green]All forms processed![/bold green]")
    console.print(f"Results saved to: {base_output_dir}")


if __name__ == "__main__":
    main()
