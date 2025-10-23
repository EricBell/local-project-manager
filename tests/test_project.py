"""Tests for project data models and methods."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from lpm.project import Classification, GitStatus, Project, ProjectType


class TestProjectType:
    """Tests for ProjectType enum."""

    def test_all_types_exist(self):
        """Test all expected project types are defined."""
        assert ProjectType.PYTHON.value == "Python"
        assert ProjectType.NODEJS.value == "Node.js"
        assert ProjectType.RUST.value == "Rust"
        assert ProjectType.GO.value == "Go"
        assert ProjectType.JAVA.value == "Java"
        assert ProjectType.PHP.value == "PHP"
        assert ProjectType.CSHARP.value == "C#/.NET"
        assert ProjectType.RUBY.value == "Ruby"
        assert ProjectType.UNKNOWN.value == "Unknown"


class TestGitStatus:
    """Tests for GitStatus enum."""

    def test_all_statuses_exist(self):
        """Test all expected git statuses are defined."""
        assert GitStatus.CLEAN.value == "clean"
        assert GitStatus.DIRTY.value == "dirty"
        assert GitStatus.UNPUSHED.value == "unpushed"
        assert GitStatus.NO_REMOTE.value == "no_remote"


class TestClassification:
    """Tests for Classification enum."""

    def test_all_classifications_exist(self):
        """Test all expected classifications are defined."""
        assert Classification.ACTIVE.value == "Active"
        assert Classification.WIP.value == "Work-in-Progress"
        assert Classification.DORMANT.value == "Dormant"
        assert Classification.STALE.value == "Stale"


class TestProject:
    """Tests for Project dataclass."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        return Project(
            path=Path("/home/user/projects/test-project"),
            name="test-project",
            has_git=True,
            git_remote="https://github.com/user/test-project.git",
            git_status=GitStatus.CLEAN,
            readme_path=Path("/home/user/projects/test-project/README.md"),
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=5),
            size_mb=10.5,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )

    def test_project_creation(self, sample_project):
        """Test project can be created with all fields."""
        assert sample_project.name == "test-project"
        assert sample_project.has_git is True
        assert sample_project.git_remote == "https://github.com/user/test-project.git"
        assert sample_project.git_status == GitStatus.CLEAN
        assert sample_project.project_type == ProjectType.PYTHON
        assert sample_project.classification == Classification.ACTIVE
        assert sample_project.is_prunable is False

    def test_age_days_recent(self):
        """Test age_days for recently modified project."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=3),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_days() == 3

    def test_age_days_old(self):
        """Test age_days for old project."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=365),
            size_mb=1.0,
            classification=Classification.STALE,
            is_prunable=True,
        )
        assert project.age_days() == 365

    def test_age_display_today(self):
        """Test age_display for project modified today."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now(),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_display() == "today"

    def test_age_display_one_day(self):
        """Test age_display for project modified 1 day ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=1),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_display() == "1d ago"

    def test_age_display_days(self):
        """Test age_display for project modified multiple days ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=5),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_display() == "5d ago"

    def test_age_display_one_week(self):
        """Test age_display for project modified 1 week ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=7),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_display() == "1w ago"

    def test_age_display_weeks(self):
        """Test age_display for project modified multiple weeks ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=21),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert project.age_display() == "3w ago"

    def test_age_display_one_month(self):
        """Test age_display for project modified 1 month ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=30),
            size_mb=1.0,
            classification=Classification.DORMANT,
            is_prunable=False,
        )
        assert project.age_display() == "1mo ago"

    def test_age_display_months(self):
        """Test age_display for project modified multiple months ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=180),
            size_mb=1.0,
            classification=Classification.DORMANT,
            is_prunable=False,
        )
        assert project.age_display() == "6mo ago"

    def test_age_display_one_year(self):
        """Test age_display for project modified 1 year ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=365),
            size_mb=1.0,
            classification=Classification.STALE,
            is_prunable=True,
        )
        assert project.age_display() == "1y ago"

    def test_age_display_years(self):
        """Test age_display for project modified multiple years ago."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=730),
            size_mb=1.0,
            classification=Classification.STALE,
            is_prunable=True,
        )
        assert project.age_display() == "2y ago"

    def test_status_icon_git_project(self):
        """Test status_icon for git project."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=True,
            git_remote="https://github.com/user/test.git",
            git_status=GitStatus.CLEAN,
            readme_path=None,
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=30),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        assert "✓" in project.status_icon()

    def test_status_icon_no_git(self):
        """Test status_icon for non-git project."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            project_type=ProjectType.UNKNOWN,
            last_modified=datetime.now() - timedelta(days=30),
            size_mb=1.0,
            classification=Classification.WIP,
            is_prunable=False,
        )
        assert "✗" in project.status_icon()

    def test_status_icon_recent_activity(self):
        """Test status_icon shows lightning for recent activity."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=True,
            git_remote="https://github.com/user/test.git",
            git_status=GitStatus.CLEAN,
            readme_path=None,
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=3),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        icon = project.status_icon()
        assert "✓" in icon
        assert "⚡" in icon

    def test_status_icon_no_recent_activity(self):
        """Test status_icon doesn't show lightning for old activity."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=True,
            git_remote="https://github.com/user/test.git",
            git_status=GitStatus.CLEAN,
            readme_path=None,
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=30),
            size_mb=1.0,
            classification=Classification.DORMANT,
            is_prunable=False,
        )
        assert "⚡" not in project.status_icon()

    def test_status_icon_dirty_git(self):
        """Test status_icon shows warning for uncommitted changes."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=True,
            git_remote="https://github.com/user/test.git",
            git_status=GitStatus.DIRTY,
            readme_path=None,
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=3),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        icon = project.status_icon()
        assert "✓" in icon
        assert "⚡" in icon
        assert "⚠" in icon

    def test_status_icon_unpushed(self):
        """Test status_icon shows warning for unpushed commits."""
        project = Project(
            path=Path("/test"),
            name="test",
            has_git=True,
            git_remote="https://github.com/user/test.git",
            git_status=GitStatus.UNPUSHED,
            readme_path=None,
            project_type=ProjectType.PYTHON,
            last_modified=datetime.now() - timedelta(days=15),
            size_mb=1.0,
            classification=Classification.ACTIVE,
            is_prunable=False,
        )
        icon = project.status_icon()
        assert "✓" in icon
        assert "⚠" in icon
        assert "⚡" not in icon  # Not recent
