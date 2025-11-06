---
name: ripgrep
description: This skill should be used when users need to search for patterns in files or codebases using ripgrep (rg). Use this skill for tasks involving recursive text search, code searching, pattern matching with regex, filtering search results by file type or path, or finding specific content across directories. Ripgrep is faster and more user-friendly than traditional grep.
---

# Ripgrep Skill

This skill provides expertise in using ripgrep (rg), a line-oriented search tool that recursively searches directories for a regex pattern. Ripgrep is extremely fast and respects your .gitignore files by default.

## About Ripgrep

Ripgrep is a command-line search tool that combines the usability of The Silver Searcher (ag) with the raw speed of grep. Written in Rust, it's optimized for searching source code and is significantly faster than traditional grep, especially on large codebases.

### Key Capabilities

- **Fast**: Written in Rust with parallelized searching
- **Smart Defaults**: Automatically respects .gitignore, skips hidden files and binary files
- **Regex Support**: Full regex support with multiple engines
- **File Type Filtering**: Built-in file type recognition
- **Context Control**: Show lines before/after matches
- **Replace Mode**: Preview and perform text replacements
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Colored Output**: Syntax highlighting for better readability

## When to Use This Skill

Use this skill when users:

- Need to search for text patterns across files or directories
- Want to find specific code patterns in a codebase
- Need to search with regex patterns
- Want to filter searches by file type or extension
- Need to find and replace text across multiple files
- Want case-sensitive or case-insensitive searches
- Need to search in specific directories while excluding others
- Ask about finding occurrences of functions, variables, or patterns
- Want faster alternatives to grep, ack, or ag
- Need to respect .gitignore rules in searches

## How to Use This Skill

### Basic Ripgrep Workflow

The basic command pattern is:

```bash
rg [OPTIONS] PATTERN [PATH...]
```

### Basic Searching

#### Simple Search

Search for a pattern in the current directory:

```bash
rg "pattern"
rg "function_name"
rg "TODO"
```

Search in a specific file or directory:

```bash
rg "pattern" file.txt
rg "pattern" src/
rg "pattern" src/ tests/
```

#### Case Sensitivity

Case-insensitive search:

```bash
rg -i "pattern"
rg --ignore-case "TODO"
```

Case-sensitive search (force, even if pattern has no uppercase):

```bash
rg -s "pattern"
rg --case-sensitive "pattern"
```

Smart case (case-insensitive unless pattern has uppercase):

```bash
rg -S "pattern"
rg --smart-case "Pattern"  # Case-sensitive because of capital P
```

#### Whole Word Matching

Match whole words only:

```bash
rg -w "word"
rg --word-regexp "function"
```

This ensures "function" matches but not "function_name".

### Regex Patterns

#### Basic Regex

Ripgrep uses Rust's regex engine by default:

```bash
# Match lines starting with "def"
rg "^def"

# Match lines ending with semicolon
rg ";$"

# Match email addresses
rg "\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

# Match function calls
rg "\w+\("

# Match numbers
rg "\b\d+\b"
```

#### Fixed Strings (Literal Search)

Search for literal strings (no regex):

```bash
rg -F "literal.string"
rg --fixed-strings "$(special*chars)"
```

This treats special regex characters as literal characters.

#### Multiline Search

Search across multiple lines:

```bash
rg -U "pattern.*\n.*another"
rg --multiline "def \w+.*\n.*return"
```

Note: Multiline search is slower than single-line.

### File Type Filtering

#### Search Specific File Types

Use built-in file type filters:

```bash
# Search only Python files
rg "pattern" -t py
rg "pattern" --type python

# Search only JavaScript/TypeScript files
rg "pattern" -t js -t ts

# Search only Markdown files
rg "pattern" -t md
```

#### Exclude File Types

Exclude specific file types:

```bash
rg "pattern" -T py
rg "pattern" --type-not python

# Exclude multiple types
rg "pattern" -T py -T js
```

#### List Available Types

See all available file types:

```bash
rg --type-list
```

#### Custom File Types

Define custom file types:

```bash
# Add a custom type
rg "pattern" --type-add 'custom:*.foo,*.bar' -t custom

# In ripgreprc or via alias
rg --type-add 'web:*.{html,css,js}' -t web "pattern"
```

### Path and File Filtering

#### Glob Patterns

Include or exclude files by glob pattern:

