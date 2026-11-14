"""Severity, Confidence, and Category enumerations for findings."""

from __future__ import annotations

from enum import Enum
from functools import total_ordering


@total_ordering
class Severity(str, Enum):
    """Severity levels for audit findings, ordered by impact."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def rank(self) -> int:
        ranks = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return ranks.get(self, 0)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Severity):
            return self.rank < other.rank
        return NotImplemented

    def is_at_least(self, threshold: Severity) -> bool:
        return self.rank >= threshold.rank

    @classmethod
    def from_str(cls, value: str | Severity) -> Severity:
        if isinstance(value, Severity):
            return value
        cleaned = str(value).strip().lower()
        for member in cls:
            if member.value == cleaned or member.name.lower() == cleaned:
                return member
        return cls.INFO


@total_ordering
class Confidence(str, Enum):
    """Confidence levels representing heuristic certainty vs confirmed defect."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        ranks = {
            Confidence.LOW: 0,
            Confidence.MEDIUM: 1,
            Confidence.HIGH: 2,
        }
        return ranks.get(self, 0)

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Confidence):
            return self.rank < other.rank
        return NotImplemented

    def is_at_least(self, threshold: Confidence) -> bool:
        return self.rank >= threshold.rank

    @classmethod
    def from_str(cls, value: str | Confidence) -> Confidence:
        if isinstance(value, Confidence):
            return value
        cleaned = str(value).strip().lower()
        for member in cls:
            if member.value == cleaned or member.name.lower() == cleaned:
                return member
        return cls.LOW


class Category(str, Enum):
    """Universal and domain categories for backend audit rules."""

    ARCHITECTURE = "architecture"
    SOLID = "solid"
    PATTERNS = "patterns"
    DATABASE = "database"
    API_DESIGN = "api_design"
    SECURITY = "security"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    TESTING = "testing"
    PRODUCTION_READINESS = "production_readiness"
    DEPENDENCY = "dependency"
    COMPLEXITY = "complexity"
    TYPING = "typing"
    ASYNC_CONCURRENCY = "async_concurrency"

    @classmethod
    def from_str(cls, value: str | Category) -> Category:
        if isinstance(value, Category):
            return value
        cleaned = str(value).strip().lower()
        for member in cls:
            if member.value == cleaned or member.name.lower() == cleaned:
                return member
        return cls.ARCHITECTURE
