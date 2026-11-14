"""API design analysis: pagination, response semantics, and error codes."""

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
class MissingPaginationRule(BaseRule):
    """Detects list endpoints returning unbounded collections without pagination."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="API-001",
                title="Missing pagination on collection endpoint",
                category=Category.API_DESIGN,
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                description="List/collection endpoint executes unbounded .all() or lacks limit/offset/cursor parameters.",
                impact="As database tables grow, returning entire tables causes severe memory bloat, high serialization latency, and server crashes.",
                recommendation="Implement limit/offset, page/size, or cursor-based pagination parameters with a sensible default limit.",
                suggested_fix="Accept limit: int = 50 and offset: int = 0 parameters and apply .limit(limit).offset(offset) to queries.",
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
                    # Check if decorated as router endpoint: @router.get("/...") or @app.get(...)
                    is_endpoint = False
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                            if dec.func.attr in ("get", "route"):
                                is_endpoint = True
                                break

                    if is_endpoint:
                        # Check if function returns .all() without limit parameter
                        param_names = [arg.arg for arg in node.args.args]
                        has_pagination_param = any(
                            p in param_names
                            for p in ["limit", "page", "size", "offset", "cursor", "skip"]
                        )
                        if not has_pagination_param:
                            for child in ast.walk(node):
                                if isinstance(child, ast.Call) and isinstance(
                                    child.func, ast.Attribute
                                ):
                                    if child.func.attr == "all" and not has_pagination_param:
                                        rel_file = context.get_relative_path(py_file)
                                        findings.append(
                                            self.create_finding(
                                                file=rel_file,
                                                line=node.lineno,
                                                description=f"Endpoint '{node.name}' queries unbounded collection with .all() without pagination arguments.",
                                                evidence=f"def {node.name}(...)",
                                            )
                                        )
                                        break
        return findings


@register_rule
class InconsistentErrorStatusRule(BaseRule):
    """Detects endpoints returning 200 OK with error payload."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="API-002",
                title="HTTP 200 OK returned with error payload",
                category=Category.API_DESIGN,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="Endpoint returns HTTP 200 or default status code while sending an error or failure response body.",
                impact="Clients, API gateways, and monitoring proxies cannot detect failures through standard HTTP status metrics (4xx/5xx).",
                recommendation="Use proper HTTP status codes: 400 Bad Request, 404 Not Found, 401 Unauthorized, etc.",
                suggested_fix="Return or raise appropriate HTTP status code (e.g., raise HTTPException(status_code=400, detail='...')).",
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
                if clean.startswith(("#", "//")):
                    continue
                # res.status(200).json({ error: ... }) or return {"success": False, "error": ...}
                if re.search(
                    r"""res\.status\s*\(\s*200\s*\)\.json\s*\(\s*\{.*(?:error|err):""", clean
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="res.status(200) returned with error payload in JSON.",
                            evidence=clean,
                        )
                    )
                elif re.search(
                    r"""return\s*\{.*['"]success['"]\s*:\s*(?:False|false)\s*,\s*['"]error['"]""",
                    clean,
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Default return payload returns {'success': false, 'error': ...} instead of raising HTTP exception.",
                            evidence=clean,
                        )
                    )
        return findings


@register_analyzer
class UniversalApiDesignAnalyzer(BaseAnalyzer):
    name = "universal-api-design"
    description = "Evaluates API design semantics, pagination, and HTTP status codes"
    category = Category.API_DESIGN

    def get_rules(self) -> List[BaseRule]:
        return [MissingPaginationRule(), InconsistentErrorStatusRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
