"""Unit tests for baseline snapshot saving and matching."""

from pathlib import Path

from auditor.baselines import Baseline
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding


def test_baseline_save_and_load(tmp_path: Path):
    f1 = Finding(
        rule_id="ARCH-001",
        title="Direct infra coupling",
        category=Category.ARCHITECTURE,
        severity=Severity.HIGH,
        confidence=Confidence.HIGH,
        description="Coupling",
        file="app/routes.py",
        line=12,
    )
    f2 = Finding(
        rule_id="SEC-001",
        title="Hardcoded key",
        category=Category.SECURITY,
        severity=Severity.CRITICAL,
        confidence=Confidence.HIGH,
        description="Key found",
        file="app/secrets.py",
        line=5,
    )

    baseline_path = tmp_path / "baseline.json"
    Baseline.save([f1, f2], baseline_path)
    assert baseline_path.is_file()

    loaded = Baseline.load(baseline_path)
    assert loaded.contains(f1)
    assert loaded.contains(f2)

    # Different finding should not be contained
    f3 = Finding(
        rule_id="DB-001",
        title="N+1 query",
        category=Category.DATABASE,
        severity=Severity.HIGH,
        confidence=Confidence.MEDIUM,
        description="N+1 in loop",
        file="app/services.py",
        line=40,
    )
    assert not loaded.contains(f3)
