"""Tests for testing analysis rules."""

from pathlib import Path

from auditor.analyzers.universal.testing import MissingTestSuiteRule, VacuousTestRule


def test_missing_test_suite_rule(tmp_path: Path, make_context):
    # Create 3 source files without tests
    (tmp_path / "a.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "b.py").write_text("y = 2", encoding="utf-8")
    (tmp_path / "c.py").write_text("z = 3", encoding="utf-8")

    ctx = make_context(tmp_path)
    rule = MissingTestSuiteRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "TEST-001"


def test_vacuous_test_rule(tmp_path: Path, make_context):
    p = tmp_path / "test_ops.py"
    code = """def test_something():
    do_something()
    # No assertions
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = VacuousTestRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "TEST-002"
