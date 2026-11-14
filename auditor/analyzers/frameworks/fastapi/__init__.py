"""FastAPI framework analyzer and rules."""

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
class FastApiRawSqlInRouteRule(BaseRule):
    """Detects direct raw SQL execution inside FastAPI route endpoints."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="FASTAPI-001",
                title="Direct raw SQL execution inside route endpoint",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="FastAPI endpoint directly executes raw SQL query strings instead of delegating to a repository or ORM service.",
                impact="Violates separation of concerns, mixes HTTP transport with database schemas, and makes unit testing endpoints difficult.",
                recommendation="Move database queries into a dedicated repository or service class injected via Depends().",
                suggested_fix="Create a UserRepository and inject it into the route handler via Depends(get_user_repo).",
                framework="fastapi",
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
                    # Check if decorated as router endpoint: @router.get/post/etc.
                    is_endpoint = False
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            if dec.func.attr in (
                                "get",
                                "post",
                                "put",
                                "delete",
                                "patch",
                                "api_route",
                            ):
                                is_endpoint = True
                                break

                    if is_endpoint:
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call) and isinstance(
                                child.func, ast.Attribute
                            ):
                                if child.func.attr in ("execute", "raw"):
                                    if child.args:
                                        first_arg = child.args[0]
                                        is_raw_sql = False
                                        if isinstance(
                                            first_arg, (ast.Constant, ast.JoinedStr, ast.BinOp)
                                        ):
                                            is_raw_sql = True
                                        elif isinstance(first_arg, ast.Name):
                                            # Variable named query or sql, or lookup in function scope
                                            if any(
                                                term in first_arg.id.lower()
                                                for term in ["query", "sql"]
                                            ):
                                                is_raw_sql = True
                                        if is_raw_sql:
                                            rel_file = context.get_relative_path(py_file)
                                            findings.append(
                                                self.create_finding(
                                                    file=rel_file,
                                                    line=child.lineno,
                                                    description=f"Raw SQL execution inside route '{node.name}'.",
                                                    evidence=f"db.{child.func.attr}(...) in @router endpoint",
                                                )
                                            )
        return findings


@register_rule
class FastApiMissingResponseModelRule(BaseRule):
    """Detects mutating route endpoints without response_model or status_code."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="FASTAPI-002",
                title="Missing response_model on route endpoint",
                category=Category.API_DESIGN,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="FastAPI route endpoint does not declare a response_model, bypassing automatic schema filtering and OpenAPI documentation.",
                impact="Internal model fields (like hashed passwords or internal IDs) can be accidentally leaked to clients in responses.",
                recommendation="Explicitly specify response_model=UserResponse in the router decorator.",
                suggested_fix="@router.post('/users', response_model=UserResponse, status_code=201)",
                framework="fastapi",
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
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            if dec.func.attr in ("post", "put"):
                                has_response_model = any(
                                    kw.arg == "response_model" for kw in dec.keywords
                                )
                                if not has_response_model:
                                    rel_file = context.get_relative_path(py_file)
                                    findings.append(
                                        self.create_finding(
                                            file=rel_file,
                                            line=node.lineno,
                                            description=f"FastAPI mutating endpoint '{node.name}' has no response_model declared.",
                                            evidence=f"@{dec.func.attr}(...) without response_model",
                                        )
                                    )
        return findings


@register_analyzer
class FastApiFrameworkAnalyzer(BaseAnalyzer):
    name = "fastapi-framework"
    description = (
        "Framework analysis for FastAPI: route boundaries, response models, and async hygiene"
    )
    framework = "fastapi"
    language = "python"

    def get_rules(self) -> List[BaseRule]:
        return [FastApiRawSqlInRouteRule(), FastApiMissingResponseModelRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
