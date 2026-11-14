"""Integration with pytest test runner."""

from __future__ import annotations

from pathlib import Path
from typing import List

from auditor.core.severity import Category, Confidence, Severity
from auditor.integrations.external_tools import ExternalToolRunner
from auditor.models import Finding


class PytestIntegration(ExternalToolRunner):
    tool_binary = "pytest"

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        if not cls.is_available():
            return []

        # Run pytest collection to check test viability
        proc = cls.run_command(["--collect-only", "-q"], cwd=project_root)
        if not proc:
            return []

        findings: List[Finding] = []
        if proc.returncode != 0 and "error" in proc.stdout.lower():
            findings.append(
                Finding(
                    rule_id="EXT-PYTEST-ERR",
                    title="pytest test collection failed",
                    category=Category.TESTING,
                    severity=Severity.HIGH,
                    confidence=Confidence.HIGH,
                    file="tests",
                    line=1,
                    language="python",
                    description="Pytest failed to collect test cases due to an import or syntax error in test files.",
                    impact="Tests cannot run, rendering CI test verification non-operational.",
                    recommendation="Run 'pytest --collect-only' locally and resolve test collection errors.",
                )
            )
        return findings
