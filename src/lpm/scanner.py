"""Directory scanning and project detection."""

import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

from .git_utils import get_git_info
from .project import Classification, Project, ProjectType


# Project type detection mappings
PROJECT_TYPE_MARKERS = {
    ProjectType.PYTHON: ["pyproject.toml", "setup.py", "requirements.txt"],
    ProjectType.NODEJS: ["package.json"],
    ProjectType.RUST: ["Cargo.toml"],
    ProjectType.GO: ["go.mod"],
    ProjectType.JAVA: ["pom.xml", "build.gradle"],
    ProjectType.PHP: ["composer.json"],
    ProjectType.CSHARP: [".csproj", ".sln"],
    ProjectType.RUBY: ["Gemfile"],
}

README_NAMES = ["README.md", "README.txt", "readme.md", "readme.txt", "Readme.md", "Readme.txt"]


def detect_project_type(project_path: Path) -> ProjectType:
    """
    Detect project type based on manifest files.

    Args:
        project_path: Path to project directory

    Returns:
        ProjectType enum value
    """
    for project_type, markers in PROJECT_TYPE_MARKERS.items():
        for marker in markers:
            if "*" in marker:  # Handle glob patterns like *.csproj
                if list(project_path.glob(marker)):
                    return project_type
            else:
                if (project_path / marker).exists():
                    return project_type

    return ProjectType.UNKNOWN


def should_ignore_directory(dir_name: str, ignore_patterns: List[str]) -> bool:
    """
    Check if directory should be ignored based on patterns.

    Args:
        dir_name: Name of directory
        ignore_patterns: List of patterns to ignore

    Returns:
        True if directory should be ignored
    """
    return dir_name in ignore_patterns


def get_directory_size(path: Path) -> float:
    """
    Calculate total size of directory in MB.

    Args:
        path: Path to directory

    Returns:
        Size in megabytes
    """
    total_size = 0

    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                try:
                    total_size += filepath.stat().st_size
                except (OSError, FileNotFoundError):
                    # Skip files we can't access
                    continue
    except (OSError, PermissionError):
        # Can't access directory
        return 0.0

    return total_size / (1024 * 1024)  # Convert to MB


def get_last_modified(path: Path) -> datetime:
    """
    Get the most recent modification time in directory tree.

    Args:
        path: Path to directory

    Returns:
        datetime of most recent modification
    """
    most_recent = datetime.fromtimestamp(path.stat().st_mtime)

    try:
        for dirpath, dirnames, filenames in os.walk(path):
            # Check directory modification time
            dir_path = Path(dirpath)
            try:
                dir_mtime = datetime.fromtimestamp(dir_path.stat().st_mtime)
                if dir_mtime > most_recent:
                    most_recent = dir_mtime
            except (OSError, FileNotFoundError):
                continue

            # Check file modification times
            for filename in filenames:
                filepath = dir_path / filename
                try:
                    file_mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    if file_mtime > most_recent:
                        most_recent = file_mtime
                except (OSError, FileNotFoundError):
                    continue
    except (OSError, PermissionError):
        # Can't access directory
        pass

    return most_recent


def find_readme(project_path: Path) -> Path | None:
    """
    Find README file in project directory.

    Args:
        project_path: Path to project directory

    Returns:
        Path to README file or None if not found
    """
    for readme_name in README_NAMES:
        readme_path = project_path / readme_name
        if readme_path.exists() and readme_path.is_file():
            return readme_path

    return None


def is_project_directory(path: Path) -> bool:
    """
    Determine if directory is a project (has git, README, or type marker).

    Args:
        path: Path to directory

    Returns:
        True if directory appears to be a project
    """
    # Check for .git
    if (path / ".git").exists():
        return True

    # Check for README
    if find_readme(path) is not None:
        return True

    # Check for project type markers
    if detect_project_type(path) != ProjectType.UNKNOWN:
        return True

    return False


def classify_project(
    last_modified: datetime,
    has_git_remote: bool,
    has_readme: bool,
    active_threshold: int = 30,
    dormant_threshold: int = 180,
) -> Classification:
    """
    Classify project based on age and characteristics.

    Args:
        last_modified: Last modification datetime
        has_git_remote: Whether project has git remote
        has_readme: Whether project has README
        active_threshold: Days threshold for active classification
        dormant_threshold: Days threshold for dormant classification

    Returns:
        Classification enum value
    """
    age_days = (datetime.now() - last_modified).days

    if age_days <= active_threshold:
        if has_git_remote or has_readme:
            return Classification.ACTIVE
        else:
            return Classification.WIP
    elif age_days <= dormant_threshold:
        return Classification.DORMANT
    else:
        return Classification.STALE


