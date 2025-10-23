# Product Requirements Document: Local Project Manager

## Problem Statement

Developers accumulate numerous local projects over time in various states:
- **Cloud-backed** (GitHub, Bitbucket, GitLab) vs. **local-only**
- **Active development** vs. **dormant experiments** vs. **abandoned throwaway code**
- **Well-documented** vs. **undocumented**
- **Committed** vs. **uncommitted changes**

The challenge: **No systematic way to inventory, assess health, and prune local projects**, leading to:
- Lost track of what exists and in what state
- Uncertainty about which projects have cloud backups
- Difficulty identifying safe-to-delete candidates
- Wasted disk space on forgotten experiments

## Solution Overview

Local Project Manager is a **Python TUI (Text User Interface) application** built with Textual that provides:
- **Multi-signal project detection** (git repos, project type manifests, READMEs, file activity)
- **Project health classification** (Active, Work-in-Progress, Dormant, Stale)
- **README management** (view, edit, create, delete)
- **Pruning workflow** with safe deletion confirmation
- **VS Code integration** for seamless project opening

## Core Requirements

### 1. Project Detection & Scanning

**1.1 Directory Scanning**
- Scan current directory and all subdirectories recursively
- Support user-specified starting directory
- Async scanning for performance with large directory trees
- Progress indicator during scan

**1.2 Project Identification Signals**

Detect projects using **multiple signals** (not just README):

| Signal | Detection Method | Purpose |
|--------|-----------------|---------|
| **Git Repository** | `.git` directory exists | Identifies version-controlled projects, enables remote status check |
| **Project Type** | Manifest files (see table below) | Categorizes by language/framework |
| **README** | `.md`, `.txt` files named README (case-insensitive) | Indicates documented projects |
| **File Activity** | Most recent modification timestamp in tree | Identifies active vs. abandoned |
| **Size** | Total directory size (MB) | Helps prioritize pruning candidates |

**Project Type Detection:**

| File/Directory | Project Type |
|----------------|-------------|
| `package.json` | Node.js/JavaScript |
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java |
| `composer.json` | PHP |
| `.csproj`, `.sln` | C# / .NET |
| `Gemfile` | Ruby |

**1.3 Git Metadata Extraction**

For projects with `.git`:
- Check if remote is configured (any remote, not just origin)
- Extract primary remote URL (prefer origin)
- Detect working tree status:
  - **Clean**: No uncommitted changes, nothing to push
  - **Dirty**: Uncommitted changes exist
  - **Unpushed**: Commits ahead of remote

### 2. Project Classification

Automatically classify projects based on combined signals:

| Classification | Criteria |
|----------------|----------|
| **Active** | Modified ≤ 30 days ago AND (has git remote OR has README) |
| **Work-in-Progress** | Modified ≤ 30 days ago AND no git remote AND no README |
| **Dormant** | Modified 30-180 days ago |
| **Stale** | Modified > 180 days ago |

**Pruning Candidate Flags:**
- Stale (> 180 days old)
- AND no git remote
- AND size > configurable threshold (default: 10 MB) OR size < configurable threshold (default: 1 MB for tiny experiments)

### 3. User Interface Design

**3.1 Layout (Three-Panel Design)**

```
┌─ Local Project Manager ──────────────────────────────────┐
│ Scan Path: /home/user/projects         [F1] Help  [F10] Quit │
├───────────────────────────────────────────────────────────┤
│ Summary: 47 projects | Active: 12 | Dormant: 18 | Stale: 8 | Prunable: 5 │
├─ Filters ─────────────────────────────────────────────────┤
│ ○ All  ● Active  ○ WIP  ○ Dormant  ○ Stale  ○ No Remote  ○ No README │
├─ Project List (23/47) ─────────────────────────────────────┤
│ ▶ ✓⚡ site2pdf/                Python    Remote ✓   7d ago │
│ ▼ ✓  local-project-manager    Python    Remote ✗   2h ago │
│     ├─ README.md (exists)                                 │
│     ├─ Last: 2025-10-22 14:30                            │
│     └─ Size: 2.3 MB                                       │
│ ▶ ✗  experiment-2024           Unknown   Remote ✗  180d ago │
│ ▶ ✓⚠  old-client-work          Node.js   Remote ✓  240d ago │
├─ Actions (local-project-manager) ──────────────────────────┤
│ [V]iew README  [E]dit README  [C]reate README  [D]elete README │
│ [O]pen in VS Code  [G]it Status  [P]rune Project  [R]efresh │
└───────────────────────────────────────────────────────────┘
```

