"""Extract information from research papers based on form definition.

This script reads a form definition from an Excel file and extracts the specified
information from research papers using LLM-based extraction.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def load_form_definition(excel_path: Path) -> pd.DataFrame:
    """Load and parse the form definition from Excel."""
    df = pd.read_excel(excel_path)

    # Filter to get only the substantive fields
    substantive_types = ["text", "integer", "date", "select_one", "select_multiple"]

    # Get fields that have labels and are substantive types
    fields = df[
        (df["label"].notna())
        & (df["rando"].apply(lambda x: any(t in str(x) for t in substantive_types)))
    ].copy()

    return fields


def create_extraction_prompt(fields: pd.DataFrame, paper_text: str) -> str:
    """Create a prompt for LLM to extract information based on form fields."""
    # Group fields by logical sections based on field names
    sections = {
        "Publication Details": [],
        "Study Design": [],
        "Interventions/Treatments": [],
        "Credit/Loan Details": [],
        "Outcomes": [],
        "Geographic Information": [],
        "Sample Information": [],
    }

    for _, field in fields.iterrows():
        name = field["name"]
        label = field["label"]
        field_type = field["rando"]

        # Categorize fields
        if any(x in name.lower() for x in ["study", "pub", "auth", "link"]):
            sections["Publication Details"].append((name, label, field_type))
        elif any(x in name.lower() for x in ["int", "treat", "comp", "control"]):
            sections["Interventions/Treatments"].append((name, label, field_type))
        elif any(x in name.lower() for x in ["loan", "credit", "bank"]):
            sections["Credit/Loan Details"].append((name, label, field_type))
        elif "outcome" in name.lower():
            sections["Outcomes"].append((name, label, field_type))
        elif any(x in name.lower() for x in ["geo", "country"]):
            sections["Geographic Information"].append((name, label, field_type))
        elif any(x in name.lower() for x in ["samp", "unit"]):
            sections["Sample Information"].append((name, label, field_type))
        else:
            sections["Study Design"].append((name, label, field_type))

    # Build the prompt
    prompt = f"""You are a research assistant extracting structured information from an academic paper.

Please carefully read the paper and extract the following information. For each field:
- Provide the exact information requested
- If information is not found, respond with "NOT FOUND"
- For numeric fields, provide only numbers
- For date fields, use YYYY-MM-DD format
- For select fields, choose from provided options when applicable

PAPER TEXT:
{paper_text[:50000]}  # Limit to avoid token limits

EXTRACTION FIELDS:

"""

    for section_name, section_fields in sections.items():
        if section_fields:
            prompt += f"\n## {section_name}\n"
            for name, label, field_type in section_fields:
                prompt += f"\n**{name}**: {label}\n"
                prompt += f"Type: {field_type}\n"

    prompt += """

Please provide your response as a JSON object with field names as keys and extracted values as values.
Example format:
{
    "studyID": "12345",
    "IPA_studyName": "Impact of Microcredit on Household Income",
    "pubYear": "2023",
    "authNum": 3
}
"""

    return prompt


def extract_with_llm(prompt: str, api_key: str) -> dict[str, Any]:
    """Use Claude to extract information from the paper."""
    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
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


def main():
    """Execute the main extraction workflow."""
    # Paths
    form_path = Path("data/DEV_stage1_ipaMC_v1 (1).xlsx")
    papers_dir = Path("papers")
    output_dir = Path("output/form_extractions")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check for API key
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[red]Error: ANTHROPIC_API_KEY not found in environment[/red]")
        console.print(
            "[yellow]Please set it in .env file or environment variables[/yellow]"
        )
        sys.exit(1)

    console.print(f"[cyan]Loading form definition from {form_path}...[/cyan]")
    fields = load_form_definition(form_path)
    console.print(f"[green]Found {len(fields)} extraction fields[/green]")

    # Get papers
    papers = list(papers_dir.glob("*.pdf"))
    if not papers:
        console.print("[yellow]No PDF files found in papers directory[/yellow]")
        return

    console.print(f"\n[cyan]Found {len(papers)} papers to process[/cyan]\n")

    # Store all extractions for Excel output
    all_extractions = []

    for paper in papers:
        console.print(f"[bold]Processing: {paper.name}[/bold]")

        try:
            # First, extract text from the paper using enlace
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Extracting paper content...", total=None)

                # Use the existing extraction to get markdown
                output_path = Path("output") / paper.stem
                markdown_path = output_path / f"{paper.stem}.md"

                if not markdown_path.exists():
                    console.print("[yellow]Running enlace extraction first...[/yellow]")
                    import subprocess

                    result = subprocess.run(
                        ["uv", "run", "enlace", "extract", str(paper)],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        console.print(
                            f"[red]Failed to extract paper: {result.stderr}[/red]"
                        )
                        continue

                # Read the markdown
                paper_text = markdown_path.read_text(encoding="utf-8")
                progress.update(task, description="Creating extraction prompt...")

                # Create prompt
                prompt = create_extraction_prompt(fields, paper_text)

                progress.update(task, description="Extracting with Claude...")

                # Extract with LLM
                extracted_data = extract_with_llm(prompt, api_key)

                progress.update(task, description="Saving results...")

                # Save results
                output_file = output_dir / f"{paper.stem}_extraction.json"
                output_file.write_text(
                    json.dumps(extracted_data, indent=2), encoding="utf-8"
                )

                # Add paper name to extraction data for Excel
                extraction_with_paper = {"paper_id": paper.stem, **extracted_data}
                all_extractions.append(extraction_with_paper)

                console.print(f"[green]✓ Extraction saved to: {output_file}[/green]")
                console.print(f"[dim]Extracted {len(extracted_data)} fields[/dim]\n")

        except Exception as e:
            console.print(f"[red]✗ Error processing {paper.name}: {str(e)}[/red]\n")
            continue

    # Create Excel file with all extractions
    if all_extractions:
        console.print("\n[cyan]Creating Excel file with all extractions...[/cyan]")
        try:
            # Convert to DataFrame
            df = pd.DataFrame(all_extractions)

            # Save to Excel
            excel_file = output_dir / "all_extractions.xlsx"
            df.to_excel(excel_file, index=False, engine="openpyxl")

            console.print(f"[green]✓ Excel file created: {excel_file}[/green]")
            console.print(
                f"[dim]{len(all_extractions)} papers × {len(df.columns)} fields[/dim]"
            )
        except Exception as e:
            console.print(f"[red]✗ Error creating Excel file: {str(e)}[/red]")
    else:
        console.print("\n[yellow]No extractions to save to Excel[/yellow]")


if __name__ == "__main__":
    main()
