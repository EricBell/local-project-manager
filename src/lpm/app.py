"""Main Textual TUI application."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static

from .config import Config
from .project import Classification, Project
from .readme_manager import create_readme, delete_readme, view_readme
from .scanner import scan_for_projects


class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog for confirmations."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Container {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }

    ConfirmDialog Label {
        width: 100%;
        content-align: center middle;
        padding: 1;
    }

    ConfirmDialog Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }

    ConfirmDialog Button {
        margin: 0 2;
    }
    """

    def __init__(self, message: str, title: str = "Confirm"):
        super().__init__()
        self.message = message
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Container():
            yield Label(f"[b]{self.title}[/b]")
            yield Label(self.message)
            with Horizontal():
                yield Button("Yes", variant="error", id="yes")
                yield Button("No", variant="primary", id="no")

    @on(Button.Pressed, "#yes")
    def on_yes(self):
        """Handle Yes button."""
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def on_no(self):
        """Handle No button."""
        self.dismiss(False)


class ReadmeViewer(ModalScreen):
    """Modal screen for viewing README content."""

    DEFAULT_CSS = """
    ReadmeViewer {
        align: center middle;
    }

    ReadmeViewer > Container {
        width: 90%;
        height: 90%;
        border: thick $background 80%;
        background: $surface;
    }

    ReadmeViewer VerticalScroll {
        width: 100%;
        height: 1fr;
        padding: 1;
    }

    ReadmeViewer Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
        dock: bottom;
    }
    """

    def __init__(self, content: str, title: str = "README"):
        super().__init__()
        self.content = content
        self.title = title

    def compose(self) -> ComposeResult:
        """Compose the README viewer."""
        with Container():
            yield Label(f"[b]{self.title}[/b]")
            with VerticalScroll():
                yield Static(self.content)
            with Horizontal():
                yield Button("Close", variant="primary", id="close")

    @on(Button.Pressed, "#close")
    def on_close(self):
        """Handle Close button."""
        self.dismiss()


