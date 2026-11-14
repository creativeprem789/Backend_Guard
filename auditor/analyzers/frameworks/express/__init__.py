"""Express framework analyzer and rules."""

from __future__ import annotations

import re
from typing import List

from auditor.analyzers.languages.javascript.parser import parse_js_file
from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class ExpressMissingErrorMiddlewareRule(BaseRule):
    """Detects Express applications missing standard 4-argument error handling middleware."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="EXPRESS-001",
                title="Missing global error handling middleware in Express",
                category=Category.ERROR_HANDLING,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Express server registers routes but contains no 4-argument error-handling middleware (err, req, res, next).",
                impact="Uncaught errors fall back to default HTML error pages, leaking internal stack traces or hanging client requests.",
                recommendation="Register a centralized 4-parameter error handler at the end of the middleware chain.",
                suggested_fix="app.use((err, req, res, next) => { logger.error(err); res.status(500).json({ error: 'Internal Server Error' }); });",
                framework="express",
                language="javascript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        js_files = context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        )

        has_routes = False
        has_error_middleware = False
        server_entry_file = None

        for f in js_files:
            data = context.get_js_structure(f) or parse_js_file(f)
            context.set_js_structure(f, data)

            if data.get("expressRoutes"):
                has_routes = True
            if data.get("expressErrorMiddleware"):
                has_error_middleware = True

            rel = context.get_relative_path(f).lower()
            if any(
                term in rel
                for term in ["app.js", "server.js", "index.js", "app.ts", "server.ts", "index.ts"]
            ):
                server_entry_file = f

        if has_routes and not has_error_middleware:
            target_path = server_entry_file or (js_files[0] if js_files else context.root_path)
            findings.append(
                self.create_finding(
                    file=context.get_relative_path(target_path),
                    line=1,
                    description="Express application defines routes but lacks a centralized (err, req, res, next) error handler.",
                    evidence="No 4-parameter middleware registered across application files",
                )
            )
        return findings


@register_rule
class ExpressAsyncRouteWithoutTryCatchRule(BaseRule):
    """Detects async Express route handlers without try/catch or async handler wrapper."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="EXPRESS-003",
                title="Async Express route handler without error handling",
                category=Category.ERROR_HANDLING,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Express 4 async route handlers do not catch promise rejections automatically; unhandled errors hang connections indefinitely.",
                impact="A thrown exception inside an async route handler leaves the client request hanging until socket timeout, exhausting server sockets.",
                recommendation="Wrap the async handler with express-async-handler or enclose the body in try/catch calling next(err).",
                suggested_fix="Wrap the handler with asyncHandler(async (req, res) => { ... }) or add try/catch.",
                framework="express",
                language="javascript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        js_files = context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        )

        for f in js_files:
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)

            for idx, line in enumerate(lines, start=1):
                # Detect async handler registered directly on router or app
                if re.search(
                    r"""\b(?:app|router)\.(?:get|post|put|delete|patch)\s*\(\s*['"][^'"]+['"]\s*,\s*async\s*\(""",
                    line,
                ):
                    # Check next 15 lines for try {
                    next_lines = "".join(lines[idx : min(idx + 15, len(lines))])
                    if "try" not in next_lines and "asyncHandler" not in line:
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=idx,
                                description="Async route handler lacks try/catch or asyncHandler wrapper; unhandled rejections will hang requests.",
                                evidence=line.strip(),
                            )
                        )
        return findings


@register_analyzer
class ExpressFrameworkAnalyzer(BaseAnalyzer):
    name = "express-framework"
    description = "Framework analysis for Express.js: error middleware, async route safety, and middleware ordering"
    framework = "express"

    def get_rules(self) -> List[BaseRule]:
        return [
            ExpressMissingErrorMiddlewareRule(),
            ExpressAsyncRouteWithoutTryCatchRule(),
        ]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
