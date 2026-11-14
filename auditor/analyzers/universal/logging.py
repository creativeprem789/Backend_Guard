"""Logging practices analysis: sensitive data leakage and unstructured stdout printing."""

from __future__ import annotations

import ast
import re
from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule

SENSITIVE_LOG_PATTERNS = re.compile(
    r"""(?:log|logger|logging|console)\.(?:info|debug|warn|warning|error)\s*\(.*?(?:password|passwd|secret|token|api_key|credit_card|authorization).*?\)""",
    re.IGNORECASE,
)


@register_rule
class SensitiveDataInLogsRule(BaseRule):
    """Detects logging of sensitive credentials, passwords, or tokens."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="LOG-001",
                title="Sensitive credential or token logged",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                description="Potential passwords, secrets, or auth tokens are interpolated into log statements.",
                impact="Log files are commonly aggregated into third-party observability platforms, exposing plain-text credentials to unauthorized personnel.",
                recommendation="Mask, redact, or hash sensitive fields before emitting log records.",
                suggested_fix="Sanitize user payloads and log only non-sensitive identifiers (e.g. user_id).",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        for f in source_files:
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                clean = line.strip()
                if clean.startswith(("#", "//", "/*", "*")):
                    continue
                if SENSITIVE_LOG_PATTERNS.search(line):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Sensitive parameter (password/token/secret) passed directly into log statement.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_rule
class UnstructuredStdoutLoggingRule(BaseRule):
    """Detects standard print() / console.log() calls in backend service code."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="LOG-002",
                title="Raw stdout printing instead of structured logger",
                category=Category.PRODUCTION_READINESS,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="Using print() or console.log() instead of a structured logging framework with log levels.",
                impact="Raw prints lack log levels, timestamps, request correlation IDs, and cannot be filtered or parsed cleanly in production log pipelines.",
                recommendation="Use a standard logging framework (e.g., standard library logging, structlog, winston, or pino).",
                suggested_fix="Replace print(...) with logger.info(...) or structured logger.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # Check Python files
        for py_file in context.get_files_for_language("python"):
            # Exclude cli / scripts / tests
            rel = context.get_relative_path(py_file)
            if any(
                term in rel.lower() for term in ["test", "cli", "script", "migration", "conftest"]
            ):
                continue

            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "print"
                ):
                    findings.append(
                        self.create_finding(
                            file=rel,
                            line=node.lineno,
                            description="print() statement used in backend service code instead of structured logger.",
                            evidence="print(...)",
                        )
                    )

        # Check JS/TS files
        for f in context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        ):
            rel = context.get_relative_path(f)
            if any(term in rel.lower() for term in ["test", "spec", "script"]):
                continue
            lines = context.get_lines(f)
            for idx, line in enumerate(lines, start=1):
                clean = line.strip()
                if clean.startswith("//") or clean.startswith("/*"):
                    continue
                if re.search(r"""\bconsole\.log\s*\(""", line):
                    findings.append(
                        self.create_finding(
                            file=rel,
                            line=idx,
                            description="console.log() used in backend service code instead of structured logger.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_analyzer
class UniversalLoggingAnalyzer(BaseAnalyzer):
    name = "universal-logging"
    description = "Analyzes logging practices, structured logging, and sensitive data leakage"
    category = Category.PRODUCTION_READINESS

    def get_rules(self) -> List[BaseRule]:
        return [SensitiveDataInLogsRule(), UnstructuredStdoutLoggingRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
