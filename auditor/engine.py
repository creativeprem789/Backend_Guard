"""Core analysis engine coordinating analyzers, rules, suppressions, and baselines."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

from auditor.analyzers import ensure_analyzers_loaded
from auditor.baselines import Baseline
from auditor.config import Config
from auditor.core.context import AnalysisContext
from auditor.core.findings import deduplicate_findings, sort_findings
from auditor.discovery import ProjectScanner
from auditor.integrations.bandit import BanditIntegration
from auditor.integrations.eslint import ESLintIntegration
from auditor.integrations.mypy import MypyIntegration
from auditor.integrations.pytest import PytestIntegration
from auditor.integrations.ruff import RuffIntegration
from auditor.models import AuditResult, Finding, ProjectInfo
from auditor.registry import AnalyzerRegistry
from auditor.suppressions import SuppressionIndex


class AuditEngine:
    """Orchestrates the entire backend codebase audit pipeline."""

    def __init__(self, root_path: Path | str, config: Optional[Config] = None) -> None:
        ensure_analyzers_loaded()
        self.root_path = Path(root_path).resolve()
        self.config = config or Config.load(self.root_path)

    def run(self) -> AuditResult:
        """Execute full audit pipeline and return unified AuditResult."""
        start_time = time.perf_counter()

        # 1. Project discovery & Technology detection
        scanner = ProjectScanner(self.root_path, self.config)
        project_info: ProjectInfo = scanner.scan()

        # 2. Context initialization
        context = AnalysisContext(project_info, self.config)

        # 3. Scan files for suppressions
        suppression_index = SuppressionIndex()
        for f in project_info.files:
            lines = context.get_lines(f)
            rel = context.get_relative_path(f)
            suppression_index.scan_file(rel, lines)

        # 4. Load baseline if specified
        baseline: Optional[Baseline] = None
        if self.config.baseline_file and self.config.baseline_file.is_file():
            baseline = Baseline.load(self.config.baseline_file)

        raw_findings: List[Finding] = []
        executed_rules: List[str] = []
        skipped_analyzers: Dict[str, str] = {}
        failed_analyzers: Dict[str, str] = {}

        # 5. Run Analyzers from registry
        for analyzer in AnalyzerRegistry.all_analyzers():
            if not analyzer.can_analyze(project_info):
                reason = "Language or framework not detected in project"
                skipped_analyzers[analyzer.name] = reason
                continue

            try:
                # Track executed rules
                for r in analyzer.get_rules():
                    if self.config.is_rule_enabled(r.rule_id):
                        executed_rules.append(r.rule_id)

                results = analyzer.analyze(context)
                raw_findings.extend(results)
            except Exception as exc:
                failed_analyzers[analyzer.name] = f"Analyzer crashed: {exc}"

        # 6. Run External Tools if requested
        if self.config.with_tools:
            tool_integrations = [
                ("ruff", RuffIntegration),
                ("eslint", ESLintIntegration),
                ("mypy", MypyIntegration),
                ("bandit", BanditIntegration),
                ("pytest", PytestIntegration),
            ]
            for tool_name, runner in tool_integrations:
                if self.config.external_tools.get(tool_name, True):
                    if runner.is_available():
                        try:
                            t_findings = runner.run(self.root_path)
                            raw_findings.extend(t_findings)
                        except Exception as e:
                            failed_analyzers[f"external-{tool_name}"] = str(e)
                    else:
                        skipped_analyzers[f"external-{tool_name}"] = (
                            f"Binary '{runner.tool_binary}' not found on PATH"
                        )

        # 7. Apply Suppressions and Baselines
        filtered_findings: List[Finding] = []
        suppressed_count = 0
        baseline_matched_count = 0

        for finding in raw_findings:
            # Check inline suppression comments
            if self.config.allow_inline_suppressions and suppression_index.is_suppressed(
                finding.file, finding.line, finding.rule_id
            ):
                suppressed_count += 1
                continue

            # Check baseline matching
            if baseline and baseline.contains(finding):
                baseline_matched_count += 1
                continue

            # Apply severity overrides from config
            effective_sev = self.config.get_effective_severity(finding.rule_id, finding.severity)
            finding.severity = effective_sev

            # Filter by confidence threshold
            if not finding.confidence.is_at_least(self.config.confidence_threshold):
                continue

            filtered_findings.append(finding)

        # 8. Deduplicate and Sort
        deduped = deduplicate_findings(filtered_findings)
        final_findings = sort_findings(deduped)

        duration = time.perf_counter() - start_time
        is_complete = len(failed_analyzers) == 0

        return AuditResult(
            project_info=project_info,
            findings=final_findings,
            executed_rules=sorted(set(executed_rules)),
            skipped_analyzers=skipped_analyzers,
            failed_analyzers=failed_analyzers,
            scan_duration_seconds=duration,
            suppressed_count=suppressed_count,
            baseline_matched_count=baseline_matched_count,
            is_complete=is_complete,
        )
