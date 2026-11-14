"""Tests for error handling rules."""

from pathlib import Path

from auditor.analyzers.universal.error_handling import (
    BroadExceptionCatchingRule,
    SilentExceptionSwallowingRule,
    StackTraceLeakedRule,
)


def test_silent_exception_swallowing(tmp_path: Path, make_context):
    p = tmp_path / "swallow.py"
    code = """def do_work():
    try:
        critical_op()
    except Exception:
        pass
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = SilentExceptionSwallowingRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "ERR-001"


def test_bare_except_rule(tmp_path: Path, make_context):
    p = tmp_path / "bare.py"
    code = """def do_work():
    try:
        operation()
    except:
        cleanup()
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = BroadExceptionCatchingRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "ERR-002"


def test_stack_trace_leakage(tmp_path: Path, make_context):
    p = tmp_path / "leak.py"
    code = """def handle_err(e):
    return {"detail": str(e)}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = StackTraceLeakedRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "ERR-003"
