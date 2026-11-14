"""Tests for complexity analysis rules."""

from pathlib import Path

from auditor.analyzers.universal.complexity import (
    CyclomaticComplexityRule,
    DeepNestingRule,
)


def test_cyclomatic_complexity_rule(tmp_path: Path, make_context):
    p = tmp_path / "complex.py"
    # Create function with 16 decision points
    code = """def too_complex(x):
    if x == 1: return 1
    elif x == 2: return 2
    elif x == 3: return 3
    elif x == 4: return 4
    elif x == 5: return 5
    elif x == 6: return 6
    elif x == 7: return 7
    elif x == 8: return 8
    elif x == 9: return 9
    elif x == 10: return 10
    elif x == 11: return 11
    elif x == 12: return 12
    elif x == 13: return 13
    elif x == 14: return 14
    elif x == 15: return 15
    elif x == 16: return 16
    return 0
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = CyclomaticComplexityRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "CMPLX-001"


def test_deep_nesting_rule(tmp_path: Path, make_context):
    p = tmp_path / "nested.py"
    code = """def deeply_nested(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        return True
    return False
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = DeepNestingRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "CMPLX-003"
