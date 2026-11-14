"""Core domain models for the Backend Guard auditor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from auditor.core.severity import Category, Confidence, Severity


@dataclass
class Finding:
    """Standardized audit finding reported by a rule or analyzer."""

    rule_id: str
    title: str
    category: Category
    severity: Severity
    confidence: Confidence
    description: str
    file: str
    line: int = 1
    column: int = 1
    language: Optional[str] = None
    framework: Optional[str] = None
    impact: str = ""
    recommendation: str = ""
    suggested_fix: str = ""
    autofix_available: bool = False
    evidence: str = ""
    code_snippet: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to standard JSON-compatible dictionary."""
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category.value
            if isinstance(self.category, Category)
            else str(self.category),
            "severity": self.severity.value
            if isinstance(self.severity, Severity)
            else str(self.severity),
            "confidence": self.confidence.value
            if isinstance(self.confidence, Confidence)
            else str(self.confidence),
            "language": self.language,
            "framework": self.framework,
            "file": self.file.replace("\\", "/"),
            "line": self.line,
            "column": self.column,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "suggested_fix": self.suggested_fix,
            "autofix_available": self.autofix_available,
            "evidence": self.evidence,
            "code_snippet": self.code_snippet,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Finding:
        return cls(
            rule_id=data["rule_id"],
            title=data.get("title", ""),
            category=Category.from_str(data.get("category", "architecture")),
            severity=Severity.from_str(data.get("severity", "info")),
            confidence=Confidence.from_str(data.get("confidence", "low")),
            file=data.get("file", ""),
            line=data.get("line", 1),
            column=data.get("column", 1),
            language=data.get("language"),
            framework=data.get("framework"),
            description=data.get("description", ""),
            impact=data.get("impact", ""),
            recommendation=data.get("recommendation", ""),
            suggested_fix=data.get("suggested_fix", ""),
            autofix_available=data.get("autofix_available", False),
            evidence=data.get("evidence", ""),
            code_snippet=data.get("code_snippet", ""),
            metadata=data.get("metadata", {}),
        )

    def fingerprint(self) -> str:
        """Deterministic fingerprint for baseline comparison."""
        norm_file = self.file.replace("\\", "/")
        return f"{self.rule_id}:{norm_file}:{self.line}:{self.title}"


@dataclass
class TechnologyDetection:
    """Detected language or framework with evidence."""

    name: str
    kind: str  # 'language' or 'framework'
    confidence: Confidence
    version: Optional[str] = None
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "confidence": self.confidence.value,
            "version": self.version,
            "evidence": self.evidence,
        }


@dataclass
class ProjectInfo:
    """Metadata about the audited project codebase."""

    root_path: Path
    name: str
    detected_languages: Dict[str, TechnologyDetection] = field(default_factory=dict)
    detected_frameworks: Dict[str, TechnologyDetection] = field(default_factory=dict)
    files: List[Path] = field(default_factory=list)
    files_by_language: Dict[str, List[Path]] = field(default_factory=dict)
    total_lines: int = 0
    excluded_paths: List[str] = field(default_factory=list)

    def has_language(self, language: str) -> bool:
        return language.lower() in [lang.lower() for lang in self.detected_languages.keys()]

    def has_framework(self, framework: str) -> bool:
        return framework.lower() in [f.lower() for f in self.detected_frameworks.keys()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "root_path": str(self.root_path),
            "total_files": len(self.files),
            "total_lines": self.total_lines,
            "languages": {k: v.to_dict() for k, v in self.detected_languages.items()},
            "frameworks": {k: v.to_dict() for k, v in self.detected_frameworks.items()},
        }


@dataclass
class AuditResult:
    """Full outcome of an audit execution."""

    project_info: ProjectInfo
    findings: List[Finding] = field(default_factory=list)
    executed_rules: List[str] = field(default_factory=list)
    skipped_analyzers: Dict[str, str] = field(default_factory=dict)
    failed_analyzers: Dict[str, str] = field(default_factory=dict)
    scan_duration_seconds: float = 0.0
    suppressed_count: int = 0
    baseline_matched_count: int = 0
    is_complete: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    def summary_by_severity(self) -> Dict[str, int]:
        return {
            Severity.CRITICAL.value: self.critical_count,
            Severity.HIGH.value: self.high_count,
            Severity.MEDIUM.value: self.medium_count,
            Severity.LOW.value: self.low_count,
            Severity.INFO.value: self.info_count,
        }

    def summary_by_category(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for f in self.findings:
            cat_name = f.category.value if isinstance(f.category, Category) else str(f.category)
            summary[cat_name] = summary.get(cat_name, 0) + 1
        return summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": {
                "tool": "backend-guard",
                "version": "1.0.0",
                "created_at": self.created_at,
                "duration_seconds": round(self.scan_duration_seconds, 3),
                "is_complete": self.is_complete,
            },
            "project": self.project_info.to_dict(),
            "summary": {
                "total_findings": self.total_findings,
                "by_severity": self.summary_by_severity(),
                "by_category": self.summary_by_category(),
                "suppressed_count": self.suppressed_count,
                "baseline_matched_count": self.baseline_matched_count,
            },
            "execution": {
                "executed_rules": self.executed_rules,
                "skipped_analyzers": self.skipped_analyzers,
                "failed_analyzers": self.failed_analyzers,
            },
            "findings": [f.to_dict() for f in self.findings],
        }
