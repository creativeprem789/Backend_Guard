"""Configuration loading and validation for Backend Guard."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set

# Python 3.11+ has tomllib in the standard library
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

from auditor.core.severity import Confidence, Severity


@dataclass
class ComplexityThresholds:
    max_cyclomatic_complexity: int = 15
    max_function_lines: int = 60
    max_file_lines: int = 600
    max_function_parameters: int = 6
    max_nested_blocks: int = 4


@dataclass
class Config:
    """Project-level audit configuration."""

    # Rules
    enabled_rules: Optional[Set[str]] = None
    disabled_rules: Set[str] = field(default_factory=set)
    severity_overrides: Dict[str, Severity] = field(default_factory=dict)
    confidence_threshold: Confidence = Confidence.LOW
    failure_threshold: Severity = Severity.HIGH  # exit code 1 if findings >= this threshold

    # Languages and frameworks
    selected_languages: Optional[Set[str]] = None
    selected_frameworks: Optional[Set[str]] = None

    # Exclusions
    exclude_dirs: Set[str] = field(
        default_factory=lambda: {
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "env",
            ".env",
            "__pycache__",
            "dist",
            "build",
            ".tox",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "coverage",
            ".idea",
            ".vscode",
            "migrations",
        }
    )
    exclude_files: Set[str] = field(
        default_factory=lambda: {
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
        }
    )
    respect_gitignore: bool = True

    # Complexity
    complexity: ComplexityThresholds = field(default_factory=ComplexityThresholds)

    # Baselines & suppressions
    baseline_file: Optional[Path] = None
    allow_inline_suppressions: bool = True

    # External tools
    with_tools: bool = False
    external_tools: Dict[str, bool] = field(
        default_factory=lambda: {
            "ruff": True,
            "eslint": True,
            "mypy": True,
            "pytest": True,
            "bandit": True,
        }
    )

    def is_rule_enabled(self, rule_id: str) -> bool:
        if rule_id in self.disabled_rules:
            return False
        if self.enabled_rules is not None:
            return rule_id in self.enabled_rules
        return True

    def get_effective_severity(self, rule_id: str, default_severity: Severity) -> Severity:
        return self.severity_overrides.get(rule_id, default_severity)

    @classmethod
    def default(cls) -> Config:
        return cls()

    @classmethod
    def load(cls, root_path: Path, config_file: Optional[Path] = None) -> Config:
        """Load configuration from root directory searching for backend-auditor.toml."""
        candidate_paths = [
            config_file,
            root_path / "backend-auditor.toml",
            root_path / "backend-guard.toml",
            root_path / ".backend-auditor.toml",
        ]

        found_path: Optional[Path] = None
        for p in candidate_paths:
            if p and p.is_file():
                found_path = p
                break

        cfg = cls.default()
        if not found_path or tomllib is None:
            return cfg

        try:
            with open(found_path, "rb") as f:
                data = tomllib.load(f)
            cls._apply_toml_dict(cfg, data, root_path)
        except Exception:
            # Fall back to defaults on parsing error without crashing
            pass
        return cfg

    @classmethod
    def _apply_toml_dict(cls, cfg: Config, data: Dict[str, Any], root_path: Path) -> None:
        general = data.get("general", {})
        rules_sec = data.get("rules", {})
        exclusions = data.get("exclusions", {})
        complexity_sec = data.get("complexity", {})
        tools_sec = data.get("tools", {})

        if "failure_threshold" in general:
            cfg.failure_threshold = Severity.from_str(general["failure_threshold"])
        if "confidence_threshold" in general:
            cfg.confidence_threshold = Confidence.from_str(general["confidence_threshold"])
        if "baseline" in general:
            cfg.baseline_file = root_path / general["baseline"]

        if "enable" in rules_sec and isinstance(rules_sec["enable"], list):
            cfg.enabled_rules = set(rules_sec["enable"])
        if "disable" in rules_sec and isinstance(rules_sec["disable"], list):
            cfg.disabled_rules = set(rules_sec["disable"])
        if "severity" in rules_sec and isinstance(rules_sec["severity"], dict):
            for r_id, s_val in rules_sec["severity"].items():
                cfg.severity_overrides[r_id] = Severity.from_str(s_val)

        if "dirs" in exclusions and isinstance(exclusions["dirs"], list):
            cfg.exclude_dirs.update(exclusions["dirs"])
        if "files" in exclusions and isinstance(exclusions["files"], list):
            cfg.exclude_files.update(exclusions["files"])
        if "respect_gitignore" in exclusions:
            cfg.respect_gitignore = bool(exclusions["respect_gitignore"])

        if complexity_sec:
            if "max_cyclomatic_complexity" in complexity_sec:
                cfg.complexity.max_cyclomatic_complexity = int(
                    complexity_sec["max_cyclomatic_complexity"]
                )
            if "max_function_lines" in complexity_sec:
                cfg.complexity.max_function_lines = int(complexity_sec["max_function_lines"])
            if "max_file_lines" in complexity_sec:
                cfg.complexity.max_file_lines = int(complexity_sec["max_file_lines"])

        if tools_sec:
            for tool_name, enabled in tools_sec.items():
                if isinstance(enabled, bool):
                    cfg.external_tools[tool_name] = enabled
