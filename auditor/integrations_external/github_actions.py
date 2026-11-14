"""GitHub Actions integration: workflow commands and annotation formatting."""

from __future__ import annotations

import sys
from typing import TextIO

from auditor.core.severity import Severity
from auditor.models import AuditResult


class GitHubActionsAnnotation:
    """Formats findings as GitHub Actions workflow commands (::error, ::warning)."""

    @staticmethod
    def print_annotations(result: AuditResult, stream: TextIO = sys.stdout) -> None:
        for f in result.findings:
            cmd = "error" if f.severity in (Severity.CRITICAL, Severity.HIGH) else "warning"
            file_clean = f.file.replace("\\", "/")
            stream.write(
                f"::{cmd} file={file_clean},line={f.line},title={f.rule_id} {f.title}::{f.description} (Fix: {f.recommendation})\n"
            )
