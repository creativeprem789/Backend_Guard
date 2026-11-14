"""Python AST parsing and visitor utilities."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import List


class FunctionInfo:
    """Extracted metadata for a Python function."""

    def __init__(self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: Path) -> None:
        self.node = node
        self.file_path = file_path
        self.name = node.name
        self.is_async = isinstance(node, ast.AsyncFunctionDef)
        self.lineno = node.lineno
        self.end_lineno = getattr(node, "end_lineno", node.lineno)
        self.has_return_type = node.returns is not None
        self.args_without_types = [
            arg.arg
            for arg in node.args.args
            if arg.annotation is None and arg.arg not in ("self", "cls")
        ]
        self.decorators = [self._decorator_name(d) for d in node.decorator_list]

    @staticmethod
    def _decorator_name(dec: ast.expr) -> str:
        if isinstance(dec, ast.Name):
            return dec.id
        if isinstance(dec, ast.Attribute):
            return dec.attr
        if isinstance(dec, ast.Call):
            return FunctionInfo._decorator_name(dec.func)
        return ""


def extract_functions(tree: ast.AST, file_path: Path) -> List[FunctionInfo]:
    """Extract all top-level and class-level functions from an AST."""
    funcs: List[FunctionInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append(FunctionInfo(node, file_path))
    return funcs
