"""Python type annotation checks for backend public interfaces."""

from __future__ import annotations

import ast
from typing import List

from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_rule


@register_rule
class MissingTypeAnnotationsRule(BaseRule):
    """Detects public service or controller functions missing type annotations."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PY-TYPE-001",
                title="Missing type annotations on public function",
                category=Category.TYPING,
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                description="Public function in service or controller module lacks parameter or return type annotations.",
                impact="Decreases readability, prevents static type checkers (mypy/pyright) from catching type bugs, and breaks schema generators.",
                recommendation="Add explicit PEP 484 type annotations for parameters and return types.",
                suggested_fix="def process_order(order_id: str, quantity: int) -> bool:",
                language="python",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            rel_file = context.get_relative_path(py_file)
            # Focus on service / route / controller modules
            if not any(
                term in rel_file.lower()
                for term in ["service", "router", "controller", "api", "handler"]
            ):
                continue

            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Ignore private or magic methods
                    if node.name.startswith("_"):
                        continue
                    # Check return type annotation
                    unannotated_args = [
                        a.arg
                        for a in node.args.args
                        if a.annotation is None and a.arg not in ("self", "cls")
                    ]
                    missing_return = node.returns is None

                    if unannotated_args or missing_return:
                        issues = []
                        if unannotated_args:
                            issues.append(f"untyped parameters ({', '.join(unannotated_args)})")
                        if missing_return:
                            issues.append("missing return type annotation")

                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=node.lineno,
                                description=f"Function '{node.name}' has {', '.join(issues)}.",
                                evidence=f"def {node.name}(...)",
                            )
                        )
        return findings
