"""Tests for Express framework analyzer."""

from pathlib import Path

from auditor.analyzers.frameworks.express import (
    ExpressAsyncRouteWithoutTryCatchRule,
    ExpressMissingErrorMiddlewareRule,
)


def test_express_missing_error_middleware(tmp_path: Path, make_context):
    p = tmp_path / "server.js"
    code = """const express = require('express');
const app = express();
app.get('/items', (req, res) => res.json([]));
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = ExpressMissingErrorMiddlewareRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXPRESS-001"


def test_express_async_without_try_catch(tmp_path: Path, make_context):
    p = tmp_path / "routes.js"
    code = """app.get('/async-call', async (req, res) => {
    const data = await fetchDetails();
    res.json(data);
});
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = ExpressAsyncRouteWithoutTryCatchRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "EXPRESS-003"
