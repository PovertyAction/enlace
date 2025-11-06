---
name: eza
description: This skill should be used when users need to list files and directories with modern, colorful, and feature-rich output. Use this skill for tasks involving directory listing, file inspection, tree views, git status integration, file permissions display, or exploring filesystem structure. Eza is a modern replacement for ls with better defaults and more features.
---

# Eza Skill

This skill provides expertise in using eza, a modern, maintained replacement for the traditional `ls` command. Eza offers better defaults, more features, and colorful output to make file listing more informative and user-friendly.

## About Eza

Eza is a modern replacement for `ls` (and the unmaintained `exa`) that displays files and directories with colors, icons, git integration, and tree views. Written in Rust, it's fast, feature-rich, and provides sensible defaults for everyday use.

### Key Capabilities

- **Colorful Output**: Syntax highlighting and color-coded file types
- **Git Integration**: Show git status alongside files
- **Tree Views**: Display directory structure as trees
- **Icons**: Display file type icons (with Nerd Fonts)
- **Extended Attributes**: Show file metadata, permissions, timestamps
- **Grid and Table Views**: Multiple layout options
- **Cross-platform**: Works on Linux, macOS, and Windows
- **Fast**: Written in Rust for performance

## When to Use This Skill

Use this skill when users:

- Need to list files and directories
- Want colorful, readable file listings
- Need to see git status alongside files
- Want to view directory trees
- Need to inspect file permissions and metadata
- Want to sort files by various attributes
- Need to see file sizes in human-readable format
- Ask about exploring directory structure
- Want modern alternatives to `ls` or `tree`
- Need to filter or find specific file types

## How to Use This Skill

### Basic Eza Workflow

The basic command pattern is:

```bash
eza [OPTIONS] [FILES...]
```

### Basic Listing

#### Simple List

List files in current directory:

```bash
eza
eza .
```

List specific directory:

```bash
eza /path/to/dir
eza src/ tests/
```

#### Long Format

Show detailed information (like `ls -l`):

```bash
eza -l
eza --long
```

Shows: permissions, size, user, group, timestamp, name

#### All Files

Show hidden files and directories:

```bash
eza -a
eza --all
```

Show all files including `.` and `..`:

```bash
eza -aa
eza --all --all
```

#### Common Combination

Long format with all files:

```bash
eza -la
eza -l -a
eza --long --all
```

### Display Formats

#### Grid View (Default)

Display files in a grid:

```bash
eza -G
eza --grid
```

#### One File Per Line

List one file per line:

```bash
eza -1
eza --oneline
```

#### Long Grid

Combine long format with grid for wide terminals:

```bash
eza -l --grid
```

#### Across Columns

List files across columns instead of down:

```bash
eza -x
eza --across
```

### Tree View

#### Basic Tree

Display directory structure as tree:

```bash
eza --tree
eza -T
```

#### Tree with Depth Limit

Limit tree depth:

```bash
# 2 levels deep
eza --tree --level=2
eza -T -L2

# 3 levels deep
eza --tree --level=3
eza -T -L3
```

#### Tree with Long Format

Combine tree with detailed information:

```bash
eza --tree --long
eza -T -l
```

#### Tree for Specific Directory

```bash
eza --tree src/
eza -T -L2 /usr/local
```

### Sorting

#### Sort by Name (Default)

```bash
eza
eza --sort=name
```

#### Sort by Size

```bash
eza -l --sort=size
eza -l -s size
```

#### Sort by Modified Time

```bash
eza -l --sort=modified
eza -l -s mod
eza -l -s modified
```

Reverse order (newest first):

```bash
eza -l --sort=modified --reverse
eza -l -s mod -r
```

#### Sort by Created Time

```bash
eza -l --sort=created
eza -l -s cr
```

#### Sort by Accessed Time

```bash
eza -l --sort=accessed
eza -l -s acc
```

#### Sort by Extension

```bash
eza -l --sort=extension
eza -l -s ext
```

#### Sort by Type

Group directories first, then files:

```bash
eza -l --sort=type
eza -l --group-directories-first
```

### File Information

#### Show File Headers

Show column headers in long format:

```bash
eza -l --header
eza -lh
```

#### Show Inode Numbers

```bash
eza -l --inode
eza -li
```

#### Show Number of Hard Links

```bash
eza -l --links
eza -lH
```