```bash
# Search only in specific files
rg "pattern" -g "*.py"
rg "pattern" -g "*.{js,ts,jsx,tsx}"

# Exclude specific files
rg "pattern" -g "!*.min.js"
rg "pattern" -g "!test_*"

# Combine include and exclude
rg "pattern" -g "*.py" -g "!test_*"
```

#### Search Hidden Files

Include hidden files and directories:

```bash
rg "pattern" --hidden
rg "pattern" -uu  # -uu = --no-ignore --hidden
```

#### Ignore .gitignore

Search all files, even those in .gitignore:

```bash
rg "pattern" --no-ignore
rg "pattern" -u
```

#### Full Override (Search Everything)

Search absolutely everything:

```bash
rg "pattern" -uuu
# -uuu = --no-ignore --hidden --binary
```

### Output Control

#### Show Only File Names

Show only files containing matches:

```bash
rg "pattern" -l
rg "pattern" --files-with-matches
```

Show files without matches:

```bash
rg "pattern" -L
rg "pattern" --files-without-match
```

#### Count Matches

Count matches per file:

```bash
rg "pattern" -c
rg "pattern" --count
```

Show total count only:

```bash
rg "pattern" --count-matches
```

#### Show Context

Show lines before and after matches:

```bash
# Show 3 lines before and after
rg "pattern" -C 3
rg "pattern" --context 3

# Show 2 lines before
rg "pattern" -B 2
rg "pattern" --before-context 2

# Show 2 lines after
rg "pattern" -A 2
rg "pattern" --after-context 2
```

#### Line Numbers

Show line numbers (default):

```bash
rg "pattern" -n
```

Hide line numbers:

```bash
rg "pattern" -N
rg "pattern" --no-line-number
```

Show column numbers:

```bash
rg "pattern" --column
```

#### Show File Headers

Show filenames before matches (default in multi-file search):

```bash
rg "pattern" --heading
```

Show filename on each line:

```bash
rg "pattern" --no-heading
```

Suppress filename output:

```bash
rg "pattern" -I
rg "pattern" --no-filename
```

### Advanced Features

#### Replace Mode

Preview replacements without modifying files:

```bash
rg "old_pattern" -r "new_text"
rg "function_(\w+)" -r "method_$1"
```

To actually replace (requires additional tools like sed or custom scripts):

```bash
# Using ripgrep with sed (careful!)
rg "pattern" -l | xargs sed -i 's/old/new/g'
```

#### Search and Replace with Capture Groups

Use capture groups in replacements:

```bash
# Replace function_name with methodName
rg "function_(\w+)" -r "method${1^}"

# Extract and reformat
rg '(\w+)@(\w+)\.com' -r '$2 domain: $1'
```

#### Pass-through (Filtering)

Use ripgrep as a filter:

```bash
# Search for "error" in git log
git log | rg "error"

# Search for pattern in command output
cat file.txt | rg "pattern"
```

#### JSON Output

Output results in JSON format:

```bash
rg "pattern" --json
```

Useful for programmatic processing.

#### Statistics

Show search statistics:

```bash
rg "pattern" --stats
```

Shows number of files searched, matches found, bytes searched, etc.

#### Sorted Output

Sort results by file path:

```bash
rg "pattern" --sort path
rg "pattern" --sort modified  # By modification time
rg "pattern" --sort created   # By creation time
rg "pattern" --sort accessed  # By access time
```

### Common Patterns and Use Cases

#### Find TODO Comments

```bash
rg "TODO|FIXME|HACK|XXX" -t py
rg "TODO:" --type-not test
```

#### Find Function Definitions

```bash
# Python functions
rg "^def \w+\(" -t py

# JavaScript functions
rg "function \w+\(|const \w+ = \(" -t js

# Find all function calls to specific function
rg "myFunction\(" -w
```

#### Find Imports

```bash
# Python imports
rg "^import |^from .* import" -t py

# JavaScript imports
rg "^import .* from" -t js -t ts
```

#### Search for Errors/Exceptions

```bash
rg "error|exception|fail" -i
rg "raise |throw " --type-not test
```

#### Find Specific Variable Usage

```bash
# Find all uses of a variable
rg "\bvariable_name\b"

# Find variable assignments
rg "variable_name\s*="
```

#### Find Long Lines

