"""Unit tests for project scanner and technology detection."""

from pathlib import Path

from auditor.config import Config
from auditor.discovery import ProjectScanner


def test_detect_python_fastapi(good_fastapi_dir: Path):
    scanner = ProjectScanner(good_fastapi_dir, Config.default())
    info = scanner.scan()

    assert info.has_language("python")
    assert info.has_framework("fastapi")
    assert len(info.files) > 0
    assert info.total_lines > 0


def test_detect_node_express(good_express_dir: Path):
    scanner = ProjectScanner(good_express_dir, Config.default())
    info = scanner.scan()

    assert info.has_language("javascript")
    assert info.has_framework("express")


def test_detect_typescript_nestjs(good_nestjs_dir: Path):
    scanner = ProjectScanner(good_nestjs_dir, Config.default())
    info = scanner.scan()

    assert info.has_language("typescript")
    assert info.has_framework("nestjs")


def test_respect_gitignore(tmp_path: Path):
    gi = tmp_path / ".gitignore"
    gi.write_text("ignored_dir/\n*.tmp\n", encoding="utf-8")

    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "secret.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "data.tmp").write_text("temp", encoding="utf-8")
    (tmp_path / "real.py").write_text("y = 2", encoding="utf-8")

    scanner = ProjectScanner(tmp_path, Config.default())
    info = scanner.scan()

    file_names = [f.name for f in info.files]
    assert "real.py" in file_names
    assert "secret.py" not in file_names
    assert "data.tmp" not in file_names
