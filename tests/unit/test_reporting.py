"""Unit tests for JSON, Markdown, Terminal, and SARIF reporters."""

import json
from pathlib import Path

from auditor.core.severity import Category, Confidence, Severity
from auditor.models import AuditResult, Finding, ProjectInfo
from auditor.reporting.json_report import JsonReporter
from auditor.reporting.markdown_report import MarkdownReporter
from auditor.reporting.sarif_report import SarifReporter


def create_sample_result() -> AuditResult:
    pinfo = ProjectInfo(root_path=Path("/test_proj"), name="test_proj")
    f1 = Finding(
        rule_id="SEC-001",
        title="Hardcoded API secret",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        file="app/config.py",
        line=14,
        description="Found API secret in config",
        impact="Compromise",
        recommendation="Use env vars",
        suggested_fix="os.getenv('KEY')",
    )
    return AuditResult(
        project_info=pinfo,
        findings=[f1],
        executed_rules=["SEC-001"],
    )


def test_json_reporting():
    res = create_sample_result()
    raw_json = JsonReporter.generate(res)
    data = json.loads(raw_json)
    assert data["meta"]["tool"] == "backend-guard"
    assert data["summary"]["total_findings"] == 1
    assert data["findings"][0]["rule_id"] == "SEC-001"


def test_markdown_reporting():
    res = create_sample_result()
    md = MarkdownReporter.generate(res)
    assert "# 🛡️ Backend Guard Audit Report: test_proj" in md
    assert "SEC-001" in md
    assert "Hardcoded API secret" in md
    assert "os.getenv('KEY')" in md


def test_sarif_reporting():
    res = create_sample_result()
    raw_sarif = SarifReporter.generate(res)
    sarif = json.loads(raw_sarif)
    assert sarif["version"] == "2.1.0"
    runs = sarif["runs"]
    assert len(runs) == 1
    assert runs[0]["tool"]["driver"]["name"] == "Backend Guard"
    assert len(runs[0]["results"]) == 1
    assert runs[0]["results"][0]["ruleId"] == "SEC-001"
    assert runs[0]["results"][0]["level"] == "error"