```bash
# Find lines longer than 100 characters
rg ".{100,}"
```

#### Search in Specific Languages

```bash
# Search Python files
rg "class \w+" -t py

# Search web files
rg "pattern" -t html -t css -t js

# Search config files
rg "pattern" -t yaml -t toml -t json
```

#### Find Binary Files Containing Text

```bash
rg "pattern" --binary
rg "pattern" -a
```

### Excluding Directories and Files

#### Common Exclusions

```bash
# Exclude node_modules and build directories
rg "pattern" -g "!node_modules/" -g "!build/"

# Exclude test files
rg "pattern" -g "!*test*" -g "!*spec*"

# Exclude minified files
rg "pattern" -g "!*.min.js"
```

#### Using .ignore Files

Create a `.ignore` file (similar to .gitignore) in your project root:

```text
node_modules/
dist/
build/
*.log
.venv/
```

Ripgrep will automatically respect this file.

### Output Formatting

#### Color Control

Force color output (e.g., when piping):

```bash
rg "pattern" --color always
```

Disable color:

```bash
rg "pattern" --color never
```

#### Compact Output

Show only matches (no filenames or line numbers):

```bash
rg "pattern" -I -N --no-heading
```

#### Custom Color Scheme

Set colors via environment variables:

```bash
export RIPGREP_CONFIG_PATH="$HOME/.ripgreprc"
```

In `~/.ripgreprc`:

```text
--colors=match:fg:yellow
--colors=match:bg:black
--colors=line:fg:cyan
```

### Performance Optimization

#### Parallel Processing

Ripgrep parallelizes by default. Control thread count:

```bash
# Use 4 threads
rg "pattern" -j 4
rg "pattern" --threads 4

# Use single thread (useful for debugging)
rg "pattern" -j 1
```

#### Memory Mapping

Enable/disable memory maps:

```bash
# Disable memory maps (use for network drives)
rg "pattern" --no-mmap

# Force memory maps
rg "pattern" --mmap
```

#### Search Zip Files

Search within compressed archives:

```bash
rg "pattern" -z
rg "pattern" --search-zip
```

### Configuration File

Create a configuration file for default options:

**Location**: `~/.ripgreprc` or set `RIPGREP_CONFIG_PATH`

**Example .ripgreprc**:

```text
# Default options
--smart-case
--hidden
--follow
--max-columns=150
--max-columns-preview

# Color scheme
--colors=match:fg:yellow
--colors=match:style:bold
--colors=line:fg:cyan
--colors=path:fg:green

# Custom type definitions
--type-add=web:*.{html,css,js,jsx,ts,tsx,vue}
--type-add=config:*.{json,yaml,yml,toml,ini,conf}

# Default exclusions (in addition to .gitignore)
--glob=!node_modules/
--glob=!.git/
--glob=!dist/
--glob=!build/
```

Apply config in command:

```bash
export RIPGREP_CONFIG_PATH="$HOME/.ripgreprc"
rg "pattern"
```

### Integration with Other Tools

#### With fzf (Fuzzy Finder)

Interactive search with preview:

```bash
rg --files | fzf --preview 'rg --color=always --context 3 {}'
```

#### With xargs

Process matching files:

```bash
# Format all Python files containing a pattern
rg "pattern" -t py -l | xargs black

# Remove all files containing a pattern
rg "deprecated" -l | xargs rm
```

#### With vim/neovim

Use ripgrep as grep program:

```vim
set grepprg=rg\ --vimgrep\ --smart-case\ --follow
```

#### With VS Code

VS Code uses ripgrep by default for file search.

### Comparison with Other Tools

#### Ripgrep vs grep

```bash
# grep
grep -r "pattern" .
grep -r "pattern" --include="*.py" .

# ripgrep (faster, respects .gitignore)
rg "pattern"
rg "pattern" -t py
```

#### Ripgrep vs The Silver Searcher (ag)

```bash
# ag
ag "pattern"
ag "pattern" --python

# ripgrep (similar syntax, faster)
rg "pattern"
rg "pattern" -t py
```

#### Ripgrep vs ack

```bash
# ack
ack "pattern"
ack --type=python "pattern"

# ripgrep
rg "pattern"
rg "pattern" -t py
```

### Troubleshooting

#### No Results Found

If ripgrep finds no results:

