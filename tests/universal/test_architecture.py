"""Tests for universal architecture rules."""

from pathlib import Path

from auditor.analyzers.universal.architecture import CircularDependencyRule, PresentationToInfraRule


def test_presentation_to_infra_rule(tmp_path: Path, make_context):
    routes = tmp_path / "app" / "routers"
    routes.mkdir(parents=True)
    r_file = routes / "users.py"
    r_file.write_text("from app.infra import db\n", encoding="utf-8")

    infra = tmp_path / "app" / "infra"
    infra.mkdir(parents=True)
    i_file = infra / "db.py"
    i_file.write_text("class DB: pass\n", encoding="utf-8")

    ctx = make_context(tmp_path)
    # Populate graph
    ctx.dependency_graph.get_or_create_node("app.routers.users", r_file, "python")
    ctx.dependency_graph.get_or_create_node("app.infra.db", i_file, "python")
    ctx.dependency_graph.add_dependency("app.routers.users", "app.infra.db")

    rule = PresentationToInfraRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "ARCH-001"


def test_circular_dependency_rule(tmp_path: Path, make_context):
    f_a = tmp_path / "mod_a.py"
    f_b = tmp_path / "mod_b.py"
    f_a.write_text("import mod_b", encoding="utf-8")
    f_b.write_text("import mod_a", encoding="utf-8")

    ctx = make_context(tmp_path)
    ctx.dependency_graph.get_or_create_node("mod_a", f_a, "python")
    ctx.dependency_graph.get_or_create_node("mod_b", f_b, "python")
    ctx.dependency_graph.add_dependency("mod_a", "mod_b")
    ctx.dependency_graph.add_dependency("mod_b", "mod_a")

    rule = CircularDependencyRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "ARCH-003"
