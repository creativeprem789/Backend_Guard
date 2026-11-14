"""TypeScript import extraction and dependency graph integration."""

from __future__ import annotations

from auditor.analyzers.languages.javascript.imports import populate_js_dependency_graph

__all__ = ["populate_js_dependency_graph"]
