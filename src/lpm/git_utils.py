"""Git repository introspection utilities."""

from pathlib import Path
from typing import Optional, Tuple

from git import GitCommandError, InvalidGitRepositoryError, Repo

from .project import GitStatus


def get_git_info(project_path: Path) -> Tuple[bool, Optional[str], Optional[GitStatus]]:
    """
    Extract git information from a project directory.

    Returns:
        Tuple of (has_git, remote_url, git_status)
    """
    git_dir = project_path / ".git"

    if not git_dir.exists():
        return False, None, None

    try:
        repo = Repo(project_path)

        # Get remote URL (prefer origin)
        remote_url = None
        if repo.remotes:
            if "origin" in [r.name for r in repo.remotes]:
                origin = repo.remote("origin")
                if origin.urls:
                    remote_url = next(origin.urls, None)
            else:
                # Use first available remote
                first_remote = repo.remotes[0]
                if first_remote.urls:
                    remote_url = next(first_remote.urls, None)

        # Determine git status
        if remote_url is None:
            git_status = GitStatus.NO_REMOTE
        elif repo.is_dirty(untracked_files=True):
            git_status = GitStatus.DIRTY
        else:
            # Check if there are unpushed commits
            try:
                # Get current branch
                if repo.head.is_detached:
                    git_status = GitStatus.CLEAN
                else:
                    current_branch = repo.active_branch
                    tracking_branch = current_branch.tracking_branch()

                    if tracking_branch is None:
                        # Local branch with no upstream
                        git_status = GitStatus.NO_REMOTE
                    else:
                        # Check if ahead of remote
                        commits_ahead = list(
                            repo.iter_commits(f"{tracking_branch}..{current_branch}")
                        )
                        if commits_ahead:
                            git_status = GitStatus.UNPUSHED
                        else:
                            git_status = GitStatus.CLEAN
            except (GitCommandError, ValueError):
                git_status = GitStatus.CLEAN

        return True, remote_url, git_status

    except (InvalidGitRepositoryError, GitCommandError) as e:
        # .git exists but is corrupted/invalid
        return True, None, None
