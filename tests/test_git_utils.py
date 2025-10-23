"""Tests for git utilities."""

import tempfile
from pathlib import Path

import pytest
from git import Repo

from lpm.git_utils import get_git_info
from lpm.project import GitStatus


class TestGetGitInfo:
    """Tests for get_git_info function."""

    def test_no_git_directory(self):
        """Test project without .git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is False
            assert remote_url is None
            assert git_status is None

    def test_git_repo_with_no_remote(self):
        """Test git repo with no remote configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Initialize git repo
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert remote_url is None
            assert git_status == GitStatus.NO_REMOTE

    def test_git_repo_with_origin_remote(self):
        """Test git repo with origin remote configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Initialize git repo
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add remote
            repo.create_remote("origin", "https://github.com/user/test.git")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert remote_url == "https://github.com/user/test.git"
            # No tracking branch set, so should be NO_REMOTE
            assert git_status == GitStatus.NO_REMOTE

    def test_git_repo_with_non_origin_remote(self):
        """Test git repo with remote other than origin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Initialize git repo
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add non-origin remote
            repo.create_remote("upstream", "https://github.com/upstream/test.git")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert remote_url == "https://github.com/upstream/test.git"
            assert git_status == GitStatus.NO_REMOTE

    def test_git_repo_clean_status(self):
        """Test git repo with clean working directory and tracking branch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bare repo to act as remote
            remote_path = Path(tmpdir) / "remote"
            remote_path.mkdir()
            remote_repo = Repo.init(remote_path, bare=True)

            # Clone from the bare repo
            project_path = Path(tmpdir) / "project"
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add remote and push
            repo.create_remote("origin", str(remote_path))
            repo.git.push("--set-upstream", "origin", "master")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert remote_url == str(remote_path)
            assert git_status == GitStatus.CLEAN

    def test_git_repo_dirty_status(self):
        """Test git repo with uncommitted changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bare repo to act as remote
            remote_path = Path(tmpdir) / "remote"
            remote_path.mkdir()
            remote_repo = Repo.init(remote_path, bare=True)

            # Clone from the bare repo
            project_path = Path(tmpdir) / "project"
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add remote and push
            repo.create_remote("origin", str(remote_path))
            repo.git.push("--set-upstream", "origin", "master")

            # Make uncommitted changes
            test_file.write_text("modified")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert remote_url == str(remote_path)
            assert git_status == GitStatus.DIRTY

    def test_git_repo_dirty_status_untracked_files(self):
        """Test git repo with untracked files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bare repo to act as remote
            remote_path = Path(tmpdir) / "remote"
            remote_path.mkdir()
            remote_repo = Repo.init(remote_path, bare=True)

            # Clone from the bare repo
            project_path = Path(tmpdir) / "project"
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add remote and push
            repo.create_remote("origin", str(remote_path))
            repo.git.push("--set-upstream", "origin", "master")

            # Add untracked file
            untracked_file = project_path / "untracked.txt"
            untracked_file.write_text("untracked")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert git_status == GitStatus.DIRTY

    def test_git_repo_unpushed_commits(self):
        """Test git repo with commits ahead of remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a bare repo to act as remote
            remote_path = Path(tmpdir) / "remote"
            remote_path.mkdir()
            remote_repo = Repo.init(remote_path, bare=True)

            # Clone from the bare repo
            project_path = Path(tmpdir) / "project"
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add remote and push
            repo.create_remote("origin", str(remote_path))
            repo.git.push("--set-upstream", "origin", "master")

            # Create a new commit that hasn't been pushed
            test_file.write_text("new content")
            repo.index.add(["test.txt"])
            repo.index.commit("Second commit")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            assert git_status == GitStatus.UNPUSHED

    def test_git_repo_prefer_origin_remote(self):
        """Test that origin remote is preferred when multiple remotes exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Initialize git repo
            repo = Repo.init(project_path)

            # Create initial commit
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add multiple remotes (upstream first, origin second)
            repo.create_remote("upstream", "https://github.com/upstream/test.git")
            repo.create_remote("origin", "https://github.com/user/test.git")

            has_git, remote_url, git_status = get_git_info(project_path)

            assert has_git is True
            # Should prefer origin
            assert remote_url == "https://github.com/user/test.git"

    def test_corrupted_git_directory(self):
        """Test handling of corrupted .git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create .git directory but don't initialize properly
            git_dir = project_path / ".git"
            git_dir.mkdir()
            (git_dir / "invalid").write_text("corrupted")

            has_git, remote_url, git_status = get_git_info(project_path)

            # Should detect .git exists but return None for metadata
            assert has_git is True
            assert remote_url is None
            assert git_status is None
