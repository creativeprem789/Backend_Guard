"""Tests for security vulnerability rules."""

from pathlib import Path

from auditor.analyzers.universal.security import (
    CommandInjectionRule,
    HardcodedSecretsRule,
    InsecureCorsRule,
    SqlInjectionRule,
)


def test_hardcoded_secrets_detection(tmp_path: Path, make_context):
    p = tmp_path / "app.py"
    # Construct test key dynamically to prevent static rule self-triggering
    sample_key = "api_" + "key=abcdef12345678901234"
    p.write_text(f"API_KEY = '{sample_key}'\n", encoding="utf-8")

    ctx = make_context(tmp_path)
    rule = HardcodedSecretsRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-001"


def test_sql_injection_detection(tmp_path: Path, make_context):
    p = tmp_path / "service.py"
    p.write_text(
        "def find(val):\n    db.execute(f'SELECT * FROM t WHERE x = {val}')\n", encoding="utf-8"
    )

    ctx = make_context(tmp_path)
    rule = SqlInjectionRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-002"


def test_safe_sql_no_finding(tmp_path: Path, make_context):
    p = tmp_path / "safe_service.py"
    p.write_text(
        "def find(val):\n    db.execute('SELECT * FROM t WHERE x = %s', (val,))\n", encoding="utf-8"
    )

    ctx = make_context(tmp_path)
    rule = SqlInjectionRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 0


def test_command_injection_detection(tmp_path: Path, make_context):
    p = tmp_path / "cmd.py"
    p.write_text("import os\ndef run_cmd(user_in):\n    os.system(user_in)\n", encoding="utf-8")

    ctx = make_context(tmp_path)
    rule = CommandInjectionRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-003"


def test_insecure_cors_detection(tmp_path: Path, make_context):
    p = tmp_path / "cors.py"
    # Write sample code into temp file for testing
    cors_code = (
        "app.add_middleware(CORSMiddleware, allow_origins=['" + "*'], allow_credentials=True)\n"
    )
    p.write_text(cors_code, encoding="utf-8")

    ctx = make_context(tmp_path)
    rule = InsecureCorsRule()
    findings = rule.evaluate(ctx)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC-004"
