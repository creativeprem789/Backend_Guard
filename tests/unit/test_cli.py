"""Unit tests for CLI commands and exit codes."""

from pathlib import Path

from auditor.cli import main


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert "backend-guard" in captured.out or "backend-guard" in captured.err


def test_cli_languages(capsys):
    code = main(["languages"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Python" in captured.out
    assert "JavaScript" in captured.out
    assert "TypeScript" in captured.out


def test_cli_rules(capsys):
    code = main(["rules"])
    assert code == 0
    captured = capsys.readouterr()
    assert "SEC-001" in captured.out
    assert "ARCH-001" in captured.out


def test_cli_detect(good_fastapi_dir: Path, capsys):
    code = main(["detect", str(good_fastapi_dir)])
    assert code == 0
    captured = capsys.readouterr()
    assert "FastAPI" in captured.out
    assert "Python" in captured.out


def test_cli_audit_exit_code_good_project(good_fastapi_dir: Path):
    code = main(["audit", str(good_fastapi_dir), "--format", "json"])
    assert code == 0


def test_cli_audit_exit_code_bad_project(bad_fastapi_dir: Path):
    code = main(["audit", str(bad_fastapi_dir), "--format", "json", "--fail-on", "high"])
    # Blocking findings exist (SEC-001, SEC-002, etc.) -> exit code 1
    assert code == 1


def test_cli_invalid_path():
    code = main(["audit", "/non_existent_path_xyz_123"])
    assert code == 2


def test_cli_baseline_flow(bad_fastapi_dir: Path, tmp_path: Path):
    baseline_file = tmp_path / "test_baseline.json"
    # Generate baseline
    gen_code = main(["baseline", "generate", str(bad_fastapi_dir), "-o", str(baseline_file)])
    assert gen_code == 0
    assert baseline_file.is_file()

    # Re-run audit with baseline applied -> legacy findings suppressed -> exit code 0
    audit_code = main(["audit", str(bad_fastapi_dir), "--baseline", str(baseline_file)])
    assert audit_code == 0
