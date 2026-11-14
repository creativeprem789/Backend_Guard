"""Database design and access pattern rules: N+1 queries and transaction boundaries."""

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
class NPlusOneQueryRule(BaseRule):
    """Detects database queries executed inside iterative loops (N+1 query antipattern)."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="DB-001",
                title="Potential N+1 query pattern detected in loop",
                category=Category.DATABASE,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                description="Repeated database queries or ORM lookups are executed inside a for/while loop iteration.",
                impact="Drastically multiplies database latency and round-trips; an endpoint returning 100 items executes 101 queries.",
                recommendation="Use eager loading (e.g., joinedload, selectinload) or fetch records in a single batched IN query.",
                suggested_fix="Batch query IDs using .filter(Model.id.in_(ids)) outside the loop or use eager loading.",
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
                if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                            # Look for query methods: .filter, .get, .query, .execute, .find_by
                            if child.func.attr in (
                                "query",
                                "execute",
                                "filter_by",
                                "get",
                                "find",
                                "find_one",
                            ):
                                # If caller is db or session or Model
                                caller_name = ""
                                if isinstance(child.func.value, ast.Name):
                                    caller_name = child.func.value.id
                                elif isinstance(child.func.value, ast.Attribute):
                                    caller_name = child.func.value.attr
                                if any(
                                    db_word in caller_name.lower()
                                    for db_word in ["db", "session", "repo", "cursor"]
                                ):
                                    rel_file = context.get_relative_path(py_file)
                                    findings.append(
                                        self.create_finding(
                                            file=rel_file,
                                            line=child.lineno,
                                            description=f"Database query '{caller_name}.{child.func.attr}()' executed inside loop iteration.",
                                            evidence=f"Loop query at line {child.lineno}",
                                        )
                                    )
                                    break  # One finding per loop is sufficient

        # JS/TS files
        for f in context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        ):
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            in_loop = False
            for idx, line in enumerate(lines, start=1):
                if re.search(r"""\b(?:for\s*\(|while\s*\(|\.forEach\s*\()""", line):
                    in_loop = True
                if in_loop and re.search(
                    r"""await\s+(?:db|repository|prisma|knex)\.[a-zA-Z0-9_]+\s*\(""", line
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Database query awaited inside loop iteration.",
                            evidence=line.strip(),
                        )
                    )
                    in_loop = False
                if "}" in line:
                    in_loop = False
        return findings


@register_rule
class MissingRollbackRule(BaseRule):
    """Detects database transaction blocks without rollback on error."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="DB-002",
                title="Database transaction without explicit rollback on error",
                category=Category.DATABASE,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Transaction commit occurs within try block, but except block does not call rollback().",
                impact="Leaves sessions or database connections in a poisoned or aborted state, locking tables or leaking transactions.",
                recommendation="Always call session.rollback() in exception handlers or use transactional context managers.",
                suggested_fix="Add db.rollback() or session.rollback() inside the except/catch block, or use a 'with session.begin():' context manager.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    has_commit = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                            if child.func.attr == "commit":
                                has_commit = True
                                break

                    if has_commit:
                        # Check except blocks for rollback
                        has_rollback = False
                        for handler in node.handlers:
                            for h_child in ast.walk(handler):
                                if isinstance(h_child, ast.Call) and isinstance(
                                    h_child.func, ast.Attribute
                                ):
                                    if h_child.func.attr == "rollback":
                                        has_rollback = True
                                        break
                        if not has_rollback and node.handlers:
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description="Transaction .commit() present in try-block without matching .rollback() in except handler.",
                                    evidence="try with commit() missing rollback() in except",
                                )
                            )
        return findings


@register_analyzer
class UniversalDatabaseAnalyzer(BaseAnalyzer):
    name = "universal-database"
    description = "Evaluates database access, N+1 query patterns, and transaction safety"
    category = Category.DATABASE

    def get_rules(self) -> List[BaseRule]:
        return [NPlusOneQueryRule(), MissingRollbackRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
