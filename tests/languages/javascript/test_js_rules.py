"""Tests for JavaScript and TypeScript rules."""

from pathlib import Path

from auditor.analyzers.languages.javascript.rules import (
    DangerousEvalRule,
    SyncBlockingInJsRule,
)
from auditor.analyzers.languages.typescript.rules import ExcessiveAnyTypeRule


def test_sync_blocking_in_node(tmp_path: Path, make_context):
    p = tmp_path / "server.js"
    code = """const fs = require('fs');
function readConfig() {
    return fs.readFileSync('conf.json', 'utf-8');
}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = SyncBlockingInJsRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "JS-001"


def test_dangerous_eval(tmp_path: Path, make_context):
    p = tmp_path / "calc.js"
    code = """function compute(expr) {
    return eval(expr);
}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = DangerousEvalRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "JS-003"


def test_excessive_any_type(tmp_path: Path, make_context):
    p = tmp_path / "service.ts"
    code = """export function processData(input: any): any {
    return input;
}
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = ExcessiveAnyTypeRule()
    findings = rule.evaluate(ctx)
    assert len(findings) >= 1
    assert findings[0].rule_id == "TS-001"
