"""Dependency management and coupling evaluation rules."""

from __future__ import annotations

import logging
import re
from typing import List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule

logger = logging.getLogger(__name__)


@register_rule
class UnpinnedDependencyRule(BaseRule):
    """Detects unpinned or wildcard dependencies in project manifests."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="DEP-002",
                title="Unpinned dependency version in production manifest",
                category=Category.DEPENDENCY,
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                description="Dependencies in requirements.txt or package.json use wildcard '*' or lack version constraints.",
                impact="Builds are non-deterministic; upstream minor or major breaking updates can cause production outages without notice.",
                recommendation="Pin dependencies to specific or compatible version ranges (e.g., package==1.2.3 or package~=1.2.0).",
                suggested_fix="Specify exact or compatible version specifiers in the dependency manifest.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for f in context.project_info.files:
            if f.name == "requirements.txt":
                lines = context.get_lines(f)
                rel_file = context.get_relative_path(f)
                for idx, line in enumerate(lines, start=1):
                    clean = line.strip().split("#")[0].strip()
                    if not clean or clean.startswith("-"):
                        continue
                    # Match package names with no version or '*'
                    if re.match(r"^[a-zA-Z0-9_\-]+(?:\s*==\s*\*|\s*)$", clean):
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=idx,
                                description=f"Dependency '{clean}' is completely unpinned without version constraints.",
                                evidence=line.strip(),
                            )
                        )
            elif f.name == "package.json":
                try:
                    import json

                    content = context.get_content(f)
                    data = json.loads(content)
                    rel_file = context.get_relative_path(f)
                    for dep_type in ("dependencies", "devDependencies"):
                        deps = data.get(dep_type, {})
                        if isinstance(deps, dict):
                            for pkg, ver in deps.items():
                                if ver in ("*", "latest"):
                                    findings.append(
                                        self.create_finding(
                                            file=rel_file,
                                            line=1,
                                            description=f"Package '{pkg}' in '{dep_type}' is specified as '{ver}'.",
                                            evidence=f'"{pkg}": "{ver}"',
                                        )
                                    )
                except (json.JSONDecodeError, OSError) as exc:
                    logger.debug("Failed parsing package.json at %s: %s", rel_file, exc)
        return findings


@register_analyzer
class UniversalDependencyAnalyzer(BaseAnalyzer):
    name = "universal-dependency"
    description = "Evaluates dependency pinning and module coupling metrics"
    category = Category.DEPENDENCY

    def get_rules(self) -> List[BaseRule]:
        return [UnpinnedDependencyRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
