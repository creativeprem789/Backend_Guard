"""Core architecture and interfaces for Backend Guard."""

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.dependency_graph import DependencyGraph, ModuleNode
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity

__all__ = [
    "Severity",
    "Confidence",
    "Category",
    "BaseRule",
    "RuleMetadata",
    "BaseAnalyzer",
    "AnalysisContext",
    "DependencyGraph",
    "ModuleNode",
]