class LocalProjectManagerApp(App):
    """Local Project Manager TUI Application."""

    CSS = """
    DataTable {
        height: 1fr;
    }

    #summary {
        height: 3;
        background: $boost;
        padding: 1;
    }

    #filter-bar {
        height: 3;
        background: $panel;
        padding: 1;
    }

    #actions {
        height: 5;
        background: $panel;
        padding: 1;
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("v", "view_readme", "View README"),
        Binding("c", "create_readme", "Create README"),
        Binding("d", "delete_readme", "Delete README"),
        Binding("p", "prune_project", "Prune Project"),
        Binding("o", "open_vscode", "Open in VS Code"),
        Binding("f", "cycle_filter", "Filter"),
        Binding("?", "help", "Help"),
    ]

    def __init__(self, scan_path: Path, projects: list[Project]):
        super().__init__()
        self.config = Config.load()
        self.projects: list[Project] = projects
        self.current_filter = "all"
        self.scan_path = scan_path

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Label("Loading projects...", id="summary"),
            Label("Filter: All Projects", id="filter-bar"),
            DataTable(),
            Label("Actions: [b]\\[V][/b]iew [b]\\[C][/b]reate [b]\\[D][/b]elete README | [b]\\[P][/b]rune | [b]\\[O][/b]pen in VS Code | [b]\\[R][/b]efresh | [b]\\[Q][/b]uit", id="actions"),
            id="main"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the application on mount."""
        table = self.query_one(DataTable)
        table.cursor_type = "row"

        # Add columns
        table.add_columns("Name", "Type", "Git", "Remote", "Age", "Size", "Status")

        # Populate table with pre-scanned projects
        self.update_table()

    def action_refresh(self) -> None:
        """Refresh the project list."""
        self.projects = []
        table = self.query_one(DataTable)
        table.clear()

        # Update summary
        summary = self.query_one("#summary", Label)
        summary.update("Scanning for projects...")

        # Scan for projects (no progress callback for in-TUI refresh)
        ignore_patterns = self.config.load_ignore_patterns(self.scan_path)
        self.projects = scan_for_projects(
            scan_path=self.scan_path,
            ignore_patterns=ignore_patterns,
            active_threshold=self.config.classification.active_days_threshold,
            dormant_threshold=self.config.classification.dormant_days_threshold,
            prunable_min_size_mb=self.config.classification.prunable_min_size_mb,
            prunable_max_size_mb=self.config.classification.prunable_max_size_mb,
            progress_callback=None,
        )

        # Apply current filter and populate table
        self.update_table()

    def update_table(self) -> None:
        """Update table with filtered projects."""
        table = self.query_one(DataTable)
        table.clear()

        # Filter projects
        filtered_projects = self.filter_projects()

        # Populate table
        for project in filtered_projects:
            git_icon = "✓" if project.has_git else "✗"
            remote_icon = "✓" if project.git_remote else "✗"

            table.add_row(
                project.name,
                project.project_type.value,
                git_icon,
                remote_icon,
                project.age_display(),
                f"{project.size_mb:.1f}MB",
                project.classification.value,
                key=str(project.path),
            )

        # Update summary
        summary_text = self.get_summary_text()
        summary = self.query_one("#summary", Label)
        summary.update(summary_text)

        # Update filter bar
        filter_bar = self.query_one("#filter-bar", Label)
        filter_bar.update(f"Filter: {self.current_filter.title()}")

    def filter_projects(self) -> list[Project]:
        """Filter projects based on current filter."""
        if self.current_filter == "all":
            return self.projects
        elif self.current_filter == "active":
            return [p for p in self.projects if p.classification == Classification.ACTIVE]
        elif self.current_filter == "wip":
            return [p for p in self.projects if p.classification == Classification.WIP]
        elif self.current_filter == "dormant":
            return [p for p in self.projects if p.classification == Classification.DORMANT]
        elif self.current_filter == "stale":
            return [p for p in self.projects if p.classification == Classification.STALE]
        elif self.current_filter == "prunable":
            return [p for p in self.projects if p.is_prunable]
        elif self.current_filter == "no_remote":
            return [p for p in self.projects if p.git_remote is None]
        elif self.current_filter == "no_readme":
            return [p for p in self.projects if p.readme_path is None]
        else:
            return self.projects

    def get_summary_text(self) -> str:
        """Get summary text for header."""
        total = len(self.projects)
        active = len([p for p in self.projects if p.classification == Classification.ACTIVE])
        dormant = len([p for p in self.projects if p.classification == Classification.DORMANT])
        stale = len([p for p in self.projects if p.classification == Classification.STALE])
        prunable = len([p for p in self.projects if p.is_prunable])

        return f"Projects: {total} | Active: {active} | Dormant: {dormant} | Stale: {stale} | Prunable: {prunable}"

    def action_cycle_filter(self) -> None:
        """Cycle through available filters."""
        filters = ["all", "active", "wip", "dormant", "stale", "prunable", "no_remote", "no_readme"]
        current_index = filters.index(self.current_filter)
        self.current_filter = filters[(current_index + 1) % len(filters)]
        self.update_table()

    def get_selected_project(self) -> Project | None:
        """Get currently selected project."""
        table = self.query_one(DataTable)
        if table.cursor_row is None or table.cursor_row < 0:
            return None

        # Check if table has any rows
        if table.row_count == 0:
            return None

        row_key = table.get_row_at(table.cursor_row)[0]
        project_path = Path(row_key)

        for project in self.projects:
            if project.path == project_path:
                return project

        return None

    def action_view_readme(self) -> None:
        """View README for selected project."""
        project = self.get_selected_project()
        if project is None:
            return

        if project.readme_path is None:
            self.notify("No README found for this project", severity="warning")
            return

        try:
            content = view_readme(project.readme_path)
            self.push_screen(ReadmeViewer(content, f"README - {project.name}"))
        except Exception as e:
            self.notify(f"Error reading README: {e}", severity="error")

    def action_create_readme(self) -> None:
        """Create README for selected project."""
        project = self.get_selected_project()
        if project is None:
            return

        if project.readme_path is not None:
            self.notify("README already exists", severity="warning")
            return

        async def confirm_and_create(confirmed: bool) -> None:
            if confirmed:
                try:
                    create_readme(project.path, project.name, project.project_type)
                    self.notify(f"README created for {project.name}", severity="information")
                    self.action_refresh()
                except Exception as e:
                    self.notify(f"Error creating README: {e}", severity="error")

        self.push_screen(
            ConfirmDialog(f"Create README for {project.name}?"),
            confirm_and_create
        )

    def action_delete_readme(self) -> None:
        """Delete README for selected project."""
        project = self.get_selected_project()
        if project is None:
            return

        if project.readme_path is None:
            self.notify("No README to delete", severity="warning")
            return

        async def confirm_and_delete(confirmed: bool) -> None:
            if confirmed:
                try:
                    delete_readme(project.readme_path)
                    self.notify(f"README deleted for {project.name}", severity="information")
                    self.action_refresh()
                except Exception as e:
                    self.notify(f"Error deleting README: {e}", severity="error")

        self.push_screen(
            ConfirmDialog(f"Delete README for {project.name}?", "Confirm Delete"),
            confirm_and_delete
        )

    def action_prune_project(self) -> None:
        """Prune (delete) selected project."""
        project = self.get_selected_project()
        if project is None:
            return

        warning = f"PERMANENTLY DELETE {project.name}?\n\nPath: {project.path}\nSize: {project.size_mb:.1f}MB"

        if project.has_git and project.git_status and project.git_status.value in ["dirty", "unpushed"]:
            warning += "\n\n⚠ WARNING: Project has uncommitted or unpushed changes!"

        async def confirm_and_prune(confirmed: bool) -> None:
            if confirmed:
                try:
                    shutil.rmtree(project.path)
                    self.notify(f"Project {project.name} deleted", severity="information")
                    self.action_refresh()
                except Exception as e:
                    self.notify(f"Error deleting project: {e}", severity="error")

        self.push_screen(
            ConfirmDialog(warning, "⚠ PERMANENT DELETE"),
            confirm_and_prune
        )

    def action_open_vscode(self) -> None:
        """Open selected project in VS Code."""
        project = self.get_selected_project()
        if project is None:
            return

        vscode_cmd = self.config.integrations.vscode_cmd

        try:
            subprocess.run([vscode_cmd, str(project.path)], check=True)
            self.notify(f"Opening {project.name} in VS Code", severity="information")
        except FileNotFoundError:
            self.notify(f"VS Code command '{vscode_cmd}' not found", severity="error")
        except subprocess.CalledProcessError as e:
            self.notify(f"Error opening VS Code: {e}", severity="error")

    def action_help(self) -> None:
        """Show help information."""
        help_text = """
[b]Keyboard Shortcuts[/b]

[b]Navigation:[/b]
  ↑/↓ or k/j - Move selection up/down
  PgUp/PgDn - Page up/down
  Home/End - First/last project

[b]Actions:[/b]
  v - View README
  c - Create README
  d - Delete README
  p - Prune (delete) project
  o - Open in VS Code
  r - Refresh project list
  f - Cycle through filters

[b]Filters:[/b]
  All, Active, WIP, Dormant, Stale,
  Prunable, No Remote, No README

[b]Other:[/b]
  ? - Show this help
  q - Quit application
"""
        self.push_screen(ReadmeViewer(help_text, "Help"))

    def on_key(self, event: Key) -> None:
        """Handle key events for application shortcuts."""
        key_to_action = {
            "v": self.action_view_readme,
            "c": self.action_create_readme,
            "d": self.action_delete_readme,
            "p": self.action_prune_project,
            "o": self.action_open_vscode,
            "f": self.action_cycle_filter,
            "r": self.action_refresh,
            "question_mark": self.action_help,
        }

        if event.key in key_to_action:
            key_to_action[event.key]()
            event.prevent_default()