**Legend:**
- `✓` = Has git repository
- `✗` = No git repository
- `⚡` = Recent activity (< 7 days)
- `⚠` = Uncommitted or unpushed changes
- `▶` = Collapsed project
- `▼` = Expanded project

**3.2 Keyboard Navigation**

| Key(s) | Action |
|--------|--------|
| `↑/k`, `↓/j` | Navigate project list (vim-style) |
| `Space`, `Enter` | Expand/collapse project details |
| `Tab` | Cycle through filter options |
| `/` | Search/filter projects by name |
| `v` | View README in scrollable pane |
| `e` | Edit README in $EDITOR |
| `c` | Create README (with template options) |
| `d` | Delete README (with confirmation) |
| `o` | Open project in VS Code (`code <path>`) |
| `g` | View detailed git status |
| `p` | Prune project (delete permanently) |
| `r` | Refresh scan |
| `x` | Toggle multi-select mode |
| `F1` | Help/keyboard shortcuts |
| `F10`, `q` | Quit |

**3.3 Visual Design Principles**

- **Monospace layout** optimized for VS Code integrated terminal
- **Color theming**: Inherit from terminal (support light/dark modes)
- **Status indicators**: Use Unicode symbols (✓✗⚡⚠) for quick scanning
- **Responsive**: Adapt to terminal width (min 80 columns recommended)
- **Accessibility**: Support no-color mode for accessibility

### 4. README Management

**4.1 View README**
- Display in scrollable/pageable pane
- Render Markdown with basic formatting (headers, lists, code blocks)
- Show file path and last modified timestamp

**4.2 Edit README**
- Open in user's `$EDITOR` (fallback: nano/vim)
- Reload project list after edit
- Validate README still exists after edit

**4.3 Create README**
- Offer templates based on project type:
  - **Python**: Include sections for Installation, Usage, Dependencies
  - **Node.js**: Include npm scripts, dependencies
  - **Generic**: Basic structure (Title, Description, Usage)
- Pre-populate with project metadata (name, type, detected dependencies)
- Open in `$EDITOR` for immediate editing

**4.4 Delete README**
- Require confirmation prompt
- Show preview of README content before deletion
- Permanent deletion (no trash/recycle)

### 5. Pruning Workflow

**5.1 Prune Candidates**
- Auto-flag based on classification criteria
- Show in dedicated filter view
- Sort by size (largest first) or age (oldest first)

**5.2 Deletion Process**
- **Multi-select mode**: Select multiple projects with `x`, then `p`
- **Confirmation dialog**: Show list of projects to delete with total size
- **Safety check**: Warn if project has uncommitted git changes
- **Final confirmation**: Require typing "DELETE" for projects > 100 MB or with uncommitted changes
- **Permanent deletion**: Use `rm -rf` equivalent (no archive mode per user preference)
- **Post-deletion**: Refresh project list automatically

### 6. Ignore Patterns

**6.1 Default Ignore List**

Automatically skip scanning these directories:

```
node_modules/
.venv/
venv/
env/
__pycache__/
.pytest_cache/
target/           # Rust
build/
dist/
.next/            # Next.js
.nuxt/            # Nuxt.js
.gradle/
.idea/            # JetBrains IDEs
.vscode/          # (only if contains no workspace files)
```

**6.2 Configuration File**

Location: `~/.config/lpm/.lpmignore` (or `.lpmignore` in scan root)

Format (glob patterns):
```
# Custom ignores
*/temp/
*.tmp
experimental-*
```

**6.3 Nested Git Repositories**

Configuration option: `exclude_nested_git_repos: bool` (default: `false`)
- If `true`, don't scan subdirectories that contain `.git` (treat as separate projects)
- If `false`, scan all directories (may detect subprojects)

### 7. VS Code Integration

**7.1 Open in VS Code**
- Execute `code <project_path>` to open project in new VS Code window
- Handle `code` command not found gracefully (show error message)
- Option: Detect if project is already open in current VS Code workspace

**7.2 Terminal Compatibility**
- Designed for VS Code integrated terminal (bash, zsh, fish)
- Color scheme adapts to VS Code theme (light/dark)
- Clickable file paths (if terminal supports `file://` URLs)

