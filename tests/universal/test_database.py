"""Tests for database design and transaction rules."""

from pathlib import Path

from auditor.analyzers.universal.database_design import MissingRollbackRule, NPlusOneQueryRule


def test_n_plus_one_query_rule(tmp_path: Path, make_context):
    p = tmp_path / "nplusone.py"
    code = """def fetch_orders(ids):
    results = []
    for item in ids:
        order = db.get(item)
        results.append(order)
    return results
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = NPlusOneQueryRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "DB-001"


def test_missing_rollback_rule(tmp_path: Path, make_context):
    p = tmp_path / "tx.py"
    code = """def save_user():
    try:
        user = User(name='bob')
        session.add(user)
        session.commit()
    except Exception as e:
        logger.error(e)
"""
    p.write_text(code, encoding="utf-8")
    ctx = make_context(tmp_path)
    rule = MissingRollbackRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "DB-002"
