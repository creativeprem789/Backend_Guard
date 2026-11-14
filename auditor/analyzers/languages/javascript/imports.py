"""JavaScript and TypeScript import dependency graph populator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from auditor.analyzers.languages.javascript.parser import parse_js_file
from auditor.core.context import AnalysisContext


def populate_js_dependency_graph(context: AnalysisContext) -> None:
    """Populate DependencyGraph using parsed JS and TS files."""
    files = context.get_files_for_language("javascript") + context.get_files_for_language(
        "typescript"
    )

    mod_to_file: Dict[str, Path] = {}
    for f in files:
        rel = context.get_relative_path(f)
        # Normalize without extension
        base_mod = rel
        for ext in (".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs"):
            if base_mod.endswith(ext):
                base_mod = base_mod[: -len(ext)]
                break
        mod_to_file[base_mod] = f
        context.dependency_graph.get_or_create_node(base_mod, f, "javascript")

    for base_mod, f in mod_to_file.items():
        data = context.get_js_structure(f)
        if not data:
            data = parse_js_file(f)
            context.set_js_structure(f, data)

        for imp in data.get("imports", []):
            mod_target = imp.get("module", "")
            if mod_target.startswith("."):
                # Relative import resolution
                resolved = (f.parent / mod_target).resolve()
                rel_resolved = context.get_relative_path(resolved)
                for candidate_mod in mod_to_file.keys():
                    if rel_resolved.startswith(candidate_mod):
                        context.dependency_graph.add_dependency(base_mod, candidate_mod)
                        break
