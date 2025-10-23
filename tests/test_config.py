"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from lpm.config import (
    ClassificationConfig,
    Config,
    IntegrationsConfig,
    ScanConfig,
    UIConfig,
    DEFAULT_IGNORE_PATTERNS,
)


class TestScanConfig:
    """Tests for ScanConfig."""

    def test_default_values(self):
        """Test ScanConfig has correct defaults."""
        config = ScanConfig()
        assert config.default_path == Path.cwd()
        assert config.exclude_nested_git_repos is False
        assert config.ignore_patterns == DEFAULT_IGNORE_PATTERNS

    def test_default_ignore_patterns_contain_common_dirs(self):
        """Test default ignore patterns include common directories."""
        assert "node_modules" in DEFAULT_IGNORE_PATTERNS
        assert ".venv" in DEFAULT_IGNORE_PATTERNS
        assert "venv" in DEFAULT_IGNORE_PATTERNS
        assert "__pycache__" in DEFAULT_IGNORE_PATTERNS
        assert "target" in DEFAULT_IGNORE_PATTERNS
        assert "build" in DEFAULT_IGNORE_PATTERNS


class TestClassificationConfig:
    """Tests for ClassificationConfig."""

    def test_default_values(self):
        """Test ClassificationConfig has correct defaults."""
        config = ClassificationConfig()
        assert config.active_days_threshold == 30
        assert config.dormant_days_threshold == 180
        assert config.prunable_min_size_mb == 10.0
        assert config.prunable_max_size_mb == 1.0


class TestUIConfig:
    """Tests for UIConfig."""

    def test_default_values(self):
        """Test UIConfig has correct defaults."""
        config = UIConfig()
        assert config.color_scheme == "auto"
        assert config.vim_mode is True
        assert config.default_filter == "all"


class TestIntegrationsConfig:
    """Tests for IntegrationsConfig."""

    def test_default_values(self):
        """Test IntegrationsConfig has correct defaults."""
        config = IntegrationsConfig()
        assert config.vscode_cmd == "code"
        # editor defaults to $EDITOR or "nano"
        assert config.editor in ["nano", "vim", "vi", "emacs"] or "/" in config.editor


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self):
        """Test Config initializes with all default sub-configs."""
        config = Config()
        assert isinstance(config.scan, ScanConfig)
        assert isinstance(config.classification, ClassificationConfig)
        assert isinstance(config.ui, UIConfig)
        assert isinstance(config.integrations, IntegrationsConfig)

    def test_load_nonexistent_config(self):
        """Test loading config when file doesn't exist returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.toml"
            config = Config.load(config_path)

            # Should use defaults
            assert config.scan.default_path == Path.cwd()
            assert config.classification.active_days_threshold == 30
            assert config.ui.vim_mode is True

    def test_load_empty_config(self):
        """Test loading empty config file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("")

            config = Config.load(config_path)

            # Should use defaults
            assert config.scan.default_path == Path.cwd()
            assert config.classification.active_days_threshold == 30

    def test_load_partial_config(self):
        """Test loading config with only some values set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("""
[scan]
exclude_nested_git_repos = true

[classification]
active_days_threshold = 14
""")

            config = Config.load(config_path)

            # Custom values
            assert config.scan.exclude_nested_git_repos is True
            assert config.classification.active_days_threshold == 14

            # Defaults for non-specified values
            assert config.scan.default_path == Path.cwd()
            assert config.classification.dormant_days_threshold == 180
            assert config.ui.vim_mode is True

    def test_load_full_config(self):
        """Test loading config with all values set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text(f"""
[scan]
default_path = "{tmpdir}/projects"
exclude_nested_git_repos = true
ignore_patterns = ["custom_dir", "*.tmp"]

[classification]
active_days_threshold = 14
dormant_days_threshold = 90
prunable_min_size_mb = 50.0
prunable_max_size_mb = 0.5

[ui]
color_scheme = "dark"
vim_mode = false
default_filter = "active"

[integrations]
editor = "vim"
vscode_cmd = "code-insiders"
""")

            config = Config.load(config_path)

            # Scan config
            assert config.scan.default_path == Path(tmpdir) / "projects"
            assert config.scan.exclude_nested_git_repos is True
            # Should have both defaults and custom patterns
            assert "custom_dir" in config.scan.ignore_patterns
            assert "*.tmp" in config.scan.ignore_patterns

            # Classification config
            assert config.classification.active_days_threshold == 14
            assert config.classification.dormant_days_threshold == 90
            assert config.classification.prunable_min_size_mb == 50.0
            assert config.classification.prunable_max_size_mb == 0.5

            # UI config
            assert config.ui.color_scheme == "dark"
            assert config.ui.vim_mode is False
            assert config.ui.default_filter == "active"

            # Integrations config
            assert config.integrations.editor == "vim"
            assert config.integrations.vscode_cmd == "code-insiders"

    def test_load_ignore_patterns_from_local_file(self):
        """Test loading ignore patterns from .lpmignore in scan root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scan_root = Path(tmpdir)
            ignore_file = scan_root / ".lpmignore"
            ignore_file.write_text("""
# Comment line
node_modules
temp/
*.log
""")

            config = Config()
            patterns = config.load_ignore_patterns(scan_root)

            # Should include defaults plus custom patterns
            assert "node_modules" in patterns
            assert "temp/" in patterns
            assert "*.log" in patterns
            # Should not include comments
            assert "# Comment line" not in patterns

    def test_load_ignore_patterns_empty_lines_and_comments(self):
        """Test that empty lines and comments are filtered out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scan_root = Path(tmpdir)
            ignore_file = scan_root / ".lpmignore"
            ignore_file.write_text("""
# This is a comment

node_modules

# Another comment
*.tmp

""")

            config = Config()
            patterns = config.load_ignore_patterns(scan_root)

            # Comments and empty lines should be filtered
            for pattern in patterns:
                assert pattern.strip() != ""
                assert not pattern.startswith("#")

    def test_load_ignore_patterns_no_file(self):
        """Test loading ignore patterns when no .lpmignore exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scan_root = Path(tmpdir)

            config = Config()
            patterns = config.load_ignore_patterns(scan_root)

            # Should only have defaults
            assert patterns == DEFAULT_IGNORE_PATTERNS

    def test_expanduser_in_default_path(self):
        """Test that ~ is expanded in default_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("""
[scan]
default_path = "~/projects"
""")

            config = Config.load(config_path)

            # ~ should be expanded
            assert str(config.scan.default_path) != "~/projects"
            assert config.scan.default_path == Path.home() / "projects"