#### Show File Sizes

Human-readable sizes (default in long format):

```bash
eza -l
```

Binary units (1024-based):

```bash
eza -l --binary
eza -lb
```

Bytes only:

```bash
eza -l --bytes
eza -lB
```

#### Show Blocks

Show number of filesystem blocks:

```bash
eza -l --blocks
eza -lS
```

#### Show File Permissions

Show octal permissions:

```bash
eza -l --octal-permissions
eza -l@
```

Example output: `644` instead of `rw-r--r--`

### Time and Date Display

#### Show Timestamps

Modified time (default):

```bash
eza -l
```

Created time:

```bash
eza -l --created
eza -l --time=created
```

Accessed time:

```bash
eza -l --accessed
eza -l --time=accessed
```

#### Time Styles

ISO format:

```bash
eza -l --time-style=iso
```

Long ISO format:

```bash
eza -l --time-style=long-iso
```

Full timestamp:

```bash
eza -l --time-style=full-iso
```

Relative time (e.g., "2 hours ago"):

```bash
eza -l --time-style=relative
```

### Git Integration

#### Show Git Status

Display git status for files:

```bash
eza -l --git
eza -l --git --git-ignore
```

Shows status indicators:

- `N` - New (untracked)
- `M` - Modified
- `D` - Deleted
- `R` - Renamed
- `T` - Type changed
- `I` - Ignored
- `-` - No changes

#### Git Ignored Files

Respect .gitignore:

```bash
eza --git-ignore
```

Show git-ignored files differently:

```bash
eza -l --git --git-ignore
```

### Icons and Colors

#### Show Icons

Display file type icons (requires Nerd Fonts):

```bash
eza --icons
eza --icons=always
```

Disable icons:

```bash
eza --icons=never
```

Auto-detect (icons if terminal supports):

```bash
eza --icons=auto
```

#### Color Options

Always use colors:

```bash
eza --color=always
```

Never use colors:

```bash
eza --color=never
```

Auto-detect colors:

```bash
eza --color=auto
```

Color scale for file sizes and ages:

```bash
eza -l --color-scale
eza -l --color-scale=size
eza -l --color-scale=age
```

### Filtering and Ignoring

#### Show Only Directories

```bash
eza -D
eza --only-dirs
```

#### Show Only Files

```bash
eza -f
eza --only-files
```

#### Ignore Glob Patterns

Ignore files matching pattern:

```bash
eza --ignore-glob="*.log"
eza --ignore-glob="*.tmp|*.bak"
```

Multiple patterns:

```bash
eza --ignore-glob="*.log" --ignore-glob="node_modules"
```

#### Show Git Repos

Show git repository status:

```bash
eza -l --git-repos
```

### Extended Attributes

#### Show Extended Attributes (xattr)

On systems that support it (macOS, Linux):

```bash
eza -l --extended
eza -l@
```

Shows attributes like:

- macOS: com.apple.quarantine, com.apple.metadata
- Linux: security.selinux, user.* attributes

#### Show Security Context

Show SELinux context (Linux):

```bash
eza -l --context
eza -lZ
```

### Hyperlinks

#### Hyperlink File Names

Make filenames clickable in supported terminals:

```bash
eza --hyperlink
```

### Common Use Cases

#### Daily Usage - Basic Listing

Replace `ls -la`:

```bash
eza -la
eza -la --icons
```

With git status:

```bash
eza -la --git --icons
```

#### Explore Directory Structure

Tree view with icons and git:

```bash
eza --tree --level=3 --icons --git-ignore
eza -T -L3 --icons --git-ignore
```

#### Find Large Files

Sort by size, largest first:

```bash
eza -la --sort=size --reverse
eza -la -s size -r
```

#### Find Recently Modified Files

Sort by modification time, newest first:

```bash
eza -la --sort=modified --reverse
eza -la -s mod -r
```

Show relative timestamps:

```bash
eza -la --sort=modified --reverse --time-style=relative
```

#### Inspect File Permissions

Show octal permissions:

```bash
eza -la --octal-permissions
eza -la@
```

#### Clean Directory Listing

Only files, sorted by name:

```bash
eza -f --sort=name
```

Only directories:

```bash
eza -D --sort=name
```

#### Development Workflow

Show project structure with git status:

```bash
eza -la --tree --level=2 --git --icons --git-ignore
```

Ignore common directories:

```bash
eza -la --tree --ignore-glob="node_modules|.git|dist|build" --icons
```

#### Check Git Status

See which files have changes:

```bash
eza -la --git --sort=modified
```

#### Documentation Inspection

Find markdown files:

```bash
eza -f | grep -i "\.md$"
eza --tree --level=2 | grep -i "\.md"
```

#### Size Analysis

Show sizes in different formats:

```bash
# Human readable
eza -la

# Bytes only
eza -laB

# Binary units (KB, MB, GB)
eza -lab
```

### Aliases and Configuration

#### Common Aliases

Add to shell configuration (~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish):

**Bash/Zsh:**

```bash
# Basic replacement for ls
alias ls='eza'
alias ll='eza -l'
alias la='eza -la'
alias lt='eza --tree'

# Detailed listings
alias l='eza -la --icons --git'
alias ls-tree='eza --tree --level=2 --icons'
alias ls-git='eza -la --git --icons --sort=modified'

# Specialty listings
alias ls-size='eza -la --sort=size --reverse'
alias ls-time='eza -la --sort=modified --reverse'
alias ls-dirs='eza -D'
alias ls-files='eza -f'

# Tree views
alias tree='eza --tree --icons'
alias tree2='eza --tree --level=2 --icons'
alias tree3='eza --tree --level=3 --icons'
```

**Fish:**

```fish
# Basic replacement for ls
alias ls='eza'
alias ll='eza -l'
alias la='eza -la'

# Detailed listings
alias l='eza -la --icons --git'
```

#### Environment Variables

Configure default behavior with environment variables:

```bash
# Set default color mode
export EZA_COLORS="reset"

# Set default icons mode
export EZA_ICONS_AUTO=1

# Set default time style
export TIME_STYLE="long-iso"
```

#### Configuration File

Eza supports a config file at `~/.config/eza/theme.yml` for custom colors:

```yaml
# Custom color theme
filekinds:
  normal: 38;5;255
  directory: 38;5;33
  symlink: 38;5;51
  pipe: 38;5;136
  block_device: 38;5;136
  char_device: 38;5;136
  socket: 38;5;136
  special: 38;5;136

perms:
  user_read: 38;5;148
  user_write: 38;5;203
  user_execute_file: 38;5;113
  group_read: 38;5;185
  group_write: 38;5;216
  group_execute: 38;5;107
  other_read: 38;5;221
  other_write: 38;5;209
  other_execute: 38;5;143
```

### Advanced Features

#### Classify Output

Add indicators to filenames:

```bash
eza -F
eza --classify
```

Adds:

- `/` for directories
- `*` for executables
- `@` for symlinks
- `|` for pipes
- `=` for sockets

#### Absolute Paths

Show absolute paths:

```bash
eza --absolute
eza -lpathname
```

#### Dereference Symlinks

Follow symlinks:

```bash
eza -l --dereference
eza -lL
```

#### Show Total Size

Show total size of directory contents:

```bash
eza -l --total-size
```

#### Smart Group

Group items intelligently:

```bash
eza -l --smart-group
```

#### Width Control

Set output width:

```bash
eza --width=80
eza -w 80
```

### Comparison with ls

#### Basic Listing

```bash
# ls
ls -la

# eza (equivalent)
eza -la

# eza (enhanced)
eza -la --icons --git
```

#### Tree View

```bash
# tree command
tree -L 2

# eza equivalent
eza --tree --level=2
eza -T -L2

# eza enhanced
eza -T -L2 --icons --git-ignore
```

#### Sort by Time

```bash
# ls
ls -lt

# eza
eza -l --sort=modified
eza -l -s mod
```

#### Human Readable Sizes

```bash
# ls
ls -lh

# eza (default behavior)
eza -l
```

### Troubleshooting

#### Icons Not Showing

If icons appear as boxes or question marks:

1. Install a Nerd Font: <https://www.nerdfonts.com/>
2. Configure your terminal to use the Nerd Font
3. Verify with: `eza --icons /`

Alternatively, disable icons:

```bash
eza -la  # Without --icons flag
```

#### Colors Not Displaying

If colors don't appear:

1. Check terminal supports colors
2. Force color: `eza --color=always`
3. Check `$TERM` environment variable
4. Try different terminal emulator

#### Git Status Not Showing

If `--git` doesn't show status:

1. Ensure you're in a git repository
2. Check git is installed: `git --version`
3. Verify git repository: `git status`

#### Performance with Large Directories

If eza is slow on large directories:

1. Disable git integration: remove `--git` flag
2. Reduce tree depth: `--level=1`
3. Use `--ignore-glob` to exclude large subdirectories
4. Avoid `--tree` on very large hierarchies

### Best Practices

1. **Use Icons Sparingly**: Icons require Nerd Fonts and may slow output on very large directories
2. **Leverage Git Integration**: Use `--git` when working in repositories for instant status
3. **Create Aliases**: Set up aliases for common patterns to save typing
4. **Respect .gitignore**: Use `--git-ignore` when viewing project trees
5. **Use Tree View Wisely**: Limit depth with `--level` to avoid overwhelming output
6. **Sort Appropriately**: Sort by `modified` to find recent work, by `size` to find large files
7. **Color Scale**: Use `--color-scale` to visually identify large or old files
8. **Combine Filters**: Use `--only-files` or `--only-dirs` with other options for focused views
9. **Time Styles**: Use `relative` time style for quick glances, `iso` for precise timestamps
10. **Ignore Patterns**: Use `--ignore-glob` to skip irrelevant directories (node_modules, .git, etc.)

### Quick Reference

**Basic Usage**:

- `eza` - List files
- `eza -la` - Long format, all files
- `eza --tree` - Tree view
- `eza --icons` - Show icons

**Sorting**:

- `eza -l -s size` - Sort by size
- `eza -l -s mod -r` - Sort by modified (newest first)
- `eza -l -s created` - Sort by created time
- `eza --group-directories-first` - Directories first

**Filtering**:

- `eza -D` - Only directories
- `eza -f` - Only files
- `eza --ignore-glob="*.log"` - Ignore pattern
- `eza --git-ignore` - Respect .gitignore

**Git Integration**:

- `eza -l --git` - Show git status
- `eza --git-ignore` - Ignore git-ignored files
- `eza -l --git-repos` - Show git repository info

**Display Options**:

- `eza -l` - Long format
- `eza -lh` - With headers
- `eza -T -L2` - Tree, 2 levels deep
- `eza -l --time-style=relative` - Relative timestamps

**Advanced**:

- `eza -l@` - Show octal permissions
- `eza -l --color-scale` - Color-code by size/age
- `eza -l --hyperlink` - Hyperlink filenames
- `eza -l --total-size` - Show total directory size

### Integration Examples

#### Find and List

Find Python files and list with details:

```bash
find . -name "*.py" -type f | xargs eza -l --sort=size
```

#### Watch Directory

Watch directory for changes:

```bash
watch -n 1 'eza -la --sort=modified --color=always'
```

#### Filter with ripgrep

List files containing pattern:

```bash
rg -l "pattern" | xargs eza -l
```

#### Export to File

Save listing to file (without colors):

```bash
eza -la --color=never > files.txt
```

#### Count File Types

Count files by extension:

```bash
eza -f | grep -oE '\.[^.]+$' | sort | uniq -c | sort -rn
```

## Installation

Eza can be installed via multiple methods:

**Using package managers**:

```bash
# macOS (Homebrew)
brew install eza

# Debian/Ubuntu
sudo apt install eza

# Fedora
sudo dnf install eza

# Arch Linux
sudo pacman -S eza

# Gentoo
emerge sys-apps/eza

# Nix
nix-env -i eza

# Windows (Scoop)
scoop install eza

# Windows (Chocolatey)
choco install eza

# Windows (Winget)
winget install eza-community.eza
```

**Using Cargo (Rust package manager)**:

```bash
cargo install eza
```

**From binary releases**:

Download from: <https://github.com/eza-community/eza/releases>

**Optional: Install Nerd Fonts**:

For icon support, install a Nerd Font:

```bash
# macOS
brew tap homebrew/cask-fonts
brew install --cask font-hack-nerd-font

# Manual installation
# Download from: https://www.nerdfonts.com/
```

Verify installation:

```bash
eza --version
eza --help
```

## Resources

- Official website: <https://eza.rocks/>
- GitHub repository: <https://github.com/eza-community/eza>
- Documentation: <https://eza.rocks/docs/>
- Nerd Fonts: <https://www.nerdfonts.com/>
- Color customization: <https://the.exa.website/docs/colour-themes>
