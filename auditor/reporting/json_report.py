"""JSON report generator for machine consumption and AI coding assistants."""

from __future__ import annotations

import json

from auditor.models import AuditResult


class JsonReporter:
    """Serializes AuditResult into standardized JSON format."""

    @staticmethod
    def generate(result: AuditResult, indent: int = 2) -> str:
        return json.dumps(result.to_dict(), indent=indent)
