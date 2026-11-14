"""Markdown report generator for documentation and developer pull requests."""

from __future__ import annotations

from typing import List

from auditor.core.severity import Severity
from auditor.models import AuditResult


class MarkdownReporter:
    """Generates comprehensive GitHub Flavored Markdown audit report."""

    @classmethod
    def generate(cls, result: AuditResult) -> str:
        p = result.project_info
        lines: List[str] = []

        lines.append(f"# 🛡️ Backend Guard Audit Report: {p.name}")
        lines.append("")
        lines.append(
            f"> Audited on `{result.created_at}` in `{result.scan_duration_seconds:.2f}` seconds."
        )
        lines.append("")

        # Overview Table
        lines.append("## 📊 Executive Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| **Target Codebase** | `{p.root_path}` |")
        lines.append(f"| **Total Files** | {len(p.files)} |")
        lines.append(f"| **Total Lines of Code** | {p.total_lines:,} |")

        langs = ", ".join(v.name for v in p.detected_languages.values()) or "None"
        fws = ", ".join(v.name for v in p.detected_frameworks.values()) or "None detected"
        lines.append(f"| **Detected Languages** | {langs} |")
        lines.append(f"| **Detected Frameworks** | {fws} |")
        lines.append(f"| **Total Findings** | **{result.total_findings}** |")
        lines.append(
            f"| **Audit Status** | {'✅ Complete' if result.is_complete else '⚠️ Incomplete (errors occurred)'} |"
        )
        lines.append("")

        # Severity breakdown
        sev = result.summary_by_severity()
        lines.append("### Findings by Severity")
        lines.append("")
        lines.append(f"- 🔴 **Critical**: {sev['critical']}")
        lines.append(f"- 🟠 **High**: {sev['high']}")
        lines.append(f"- 🟡 **Medium**: {sev['medium']}")
        lines.append(f"- 🔵 **Low**: {sev['low']}")
        lines.append(f"- ⚪ **Info**: {sev['info']}")
        lines.append("")

        if result.findings:
            lines.append("## 🔍 Findings Summary Table")
            lines.append("")
            lines.append("| # | Severity | Rule ID | Title | Location |")
            lines.append("|---|---|---|---|---|")
            for idx, f in enumerate(result.findings, start=1):
                sev_icon = {
                    Severity.CRITICAL: "🔴 Critical",
                    Severity.HIGH: "🟠 High",
                    Severity.MEDIUM: "🟡 Medium",
                    Severity.LOW: "🔵 Low",
                    Severity.INFO: "⚪ Info",
                }.get(f.severity, f.severity.value)
                lines.append(
                    f"| {idx} | {sev_icon} | `{f.rule_id}` | {f.title} | `{f.file}:{f.line}` |"
                )
            lines.append("")

            lines.append("## 🛠️ Detailed Findings and Actionable Fixes")
            lines.append("")
            for idx, f in enumerate(result.findings, start=1):
                lines.append(f"### {idx}. [{f.severity.value.upper()}] {f.rule_id}: {f.title}")
                lines.append(f"- **File**: `{f.file}` (Line {f.line})")
                lines.append(
                    f"- **Category**: `{f.category.value if hasattr(f.category, 'value') else f.category}`"
                )
                lines.append(
                    f"- **Confidence**: `{f.confidence.value if hasattr(f.confidence, 'value') else f.confidence}`"
                )
                lines.append("")
                lines.append(f"**Description**:\n{f.description}")
                lines.append("")
                if f.evidence:
                    lines.append(f"**Evidence**:\n```\n{f.evidence}\n```")
                    lines.append("")
                if f.impact:
                    lines.append(f"**Architectural / Runtime Impact**:\n{f.impact}")
                    lines.append("")
                if f.recommendation:
                    lines.append(f"**Recommendation**:\n{f.recommendation}")
                    lines.append("")
                if f.suggested_fix:
                    lines.append(f"**Suggested Fix / Example**:\n```\n{f.suggested_fix}\n```")
                    lines.append("")
                lines.append("---")
                lines.append("")
        else:
            lines.append("## ✅ Clean Audit")
            lines.append(
                "No defects, architectural boundary violations, or security risks were detected."
            )
            lines.append("")

        # Methodology & Limitations
        lines.append("## ℹ️ Analysis Scope and Limitations")
        lines.append("")
        lines.append(
            "- Static analysis evaluates code structure, patterns, and known defect signatures."
        )
        lines.append(
            "- Dynamic runtime behavior, infrastructure configurations, and cloud deployment states must be verified independently."
        )
        lines.append(
            "- False positives can be managed using inline `# backend-auditor: ignore <RULE_ID>` comments or baseline files."
        )
        lines.append("")

        return "\n".join(lines)