### 8. Advanced Features

**8.1 Search & Filter**
- Text search: Filter projects by name (regex support)
- Combined filters: e.g., "Stale + No Remote + Python"
- Save filter presets in config

**8.2 Export Inventory**
- Generate JSON report: All project metadata
- Generate CSV report: Tabular view (path, type, git remote, last modified, size)
- Use case: External analysis, backups

**8.3 Configuration**

Location: `~/.config/lpm/config.toml`

```toml
[scan]
default_path = "/home/user/projects"
exclude_nested_git_repos = false
ignore_patterns_file = "~/.config/lpm/.lpmignore"

[classification]
active_days_threshold = 30
dormant_days_threshold = 180
prunable_min_size_mb = 10
prunable_max_size_mb = 1  # Tiny experiments

[ui]
color_scheme = "auto"  # auto, light, dark, none
vim_mode = true
default_filter = "all"  # all, active, stale, prunable

[integrations]
editor = "$EDITOR"  # or "nano", "vim", "code --wait"
vscode_cmd = "code"
```

## Technical Architecture

### Technology Stack
- **Language**: Python 3.10+
- **TUI Framework**: [Textual](https://textual.textualize.io/)
- **Package Manager**: uv (recommended) or poetry
- **Dependencies**:
  - `textual` - TUI framework
  - `gitpython` - Git repository introspection
  - `rich` - Terminal formatting (used by Textual)
  - `toml` - Configuration parsing

### Data Model

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

class ProjectType(Enum):
    PYTHON = "Python"
    NODEJS = "Node.js"
    RUST = "Rust"
    GO = "Go"
    JAVA = "Java"
    PHP = "PHP"
    CSHARP = "C#/.NET"
    RUBY = "Ruby"
    UNKNOWN = "Unknown"

class GitStatus(Enum):
    CLEAN = "clean"
    DIRTY = "dirty"           # Uncommitted changes
    UNPUSHED = "unpushed"     # Commits ahead of remote
    NO_REMOTE = "no_remote"

class Classification(Enum):
    ACTIVE = "Active"
    WIP = "Work-in-Progress"
    DORMANT = "Dormant"
    STALE = "Stale"

@dataclass
class Project:
    path: Path
    name: str
    has_git: bool
    git_remote: Optional[str]
    git_status: Optional[GitStatus]
    readme_path: Optional[Path]
    project_type: ProjectType
    last_modified: datetime
    size_mb: float
    classification: Classification
    is_prunable: bool
```

### Module Structure

```
lpm/
├── __init__.py
├── __main__.py           # Entry point
├── app.py                # Main Textual app
├── scanner.py            # Directory scanning logic
├── project.py            # Project data model
├── git_utils.py          # Git introspection
├── readme_manager.py     # README CRUD operations
├── config.py             # Configuration loading
├── filters.py            # Project filtering logic
└── widgets/
    ├── __init__.py
    ├── project_list.py   # Project list widget
    ├── detail_pane.py    # Project detail view
    ├── filter_bar.py     # Filter selector
    └── readme_viewer.py  # README display widget
```

### Performance Considerations

- **Async scanning**: Use `asyncio` for directory traversal to avoid blocking UI
- **Lazy loading**: Load project details on-demand (expand action)
- **Caching**: Cache scan results with invalidation on manual refresh
- **Parallel processing**: Scan multiple subdirectories concurrently
- **Size calculation**: Option to skip for faster initial scan

## Success Criteria

1. **Project Discovery**: Accurately detects 100% of projects with git repos or type manifests
2. **Performance**: Scans 1000+ projects in < 30 seconds
3. **Usability**: Users can identify prunable projects within 1 minute of launch
4. **Reliability**: No false positives in pruning suggestions (only stale + no remote)
5. **Integration**: Seamlessly opens projects in VS Code when `code` command available

## Future Enhancements (Out of Scope for v1)

- Cloud sync detection (last push date, behind/ahead commit count)
- GitHub/Bitbucket API integration (check if remote repo still exists)
- Automatic archiving (tar.gz) before deletion option
- Project tagging system (work, personal, experiments)
- Dependency vulnerability scanning
- Disk space visualization (treemap of project sizes)
- Integration with `tmux` for session management
- Web UI companion for remote browsing
