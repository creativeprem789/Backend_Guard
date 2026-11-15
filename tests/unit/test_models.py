"""Unit tests for models and severity enumerations."""

from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding, TechnologyDetection


def test_severity_ordering():
    assert Severity.INFO < Severity.LOW
    assert Severity.LOW < Severity.MEDIUM
    assert Severity.MEDIUM < Severity.HIGH
    assert Severity.HIGH < Severity.CRITICAL
    assert Severity.CRITICAL.is_at_least(Severity.HIGH)
    assert not Severity.LOW.is_at_least(Severity.MEDIUM)


def test_confidence_ordering():
    assert Confidence.LOW < Confidence.MEDIUM
    assert Confidence.MEDIUM < Confidence.HIGH
    assert Confidence.HIGH.is_at_least(Confidence.LOW)


def test_finding_serialization():
    finding = Finding(
        rule_id="SEC-001",
        title="Hardcoded secret",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        description="Found API secret in file",
        file="app/config.py",
        line=10,
        column=5,
        language="python",
        impact="Credential compromise",
        recommendation="Use env vars",
        suggested_fix="SECRET = os.getenv('SECRET')",
    )

    d = finding.to_dict()
    assert d["rule_id"] == "SEC-001"
    assert d["severity"] == "critical"
    assert d["category"] == "security"
    assert d["file"] == "app/config.py"

    restored = Finding.from_dict(d)
    assert restored.rule_id == "SEC-001"
    assert restored.severity == Severity.CRITICAL
    assert restored.confidence == Confidence.HIGH
    assert restored.category == Category.SECURITY


def test_technology_detection_dict():
    det = TechnologyDetection(
        name="FastAPI",
        kind="framework",
        confidence=Confidence.HIGH,
        evidence=["fastapi import in main.py"],
    )
    d = det.to_dict()
    assert d["name"] == "FastAPI"
    assert d["confidence"] == "high"
    assert len(d["evidence"]) == 1
