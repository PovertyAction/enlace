# Stata Skill

This skill enables Claude to help develop and test Stata code.

## What This Skill Does

The Stata skill provides:

- Guidance for writing and executing Stata .do files
- Command-line Stata execution via Python's stata_setup and pystata
- Templates and scripts for creating Stata code
- Quick reference for common Stata commands and syntax

## When to Use

Invoke this skill when you need to:

- Write or edit Stata .do files in do_files/
- Execute Stata code from the command line
- Create new Stata materials
- Debug Stata syntax errors
- Test Stata code execution
- Generate template .do files

## Skill Contents

### SKILL.md

Main skill instructions covering:

- Stata command-line setup with stata_setup
- Stata .do file conventions and best practices
- Workflow for testing Stata code

### Scripts (`scripts/`)

- **run_stata.py**: Execute Stata commands or .do files with error handling
- **create_do_template.py**: Generate new .do files

### References (`references/`)

- **stata_quick_reference.md**: Common Stata commands and syntax patterns

### Assets (`assets/`)

- **template.do**: Standard .do file template with proper structure

## Installation

The skill is already installed in your project at:

```text
.claude/skills/stata/
```

## Usage

### Activating the Skill

To use the skill, simply type:

```text
/stata
```

Or mention Stata-related tasks in your conversation, and Claude will automatically activate the skill when appropriate.

### Running Stata Code

The skill enables Claude to execute Stata code using your local Stata installation:

1. Ensure your Python environment has stata-setup installed
2. Configure your Stata path (e.g., `C:\Program Files\Stata18\`)
3. Run .do files or individual Stata commands through Python

### Creating New .do Files

Use the included script to generate template files:

```bash
uv run python .claude/skills/stata/scripts/create_do_template.py output.do \
  --project "My Project" \
  --purpose "Data cleaning" \
  --author "Your Name"
```

## Examples

### Example 1: Testing a .do File

```text
User: Test the data cleaning script in do_files/paper-analysis/clean.do
Claude: [Uses stata skill to run the .do file and reports results]
```

### Example 2: Debugging Stata Code

```text
User: This loop isn't working correctly: foreach var in age income { ... }
Claude: [Uses stata skill references to identify syntax error and suggest fix]
```

## Requirements

- Stata installed locally (Stata 14+ recommended)
- Python environment with stata-setup and pystata packages
- uv for Python environment management

## File Structure

```text

stata/
├── SKILL.md                          # Main skill instructions
├── README.md                         # This file
├── scripts/
│   ├── run_stata.py                  # Execute Stata code
│   └── create_do_template.py         # Generate .do templates
├── references/
│   └── stata_quick_reference.md      # Common Stata commands
└── assets/
    └── template.do                   # .do file template

```

## Customization

### Stata Path Configuration

Update the default Stata path in `scripts/run_stata.py` if your installation differs from the default `C:\Program Files\Stata18\`.

### Template Customization

Modify `assets/template.do` to match your organization's coding standards and conventions.

## Troubleshooting

### "stata_setup not found"

Install with: `uv add stata-setup`

### "Stata path not found"

Verify your Stata installation path and update the configuration in run_stata.py

### Encoding errors on Windows

Ensure your terminal supports UTF-8 encoding

## Contributing

To improve this skill:

1. Update SKILL.md with new instructions or guidance
2. Add new scripts to `scripts/` for repeated tasks
3. Expand references with additional Stata patterns
4. Update assets with improved templates

## Version History

- v1.0 (2025-11-04): Initial creation with core Stata development capabilities
