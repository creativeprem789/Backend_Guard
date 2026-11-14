"""Base runner for external linting, static analysis, and testing tools."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from auditor.models import Finding


class ExternalToolRunner:
    """Safely runs external tools via subprocess with timeouts and graceful missing-tool handling."""

    tool_binary: str = ""
    timeout_seconds: int = 30

    @classmethod
    def is_available(cls) -> bool:
        """Check if binary is installed and executable in PATH."""
        return shutil.which(cls.tool_binary) is not None

    @classmethod
    def run_command(cls, args: List[str], cwd: Path) -> Optional[subprocess.CompletedProcess]:
        if not cls.is_available():
            return None
        try:
            return subprocess.run(
                [cls.tool_binary] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=cls.timeout_seconds,
                check=False,
            )
        except Exception:
            return None

    @classmethod
    def run(cls, project_root: Path) -> List[Finding]:
        """Execute external tool and convert output into standard Finding objects."""
        return []
