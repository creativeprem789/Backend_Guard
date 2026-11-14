"""TypeScript parser and imports bridging."""

from __future__ import annotations

from auditor.analyzers.languages.javascript.imports import populate_js_dependency_graph
from auditor.analyzers.languages.javascript.parser import parse_js_file

__all__ = ["parse_js_file", "populate_js_dependency_graph"]
