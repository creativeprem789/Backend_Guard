"""Abstract base analyzer definition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from auditor.core.severity import Category

if TYPE_CHECKING:
    from auditor.core.context import AnalysisContext
    from auditor.core.rule import BaseRule
    from auditor.models import Finding, ProjectInfo


class BaseAnalyzer(ABC):
    """Abstract base class for all language, framework, and universal analyzers."""

    name: str = "base-analyzer"
    description: str = "Base analyzer"
    language: Optional[str] = None
    framework: Optional[str] = None
    category: Optional[Category] = None

    def can_analyze(self, project_info: ProjectInfo) -> bool:
        """Determine if this analyzer can run on the discovered project."""
        if self.language and not project_info.has_language(self.language):
            return False
        if self.framework and not project_info.has_framework(self.framework):
            return False
        return True

    def get_rules(self) -> List[BaseRule]:
        """Return list of rules registered with or executed by this analyzer."""
        return []

    @abstractmethod
    def analyze(self, context: AnalysisContext) -> List[Finding]:
        """Execute the analyzer against the project context."""
        pass