def is_prunable(
    classification: Classification,
    has_git_remote: bool,
    size_mb: float,
    min_size_mb: float = 10.0,
    max_size_mb: float = 1.0,
) -> bool:
    """
    Determine if project is a candidate for pruning.

    Args:
        classification: Project classification
        has_git_remote: Whether project has git remote
        size_mb: Project size in MB
        min_size_mb: Minimum size threshold for pruning
        max_size_mb: Maximum size threshold for tiny experiments

    Returns:
        True if project is prunable
    """
    if classification != Classification.STALE:
        return False

    if has_git_remote:
        return False

    # Prune if large (> min_size_mb) or tiny (< max_size_mb)
    return size_mb > min_size_mb or size_mb < max_size_mb


def scan_for_projects(
    scan_path: Path,
    ignore_patterns: List[str],
    active_threshold: int = 30,
    dormant_threshold: int = 180,
    prunable_min_size_mb: float = 10.0,
    prunable_max_size_mb: float = 1.0,
    _check_root: bool = True,
    progress_callback: Optional[Callable[[Path, int], None]] = None,
) -> List[Project]:
    """
    Recursively scan directory for projects.

    Args:
        scan_path: Root path to scan
        ignore_patterns: Directory names to ignore
        active_threshold: Days for active classification
        dormant_threshold: Days for dormant classification
        prunable_min_size_mb: Min size for pruning candidates
        prunable_max_size_mb: Max size for tiny experiments
        _check_root: Internal param to check scan_path itself (only on initial call)
        progress_callback: Optional callback function(current_path, project_count) for progress updates

    Returns:
        List of detected Project objects
    """
    projects = []

    # First, check if the scan_path itself is a project (only on initial call)
    if _check_root and is_project_directory(scan_path):
        if progress_callback:
            progress_callback(scan_path, 0)
        has_git, git_remote, git_status = get_git_info(scan_path)
        readme_path = find_readme(scan_path)
        project_type = detect_project_type(scan_path)
        last_modified = get_last_modified(scan_path)
        size_mb = get_directory_size(scan_path)

        classification = classify_project(
            last_modified=last_modified,
            has_git_remote=git_remote is not None,
            has_readme=readme_path is not None,
            active_threshold=active_threshold,
            dormant_threshold=dormant_threshold,
        )

        prunable = is_prunable(
            classification=classification,
            has_git_remote=git_remote is not None,
            size_mb=size_mb,
            min_size_mb=prunable_min_size_mb,
            max_size_mb=prunable_max_size_mb,
        )

        project = Project(
            path=scan_path,
            name=scan_path.name,
            has_git=has_git,
            git_remote=git_remote,
            git_status=git_status,
            readme_path=readme_path,
            project_type=project_type,
            last_modified=last_modified,
            size_mb=size_mb,
            classification=classification,
            is_prunable=prunable,
        )

        projects.append(project)

    # Now scan subdirectories
    try:
        for entry in os.scandir(scan_path):
            if not entry.is_dir(follow_symlinks=False):
                continue

            dir_name = entry.name
            dir_path = Path(entry.path)

            # Skip ignored directories
            if should_ignore_directory(dir_name, ignore_patterns):
                continue

            # Report progress for this directory
            if progress_callback:
                progress_callback(dir_path, len(projects))

            # Check if this directory is a project
            if is_project_directory(dir_path):
                # Extract project metadata
                has_git, git_remote, git_status = get_git_info(dir_path)
                readme_path = find_readme(dir_path)
                project_type = detect_project_type(dir_path)
                last_modified = get_last_modified(dir_path)
                size_mb = get_directory_size(dir_path)

                # Classify project
                classification = classify_project(
                    last_modified=last_modified,
                    has_git_remote=git_remote is not None,
                    has_readme=readme_path is not None,
                    active_threshold=active_threshold,
                    dormant_threshold=dormant_threshold,
                )

                # Determine if prunable
                prunable = is_prunable(
                    classification=classification,
                    has_git_remote=git_remote is not None,
                    size_mb=size_mb,
                    min_size_mb=prunable_min_size_mb,
                    max_size_mb=prunable_max_size_mb,
                )

                project = Project(
                    path=dir_path,
                    name=dir_name,
                    has_git=has_git,
                    git_remote=git_remote,
                    git_status=git_status,
                    readme_path=readme_path,
                    project_type=project_type,
                    last_modified=last_modified,
                    size_mb=size_mb,
                    classification=classification,
                    is_prunable=prunable,
                )

                projects.append(project)

            # Recursively scan subdirectories (pass _check_root=False to avoid duplicate detection)
            sub_projects = scan_for_projects(
                scan_path=dir_path,
                ignore_patterns=ignore_patterns,
                active_threshold=active_threshold,
                dormant_threshold=dormant_threshold,
                prunable_min_size_mb=prunable_min_size_mb,
                prunable_max_size_mb=prunable_max_size_mb,
                _check_root=False,
                progress_callback=progress_callback,
            )
            projects.extend(sub_projects)

    except (OSError, PermissionError):
        # Can't access directory, skip it
        pass

    return projects
