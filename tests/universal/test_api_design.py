"""Tests for API design rules."""

from pathlib import Path

from auditor.analyzers.universal.api_design import (
    InconsistentErrorStatusRule,
    MissingPaginationRule,
)


def test_missing_pagination_rule(tmp_path: Path, make_context):
    p = tmp_path / "router.py"
    code = """@router.get('/items')
def get_items():
    return db.query(Item).all()
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = MissingPaginationRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "API-001"


def test_inconsistent_error_status_rule(tmp_path: Path, make_context):
    p = tmp_path / "api.py"
    code = """def bad_handler():
    return {'success': False, 'error': 'Invalid token'}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = InconsistentErrorStatusRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "API-002"
