"""Python import extraction and dependency graph populator."""

from __future__ import annotations

import ast
from typing import Set

from auditor.core.context import AnalysisContext


def extract_python_imports(tree: ast.AST) -> Set[str]:
    """Extract imported module names from Python AST."""
    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def populate_python_dependency_graph(context: AnalysisContext) -> None:
    """Populate project DependencyGraph using Python AST imports."""
    py_files = context.get_files_for_language("python")

    # Map of module name to file path
    mod_to_file = {}
    for f in py_files:
        rel = context.get_relative_path(f)
        mod_id = rel.replace(".py", "").replace("/", ".").replace("\\", ".")
        mod_to_file[mod_id] = f
        context.dependency_graph.get_or_create_node(mod_id, f, "python")

    for mod_id, file_path in mod_to_file.items():
        tree = context.get_python_ast(file_path)
        if not tree:
            continue

        for node in ast.walk(tree):
            target_mod = ""
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_mod = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    target_mod = node.module

            if target_mod:
                # Check if target matches any internal module
                for internal_id in mod_to_file.keys():
                    if target_mod == internal_id or target_mod.startswith(internal_id + "."):
                        context.dependency_graph.add_dependency(mod_id, internal_id)
                        break
