"""Integration with ESLint."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from auditor.core.severity import Category, Confidence, Severity
from auditor.integrations.external_tools import ExternalToolRunner
from auditor.models import Finding

logger = logging.getLogger(__name__)


class ESLintIntegration(ExternalToolRunner):
    tool_binary = "eslint"

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        if not cls.is_available():
            return []

        proc = cls.run_command([".", "--format=json"], cwd=project_root)
        if not proc or not proc.stdout.strip():
            return []

        findings: List[Finding] = []
        try:
            data = json.loads(proc.stdout)
            for file_entry in data:
                f_path = file_entry.get("filePath", "")
                try:
                    rel_f = str(Path(f_path).relative_to(project_root)).replace("\\", "/")
                except ValueError:
                    rel_f = f_path.replace("\\", "/")

                for msg in file_entry.get("messages", []):
                    rule_id = msg.get("ruleId") or "ESLINT"
                    findings.append(
                        Finding(
                            rule_id=f"EXT-ESLINT-{rule_id}",
                            title=f"ESLint: {rule_id}",
                            category=Category.ARCHITECTURE,
                            severity=Severity.MEDIUM if msg.get("severity") == 2 else Severity.LOW,
                            confidence=Confidence.HIGH,
                            file=rel_f,
                            line=msg.get("line", 1),
                            column=msg.get("column", 1),
                            language="javascript",
                            description=msg.get("message", ""),
                            impact="JavaScript code quality defect reported by ESLint.",
                            recommendation="Address ESLint warning/error.",
                        )
                    )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.debug("Failed parsing ESLint output: %s", exc)
        return findings
