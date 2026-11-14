"""Abstract base rule and rule metadata definition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from auditor.core.severity import Category, Confidence, Severity

if TYPE_CHECKING:
    from auditor.core.context import AnalysisContext
    from auditor.models import Finding


@dataclass
class RuleMetadata:
    """Static metadata describing a backend audit rule."""

    rule_id: str
    title: str
    category: Category
    severity: Severity
    confidence: Confidence
    description: str
    impact: str
    recommendation: str
    suggested_fix: str
    autofix_available: bool = False
    language: Optional[str] = None
    framework: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "category": self.category.value,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "description": self.description,
            "impact": self.impact,
            "recommendation": self.recommendation,
            "suggested_fix": self.suggested_fix,
            "autofix_available": self.autofix_available,
            "language": self.language,
            "framework": self.framework,
            "tags": self.tags,
        }


class BaseRule(ABC):
    """Abstract base class for all Backend Guard rules."""

    metadata: RuleMetadata

    def __init__(self, metadata: Optional[RuleMetadata] = None) -> None:
        if metadata is not None:
            self.metadata = metadata

    @property
    def rule_id(self) -> str:
        return self.metadata.rule_id

    @property
    def title(self) -> str:
        return self.metadata.title

    @property
    def category(self) -> Category:
        return self.metadata.category

    @property
    def severity(self) -> Severity:
        return self.metadata.severity

    @property
    def confidence(self) -> Confidence:
        return self.metadata.confidence

    def is_applicable(self, context: AnalysisContext) -> bool:
        """Check whether the rule is applicable to the current project context."""
        if self.metadata.language and not context.project_info.has_language(self.metadata.language):
            return False
        if self.metadata.framework and not context.project_info.has_framework(
            self.metadata.framework
        ):
            return False
        return True

    def create_finding(
        self,
        file: str,
        line: int = 1,
        column: int = 1,
        title: Optional[str] = None,
        description: Optional[str] = None,
        severity: Optional[Severity] = None,
        confidence: Optional[Confidence] = None,
        impact: Optional[str] = None,
        recommendation: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        evidence: str = "",
        code_snippet: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Finding:
        """Factory helper creating a Finding prepopulated with rule defaults."""
        from auditor.models import Finding

        return Finding(
            rule_id=self.rule_id,
            title=title or self.title,
            category=self.category,
            severity=severity or self.severity,
            confidence=confidence or self.confidence,
            language=self.metadata.language,
            framework=self.metadata.framework,
            file=file,
            line=line,
            column=column,
            description=description or self.metadata.description,
            impact=impact or self.metadata.impact,
            recommendation=recommendation or self.metadata.recommendation,
            suggested_fix=suggested_fix or self.metadata.suggested_fix,
            autofix_available=self.metadata.autofix_available,
            evidence=evidence,
            code_snippet=code_snippet,
            metadata=metadata or {},
        )

    @abstractmethod
    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        """Execute rule analysis over the context and return any detected findings."""
        pass
