"""Project data model and related enums."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ProjectType(Enum):
    """Types of projects based on detected manifest files."""

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
    """Git repository status."""

    CLEAN = "clean"
    DIRTY = "dirty"           # Uncommitted changes
    UNPUSHED = "unpushed"     # Commits ahead of remote
    NO_REMOTE = "no_remote"   # No remote configured


class Classification(Enum):
    """Project health classification."""

    ACTIVE = "Active"
    WIP = "Work-in-Progress"
    DORMANT = "Dormant"
    STALE = "Stale"


@dataclass
class Project:
    """Represents a detected project with all metadata."""

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

    def age_days(self) -> int:
        """Calculate age of project in days."""
        return (datetime.now() - self.last_modified).days

    def age_display(self) -> str:
        """Human-readable age display."""
        days = self.age_days()

        if days == 0:
            return "today"
        elif days == 1:
            return "1d ago"
        elif days < 7:
            return f"{days}d ago"
        elif days < 30:
            weeks = days // 7
            return f"{weeks}w ago" if weeks > 1 else "1w ago"
        elif days < 365:
            months = days // 30
            return f"{months}mo ago" if months > 1 else "1mo ago"
        else:
            years = days // 365
            return f"{years}y ago" if years > 1 else "1y ago"

    def status_icon(self) -> str:
        """Visual status indicator."""
        icons = []

        # Git status
        if self.has_git:
            icons.append("✓")
        else:
            icons.append("✗")

        # Activity
        if self.age_days() < 7:
            icons.append("⚡")

        # Uncommitted/unpushed changes
        if self.git_status in (GitStatus.DIRTY, GitStatus.UNPUSHED):
            icons.append("⚠")

        return " ".join(icons)
