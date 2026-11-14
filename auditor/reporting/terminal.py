"""Terminal report formatter with readable cards, severity colors, and summaries."""

from __future__ import annotations

import sys
from typing import TextIO

from auditor.core.severity import Severity
from auditor.models import AuditResult

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

SEVERITY_COLORS = {
    Severity.CRITICAL: f"{BOLD}{RED}",
    Severity.HIGH: RED,
    Severity.MEDIUM: YELLOW,
    Severity.LOW: BLUE,
    Severity.INFO: DIM,
}


class TerminalReporter:
    """Renders formatted audit results to standard output."""

    @classmethod
    def render(
        cls, result: AuditResult, stream: TextIO = sys.stdout, use_color: bool = True
    ) -> None:
        def c(text: str, color_code: str) -> str:
            return f"{color_code}{text}{RESET}" if use_color else text

        p = result.project_info

        stream.write("\n")
        stream.write(c("=" * 76, DIM) + "\n")
        stream.write(f" {c('🛡️  BACKEND GUARD AUDIT REPORT', BOLD)} - {c(p.name, CYAN)}\n")
        stream.write(c("=" * 76, DIM) + "\n")

        # Project Tech Summary
        lang_list = (
            ", ".join(f"{v.name} ({v.confidence.value})" for v in p.detected_languages.values())
            or "None"
        )
        fw_list = (
            ", ".join(f"{v.name} ({v.confidence.value})" for v in p.detected_frameworks.values())
            or "None detected"
        )
        stream.write(f"  {c('Root:', DIM)}       {p.root_path}\n")
        stream.write(f"  {c('Languages:', DIM)}  {lang_list}\n")
        stream.write(f"  {c('Frameworks:', DIM)} {fw_list}\n")
        stream.write(
            f"  {c('Scanned:', DIM)}    {len(p.files)} files ({p.total_lines:,} lines of code) in {result.scan_duration_seconds:.2f}s\n"
        )
        stream.write(c("-" * 76, DIM) + "\n\n")

        # Findings Summary Badge
        stream.write(f"  {c('FINDINGS SUMMARY:', BOLD)}\n")
        sev_counts = result.summary_by_severity()
        stream.write(
            f"   Critical: {c(str(sev_counts['critical']), BOLD + RED)}  |  "
            f"High: {c(str(sev_counts['high']), RED)}  |  "
            f"Medium: {c(str(sev_counts['medium']), YELLOW)}  |  "
            f"Low: {c(str(sev_counts['low']), BLUE)}  |  "
            f"Info: {c(str(sev_counts['info']), DIM)}\n"
        )
        if result.suppressed_count > 0:
            stream.write(
                f"   {c(f'({result.suppressed_count} findings suppressed by inline comments)', DIM)}\n"
            )
        if result.baseline_matched_count > 0:
            stream.write(
                f"   {c(f'({result.baseline_matched_count} findings matched existing baseline)', DIM)}\n"
            )
        stream.write("\n")

        if not result.findings:
            stream.write(
                f"  {c('✅ Clean bill of health! No architectural or defect risks detected.', GREEN + BOLD)}\n\n"
            )
            cls._render_footer(result, stream, c)
            return

        stream.write(c("-" * 76, DIM) + "\n")
        stream.write(f"  {c('DETAILED FINDINGS', BOLD)}\n")
        stream.write(c("-" * 76, DIM) + "\n\n")

        for idx, f in enumerate(result.findings, start=1):
            sev_col = SEVERITY_COLORS.get(f.severity, "")
            sev_badge = c(f"[{f.severity.value.upper()}]", sev_col)
            conf_badge = c(f"({f.confidence.value} conf)", DIM)

            stream.write(
                f" {c(str(idx) + '.', BOLD)} {sev_badge} {c(f.rule_id, BOLD)}: {f.title} {conf_badge}\n"
            )
            stream.write(f"    {c('Location:', DIM)} {c(f.file, CYAN)}:{c(str(f.line), YELLOW)}\n")
            stream.write(f"    {c('Problem:', DIM)}  {f.description}\n")

            if f.evidence:
                stream.write(f"    {c('Evidence:', DIM)} {f.evidence}\n")
            if f.impact:
                stream.write(f"    {c('Impact:', DIM)}   {f.impact}\n")
            if f.recommendation:
                stream.write(f"    {c('Fix:', DIM)}      {c(f.recommendation, GREEN)}\n")
            if f.suggested_fix:
                stream.write(f"    {c('Example:', DIM)}  {f.suggested_fix}\n")
            stream.write("\n")

        cls._render_footer(result, stream, c)

    @classmethod
    def _render_footer(cls, result: AuditResult, stream: TextIO, c) -> None:
        if result.failed_analyzers:
            stream.write(c("⚠️  FAILED / INCOMPLETE ANALYZERS:", BOLD + RED) + "\n")
            for name, reason in result.failed_analyzers.items():
                stream.write(f"   - {name}: {reason}\n")
            stream.write("\n")

        if result.skipped_analyzers:
            stream.write(c("ℹ️  Skipped Analyzers:", DIM) + "\n")
            for name, reason in sorted(result.skipped_analyzers.items()):
                stream.write(f"   - {c(name, DIM)}: {reason}\n")
            stream.write("\n")

        stream.write(c("=" * 76, DIM) + "\n\n")
