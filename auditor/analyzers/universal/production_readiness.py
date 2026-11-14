"""Production readiness analysis: health checks, graceful shutdown, and containerization."""

from __future__ import annotations

from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class MissingHealthCheckRule(BaseRule):
    """Detects backend web services lacking a health check or liveness endpoint."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PROD-001",
                title="Missing health check or liveness endpoint",
                category=Category.PRODUCTION_READINESS,
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                description="Backend API service defines HTTP routes but does not expose a standard health probe endpoint (/health, /healthz).",
                impact="Container orchestrators (Kubernetes, AWS ECS) and load balancers cannot monitor container liveness or readiness.",
                recommendation="Expose a lightweight GET /health or /healthz route that checks database connectivity and returns 200 OK.",
                suggested_fix="Add @app.get('/health') returning {'status': 'healthy'}.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        # Only evaluate if the project has web frameworks detected or defines routes
        has_framework = any(
            f in context.project_info.detected_frameworks
            for f in ["fastapi", "express", "flask", "django", "nestjs"]
        )
        if not has_framework:
            return []

        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        has_health_route = False
        for f in source_files:
            content = context.get_content(f).lower()
            if any(
                term in content
                for term in [
                    '"/health"',
                    "'/health'",
                    '"/healthz"',
                    "'/healthz'",
                    '"/ready"',
                    '"/live"',
                ]
            ):
                has_health_route = True
                break

        if not has_health_route:
            findings.append(
                self.create_finding(
                    file=context.get_relative_path(context.root_path),
                    line=1,
                    description="No standard health probe endpoint (/health or /healthz) discovered in backend API.",
                    evidence="No health route found across project files",
                )
            )
        return findings


@register_analyzer
class UniversalProductionReadinessAnalyzer(BaseAnalyzer):
    name = "universal-production-readiness"
    description = "Evaluates production readiness, health probes, and runtime configurations"
    category = Category.PRODUCTION_READINESS

    def get_rules(self) -> List[BaseRule]:
        return [MissingHealthCheckRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
