"""Universal architectural rules evaluating layers, dependencies, and boundaries."""

from __future__ import annotations

from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class PresentationToInfraRule(BaseRule):
    """Detects presentation layer directly coupling to infrastructure."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="ARCH-001",
                title="Direct presentation to infrastructure coupling",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Presentation layer (controllers/routers) directly imports infrastructure or raw database modules, bypassing domain/service abstraction.",
                impact="High coupling between HTTP delivery mechanics and infrastructure details makes business logic difficult to test, reuse, or refactor.",
                recommendation="Introduce a service or repository layer to isolate infrastructure details from HTTP controllers.",
                suggested_fix="Inject or call a service/repository interface rather than directly importing database clients or drivers in route handlers.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        violations = context.dependency_graph.check_layer_violations()
        for v in violations:
            if "Presentation layer directly couples" in v["reason"]:
                from_node = context.dependency_graph.nodes.get(v["from"])
                if from_node:
                    rel_file = context.get_relative_path(from_node.file_path)
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=1,
                            description=f"Route/Controller in '{rel_file}' directly imports infrastructure module '{v['to']}'.",
                            evidence=v["reason"],
                        )
                    )
        return findings


@register_rule
class CircularDependencyRule(BaseRule):
    """Detects circular dependency cycles between project modules."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="ARCH-003",
                title="Circular module dependency cycle detected",
                category=Category.ARCHITECTURE,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="A circular import loop exists between two or more modules in the project.",
                impact="Circular dependencies lead to runtime import errors, tight coupling, difficult refactoring, and unpredictable initialization order.",
                recommendation="Break the cycle by extracting shared types/interfaces to a common module or applying Dependency Inversion.",
                suggested_fix="Refactor the shared dependency into a separate utility or interface module that both modules can import without mutual recursion.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        cycles = context.dependency_graph.find_cycles()
        for cycle in cycles:
            first_mod = cycle[0]
            node = context.dependency_graph.nodes.get(first_mod)
            file_path = str(node.file_path) if node else first_mod
            rel_file = context.get_relative_path(file_path)
            cycle_str = " -> ".join(cycle)
            findings.append(
                self.create_finding(
                    file=rel_file,
                    line=1,
                    description=f"Circular dependency detected: {cycle_str}",
                    evidence=cycle_str,
                )
            )
        return findings


@register_analyzer
class UniversalArchitectureAnalyzer(BaseAnalyzer):
    name = "universal-architecture"
    description = "Evaluates backend architecture, layer boundaries, and module coupling"
    category = Category.ARCHITECTURE

    def get_rules(self) -> List[BaseRule]:
        return [PresentationToInfraRule(), CircularDependencyRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
