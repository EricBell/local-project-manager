# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Local Project Manager is a Python TUI (Text User Interface) application built with Textual that helps identify, manage, and prune local projects by scanning directories for README files.

## Project Status

This is an early-stage project. The codebase currently contains only documentation files. No implementation code exists yet.

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

## Development Setup

When implementing this project, you will need to:

1. Initialize Python project structure with a package manager (uv, poetry, or pip with requirements.txt)
2. Add Textual as the primary dependency
3. Set up typical Python tooling (linting, formatting, testing)

## Key Design Considerations

- **Directory Scanning**: Must support both current directory and user-specified paths with recursive subdirectory traversal
- **Ignore Patterns**: Implement configurable ignore list starting with `node_modules`, expandable to exclude subprojects
- **README Display**: Implement scrolling/paging viewer for existing README files
- **File Operations**: Support view, edit, delete for existing READMEs; create for missing ones
- **Subproject Logic**: Handle nested projects (e.g., `site2pdf/version/`, `site2pdf/todo/`) with optional exclusion

## Testing

When implementing, create tests for:
- Directory traversal and filtering logic
- README file detection across multiple formats
- Ignore pattern matching
- File operations (view, edit, create, delete)
