"""Tests for FastAPI framework analyzer."""

from pathlib import Path

from auditor.analyzers.frameworks.fastapi import (
    FastApiMissingResponseModelRule,
    FastApiRawSqlInRouteRule,
)


def test_fastapi_raw_sql_in_route(tmp_path: Path, make_context):
    p = tmp_path / "routes.py"
    code = """from fastapi import APIRouter
router = APIRouter()

@router.get('/users')
def get_users():
    return db.execute('SELECT * FROM users')
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = FastApiRawSqlInRouteRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "FASTAPI-001"


def test_fastapi_missing_response_model(tmp_path: Path, make_context):
    p = tmp_path / "routes.py"
    code = """from fastapi import APIRouter
router = APIRouter()

@router.post('/users')
def create_user():
    return {'id': 1}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = FastApiMissingResponseModelRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "FASTAPI-002"
