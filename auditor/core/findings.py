"""Utility operations for managing, sorting, deduplicating, and filtering findings."""

from __future__ import annotations

from typing import Dict, List, Optional

from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding


def deduplicate_findings(findings: List[Finding]) -> List[Finding]:
    """Deduplicate findings based on unique location and rule ID."""
    seen = set()
    deduped: List[Finding] = []
    for f in findings:
        key = (f.rule_id, f.file.replace("\\", "/"), f.line, f.column)
        if key not in seen:
            seen.add(key)
            deduped.append(f)
    return deduped


def sort_findings(findings: List[Finding]) -> List[Finding]:
    """Sort findings by severity descending, confidence descending, file ascending, line ascending."""
    return sorted(
        findings,
        key=lambda f: (
            -f.severity.rank,
            -f.confidence.rank,
            f.file,
            f.line,
            f.column,
            f.rule_id,
        ),
    )


def filter_findings(
    findings: List[Finding],
    min_severity: Optional[Severity] = None,
    min_confidence: Optional[Confidence] = None,
    category: Optional[Category] = None,
    language: Optional[str] = None,
    framework: Optional[str] = None,
) -> List[Finding]:
    """Filter findings according to severity, confidence, or categorization thresholds."""
    filtered = findings
    if min_severity is not None:
        filtered = [f for f in filtered if f.severity.is_at_least(min_severity)]
    if min_confidence is not None:
        filtered = [f for f in filtered if f.confidence.is_at_least(min_confidence)]
    if category is not None:
        filtered = [f for f in filtered if f.category == category]
    if language is not None:
        filtered = [f for f in filtered if f.language and f.language.lower() == language.lower()]
    if framework is not None:
        filtered = [f for f in filtered if f.framework and f.framework.lower() == framework.lower()]
    return filtered


def group_findings_by_file(findings: List[Finding]) -> Dict[str, List[Finding]]:
    """Group findings by normalized file path."""
    groups: Dict[str, List[Finding]] = {}
    for f in findings:
        norm_file = f.file.replace("\\", "/")
        groups.setdefault(norm_file, []).append(f)
    return groups


def group_findings_by_category(findings: List[Finding]) -> Dict[str, List[Finding]]:
    """Group findings by category string."""
    groups: Dict[str, List[Finding]] = {}
    for f in findings:
        cat_key = f.category.value if isinstance(f.category, Category) else str(f.category)
        groups.setdefault(cat_key, []).append(f)
    return groups
