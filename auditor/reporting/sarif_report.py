"""OASIS SARIF v2.1.0 report generator for GitHub Code Scanning integration."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from auditor.core.severity import Severity
from auditor.models import AuditResult, Finding


class SarifReporter:
    """Generates standard SARIF v2.1.0 JSON payloads."""

    @classmethod
    def generate(cls, result: AuditResult, indent: int = 2) -> str:
        sarif_payload = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Backend Guard",
                            "semanticVersion": "1.0.0",
                            "informationUri": "https://github.com/backend-guard/backend-auditor",
                            "rules": cls._build_sarif_rules(result.findings),
                        }
                    },
                    "results": cls._build_sarif_results(result.findings),
                }
            ],
        }
        return json.dumps(sarif_payload, indent=indent)

    @classmethod
    def _map_severity_to_sarif_level(cls, severity: Severity) -> str:
        if severity in (Severity.CRITICAL, Severity.HIGH):
            return "error"
        if severity == Severity.MEDIUM:
            return "warning"
        return "note"

    @classmethod
    def _build_sarif_rules(cls, findings: List[Finding]) -> List[Dict[str, Any]]:
        rules_map: Dict[str, Dict[str, Any]] = {}
        for f in findings:
            if f.rule_id not in rules_map:
                rules_map[f.rule_id] = {
                    "id": f.rule_id,
                    "name": f.rule_id.replace("-", "_"),
                    "shortDescription": {"text": f.title},
                    "fullDescription": {"text": f.description},
                    "help": {
                        "text": f"{f.recommendation}\n\nSuggested Fix:\n{f.suggested_fix}",
                        "markdown": f"### Recommendation\n{f.recommendation}\n\n```\n{f.suggested_fix}\n```",
                    },
                    "defaultConfiguration": {"level": cls._map_severity_to_sarif_level(f.severity)},
                }
        return list(rules_map.values())

    @classmethod
    def _build_sarif_results(cls, findings: List[Finding]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for f in findings:
            results.append(
                {
                    "ruleId": f.rule_id,
                    "level": cls._map_severity_to_sarif_level(f.severity),
                    "message": {"text": f"{f.title}: {f.description}"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": f.file.replace("\\", "/"),
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "startLine": max(1, f.line),
                                    "startColumn": max(1, f.column),
                                },
                            }
                        }
                    ],
                }
            )
        return results