1. Check if files are in .gitignore: try `rg "pattern" -u`
2. Check if files are hidden: try `rg "pattern" --hidden`
3. Check if files are binary: try `rg "pattern" -a`
4. Verify regex pattern: try `rg -F "literal_pattern"`
5. Check file type filters: try without `-t` flag

#### Too Many Results

If overwhelmed by results:

1. Add file type filters: `-t py`
2. Use more specific patterns
3. Exclude directories: `-g "!tests/"`
4. Use word boundaries: `-w "pattern"`
5. Limit context: reduce `-C` value

#### Pattern Not Matching

If pattern should match but doesn't:

1. Try case-insensitive: `-i`
2. Try fixed strings: `-F`
3. Check for hidden characters
4. Use multiline mode if needed: `-U`
5. Verify regex syntax (Rust regex flavor)

#### Performance Issues

If ripgrep is slow:

1. Exclude large directories: `-g "!large_dir/"`
2. Reduce thread count: `-j 1` (for debugging)
3. Disable memory maps on network drives: `--no-mmap`
4. Add files to .ignore

### Best Practices

1. **Use Smart Case**: Enable `--smart-case` by default for convenience
2. **Respect .gitignore**: Keep default behavior; use `-u` only when needed
3. **Use File Types**: Prefer `-t py` over `-g "*.py"` for standard types
4. **Create .ignore Files**: Add project-specific exclusions
5. **Use Configuration File**: Set up `.ripgreprc` for consistent behavior
6. **Learn Regex**: Invest time in learning regex for powerful searches
7. **Use Word Boundaries**: `-w` prevents false positives
8. **Preview Before Replace**: Always use `-r` to preview before bulk edits
9. **Combine with Other Tools**: Use with fzf, xargs, etc. for workflows
10. **Check Documentation**: Use `rg --help` for quick reference

### Common Aliases

Add to shell configuration (~/.bashrc or ~/.zshrc):

```bash
# Case-insensitive search
alias rgi='rg -i'

# Search with context
alias rgc='rg -C 3'

# Search hidden files
alias rgh='rg --hidden'

# Search everything
alias rgall='rg -uuu'

# List files only
alias rgl='rg -l'

# Count matches
alias rgcount='rg -c'

# Search TODOs
alias todo='rg "TODO|FIXME|HACK|XXX"'

# Search Python files
alias rgpy='rg -t py'

# Search JavaScript/TypeScript files
alias rgjs='rg -t js -t ts'
```

### Quick Reference

**Basic Usage**:

- `rg "pattern"` - Search current directory
- `rg "pattern" path/` - Search specific path
- `rg -i "pattern"` - Case-insensitive
- `rg -w "word"` - Whole word

**File Filtering**:

- `rg "pattern" -t py` - Only Python files
- `rg "pattern" -T py` - Exclude Python files
- `rg "pattern" -g "*.js"` - Glob pattern
- `rg "pattern" --hidden` - Include hidden files

**Output Control**:

- `rg "pattern" -l` - Show file names only
- `rg "pattern" -c` - Count matches
- `rg "pattern" -C 3` - Show 3 lines context
- `rg "pattern" --json` - JSON output

**Advanced**:

- `rg "pattern" -r "replacement"` - Replace preview
- `rg "pattern" -u` - Ignore .gitignore
- `rg "pattern" -U` - Multiline search
- `rg "pattern" --stats` - Show statistics

## Installation

Ripgrep can be installed via multiple methods:

**Using package managers**:

```bash
# macOS
brew install ripgrep

# Debian/Ubuntu
sudo apt install ripgrep

# Fedora
sudo dnf install ripgrep

# Arch Linux
sudo pacman -S ripgrep

# Windows (Chocolatey)
choco install ripgrep

# Windows (Scoop)
scoop install ripgrep
```

**Using Cargo (Rust package manager)**:

```bash
cargo install ripgrep
```

**From binary releases**:

Download from: <https://github.com/BurntSushi/ripgrep/releases>

Verify installation:

```bash
rg --version
```

## Resources

- Official repository: <https://github.com/BurntSushi/ripgrep>
- User guide: <https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md>
- FAQ: <https://github.com/BurntSushi/ripgrep/blob/master/FAQ.md>
- Regex syntax: <https://docs.rs/regex/latest/regex/#syntax>
- Performance comparison: <https://blog.burntsushi.net/ripgrep/>
