"""Integration with Ruff linter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from auditor.core.severity import Category, Confidence, Severity
from auditor.integrations.external_tools import ExternalToolRunner
from auditor.models import Finding


class RuffIntegration(ExternalToolRunner):
    tool_binary = "ruff"

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        if not cls.is_available():
            return []

        proc = cls.run_command(["check", ".", "--output-format=json"], cwd=project_root)
        if not proc or not proc.stdout.strip():
            return []

        findings: List[Finding] = []
        try:
            data = json.loads(proc.stdout)
            for item in data:
                f_path = item.get("filename", "")
                try:
                    rel_f = str(Path(f_path).relative_to(project_root)).replace("\\", "/")
                except ValueError:
                    rel_f = f_path.replace("\\", "/")

                code = item.get("code", "RUFF")
                msg = item.get("message", "")
                loc = item.get("location", {})
                line = loc.get("row", 1)
                col = loc.get("column", 1)

                findings.append(
                    Finding(
                        rule_id=f"EXT-RUFF-{code}",
                        title=f"Ruff: {code}",
                        category=Category.ARCHITECTURE,
                        severity=Severity.LOW,
                        confidence=Confidence.HIGH,
                        file=rel_f,
                        line=line,
                        column=col,
                        language="python",
                        description=msg,
                        impact="Code style or quality defect detected by Ruff.",
                        recommendation="Follow Ruff's suggested lint fix.",
                        suggested_fix=item.get("fix", {}).get("message", "Apply lint fix."),
                        autofix_available=item.get("fix") is not None,
                    )
                )
        except Exception:
            pass
        return findings
