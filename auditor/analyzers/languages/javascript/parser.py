"""JavaScript and TypeScript parsing bridge via Node.js helper with fallback."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

PARSER_SCRIPT = Path(__file__).parent / "js_ast_parser.js"


def parse_js_file(file_path: Path) -> Dict[str, Any]:
    """Parse JavaScript or TypeScript file into structured AST metadata."""
    node_bin = shutil.which("node")
    if node_bin and PARSER_SCRIPT.is_file():
        try:
            res = subprocess.run(
                [node_bin, str(PARSER_SCRIPT), str(file_path.resolve())],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout)
        except Exception:
            pass

    # High-fidelity fallback parser in pure Python
    return _fallback_js_parser(file_path)


def _fallback_js_parser(file_path: Path) -> Dict[str, Any]:
    """Pure Python fallback parser extracting JS/TS structure."""
    import re

    result: Dict[str, Any] = {
        "file": str(file_path),
        "totalLines": 0,
        "imports": [],
        "exports": [],
        "functions": [],
        "blockingCalls": [],
        "evalCalls": [],
        "unhandledPromises": [],
        "anyTypes": [],
        "expressRoutes": [],
        "expressErrorMiddleware": [],
    }

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        result["totalLines"] = len(lines)
        for idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith("//") or trimmed.startswith("/*") or trimmed.startswith("*"):
                continue

            # Imports
            esm = re.search(r"""import\s+(?:(?:[\w*\s{},]+)\s+from\s+)?['"]([^'"]+)['"]""", line)
            if esm:
                result["imports"].append({"module": esm.group(1), "line": idx})
            cjs = re.search(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""", line)
            if cjs:
                result["imports"].append({"module": cjs.group(1), "line": idx})

            # Blocking calls
            if re.search(
                r"""\b(?:fs\.readFileSync|fs\.writeFileSync|fs\.existsSync|crypto\.pbkdf2Sync|child_process\.execSync)\b""",
                line,
            ):
                result["blockingCalls"].append({"line": idx, "text": trimmed})

            # Eval calls
            if re.search(r"""\b(?:eval\s*\(|new\s+Function\s*\()""", line):
                result["evalCalls"].append({"line": idx, "text": trimmed})

            # Any types
            if re.search(r"""(?::\s*any\b|<any>|as\s+any\b)""", line):
                result["anyTypes"].append({"line": idx, "text": trimmed})

            # Unhandled promise
            if re.search(r"""\.then\s*\(""", line) and ".catch" not in line:
                result["unhandledPromises"].append({"line": idx, "text": trimmed})

            # Express routes
            route_m = re.search(
                r"""\b(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]\s*,\s*(?:async\s*)?(?:\(([^)]*)\)|([a-zA-Z0-9_]+))""",
                line,
            )
            if route_m:
                result["expressRoutes"].append(
                    {
                        "method": route_m.group(1),
                        "path": route_m.group(2),
                        "isAsync": "async" in line,
                        "line": idx,
                    }
                )

            # Express 4-argument error middleware: (err, req, res, next)
            if re.search(
                r"""\b(?:app|router)\.use\s*\(\s*(?:async\s*)?\(\s*[\w$]+\s*,\s*[\w$]+\s*,\s*[\w$]+\s*,\s*[\w$]+\s*\)""",
                line,
            ):
                result["expressErrorMiddleware"].append({"line": idx, "text": trimmed})

    except Exception:
        pass

    return result
