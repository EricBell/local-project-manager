"""Tests for the main TUI application."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.events import Key
from textual.keys import Keys
from textual.widgets import DataTable

from lpm.app import LocalProjectManagerApp
from lpm.project import Project, ProjectType, Classification


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    from datetime import datetime, timedelta
    from lpm.project import GitStatus

    return [
        Project(
            path=Path("/test/project1"),
            name="project1",
            project_type=ProjectType.PYTHON,
            classification=Classification.ACTIVE,
            has_git=True,
            git_remote="origin",
            git_status=GitStatus.CLEAN,
            readme_path=Path("/test/project1/README.md"),
            size_mb=10.5,
            last_modified=datetime.now() - timedelta(days=5),
            is_prunable=False
        ),
        Project(
            path=Path("/test/project2"),
            name="project2",
            project_type=ProjectType.NODEJS,
            classification=Classification.WIP,
            has_git=False,
            git_remote=None,
            git_status=None,
            readme_path=None,
            size_mb=25.0,
            last_modified=datetime.now() - timedelta(days=15),
            is_prunable=True
        )
    ]


@pytest.fixture
def app(sample_projects):
    """Create app instance for testing."""
    return LocalProjectManagerApp(Path("/test"), sample_projects)


class TestKeyboardHandling:
    """Test keyboard event handling."""

    def test_view_readme_key_triggers_action(self, app):
        """Test that 'v' key triggers view_readme action."""
        with patch.object(app, 'action_view_readme') as mock_action:
            # Simulate 'v' key press
            key_event = Key(key="v", character="v")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_create_readme_key_triggers_action(self, app):
        """Test that 'c' key triggers create_readme action."""
        with patch.object(app, 'action_create_readme') as mock_action:
            key_event = Key(key="c", character="c")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_delete_readme_key_triggers_action(self, app):
        """Test that 'd' key triggers delete_readme action."""
        with patch.object(app, 'action_delete_readme') as mock_action:
            key_event = Key(key="d", character="d")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_prune_project_key_triggers_action(self, app):
        """Test that 'p' key triggers prune_project action."""
        with patch.object(app, 'action_prune_project') as mock_action:
            key_event = Key(key="p", character="p")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_open_vscode_key_triggers_action(self, app):
        """Test that 'o' key triggers open_vscode action."""
        with patch.object(app, 'action_open_vscode') as mock_action:
            key_event = Key(key="o", character="o")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_cycle_filter_key_triggers_action(self, app):
        """Test that 'f' key triggers cycle_filter action."""
        with patch.object(app, 'action_cycle_filter') as mock_action:
            key_event = Key(key="f", character="f")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_refresh_key_triggers_action(self, app):
        """Test that 'r' key triggers refresh action."""
        with patch.object(app, 'action_refresh') as mock_action:
            key_event = Key(key="r", character="r")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_help_key_triggers_action(self, app):
        """Test that '?' key triggers help action."""
        with patch.object(app, 'action_help') as mock_action:
            key_event = Key(key="question_mark", character="?")
            app.on_key(key_event)
            mock_action.assert_called_once()

    def test_unknown_key_is_ignored(self, app):
        """Test that unknown keys don't trigger any actions."""
        with patch.object(app, 'action_view_readme') as mock_view, \
             patch.object(app, 'action_create_readme') as mock_create:
            key_event = Key(key="x", character="x")  # Unknown key
            app.on_key(key_event)
            mock_view.assert_not_called()
            mock_create.assert_not_called()

    def test_navigation_keys_are_passed_through(self, app):
        """Test that navigation keys (arrows, etc.) are not consumed."""
        # This test ensures that DataTable navigation still works
        navigation_keys = ["up", "down", "left", "right", "home", "end"]

        for key_name in navigation_keys:
            with patch.object(app, 'action_view_readme') as mock_action:
                key_event = Key(key=key_name, character="")
                app.on_key(key_event)
                # Navigation keys should not trigger app actions
                mock_action.assert_not_called()