def display_scan_results(projects: list[Project]) -> None:
    """Display scan results in terminal before TUI launch."""
    print(f"\nScan complete! Found {len(projects)} projects.")

    # Split projects by README presence
    with_readme = [p for p in projects if p.readme_path is not None]
    without_readme = [p for p in projects if p.readme_path is None]

    if with_readme:
        print(f"\nProjects with READMEs ({len(with_readme)}):")
        for project in sorted(with_readme, key=lambda p: str(p.path)):
            print(f"  • {project.readme_path}")

    if without_readme:
        print(f"\nProjects without READMEs ({len(without_readme)}):")
        for project in sorted(without_readme, key=lambda p: str(p.path)):
            print(f"  • {project.path}")

    print()  # Empty line for readability


def wait_for_user_input() -> bool:
    """Wait for user to press ENTER or 'q'. Returns True to continue, False to quit."""
    # Check if stdin is a tty (interactive)
    if not sys.stdin.isatty():
        # Non-interactive mode (piped input, etc.) - proceed automatically
        print("Non-interactive mode detected. Launching TUI...")
        return True

    try:
        import termios
        import tty

        print("Press ENTER to launch TUI, or 'q' to quit: ", end='', flush=True)

        # Get single character input without waiting for enter
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        print()  # New line after input

        if char.lower() == 'q':
            return False
        # Accept enter (newline) or any other key to continue
        return True

    except (ImportError, AttributeError, OSError):
        # Fallback for Windows or systems without termios, or non-tty
        try:
            response = input("Press ENTER to launch TUI, or 'q' to quit: ").strip().lower()
            return response != 'q'
        except (EOFError, OSError):
            # Can't get input, proceed anyway
            return True


