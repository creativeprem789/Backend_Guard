"""NestJS framework analyzer and rules."""

from __future__ import annotations

import re
from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class NestJsMissingInjectableRule(BaseRule):
    """Detects service classes in NestJS missing the @Injectable() decorator."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="NEST-001",
                title="Service class missing @Injectable() decorator",
                category=Category.PATTERNS,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="NestJS service class is not decorated with @Injectable(), preventing the IoC container from managing its lifecycle.",
                impact="NestJS cannot inject dependencies into this class or provide it to controllers, resulting in runtime DI resolution errors.",
                recommendation="Add @Injectable() decorator above the service class declaration.",
                suggested_fix="@Injectable()\nexport class UserService { ... }",
                framework="nestjs",
                language="typescript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        ts_files = context.get_files_for_language("typescript")

        for f in ts_files:
            rel_file = context.get_relative_path(f)
            if not rel_file.endswith(".service.ts"):
                continue

            lines = context.get_lines(f)
            has_injectable = any("@Injectable()" in line for line in lines)

            for idx, line in enumerate(lines, start=1):
                if re.search(r"""export\s+class\s+[a-zA-Z0-9_]+Service\b""", line):
                    if not has_injectable:
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=idx,
                                description=f"NestJS service in '{rel_file}' is missing @Injectable() decorator.",
                                evidence=line.strip(),
                            )
                        )
        return findings


@register_rule
class NestJsDirectDbInControllerRule(BaseRule):
    """Detects direct database queries executed in NestJS @Controller()."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="NEST-002",
                title="Direct database access inside NestJS controller",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="NestJS controller directly accesses database models or ORM repositories rather than delegating to an injected service.",
                impact="Breaks NestJS modular architecture, makes controllers tightly coupled to the database schema, and hampers testing.",
                recommendation="Delegate database operations to an injected service class.",
                suggested_fix="Inject UserService in the constructor and call this.userService.getUserById(id).",
                framework="nestjs",
                language="typescript",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        ts_files = context.get_files_for_language("typescript")

        for f in ts_files:
            rel_file = context.get_relative_path(f)
            if not rel_file.endswith(".controller.ts"):
                continue

            lines = context.get_lines(f)
            for idx, line in enumerate(lines, start=1):
                if re.search(
                    r"""\b(?:this\.(?:repository|repo|prisma|dataSource)\.[a-zA-Z0-9_]+\s*\()""",
                    line,
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description=f"Direct database / ORM access inside controller in '{rel_file}'.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_analyzer
class NestJsFrameworkAnalyzer(BaseAnalyzer):
    name = "nestjs-framework"
    description = (
        "Framework analysis for NestJS: dependency injection, modules, and controller boundaries"
    )
    framework = "nestjs"
    language = "typescript"

    def get_rules(self) -> List[BaseRule]:
        return [NestJsMissingInjectableRule(), NestJsDirectDbInControllerRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
