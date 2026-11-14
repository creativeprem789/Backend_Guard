"""Suppression comment parser and filter for false-positive control."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set

# Matches:
#   # backend-auditor: ignore RULE-123
#   // backend-guard: ignore RULE-123 -- reason
#   # backend-auditor: ignore RULE-1, RULE-2
INLINE_IGNORE_PATTERN = re.compile(
    r"(?:#|//|/\*)\s*(?:backend-auditor|backend-guard):\s*ignore\s+([A-Za-z0-9_,\s\-]+?)(?:\s+--.*|\s*\*/|$)",
    re.IGNORECASE,
)

BLOCK_START_PATTERN = re.compile(
    r"(?:#|//|/\*)\s*(?:backend-auditor|backend-guard):\s*ignore-block\s+([A-Za-z0-9_,\s\-]+?)(?:\s+--.*|\s*\*/|$)",
    re.IGNORECASE,
)

BLOCK_END_PATTERN = re.compile(
    r"(?:#|//|/\*)\s*(?:backend-auditor|backend-guard):\s*end-ignore-block",
    re.IGNORECASE,
)

FILE_IGNORE_PATTERN = re.compile(
    r"(?:#|//|/\*)\s*(?:backend-auditor|backend-guard):\s*ignore-file\s*([A-Za-z0-9_\-,\s]*)",
    re.IGNORECASE,
)


class SuppressionIndex:
    """Indexes suppressions found within a project's source files."""

    def __init__(self) -> None:
        # file_path -> rule_id -> set of lines (1-indexed)
        self._line_suppressions: Dict[str, Dict[str, Set[int]]] = {}
        # file_path -> set of rule_ids (or '*' for entire file)
        self._file_suppressions: Dict[str, Set[str]] = {}

    def scan_file(self, file_path: Path | str, lines: List[str]) -> None:
        """Scan file lines for suppression comments."""
        norm_file = str(file_path).replace("\\", "/")
        rule_to_lines: Dict[str, Set[int]] = {}
        file_ignored_rules: Set[str] = set()

        active_blocks: Dict[str, int] = {}  # rule_id -> start_line

        for idx, line in enumerate(lines, start=1):
            # Check file ignore
            m_file = FILE_IGNORE_PATTERN.search(line)
            if m_file:
                raw_rules = m_file.group(1).strip()
                if not raw_rules:
                    file_ignored_rules.add("*")
                else:
                    for r in raw_rules.split(","):
                        if r.strip():
                            file_ignored_rules.add(r.strip().upper())

            # Check block start
            m_block_start = BLOCK_START_PATTERN.search(line)
            if m_block_start:
                for r in m_block_start.group(1).split(","):
                    r_clean = r.strip().upper()
                    if r_clean:
                        active_blocks[r_clean] = idx

            # Check block end
            m_block_end = BLOCK_END_PATTERN.search(line)
            if m_block_end:
                active_blocks.clear()

            # Record active blocks
            for r_block in active_blocks.keys():
                rule_to_lines.setdefault(r_block, set()).add(idx)

            # Check inline ignore
            m_inline = INLINE_IGNORE_PATTERN.search(line)
            if m_inline:
                for r in m_inline.group(1).split(","):
                    r_clean = r.strip().upper()
                    if r_clean:
                        # Applies to this line and immediately next line (common pattern)
                        rule_to_lines.setdefault(r_clean, set()).add(idx)
                        rule_to_lines.setdefault(r_clean, set()).add(idx + 1)

        if rule_to_lines:
            self._line_suppressions[norm_file] = rule_to_lines
        if file_ignored_rules:
            self._file_suppressions[norm_file] = file_ignored_rules

    def is_suppressed(self, file_path: Path | str, line: int, rule_id: str) -> bool:
        """Check whether a finding at (file, line, rule_id) is suppressed."""
        norm_file = str(file_path).replace("\\", "/")
        rule_upper = rule_id.strip().upper()

        # Check file suppressions
        file_rules = self._file_suppressions.get(norm_file, set())
        if "*" in file_rules or rule_upper in file_rules:
            return True

        # Check line suppressions
        line_rules = self._line_suppressions.get(norm_file, {})
        if rule_upper in line_rules and line in line_rules[rule_upper]:
            return True
        if "*" in line_rules and line in line_rules["*"]:
            return True

        return False