def main():
    """Entry point for the application."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Local Project Manager - TUI for managing local development projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Keyboard Shortcuts:
  ↑/↓, k/j  - Navigate project list
  v         - View README
  c         - Create README
  d         - Delete README
  p         - Prune (delete) project
  o         - Open in VS Code
  f         - Cycle filters
  r         - Refresh
  ?         - Help
  q         - Quit

Filters: All, Active, WIP, Dormant, Stale, Prunable, No Remote, No README

Note: This is a TUI application. Press Ctrl+C to exit if needed, then run 'reset' if your terminal looks broken.
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Local Project Manager v0.1.0"
    )

    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Path to scan for projects (default: current directory)"
    )

    args = parser.parse_args()

    # Phase 1: Pre-TUI Scan
    from pathlib import Path
    scan_path = Path(args.path).resolve() if args.path else Path.cwd()

    print("Local Project Manager - Scanning for projects...")
    print(f"Scan path: {scan_path}\n")
    sys.stdout.flush()

    # Progress callback to show scanning progress
    def progress_callback(current_path: Path, project_count: int) -> None:
        print(f"  [{project_count}] {current_path}")
        sys.stdout.flush()

    # Perform the scan
    config = Config.load()
    ignore_patterns = config.load_ignore_patterns(scan_path)

    try:
        projects = scan_for_projects(
            scan_path=scan_path,
            ignore_patterns=ignore_patterns,
            active_threshold=config.classification.active_days_threshold,
            dormant_threshold=config.classification.dormant_days_threshold,
            prunable_min_size_mb=config.classification.prunable_min_size_mb,
            prunable_max_size_mb=config.classification.prunable_max_size_mb,
            progress_callback=progress_callback,
        )
    except KeyboardInterrupt:
        print("\n\nScan cancelled by user.")
        return
    except Exception as e:
        print(f"\n\nError during scan: {e}", file=sys.stderr)
        return

    # Display results
    display_scan_results(projects)

    # Wait for user input
    if not wait_for_user_input():
        print("Exiting without launching TUI.")
        return

    # Phase 2: Launch TUI with pre-scanned data
    app = LocalProjectManagerApp(scan_path, projects)

    try:
        app.run()
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
    except Exception as e:
        # Ensure terminal is reset on any error
        print(f"\nError: {e}", file=sys.stderr)
        print("If your terminal looks broken, run: reset", file=sys.stderr)
        raise
    finally:
        # Try to restore terminal state
        try:
            os.system("stty sane 2>/dev/null")
        except:
            pass


if __name__ == "__main__":
    main()
