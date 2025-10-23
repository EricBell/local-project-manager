"""Tests for directory scanner (TDD)."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from git import Repo

from lpm.project import Classification, ProjectType
from lpm.scanner import (
    detect_project_type,
    get_directory_size,
    get_last_modified,
    scan_for_projects,
    should_ignore_directory,
)


class TestDetectProjectType:
    """Tests for project type detection."""

    def test_detect_python_pyproject_toml(self):
        """Test detection of Python project via pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "pyproject.toml").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    def test_detect_python_setup_py(self):
        """Test detection of Python project via setup.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "setup.py").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    def test_detect_python_requirements_txt(self):
        """Test detection of Python project via requirements.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "requirements.txt").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON

    def test_detect_nodejs(self):
        """Test detection of Node.js project via package.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "package.json").write_text("{}")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.NODEJS

    def test_detect_rust(self):
        """Test detection of Rust project via Cargo.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "Cargo.toml").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.RUST

    def test_detect_go(self):
        """Test detection of Go project via go.mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "go.mod").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.GO

    def test_detect_java_pom_xml(self):
        """Test detection of Java project via pom.xml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "pom.xml").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.JAVA

    def test_detect_java_build_gradle(self):
        """Test detection of Java project via build.gradle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "build.gradle").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.JAVA

    def test_detect_php(self):
        """Test detection of PHP project via composer.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "composer.json").write_text("{}")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.PHP

    def test_detect_ruby(self):
        """Test detection of Ruby project via Gemfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "Gemfile").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.RUBY

    def test_detect_unknown(self):
        """Test that unknown projects return UNKNOWN type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "somefile.txt").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.UNKNOWN

    def test_detect_python_priority_over_unknown(self):
        """Test Python detection has priority when multiple files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "pyproject.toml").write_text("")
            (project_path / "random.txt").write_text("")

            project_type = detect_project_type(project_path)
            assert project_type == ProjectType.PYTHON


class TestShouldIgnoreDirectory:
    """Tests for directory ignore logic."""

    def test_should_ignore_node_modules(self):
        """Test that node_modules is ignored."""
        assert should_ignore_directory("node_modules", ["node_modules"])

    def test_should_ignore_venv(self):
        """Test that venv directories are ignored."""
        ignore_patterns = [".venv", "venv", "env"]
        assert should_ignore_directory(".venv", ignore_patterns)
        assert should_ignore_directory("venv", ignore_patterns)
        assert should_ignore_directory("env", ignore_patterns)

    def test_should_ignore_pycache(self):
        """Test that __pycache__ is ignored."""
        assert should_ignore_directory("__pycache__", ["__pycache__"])

    def test_should_not_ignore_normal_directory(self):
        """Test that normal directories are not ignored."""
        ignore_patterns = ["node_modules", ".venv"]
        assert not should_ignore_directory("src", ignore_patterns)
        assert not should_ignore_directory("tests", ignore_patterns)

    def test_should_ignore_case_sensitive(self):
        """Test that ignore patterns are case-sensitive."""
        ignore_patterns = ["node_modules"]
        assert should_ignore_directory("node_modules", ignore_patterns)
        # This is case-sensitive
        assert not should_ignore_directory("Node_Modules", ignore_patterns)


class TestGetDirectorySize:
    """Tests for directory size calculation."""

    def test_empty_directory(self):
        """Test size of empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            size_mb = get_directory_size(Path(tmpdir))
            assert size_mb == 0.0

    def test_directory_with_single_file(self):
        """Test size calculation with single file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create 1MB file
            (project_path / "file.txt").write_bytes(b"x" * 1024 * 1024)

            size_mb = get_directory_size(project_path)
            assert 0.9 < size_mb < 1.1  # Allow for filesystem overhead

    def test_directory_with_multiple_files(self):
        """Test size calculation with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            # Create multiple files totaling ~2MB
            (project_path / "file1.txt").write_bytes(b"x" * 1024 * 1024)
            (project_path / "file2.txt").write_bytes(b"y" * 1024 * 1024)

            size_mb = get_directory_size(project_path)
            assert 1.9 < size_mb < 2.1

    def test_directory_with_subdirectories(self):
        """Test size calculation includes subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            subdir = project_path / "subdir"
            subdir.mkdir()

            (project_path / "file.txt").write_bytes(b"x" * 512 * 1024)
            (subdir / "file2.txt").write_bytes(b"y" * 512 * 1024)

            size_mb = get_directory_size(project_path)
            assert 0.9 < size_mb < 1.1  # Total ~1MB


class TestGetLastModified:
    """Tests for last modified timestamp detection."""

    def test_empty_directory(self):
        """Test last modified for empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            last_modified = get_last_modified(Path(tmpdir))
            # Should return a recent timestamp (directory creation time)
            assert isinstance(last_modified, datetime)
            assert (datetime.now() - last_modified).total_seconds() < 60

    def test_directory_with_files(self):
        """Test last modified finds most recent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create file and modify its timestamp
            old_file = project_path / "old.txt"
            old_file.write_text("old")

            # Sleep not needed - we'll manually set timestamps
            import os
            import time

            # Set old file to 1 day ago
            old_time = (datetime.now() - timedelta(days=1)).timestamp()
            os.utime(old_file, (old_time, old_time))

            # Create new file
            new_file = project_path / "new.txt"
            new_file.write_text("new")

            last_modified = get_last_modified(project_path)

            # Should be close to now (new file time)
            assert (datetime.now() - last_modified).total_seconds() < 60

    def test_directory_with_subdirectories(self):
        """Test last modified searches subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            subdir = project_path / "subdir"
            subdir.mkdir()

            # Create file in root
            root_file = project_path / "root.txt"
            root_file.write_text("root")

            import os

            old_time = (datetime.now() - timedelta(days=2)).timestamp()
            os.utime(root_file, (old_time, old_time))

            # Create newer file in subdirectory
            sub_file = subdir / "sub.txt"
            sub_file.write_text("sub")

            last_modified = get_last_modified(project_path)

            # Should find the newer file in subdirectory
            assert (datetime.now() - last_modified).total_seconds() < 60


