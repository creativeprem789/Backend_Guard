"""JavaScript language-specific rules and analyzer implementation."""

from __future__ import annotations

from typing import List

from auditor.analyzers.languages.javascript.imports import populate_js_dependency_graph
from auditor.analyzers.languages.javascript.parser import parse_js_file
from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class SyncBlockingInJsRule(BaseRule):
    """Detects synchronous blocking operations (fs.readFileSync, etc.) in server code."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="JS-001",
                title="Synchronous blocking I/O call in Node.js server",
                category=Category.ASYNC_CONCURRENCY,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Synchronous calls like fs.readFileSync, fs.writeFileSync, or crypto.pbkdf2Sync block the single Node.js event loop thread.",
                impact="All concurrent client requests are completely stalled while the synchronous I/O operation finishes, degrading server throughput.",
                recommendation="Use asynchronous non-blocking versions: fs.promises.readFile() with async/await.",
                suggested_fix="const data = await fs.promises.readFile(filePath, 'utf-8');",
                language="javascript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        js_files = context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        )

        for f in js_files:
            rel_file = context.get_relative_path(f)
            data = context.get_js_structure(f) or parse_js_file(f)
            context.set_js_structure(f, data)

            for call in data.get("blockingCalls", []):
                findings.append(
                    self.create_finding(
                        file=rel_file,
                        line=call["line"],
                        description=f"Synchronous blocking call detected: '{call['text']}'.",
                        evidence=call["text"],
                    )
                )
        return findings


@register_rule
class UnhandledPromiseRule(BaseRule):
    """Detects unhandled promises without .catch() handlers."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="JS-002",
                title="Unhandled promise rejection risk",
                category=Category.ERROR_HANDLING,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                description="Promise chain constructed using .then() without a matching .catch() handler.",
                impact="Unhandled promise rejections crash the Node.js process (unhandledRejection event terminates runtime in modern Node versions).",
                recommendation="Always attach a .catch() handler to promise chains or use try/catch with async/await.",
                suggested_fix="promise.then(result => ...).catch(err => logger.error(err));",
                language="javascript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        js_files = context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        )

        for f in js_files:
            rel_file = context.get_relative_path(f)
            data = context.get_js_structure(f) or parse_js_file(f)
            context.set_js_structure(f, data)

            for p in data.get("unhandledPromises", []):
                findings.append(
                    self.create_finding(
                        file=rel_file,
                        line=p["line"],
                        description="Promise .then() without explicit .catch() handler.",
                        evidence=p["text"],
                    )
                )
        return findings


@register_rule
class DangerousEvalRule(BaseRule):
    """Detects dangerous eval() or Function constructor in JavaScript."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="JS-003",
                title="Dangerous dynamic code evaluation (eval / Function)",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                description="Dynamic evaluation of code strings via eval() or new Function() allows code injection.",
                impact="Remote code execution allowing attackers to execute arbitrary system commands or exfiltrate environment credentials.",
                recommendation="Never use eval() or new Function() to execute dynamic strings or parse JSON. Use JSON.parse().",
                suggested_fix="Use JSON.parse() or a safe parser instead of eval().",
                language="javascript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        js_files = context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        )

        for f in js_files:
            rel_file = context.get_relative_path(f)
            data = context.get_js_structure(f) or parse_js_file(f)
            context.set_js_structure(f, data)

            for e in data.get("evalCalls", []):
                findings.append(
                    self.create_finding(
                        file=rel_file,
                        line=e["line"],
                        description=f"eval() or new Function() used: '{e['text']}'.",
                        evidence=e["text"],
                    )
                )
        return findings


@register_analyzer
class JavaScriptLanguageAnalyzer(BaseAnalyzer):
    name = "javascript-language"
    description = "Static analysis for JavaScript backend codebases: blocking I/O, promise rejections, and eval safety"
    language = "javascript"

    def get_rules(self) -> List[BaseRule]:
        return [SyncBlockingInJsRule(), UnhandledPromiseRule(), DangerousEvalRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        populate_js_dependency_graph(context)
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
