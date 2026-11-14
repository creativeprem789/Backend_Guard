"""SOLID principle evaluation rules."""

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
class GodClassRule(BaseRule):
    """Detects God classes violating Single Responsibility Principle."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SOLID-001",
                title="Single Responsibility Principle: God class detected",
                category=Category.SOLID,
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                description="Class contains an excessively high number of methods and responsibilities, indicating poor cohesion.",
                impact="Large monolithic classes are difficult to test, maintain, understand, and frequently become merge conflict hotspots.",
                recommendation="Decompose the class into smaller, cohesive domain services or delegate sub-tasks to specialized components.",
                suggested_fix="Extract related methods into separate service or utility classes and use composition.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [
                        n
                        for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    # High threshold to prevent false positives: > 15 methods and > 250 lines
                    class_lines = (node.end_lineno or node.lineno) - node.lineno + 1
                    if len(methods) >= 15 and class_lines >= 250:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Class '{node.name}' has {len(methods)} methods and spans {class_lines} lines, showing symptoms of a God Class.",
                                evidence=f"Methods count: {len(methods)}, Class length: {class_lines} lines",
                            )
                        )
        return findings


@register_rule
class TypeSwitchingRule(BaseRule):
    """Detects long type-switching cascades violating Open/Closed Principle."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SOLID-002",
                title="Open/Closed Principle: Type-checking cascade detected",
                category=Category.SOLID,
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                description="Function uses a long chain of explicit type-checks (isinstance / typeof) instead of polymorphism or strategy pattern.",
                impact="Adding new types requires modifying existing branching logic, violating the Open/Closed Principle and increasing regression risk.",
                recommendation="Replace explicit type checks with polymorphic dispatch, a dictionary mapping, or the Strategy pattern.",
                suggested_fix="Define a common method on the target types or use a registry/strategy map.",
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
                    isinstance_count = 0
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            if isinstance(child.func, ast.Name) and child.func.id == "isinstance":
                                isinstance_count += 1
                    if isinstance_count >= 5:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Function '{node.name}' contains {isinstance_count} isinstance type checks, suggesting an Open/Closed violation.",
                                evidence=f"{isinstance_count} isinstance checks within function {node.name}",
                            )
                        )
        return findings


@register_analyzer
class UniversalSolidAnalyzer(BaseAnalyzer):
    name = "universal-solid"
    description = "Evaluates SOLID design principles across backend services"
    category = Category.SOLID

    def get_rules(self) -> List[BaseRule]:
        return [GodClassRule(), TypeSwitchingRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
