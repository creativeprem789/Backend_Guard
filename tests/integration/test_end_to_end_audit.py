"""End-to-end integration tests verifying complete audit runs across realistic backends."""

from pathlib import Path

from auditor.config import Config
from auditor.engine import AuditEngine


def test_audit_good_fastapi_backend(good_fastapi_dir: Path):
    config = Config.default()
    engine = AuditEngine(good_fastapi_dir, config)
    result = engine.run()

    assert result.is_complete
    assert result.project_info.has_framework("fastapi")
    # No high or critical findings on clean code
    assert result.critical_count == 0
    assert result.high_count == 0


def test_audit_bad_fastapi_backend(bad_fastapi_dir: Path):
    config = Config.default()
    engine = AuditEngine(bad_fastapi_dir, config)
    result = engine.run()

    assert result.is_complete
    rule_ids = {f.rule_id for f in result.findings}

    # Verify expected defect detections
    assert "SEC-001" in rule_ids  # Hardcoded secret
    assert "SEC-002" in rule_ids  # SQL injection
    assert "PY-ASYNC-001" in rule_ids  # time.sleep in async def
    assert "FASTAPI-001" in rule_ids  # Raw SQL in route
    assert "DB-001" in rule_ids  # N+1 query in loop
    assert "ERR-001" in rule_ids  # except: pass
    assert "CONF-002" in rule_ids  # debug=True
    assert "DEP-002" in rule_ids  # unpinned sqlalchemy==*


def test_audit_good_express_backend(good_express_dir: Path):
    config = Config.default()
    engine = AuditEngine(good_express_dir, config)
    result = engine.run()

    assert result.is_complete
    assert result.project_info.has_framework("express")
    assert result.critical_count == 0
    assert result.high_count == 0


def test_audit_bad_express_backend(bad_express_dir: Path):
    config = Config.default()
    engine = AuditEngine(bad_express_dir, config)
    result = engine.run()

    assert result.is_complete
    rule_ids = {f.rule_id for f in result.findings}

    assert "JS-001" in rule_ids  # readFileSync
    assert "JS-003" in rule_ids  # eval()
    assert "EXPRESS-001" in rule_ids  # missing 4-arg error middleware
    assert "EXPRESS-003" in rule_ids  # async route without try/catch


def test_audit_is_strictly_read_only(bad_fastapi_dir: Path):
    # Capture modification times of all files before audit
    mtimes_before = {f: f.stat().st_mtime for f in bad_fastapi_dir.rglob("*") if f.is_file()}

    config = Config.default()
    engine = AuditEngine(bad_fastapi_dir, config)
    engine.run()

    mtimes_after = {f: f.stat().st_mtime for f in bad_fastapi_dir.rglob("*") if f.is_file()}
    assert mtimes_before == mtimes_after
