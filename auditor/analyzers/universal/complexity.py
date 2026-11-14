"""Complexity analysis: cyclomatic complexity, function length, and nesting depth."""

from __future__ import annotations

import ast
from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


def calculate_cyclomatic_complexity(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Calculate McCabe cyclomatic complexity for a Python function."""
    complexity = 1
    for child in ast.walk(func_node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    return complexity


def get_max_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Compute maximum indentation/nesting level inside a function."""
    max_d = current_depth
    for child in ast.iter_child_nodes(node):
        next_d = current_depth
        if isinstance(
            child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With, ast.AsyncWith)
        ):
            next_d = current_depth + 1
        sub_max = get_max_nesting_depth(child, next_d)
        if sub_max > max_d:
            max_d = sub_max
    return max_d


@register_rule
class CyclomaticComplexityRule(BaseRule):
    """Detects functions with excessive cyclomatic complexity."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="CMPLX-001",
                title="Excessive cyclomatic complexity in function",
                category=Category.COMPLEXITY,
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                description="Function has too many decision points and branches, making it hard to test and maintain.",
                impact="Complex functions hide edge-case bugs, are prone to regressions, and require exponential test cases to cover all paths.",
                recommendation="Break down complex logic into smaller helper functions with early returns or table-driven dispatch.",
                suggested_fix="Extract sub-logic into cohesive private helper functions or use guard clauses.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        threshold = context.config.complexity.max_cyclomatic_complexity

        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    c = calculate_cyclomatic_complexity(node)
                    if c > threshold:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Function '{node.name}' has cyclomatic complexity of {c} (exceeds threshold of {threshold}).",
                                evidence=f"Complexity: {c}, Threshold: {threshold}",
                            )
                        )
        return findings


@register_rule
class LongFunctionRule(BaseRule):
    """Detects functions exceeding maximum line length."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="CMPLX-002",
                title="Function exceeds maximum line threshold",
                category=Category.COMPLEXITY,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="Function exceeds reasonable line length threshold, reducing readability and separation of concerns.",
                impact="Long functions often mix multiple abstraction levels, making code comprehension and review difficult.",
                recommendation="Decompose the function into smaller, single-purpose functions.",
                suggested_fix="Extract sections of the function into well-named private helper functions.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        max_lines = context.config.complexity.max_function_lines

        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    lines = (node.end_lineno or node.lineno) - node.lineno + 1
                    if lines > max_lines:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Function '{node.name}' is {lines} lines long (maximum recommended is {max_lines}).",
                                evidence=f"Function lines: {lines}, Max allowed: {max_lines}",
                            )
                        )
        return findings


@register_rule
class DeepNestingRule(BaseRule):
    """Detects deeply nested blocks (Arrow Antipattern)."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="CMPLX-003",
                title="Deeply nested control structures (Arrow antipattern)",
                category=Category.COMPLEXITY,
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                description="Function contains deeply nested control flow blocks exceeding threshold depth.",
                impact="Deep nesting strains cognitive load, increases indentation, and makes following execution paths treacherous.",
                recommendation="Use guard clauses and early returns to flatten indentation levels.",
                suggested_fix="Invert if-conditions to return early instead of wrapping large code blocks in nested statements.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        max_depth = context.config.complexity.max_nested_blocks

        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depth = get_max_nesting_depth(node)
                    if depth > max_depth:
                        rel_file = context.get_relative_path(py_file)
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Function '{node.name}' has nesting depth of {depth} (maximum recommended is {max_depth}).",
                                evidence=f"Nesting depth: {depth}, Max allowed: {max_depth}",
                            )
                        )
        return findings


@register_analyzer
class UniversalComplexityAnalyzer(BaseAnalyzer):
    name = "universal-complexity"
    description = "Analyzes cyclomatic complexity, function lengths, and control flow depth"
    category = Category.COMPLEXITY

    def get_rules(self) -> List[BaseRule]:
        return [CyclomaticComplexityRule(), LongFunctionRule(), DeepNestingRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
