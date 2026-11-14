"""Registry for rules and analyzers with discovery mechanisms."""

from __future__ import annotations

from typing import Dict, List, Optional, Type

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.rule import BaseRule
from auditor.core.severity import Category, Severity


class RuleRegistry:
    """Central registry of all available audit rules."""

    _rules: Dict[str, Type[BaseRule]] = {}
    _rule_instances: Dict[str, BaseRule] = {}

    @classmethod
    def register(cls, rule_cls: Type[BaseRule]) -> Type[BaseRule]:
        # Temporarily instantiate to get rule_id if necessary
        dummy = rule_cls()
        cls._rules[dummy.rule_id] = rule_cls
        cls._rule_instances[dummy.rule_id] = dummy
        return rule_cls

    @classmethod
    def get(cls, rule_id: str) -> Optional[BaseRule]:
        return cls._rule_instances.get(rule_id)

    @classmethod
    def all_rules(cls) -> List[BaseRule]:
        return list(cls._rule_instances.values())

    @classmethod
    def filter(
        cls,
        category: Optional[Category] = None,
        min_severity: Optional[Severity] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> List[BaseRule]:
        results = cls.all_rules()
        if category:
            results = [r for r in results if r.category == category]
        if min_severity:
            results = [r for r in results if r.severity.is_at_least(min_severity)]
        if language:
            results = [
                r
                for r in results
                if r.metadata.language is None or r.metadata.language.lower() == language.lower()
            ]
        if framework:
            results = [
                r
                for r in results
                if r.metadata.framework is None or r.metadata.framework.lower() == framework.lower()
            ]
        return results

    @classmethod
    def clear(cls) -> None:
        cls._rules.clear()
        cls._rule_instances.clear()


class AnalyzerRegistry:
    """Central registry of all language, framework, and universal analyzers."""

    _analyzers: Dict[str, Type[BaseAnalyzer]] = {}
    _analyzer_instances: Dict[str, BaseAnalyzer] = {}

    @classmethod
    def register(cls, analyzer_cls: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
        inst = analyzer_cls()
        cls._analyzers[inst.name] = analyzer_cls
        cls._analyzer_instances[inst.name] = inst
        return analyzer_cls

    @classmethod
    def get(cls, name: str) -> Optional[BaseAnalyzer]:
        return cls._analyzer_instances.get(name)

    @classmethod
    def all_analyzers(cls) -> List[BaseAnalyzer]:
        return list(cls._analyzer_instances.values())

    @classmethod
    def clear(cls) -> None:
        cls._analyzers.clear()
        cls._analyzer_instances.clear()


def register_rule(rule_cls: Type[BaseRule]) -> Type[BaseRule]:
    """Decorator to register a rule."""
    return RuleRegistry.register(rule_cls)


def register_analyzer(analyzer_cls: Type[BaseAnalyzer]) -> Type[BaseAnalyzer]:
    """Decorator to register an analyzer."""
    return AnalyzerRegistry.register(analyzer_cls)
