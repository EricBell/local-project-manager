"""Tests for README management (TDD)."""

import tempfile
from pathlib import Path

import pytest

from lpm.project import ProjectType
from lpm.readme_manager import (
    create_readme,
    delete_readme,
    get_readme_template,
    read_readme,
    view_readme,
)


class TestGetReadmeTemplate:
    """Tests for README template generation."""

    def test_python_template(self):
        """Test Python project README template."""
        template = get_readme_template(project_name="my-python-project", project_type=ProjectType.PYTHON)

        assert "my-python-project" in template
        assert "Installation" in template
        assert "Usage" in template
        assert "Dependencies" in template or "Requirements" in template

    def test_nodejs_template(self):
        """Test Node.js project README template."""
        template = get_readme_template(project_name="my-node-app", project_type=ProjectType.NODEJS)

        assert "my-node-app" in template
        assert "Installation" in template or "Install" in template
        assert "npm" in template.lower() or "yarn" in template.lower()

    def test_generic_template(self):
        """Test generic/unknown project README template."""
        template = get_readme_template(project_name="my-project", project_type=ProjectType.UNKNOWN)

        assert "my-project" in template
        assert "Description" in template or "About" in template
        assert "Usage" in template

    def test_template_has_markdown_headers(self):
        """Test that templates use proper Markdown headers."""
        template = get_readme_template(project_name="test", project_type=ProjectType.PYTHON)

        # Should have at least one # header
        assert "# test" in template or "#" in template


class TestCreateReadme:
    """Tests for README creation."""

    def test_create_readme_md(self):
        """Test creating README.md file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            readme_path = create_readme(
                project_path=project_path,
                project_name="test-project",
                project_type=ProjectType.PYTHON,
            )

            assert readme_path.exists()
            assert readme_path.name == "README.md"
            assert readme_path.parent == project_path

            content = readme_path.read_text()
            assert "test-project" in content

    def test_create_readme_uses_template(self):
        """Test that created README uses appropriate template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            readme_path = create_readme(
                project_path=project_path,
                project_name="node-app",
                project_type=ProjectType.NODEJS,
            )

            content = readme_path.read_text()
            assert "node-app" in content
            # Should use Node.js template
            assert "npm" in content.lower() or "yarn" in content.lower()

    def test_create_readme_does_not_overwrite_existing(self):
        """Test that creating README when one exists raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create existing README
            existing_readme = project_path / "README.md"
            existing_readme.write_text("# Existing README")

            with pytest.raises(FileExistsError):
                create_readme(
                    project_path=project_path,
                    project_name="test",
                    project_type=ProjectType.PYTHON,
                )

    def test_create_readme_in_nested_path(self):
        """Test creating README in nested project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "nested" / "project"
            project_path.mkdir(parents=True)

            readme_path = create_readme(
                project_path=project_path,
                project_name="nested-project",
                project_type=ProjectType.RUST,
            )

            assert readme_path.exists()
            assert readme_path.parent == project_path


class TestReadReadme:
    """Tests for reading README content."""

    def test_read_existing_readme(self):
        """Test reading an existing README file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            readme_path.write_text("# My Project\n\nThis is a test.")

            content = read_readme(readme_path)

            assert content == "# My Project\n\nThis is a test."

    def test_read_nonexistent_readme(self):
        """Test reading README that doesn't exist raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"

            with pytest.raises(FileNotFoundError):
                read_readme(readme_path)

    def test_read_empty_readme(self):
        """Test reading empty README file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            readme_path.write_text("")

            content = read_readme(readme_path)

            assert content == ""


class TestViewReadme:
    """Tests for viewing README (returns formatted content)."""

    def test_view_readme_returns_content(self):
        """Test that view_readme returns README content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            readme_path.write_text("# Test Project")

            content = view_readme(readme_path)

            assert "Test Project" in content

    def test_view_readme_preserves_formatting(self):
        """Test that view_readme preserves Markdown formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            markdown_content = """# My Project

## Features

- Feature 1
- Feature 2

```python
print("hello")
```
"""
            readme_path.write_text(markdown_content)

            content = view_readme(readme_path)

            assert "# My Project" in content
            assert "## Features" in content
            assert "- Feature 1" in content
            assert "```python" in content


class TestDeleteReadme:
    """Tests for README deletion."""

    def test_delete_existing_readme(self):
        """Test deleting an existing README."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            readme_path.write_text("# To be deleted")

            assert readme_path.exists()

            delete_readme(readme_path)

            assert not readme_path.exists()

    def test_delete_nonexistent_readme(self):
        """Test deleting README that doesn't exist raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"

            with pytest.raises(FileNotFoundError):
                delete_readme(readme_path)

    def test_delete_only_removes_readme(self):
        """Test that delete only removes README, not other files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            readme_path = Path(tmpdir) / "README.md"
            readme_path.write_text("# README")

            other_file = Path(tmpdir) / "other.txt"
            other_file.write_text("Keep this")

            delete_readme(readme_path)

            assert not readme_path.exists()
            assert other_file.exists()
