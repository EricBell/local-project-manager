"""Configuration management for Local Project Manager."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:
    import tomllib
except ImportError:
    import tomli as tomllib


DEFAULT_IGNORE_PATTERNS = [
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    "target",
    "build",
    "dist",
    ".next",
    ".nuxt",
    ".gradle",
    ".idea",
]


@dataclass
class ScanConfig:
    """Scanning configuration."""

    default_path: Path = field(default_factory=lambda: Path.cwd())
    exclude_nested_git_repos: bool = False
    ignore_patterns: List[str] = field(default_factory=lambda: DEFAULT_IGNORE_PATTERNS.copy())


@dataclass
class ClassificationConfig:
    """Project classification thresholds."""

    active_days_threshold: int = 30
    dormant_days_threshold: int = 180
    prunable_min_size_mb: float = 10.0
    prunable_max_size_mb: float = 1.0


@dataclass
class UIConfig:
    """UI preferences."""

    color_scheme: str = "auto"
    vim_mode: bool = True
    default_filter: str = "all"


@dataclass
class IntegrationsConfig:
    """External tool integrations."""

    editor: str = field(default_factory=lambda: os.environ.get("EDITOR", "nano"))
    vscode_cmd: str = "code"


@dataclass
class Config:
    """Main configuration container."""

    scan: ScanConfig = field(default_factory=ScanConfig)
    classification: ClassificationConfig = field(default_factory=ClassificationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """Load configuration from file or use defaults."""
        config = cls()

        if config_path is None:
            # Try default location
            config_path = Path.home() / ".config" / "lpm" / "config.toml"

        if config_path.exists():
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            # Update scan config
            if "scan" in data:
                scan_data = data["scan"]
                if "default_path" in scan_data:
                    config.scan.default_path = Path(scan_data["default_path"]).expanduser()
                if "exclude_nested_git_repos" in scan_data:
                    config.scan.exclude_nested_git_repos = scan_data["exclude_nested_git_repos"]
                if "ignore_patterns" in scan_data:
                    config.scan.ignore_patterns.extend(scan_data["ignore_patterns"])

            # Update classification config
            if "classification" in data:
                class_data = data["classification"]
                if "active_days_threshold" in class_data:
                    config.classification.active_days_threshold = class_data["active_days_threshold"]
                if "dormant_days_threshold" in class_data:
                    config.classification.dormant_days_threshold = class_data["dormant_days_threshold"]
                if "prunable_min_size_mb" in class_data:
                    config.classification.prunable_min_size_mb = class_data["prunable_min_size_mb"]
                if "prunable_max_size_mb" in class_data:
                    config.classification.prunable_max_size_mb = class_data["prunable_max_size_mb"]

            # Update UI config
            if "ui" in data:
                ui_data = data["ui"]
                if "color_scheme" in ui_data:
                    config.ui.color_scheme = ui_data["color_scheme"]
                if "vim_mode" in ui_data:
                    config.ui.vim_mode = ui_data["vim_mode"]
                if "default_filter" in ui_data:
                    config.ui.default_filter = ui_data["default_filter"]

            # Update integrations config
            if "integrations" in data:
                int_data = data["integrations"]
                if "editor" in int_data:
                    config.integrations.editor = int_data["editor"]
                if "vscode_cmd" in int_data:
                    config.integrations.vscode_cmd = int_data["vscode_cmd"]

        return config

    def load_ignore_patterns(self, scan_root: Path) -> List[str]:
        """Load ignore patterns from .lpmignore file if exists."""
        patterns = self.scan.ignore_patterns.copy()

        # Check for .lpmignore in scan root
        ignore_file = scan_root / ".lpmignore"
        if ignore_file.exists():
            with open(ignore_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)

        # Check for global ignore file
        global_ignore = Path.home() / ".config" / "lpm" / ".lpmignore"
        if global_ignore.exists():
            with open(global_ignore) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)

        return patterns
