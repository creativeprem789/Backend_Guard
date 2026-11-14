"""Unit tests for DependencyGraph, layer classifications, and cycle detection."""

from pathlib import Path

from auditor.core.dependency_graph import DependencyGraph


def test_layer_classification():
    graph = DependencyGraph(Path("/fake"))
    n1 = graph.get_or_create_node("app.routers.users", Path("app/routers/users.py"), "python")
    n2 = graph.get_or_create_node(
        "app.services.user_service", Path("app/services/user_service.py"), "python"
    )
    n3 = graph.get_or_create_node("app.infra.db", Path("app/infra/db.py"), "python")
    n4 = graph.get_or_create_node("app.domain.user", Path("app/domain/user.py"), "python")

    assert n1.layer == "presentation"
    assert n2.layer == "service"
    assert n3.layer == "infrastructure"
    assert n4.layer == "domain"


def test_cycle_detection():
    graph = DependencyGraph(Path("/fake"))
    graph.get_or_create_node("mod_a", Path("mod_a.py"), "python")
    graph.get_or_create_node("mod_b", Path("mod_b.py"), "python")
    graph.get_or_create_node("mod_c", Path("mod_c.py"), "python")

    # Cycle: a -> b -> c -> a
    graph.add_dependency("mod_a", "mod_b")
    graph.add_dependency("mod_b", "mod_c")
    graph.add_dependency("mod_c", "mod_a")

    cycles = graph.find_cycles()
    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle[0] == cycle[-1]  # closed loop
    assert set(cycle) == {"mod_a", "mod_b", "mod_c"}


def test_coupling_metrics():
    graph = DependencyGraph(Path("/fake"))
    graph.get_or_create_node("core", Path("core.py"), "python")
    graph.get_or_create_node("leaf1", Path("leaf1.py"), "python")
    graph.get_or_create_node("leaf2", Path("leaf2.py"), "python")

    graph.add_dependency("leaf1", "core")
    graph.add_dependency("leaf2", "core")

    core_node = graph.nodes["core"]
    assert core_node.afferent_coupling == 2
    assert core_node.efferent_coupling == 0
    assert core_node.instability == 0.0  # totally stable core


def test_layer_violations():
    graph = DependencyGraph(Path("/fake"))
    graph.get_or_create_node("app.routers.users", Path("app/routers/users.py"), "python")
    graph.get_or_create_node("app.infra.database", Path("app/infra/database.py"), "python")

    # Presentation directly to infra
    graph.add_dependency("app.routers.users", "app.infra.database")
    violations = graph.check_layer_violations()
    assert len(violations) == 1
    assert "Presentation layer directly couples" in violations[0]["reason"]
