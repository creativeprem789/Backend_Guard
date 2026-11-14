"""Integration with mypy type checker."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from auditor.core.severity import Category, Confidence, Severity
from auditor.integrations.external_tools import ExternalToolRunner
from auditor.models import Finding


class MypyIntegration(ExternalToolRunner):
    tool_binary = "mypy"

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        if not cls.is_available():
            return []

        proc = cls.run_command(
            [".", "--show-error-codes", "--hide-error-context", "--no-error-summary"],
            cwd=project_root,
        )
        if not proc or not proc.stdout.strip():
            return []

        findings: List[Finding] = []
        # format: path:line: error: message [error-code]
        pattern = re.compile(
            r"^(.*?):(\d+):(?:\d+:)?\s*(error|warning|note):\s*(.*?)(?:\s*\[(.*?)\])?$"
        )
        for line in proc.stdout.splitlines():
            m = pattern.match(line.strip())
            if m:
                f_path, line_str, level, msg, code = m.groups()
                code_id = code or "TYPE"
                findings.append(
                    Finding(
                        rule_id=f"EXT-MYPY-{code_id}",
                        title=f"mypy: {code_id}",
                        category=Category.TYPING,
                        severity=Severity.HIGH if level == "error" else Severity.LOW,
                        confidence=Confidence.HIGH,
                        file=f_path.replace("\\", "/"),
                        line=int(line_str),
                        language="python",
                        description=msg,
                        impact="Type inconsistency or contract mismatch detected by mypy static type checker.",
                        recommendation="Fix type signature or variable types to satisfy type constraint.",
                    )
                )
        return findings
