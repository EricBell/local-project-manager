# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Project Manager is a Python TUI (Text User Interface) application built with Textual that helps identify, manage, and prune local projects by scanning directories for README files.

## Project Status

**IMPLEMENTED!** The project is now fully functional with:
- ✅ Complete TUI application built with Textual
- ✅ Multi-signal project detection (git, type, README, activity)
- ✅ Project classification and health scoring
- ✅ README management (view, create, delete)
- ✅ Pruning workflow with confirmations
- ✅ VS Code integration
- ✅ 91 passing unit tests with 90% code coverage
- ✅ Full TDD implementation for core modules

## Documentation

See [PRD.md](PRD.md) for detailed product requirements and specifications.

## Planned Architecture

1. **TUI Framework**: Python with Textual library
2. **Core Functionality**:
   - Recursive directory scanning (configurable starting directory)
   - README file detection (.md, .txt formats)
   - Project path identification (with and without READMEs)
   - README viewing, editing, creation, and deletion
   - Configurable ignore list (default: node_modules)
   - Subproject exclusion capability

## Usage

Run the application:

```bash
# Run from project root
uv run python main.py

# Or use the entry point
uv run lpm
```

**Keyboard Shortcuts:**
- `↑/↓` or `k/j` - Navigate projects
- `v` - View README
- `c` - Create README
- `d` - Delete README
- `p` - Prune (delete) project
- `o` - Open in VS Code
- `f` - Cycle filters
- `r` - Refresh project list
- `?` - Show help
- `q` - Quit

**Filters:** All, Active, WIP, Dormant, Stale, Prunable, No Remote, No README

## Development Setup

Dependencies are managed with `uv`:

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run the app
uv run python main.py
```

## Key Design Considerations

- **Directory Scanning**: Must support both current directory and user-specified paths with recursive subdirectory traversal
- **Ignore Patterns**: Implement configurable ignore list starting with `node_modules`, expandable to exclude subprojects
- **README Display**: Implement scrolling/paging viewer for existing README files
- **File Operations**: Support view, edit, delete for existing READMEs; create for missing ones
- **Subproject Logic**: Handle nested projects (e.g., `site2pdf/version/`, `site2pdf/todo/`) with optional exclusion

## Testing

The project has comprehensive test coverage:

- **91 tests** covering all core functionality
- **90% code coverage** across the codebase
- **TDD approach** for scanner, config, and README manager
- Test coverage includes:
  - Project data models and classification
  - Git repository introspection
  - Directory scanning and filtering
  - README file operations
  - Configuration loading

Run tests:
```bash
uv run pytest          # Run all tests
uv run pytest -v       # Verbose output
uv run pytest --cov    # With coverage report
```

## Architecture

```
src/lpm/
├── __init__.py           # Package init
├── app.py                # Main Textual TUI application
├── project.py            # Project data models & enums
├── scanner.py            # Directory scanning & detection
├── git_utils.py          # Git introspection utilities
├── config.py             # Configuration management
├── readme_manager.py     # README CRUD operations
└── widgets/              # Textual UI widgets
    └── __init__.py

tests/
├── test_project.py       # Data model tests
├── test_scanner.py       # Scanner tests (TDD)
├── test_git_utils.py     # Git utilities tests
├── test_config.py        # Configuration tests
└── test_readme_manager.py # README manager tests (TDD)
```
