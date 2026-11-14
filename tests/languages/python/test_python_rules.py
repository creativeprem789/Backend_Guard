"""Tests for Python-specific rules."""

from pathlib import Path

from auditor.analyzers.languages.python.async_checks import SyncBlockingInAsyncRule
from auditor.analyzers.languages.python.rules import (
    MutableDefaultArgumentRule,
    UnsafeDeserializationRule,
    WildcardImportRule,
)
from auditor.analyzers.languages.python.typing import MissingTypeAnnotationsRule


def test_sync_blocking_in_async(tmp_path: Path, make_context):
    p = tmp_path / "async_service.py"
    code = """import time
async def fetch_data():
    time.sleep(1)
    return True
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = SyncBlockingInAsyncRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "PY-ASYNC-001"


def test_mutable_default_argument(tmp_path: Path, make_context):
    p = tmp_path / "defaults.py"
    code = """def add_item(item, items=[]):
    items.append(item)
    return items
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = MutableDefaultArgumentRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "PY-001"


def test_unsafe_deserialization(tmp_path: Path, make_context):
    p = tmp_path / "loader.py"
    code = """import pickle
def load_data(raw):
    return pickle.loads(raw)
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = UnsafeDeserializationRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "PY-002"


def test_wildcard_import(tmp_path: Path, make_context):
    p = tmp_path / "wild.py"
    code = "from os.path import *\n"
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = WildcardImportRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "PY-003"


def test_missing_type_annotations(tmp_path: Path, make_context):
    p = tmp_path / "user_service.py"
    code = """def process_user(user_id, role):
    return True
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = MissingTypeAnnotationsRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "PY-TYPE-001"
