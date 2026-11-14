"""Configuration analysis: environment variable fallback and production debug settings."""

from __future__ import annotations

import ast
from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class ProductionDebugEnabledRule(BaseRule):
    """Detects debug mode explicitly hardcoded to True in application setup."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="CONF-002",
                title="Production debug mode hardcoded to True",
                category=Category.PRODUCTION_READINESS,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Application framework configured with debug=True explicitly hardcoded in source.",
                impact="Debug mode in production exposes interactive web shells, stack traces, and detailed system internals to external users.",
                recommendation="Read debug configuration exclusively from environment variables with a default of False in production.",
                suggested_fix="debug = os.getenv('DEBUG', 'false').lower() == 'true'",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # Check Python files
        for py_file in context.get_files_for_language("python"):
            rel_file = context.get_relative_path(py_file)
            if "test" in rel_file.lower():
                continue

            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                # FastAPI(debug=True) or Flask(__name__, debug=True) or app.run(debug=True)
                if isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if (
                            kw.arg == "debug"
                            and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True
                        ):
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description="debug=True explicitly passed to framework call.",
                                    evidence="debug=True",
                                )
                            )
                # DEBUG = True in settings.py
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "DEBUG":
                            if isinstance(node.value, ast.Constant) and node.value.value is True:
                                findings.append(
                                    self.create_finding(
                                        file=rel_file,
                                        line=node.lineno,
                                        description="DEBUG = True explicitly hardcoded.",
                                        evidence="DEBUG = True",
                                    )
                                )
        return findings


@register_analyzer
class UniversalConfigurationAnalyzer(BaseAnalyzer):
    name = "universal-configuration"
    description = "Analyzes configuration practices and production flags"
    category = Category.PRODUCTION_READINESS

    def get_rules(self) -> List[BaseRule]:
        return [ProductionDebugEnabledRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
