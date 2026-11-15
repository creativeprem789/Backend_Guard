"""Integration with Bandit security scanner."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

from auditor.core.severity import Category, Confidence, Severity
from auditor.integrations.external_tools import ExternalToolRunner
from auditor.models import Finding

logger = logging.getLogger(__name__)


class BanditIntegration(ExternalToolRunner):
    tool_binary = "bandit"

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        if not cls.is_available():
            return []

        proc = cls.run_command(["-r", ".", "-f", "json"], cwd=project_root)
        if not proc or not proc.stdout.strip():
            return []

        findings: List[Finding] = []
        try:
            data = json.loads(proc.stdout)
            for res in data.get("results", []):
                test_id = res.get("test_id", "BANDIT")
                sev_str = res.get("issue_severity", "LOW")
                conf_str = res.get("issue_confidence", "LOW")

                f_path = res.get("filename", "")
                try:
                    rel_f = str(Path(f_path).relative_to(project_root)).replace("\\", "/")
                except ValueError:
                    rel_f = f_path.replace("\\", "/")

                findings.append(
                    Finding(
                        rule_id=f"EXT-BANDIT-{test_id}",
                        title=f"Bandit: {res.get('test_name', test_id)}",
                        category=Category.SECURITY,
                        severity=Severity.from_str(sev_str),
                        confidence=Confidence.from_str(conf_str),
                        file=rel_f,
                        line=res.get("line_number", 1),
                        language="python",
                        description=res.get("issue_text", ""),
                        impact="Security issue reported by Bandit Python security scanner.",
                        recommendation="Review bandit advisory and refactor unsafe code pattern.",
                        code_snippet=res.get("code", ""),
                    )
                )
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            logger.debug("Failed parsing Bandit output: %s", exc)
        return findings
