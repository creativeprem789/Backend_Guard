"""Testing practices analysis: presence of test suites and empty/vacuous test cases."""

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
class MissingTestSuiteRule(BaseRule):
    """Detects projects with substantial backend source code but zero test files."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="TEST-001",
                title="Missing automated test suite",
                category=Category.TESTING,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="The project contains multiple backend source files but no automated test files were discovered.",
                impact="Without automated tests, code changes cannot be validated for regressions, slowing down deployment frequency.",
                recommendation="Establish an automated test suite using pytest, jest, or standard testing frameworks.",
                suggested_fix="Create a tests/ directory and add unit/integration tests for critical business logic.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        test_files = [
            f
            for f in source_files
            if any(term in f.name.lower() for term in ["test_", "_test.", ".spec.", ".test."])
            or any(part in ("tests", "test", "__tests__", "spec") for part in f.parts)
        ]

        non_test_sources = [f for f in source_files if f not in test_files]

        # If there are at least 3 non-test source files and 0 test files
        if len(non_test_sources) >= 3 and len(test_files) == 0:
            findings.append(
                self.create_finding(
                    file=context.get_relative_path(context.root_path),
                    line=1,
                    description=f"Project contains {len(non_test_sources)} source files but no test files were detected.",
                    evidence=f"0 test files found for {len(non_test_sources)} source files",
                )
            )
        return findings


@register_rule
class VacuousTestRule(BaseRule):
    """Detects test functions containing zero assertions."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="TEST-002",
                title="Vacuous test case with no assertions",
                category=Category.TESTING,
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                description="Test function executes code but contains no assert statement or expectation checks.",
                impact="Test gives false confidence by always passing even when business logic produces invalid results.",
                recommendation="Add explicit assertion checks (assert x == y or expect(x).toBe(y)).",
                suggested_fix="Assert the expected state or return value of the tested function.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            rel_file = context.get_relative_path(py_file)
            if "test" not in rel_file.lower():
                continue

            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("test_") or node.name.endswith("_test"):
                        # Check for assert statements or self.assert* calls
                        has_assert = False
                        for child in ast.walk(node):
                            if isinstance(child, ast.Assert):
                                has_assert = True
                                break
                            if isinstance(child, ast.Call) and isinstance(
                                child.func, ast.Attribute
                            ):
                                if child.func.attr.startswith("assert"):
                                    has_assert = True
                                    break
                        if not has_assert:
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description=f"Test function '{node.name}' has no assert statements.",
                                    evidence=f"def {node.name}()",
                                )
                            )
        return findings


@register_analyzer
class UniversalTestingAnalyzer(BaseAnalyzer):
    name = "universal-testing"
    description = "Evaluates test suite presence, test coverage indicators, and test quality"
    category = Category.TESTING

    def get_rules(self) -> List[BaseRule]:
        return [MissingTestSuiteRule(), VacuousTestRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