class TestScanForProjects:
    """Tests for main scanning function."""

    def test_scan_empty_directory(self):
        """Test scanning empty directory returns no projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])
            assert len(projects) == 0

    def test_scan_single_project_with_git(self):
        """Test scanning detects single git project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test-project"
            project_path.mkdir()

            # Initialize git repo
            repo = Repo.init(project_path)
            test_file = project_path / "test.txt"
            test_file.write_text("test")
            repo.index.add(["test.txt"])
            repo.index.commit("Initial commit")

            # Add project type marker
            (project_path / "package.json").write_text("{}")

            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])

            assert len(projects) == 1
            assert projects[0].name == "test-project"
            assert projects[0].has_git is True
            assert projects[0].project_type == ProjectType.NODEJS

    def test_scan_project_with_readme(self):
        """Test scanning detects README files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test-project"
            project_path.mkdir()

            # Create README
            readme = project_path / "README.md"
            readme.write_text("# Test Project")

            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])

            assert len(projects) == 1
            assert projects[0].readme_path == readme

    def test_scan_ignores_specified_directories(self):
        """Test that specified directories are ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project
            project_path = Path(tmpdir) / "project"
            project_path.mkdir()
            (project_path / "README.md").write_text("# Project")

            # Create node_modules that should be ignored
            node_modules = project_path / "node_modules"
            node_modules.mkdir()
            (node_modules / "README.md").write_text("# Should be ignored")

            projects = scan_for_projects(Path(tmpdir), ignore_patterns=["node_modules"])

            # Should find project but not node_modules
            assert len(projects) == 1
            assert projects[0].name == "project"

    def test_scan_multiple_projects(self):
        """Test scanning detects multiple projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple projects
            for i in range(3):
                project_path = Path(tmpdir) / f"project-{i}"
                project_path.mkdir()
                (project_path / "README.md").write_text(f"# Project {i}")

            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])

            assert len(projects) == 3
            project_names = {p.name for p in projects}
            assert project_names == {"project-0", "project-1", "project-2"}

    def test_scan_nested_projects(self):
        """Test scanning finds nested project directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            parent = Path(tmpdir) / "parent"
            parent.mkdir()
            (parent / "README.md").write_text("# Parent")

            child = parent / "child"
            child.mkdir()
            (child / "README.md").write_text("# Child")

            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])

            # Should find both parent and child
            assert len(projects) == 2
            project_names = {p.name for p in projects}
            assert "parent" in project_names
            assert "child" in project_names

    def test_scan_with_progress_callback(self):
        """Test that progress callback is called during scanning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple projects
            for i in range(3):
                project_path = Path(tmpdir) / f"project-{i}"
                project_path.mkdir()
                (project_path / "README.md").write_text(f"# Project {i}")

            # Track progress callback invocations
            callback_calls = []

            def progress_callback(current_path: Path, project_count: int):
                callback_calls.append((str(current_path), project_count))

            projects = scan_for_projects(
                Path(tmpdir),
                ignore_patterns=[],
                progress_callback=progress_callback
            )

            # Progress callback should have been called
            assert len(callback_calls) > 0
            assert len(projects) == 3

            # Check that callback received valid paths and counts
            for path, count in callback_calls:
                assert isinstance(path, str)
                assert isinstance(count, int)
                assert count >= 0

    def test_scan_without_progress_callback(self):
        """Test that scanning works without progress callback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "project"
            project_path.mkdir()
            (project_path / "README.md").write_text("# Project")

            # Should work fine with no progress_callback
            projects = scan_for_projects(Path(tmpdir), ignore_patterns=[])

            assert len(projects) == 1
            assert projects[0].name == "project"
