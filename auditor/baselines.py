"""Baseline management for tracking and suppressing legacy findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Set

from auditor.models import Finding


class Baseline:
    """Manages baseline snapshots of known findings."""

    def __init__(self, fingerprints: Set[str]) -> None:
        self.fingerprints = fingerprints

    @classmethod
    def load(cls, baseline_path: Path) -> Baseline:
        if not baseline_path.is_file():
            return cls(set())
        try:
            with open(baseline_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get("fingerprints", [])
            return cls(set(entries))
        except Exception:
            return cls(set())

    def contains(self, finding: Finding) -> bool:
        """Check if finding matches any fingerprint in baseline."""
        # Check strict fingerprint
        if finding.fingerprint() in self.fingerprints:
            return True
        # Check relaxed fingerprint (rule_id + file)
        norm_file = finding.file.replace("\\", "/")
        relaxed = f"{finding.rule_id}:{norm_file}"
        return relaxed in self.fingerprints

    @staticmethod
    def save(findings: List[Finding], target_path: Path) -> None:
        """Serialize findings into a new baseline file."""
        fingerprints = [f.fingerprint() for f in findings]
        relaxed_set = set()
        for f in findings:
            norm_f = f.file.replace("\\", "/")
            relaxed_set.add(f"{f.rule_id}:{norm_f}")
        payload = {
            "version": "1.0",
            "count": len(findings),
            "fingerprints": sorted(set(fingerprints) | relaxed_set),
        }
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as out_f:
            json.dump(payload, out_f, indent=2)
