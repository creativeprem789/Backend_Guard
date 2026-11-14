"""Analysis context holding project state, caches, and AST models during an audit run."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from auditor.core.dependency_graph import DependencyGraph

if TYPE_CHECKING:
    from auditor.config import Config
    from auditor.models import ProjectInfo


class AnalysisContext:
    """Shared immutable and cached analysis state across all rules and analyzers."""

    def __init__(self, project_info: ProjectInfo, config: Config) -> None:
        self.project_info = project_info
        self.config = config
        self.dependency_graph = DependencyGraph(project_info.root_path)

        # Caches
        self._content_cache: Dict[str, str] = {}
        self._lines_cache: Dict[str, List[str]] = {}
        self._python_ast_cache: Dict[str, Optional[ast.AST]] = {}
        self._js_ast_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._metrics: Dict[str, Any] = {}

    @property
    def root_path(self) -> Path:
        return self.project_info.root_path

    def get_relative_path(self, path: Path | str) -> str:
        """Return path relative to project root with normalized forward slashes."""
        p = Path(path)
        try:
            rel = p.relative_to(self.root_path)
            return str(rel).replace("\\", "/")
        except ValueError:
            return str(p).replace("\\", "/")

    def get_content(self, path: Path | str) -> str:
        """Safely read and cache file content."""
        p = Path(path)
        key = str(p.resolve())
        if key not in self._content_cache:
            try:
                self._content_cache[key] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                self._content_cache[key] = ""
        return self._content_cache[key]

    def get_lines(self, path: Path | str) -> List[str]:
        """Read and cache file as lines."""
        p = Path(path)
        key = str(p.resolve())
        if key not in self._lines_cache:
            content = self.get_content(p)
            self._lines_cache[key] = content.splitlines()
        return self._lines_cache[key]

    def get_python_ast(self, path: Path | str) -> Optional[ast.AST]:
        """Parse and cache Python AST using standard ast module."""
        p = Path(path)
        key = str(p.resolve())
        if key not in self._python_ast_cache:
            content = self.get_content(p)
            try:
                self._python_ast_cache[key] = ast.parse(content, filename=str(p))
            except Exception:
                self._python_ast_cache[key] = None
        return self._python_ast_cache[key]

    def get_js_structure(self, path: Path | str) -> Optional[Dict[str, Any]]:
        """Return parsed JS/TS structural metadata (imports, functions, routes, etc.)."""
        p = Path(path)
        key = str(p.resolve())
        return self._js_ast_cache.get(key)

    def set_js_structure(self, path: Path | str, data: Dict[str, Any]) -> None:
        p = Path(path)
        key = str(p.resolve())
        self._js_ast_cache[key] = data

    def get_files_for_language(self, language: str) -> List[Path]:
        """Return all project files detected for a specific language."""
        return self.project_info.files_by_language.get(language.lower(), [])
