"""TypeScript language-specific rules and analyzer implementation."""

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
class ExcessiveAnyTypeRule(BaseRule):
    """Detects excessive usage of unsafe 'any' type in TypeScript services."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="TS-001",
                title="Excessive use of unsafe 'any' type",
                category=Category.TYPING,
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                description="Use of explicit 'any' type suppresses compile-time type checking and defeats TypeScript's safety guarantees.",
                impact="Runtime type mismatches, null pointer exceptions, and unvalidated payloads bypass TypeScript compiler checks.",
                recommendation="Replace 'any' with 'unknown', a generic parameter, or an explicit interface / union type.",
                suggested_fix="Define a specific interface or type: interface UserPayload { id: string; }",
                language="typescript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        ts_files = context.get_files_for_language("typescript")

        for f in ts_files:
            rel_file = context.get_relative_path(f)
            data = context.get_js_structure(f) or parse_js_file(f)
            context.set_js_structure(f, data)

            any_entries = data.get("anyTypes", [])
            if any_entries:
                for entry in any_entries:
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=entry["line"],
                            description=f"Explicit 'any' type annotation used: '{entry['text']}'.",
                            evidence=entry["text"],
                        )
                    )
        return findings


@register_analyzer
class TypeScriptLanguageAnalyzer(BaseAnalyzer):
    name = "typescript-language"
    description = "Static analysis for TypeScript codebases: type strictness, interface safety, and promise hygiene"
    language = "typescript"

    def get_rules(self) -> List[BaseRule]:
        return [ExcessiveAnyTypeRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        populate_js_dependency_graph(context)
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
