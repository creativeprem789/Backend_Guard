"""Error handling analysis: silent swallowing, broad catching, and stack trace leakage."""

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


@register_rule
class SilentExceptionSwallowingRule(BaseRule):
    """Detects empty catch/except blocks that swallow errors silently."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="ERR-001",
                title="Silent exception swallowing",
                category=Category.ERROR_HANDLING,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Exceptions are caught with an empty handler or only a 'pass' statement, hiding failures completely.",
                impact="Critical bugs, database corruptions, and network timeouts are hidden, making production debugging almost impossible.",
                recommendation="Always log the exception with stack trace or re-raise it.",
                suggested_fix="Log the exception with logger.exception('Context description') or re-raise.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # Python files
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    # Check if body is just `pass` or empty
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description="Exception caught and swallowed silently with 'pass'.",
                                evidence="except ...: pass",
                            )
                        )

        # JS/TS files
        for f in context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        ):
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                if re.search(r"""catch\s*\([^)]*\)\s*\{\s*\}""", line):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Empty catch block silently swallowing exceptions.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_rule
class BroadExceptionCatchingRule(BaseRule):
    """Detects broad Exception/BaseException catches without logging or re-raising."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="ERR-002",
                title="Overly broad exception catching without re-raise",
                category=Category.ERROR_HANDLING,
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                description="Catching broad 'Exception' or 'BaseException' at low abstraction levels without logging or re-raising.",
                impact="Catches unexpected bugs, system interruptions, and syntax/type errors that should fail loudly.",
                recommendation="Catch specific exceptions (e.g. ValueError, ConnectionError) or log the full traceback.",
                suggested_fix="Catch specific domain/library exceptions instead of generic Exception.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        # Bare except:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description="Bare 'except:' statement catches SystemExit, KeyboardInterrupt, and all errors.",
                                evidence="bare except:",
                            )
                        )
                    elif isinstance(node.type, ast.Name) and node.type.id in ("BaseException",):
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Catching '{node.type.id}' interferes with process termination signals.",
                                evidence=f"except {node.type.id}:",
                            )
                        )
        return findings


@register_rule
class StackTraceLeakedRule(BaseRule):
    """Detects internal error details and stack traces returned in HTTP responses."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="ERR-003",
                title="Internal stack trace or raw error leaked to client",
                category=Category.ERROR_HANDLING,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                description="Raw exception messages or stack traces returned directly in API JSON responses.",
                impact="Exposes internal directory structures, library versions, database schema names, and secret values to attackers.",
                recommendation="Return sanitized error messages and correlation IDs to clients, keeping detailed stack traces in server logs.",
                suggested_fix="Return a generic user-friendly message and log the full error internally.",
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
                if re.search(
                    r"""['"]?(?:detail|message|error)['"]?\s*:\s*(?:str\s*\(\s*[a-zA-Z0-9_]+\s*\)|repr\s*\(\s*[a-zA-Z0-9_]+\s*\)|err\.stack|traceback\.format_exc)""",
                    line,
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Raw error object or traceback formatted into client response.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_analyzer
class UniversalErrorHandlingAnalyzer(BaseAnalyzer):
    name = "universal-error-handling"
    description = "Analyzes exception handling, swallowing, and error response sanitization"
    category = Category.ERROR_HANDLING

    def get_rules(self) -> List[BaseRule]:
        return [
            SilentExceptionSwallowingRule(),
            BroadExceptionCatchingRule(),
            StackTraceLeakedRule(),
        ]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
