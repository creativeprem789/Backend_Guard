"""Python language-specific rules and analyzer implementation."""

from __future__ import annotations

import ast
from typing import List

from auditor.analyzers.languages.python.async_checks import SyncBlockingInAsyncRule
from auditor.analyzers.languages.python.imports import populate_python_dependency_graph
from auditor.analyzers.languages.python.typing import MissingTypeAnnotationsRule
from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class MutableDefaultArgumentRule(BaseRule):
    """Detects mutable default arguments in Python function definitions."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PY-001",
                title="Dangerous mutable default argument",
                category=Category.PATTERNS,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Function uses mutable default arguments (e.g. list [], dict {}, set ()), which retain mutations across calls.",
                impact="Mutations leak across separate HTTP requests or background jobs, corrupting state and causing unpredictable data bugs.",
                recommendation="Use None as default parameter value and initialize the mutable object inside the function body.",
                suggested_fix="def func(items: Optional[List] = None): items = items if items is not None else []",
                language="python",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=default.lineno,
                                    description=f"Function '{node.name}' uses mutable default argument.",
                                    evidence=f"def {node.name}(...)",
                                )
                            )
        return findings


@register_rule
class UnsafeDeserializationRule(BaseRule):
    """Detects unsafe pickle or yaml deserialization."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PY-002",
                title="Unsafe deserialization via pickle or raw yaml.load",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                description="Deserializing untrusted data with pickle.loads or yaml.load without SafeLoader allows arbitrary code execution.",
                impact="Attackers can craft malicious serialized payloads to execute arbitrary shell commands inside your server.",
                recommendation="Use safe serialization formats like JSON, or yaml.safe_load(). Avoid pickle for untrusted network input.",
                suggested_fix="Use yaml.safe_load(data) instead of yaml.load(data, Loader=...).",
                language="python",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # pickle.loads(...)
                    if isinstance(node.func, ast.Attribute) and node.func.attr in ("loads", "load"):
                        if isinstance(node.func.value, ast.Name) and node.func.value.id in (
                            "pickle",
                            "_pickle",
                            "cPickle",
                        ):
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description=f"Unsafe {node.func.value.id}.{node.func.attr}() deserialization.",
                                    evidence=f"{node.func.value.id}.{node.func.attr}(...)",
                                )
                            )
                    # yaml.load without SafeLoader
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "load":
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == "yaml":
                            has_safe_loader = False
                            for kw in node.keywords:
                                if kw.arg == "Loader":
                                    if (
                                        isinstance(kw.value, ast.Attribute)
                                        and "Safe" in kw.value.attr
                                    ):
                                        has_safe_loader = True
                                    elif isinstance(kw.value, ast.Name) and "Safe" in kw.value.id:
                                        has_safe_loader = True
                            if not has_safe_loader:
                                rel_file = context.get_relative_path(py_file)
                                findings.append(
                                    self.create_finding(
                                        file=rel_file,
                                        line=node.lineno,
                                        description="yaml.load() invoked without SafeLoader.",
                                        evidence="yaml.load(...)",
                                    )
                                )
        return findings


@register_rule
class WildcardImportRule(BaseRule):
    """Detects wildcard imports polluting the namespace."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PY-003",
                title="Wildcard import polluting namespace",
                category=Category.PATTERNS,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="Wildcard imports ('from module import *') mask names, pollute scope, and defeat static analysis.",
                impact="Leads to name clashes, shadow definitions, and confuses developers and static analysis tools.",
                recommendation="Explicitly import only required identifiers or import the module itself.",
                suggested_fix="from module import specific_item",
                language="python",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description=f"Wildcard import 'from {node.module} import *' pollutes namespace.",
                                    evidence=f"from {node.module} import *",
                                )
                            )
        return findings


@register_analyzer
class PythonLanguageAnalyzer(BaseAnalyzer):
    name = "python-language"
    description = "Static analysis for Python codebases: async safety, typing, mutable defaults, and deserialization"
    language = "python"

    def get_rules(self) -> List[BaseRule]:
        return [
            SyncBlockingInAsyncRule(),
            MissingTypeAnnotationsRule(),
            MutableDefaultArgumentRule(),
            UnsafeDeserializationRule(),
            WildcardImportRule(),
        ]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        populate_python_dependency_graph(context)
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
