"""Code duplication detection across service endpoints and modules."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Set, Tuple

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule


@register_rule
class CodeDuplicationRule(BaseRule):
    """Detects duplicated non-trivial code blocks across files."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="DUP-001",
                title="Substantial code block duplication across modules",
                category=Category.ARCHITECTURE,
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                description="Identical or near-identical code blocks of 8+ lines are repeated across different backend files.",
                impact="Duplicated code doubles maintenance burden; bug fixes applied in one location are easily forgotten in cloned copies.",
                recommendation="Extract the common logic into a shared utility, helper function, or base class.",
                suggested_fix="Create a common utility function in a shared module and import it in both locations.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        block_size = 8
        # hash -> list of (file, start_line)
        block_hashes: Dict[str, List[Tuple[str, int]]] = {}

        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        for f in source_files:
            lines = context.get_lines(f)
            # Normalize lines: strip whitespace and ignore empty or comment lines
            norm_lines = []
            line_map = []  # norm_idx -> orig_idx
            for idx, line in enumerate(lines, start=1):
                clean = line.strip()
                if clean and not clean.startswith(("#", "//", "/*", "*")):
                    norm_lines.append(clean)
                    line_map.append(idx)

            if len(norm_lines) < block_size:
                continue

            rel_file = context.get_relative_path(f)
            for i in range(len(norm_lines) - block_size + 1):
                chunk = "".join(norm_lines[i : i + block_size])
                chunk_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
                block_hashes.setdefault(chunk_hash, []).append((rel_file, line_map[i]))

        reported_files: Set[Tuple[str, str]] = set()
        for chunk_hash, locations in block_hashes.items():
            if len(locations) > 1:
                # Find occurrences across distinct files
                distinct = {loc[0]: loc[1] for loc in locations}
                if len(distinct) > 1:
                    files_list = sorted(distinct.keys())
                    pair = (files_list[0], files_list[1])
                    if pair not in reported_files:
                        reported_files.add(pair)
                        f1, l1 = files_list[0], distinct[files_list[0]]
                        f2, l2 = files_list[1], distinct[files_list[1]]
                        findings.append(
                            self.create_finding(
                                file=f1,
                                line=l1,
                                description=f"Substantial code block ({block_size}+ lines) is duplicated in '{f2}' (line {l2}).",
                                evidence=f"Duplicated between {f1}:{l1} and {f2}:{l2}",
                            )
                        )
        return findings


@register_analyzer
class UniversalDuplicationAnalyzer(BaseAnalyzer):
    name = "universal-duplication"
    description = "Detects code duplication across backend modules"
    category = Category.ARCHITECTURE

    def get_rules(self) -> List[BaseRule]:
        return [CodeDuplicationRule()]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
