"""Module and dependency graph model for architecture and coupling analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ModuleNode:
    """Represents a source file or module in the project dependency graph."""

    module_id: str
    file_path: Path
    language: str
    imports: Set[str] = field(default_factory=set)
    imported_by: Set[str] = field(default_factory=set)
    layer: Optional[str] = None  # controller, service, repository, domain, util, config

    @property
    def afferent_coupling(self) -> int:
        """Incoming dependencies: how many other modules depend on this one."""
        return len(self.imported_by)

    @property
    def efferent_coupling(self) -> int:
        """Outgoing dependencies: how many other modules this one depends on."""
        return len(self.imports)

    @property
    def instability(self) -> float:
        """Instability index I = Ce / (Ca + Ce). 0 = totally stable, 1 = unstable."""
        total = self.afferent_coupling + self.efferent_coupling
        if total == 0:
            return 0.0
        return self.efferent_coupling / total


class DependencyGraph:
    """Project-wide dependency graph modeling file imports and architectural layers."""

    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
        self.nodes: Dict[str, ModuleNode] = {}

    def get_or_create_node(self, module_id: str, file_path: Path, language: str) -> ModuleNode:
        normalized_id = module_id.replace("\\", "/")
        if normalized_id not in self.nodes:
            self.nodes[normalized_id] = ModuleNode(
                module_id=normalized_id,
                file_path=file_path,
                language=language,
                layer=self._classify_layer(file_path),
            )
        return self.nodes[normalized_id]

    def add_dependency(self, from_module_id: str, to_module_id: str) -> None:
        from_id = from_module_id.replace("\\", "/")
        to_id = to_module_id.replace("\\", "/")
        if from_id in self.nodes:
            self.nodes[from_id].imports.add(to_id)
        if to_id in self.nodes:
            self.nodes[to_id].imported_by.add(from_id)

    def _classify_layer(self, file_path: Path) -> str:
        try:
            rel_path = file_path.relative_to(self.root_path)
            parts = [p.lower() for p in rel_path.parts]
        except (ValueError, Exception):
            parts = [p.lower() for p in file_path.parts]
        name = file_path.stem.lower()

        for p in parts + [name]:
            if any(
                term in p
                for term in [
                    "router",
                    "controller",
                    "endpoint",
                    "views",
                    "view",
                    "routes",
                    "route",
                    "handlers",
                    "handler",
                ]
            ):
                return "presentation"
            if any(term in p for term in ["service", "usecase", "use_case", "manager", "business"]):
                return "service"
            if any(term in p for term in ["repo", "repository", "dao", "query", "crud"]):
                return "repository"
            if any(
                term in p
                for term in ["models", "model", "entities", "entity", "schemas", "schema", "domain"]
            ):
                return "domain"
            if any(
                term in p
                for term in [
                    "infra",
                    "infrastructure",
                    "database",
                    "db",
                    "client",
                    "adapter",
                    "external",
                ]
            ):
                return "infrastructure"
        return "other"

    def find_cycles(self) -> List[List[str]]:
        """Find circular dependency cycles in the module graph using DFS."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: List[str] = []

        def dfs(curr: str) -> None:
            visited.add(curr)
            rec_stack.append(curr)

            node = self.nodes.get(curr)
            if node:
                for neighbor in sorted(node.imports):
                    if neighbor not in self.nodes:
                        continue
                    if neighbor in rec_stack:
                        # Cycle detected
                        cycle_start = rec_stack.index(neighbor)
                        cycle = rec_stack[cycle_start:] + [neighbor]
                        # Normalize cycle to prevent duplicates
                        if len(cycle) > 2:
                            cycles.append(cycle)
                    elif neighbor not in visited:
                        dfs(neighbor)

            rec_stack.pop()

        for module_id in sorted(self.nodes.keys()):
            if module_id not in visited:
                dfs(module_id)

        # Deduplicate cycles by canonical rotation
        unique_cycles: List[List[str]] = []
        seen_canonical: Set[Tuple[str, ...]] = set()

        for cycle in cycles:
            path = cycle[:-1]  # drop closing duplicate
            if not path:
                continue
            # Canonical cycle representation is smallest element first
            min_idx = path.index(min(path))
            rotated = tuple(path[min_idx:] + path[:min_idx])
            if rotated not in seen_canonical:
                seen_canonical.add(rotated)
                unique_cycles.append(list(rotated) + [rotated[0]])

        return unique_cycles

    def check_layer_violations(self) -> List[Dict[str, str]]:
        """Check for inappropriate dependencies across layers (e.g. presentation directly to infrastructure)."""
        violations: List[Dict[str, str]] = []
        for mod_id, node in self.nodes.items():
            if node.layer == "presentation":
                for target_id in node.imports:
                    target = self.nodes.get(target_id)
                    if target and target.layer == "infrastructure":
                        violations.append(
                            {
                                "from": mod_id,
                                "to": target_id,
                                "reason": "Presentation layer directly couples to Infrastructure layer without Service/Repository abstraction",
                            }
                        )
            elif node.layer == "domain":
                for target_id in node.imports:
                    target = self.nodes.get(target_id)
                    if target and target.layer in ("presentation", "infrastructure"):
                        violations.append(
                            {
                                "from": mod_id,
                                "to": target_id,
                                "reason": f"Domain layer couples outward to {target.layer} layer, violating Dependency Inversion",
                            }
                        )
        return violations
