"""Project entity representing an audited codebase directory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from auditor.config import Config
from auditor.discovery import ProjectScanner
from auditor.models import ProjectInfo


class Project:
    """Manages project discovery, path validation, and metadata."""

    def __init__(self, root_path: Path | str, config: Optional[Config] = None) -> None:
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists():
            raise FileNotFoundError(f"Target path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Target path is not a directory: {self.root_path}")

        self.config = config or Config.load(self.root_path)
        self.scanner = ProjectScanner(self.root_path, self.config)
        self._info: Optional[ProjectInfo] = None

    def discover(self) -> ProjectInfo:
        """Execute project discovery scanner."""
        if self._info is None:
            self._info = self.scanner.scan()
        return self._info

    @property
    def info(self) -> ProjectInfo:
        if self._info is None:
            return self.discover()
        return self._info
