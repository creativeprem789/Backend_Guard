"""Unit tests for configuration loading and validation."""

from pathlib import Path

from auditor.config import Config
from auditor.core.severity import Confidence, Severity


def test_default_config():
    cfg = Config.default()
    assert cfg.failure_threshold == Severity.HIGH
    assert cfg.confidence_threshold == Confidence.LOW
    assert "node_modules" in cfg.exclude_dirs
    assert ".git" in cfg.exclude_dirs
    assert cfg.is_rule_enabled("ARCH-001")


def test_config_rules_enable_disable():
    cfg = Config.default()
    cfg.disabled_rules.add("ARCH-001")
    assert not cfg.is_rule_enabled("ARCH-001")
    assert cfg.is_rule_enabled("SEC-001")

    cfg.enabled_rules = {"SEC-001"}
    assert cfg.is_rule_enabled("SEC-001")
    assert not cfg.is_rule_enabled("SEC-002")


def test_severity_override():
    cfg = Config.default()
    cfg.severity_overrides["API-001"] = Severity.CRITICAL
    assert cfg.get_effective_severity("API-001", Severity.LOW) == Severity.CRITICAL
    assert cfg.get_effective_severity("API-002", Severity.LOW) == Severity.LOW


def test_toml_loading(tmp_path: Path):
    toml_content = """
[general]
failure_threshold = "critical"
confidence_threshold = "medium"

[rules]
disable = ["SEC-001"]

[rules.severity]
"API-001" = "high"

[exclusions]
dirs = ["custom_dir"]
"""
    cfg_file = tmp_path / "backend-auditor.toml"
    cfg_file.write_text(toml_content, encoding="utf-8")

    cfg = Config.load(tmp_path)
    assert cfg.failure_threshold == Severity.CRITICAL
    assert cfg.confidence_threshold == Confidence.MEDIUM
    assert not cfg.is_rule_enabled("SEC-001")
    assert cfg.get_effective_severity("API-001", Severity.LOW) == Severity.HIGH
    assert "custom_dir" in cfg.exclude_dirs
