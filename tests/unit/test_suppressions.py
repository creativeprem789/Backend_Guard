"""Unit tests for inline comment and block suppressions."""

from auditor.suppressions import SuppressionIndex


def test_inline_suppression_comment():
    idx = SuppressionIndex()
    lines = [
        "import os",
        "# backend-auditor: ignore SEC-001 -- deliberate mock key",
        "API_KEY = 'secret12345'",
        "print('done')",
    ]
    idx.scan_file("test.py", lines)

    # Line 2 and line 3 should be suppressed for SEC-001
    assert idx.is_suppressed("test.py", 3, "SEC-001")
    assert not idx.is_suppressed("test.py", 4, "SEC-001")
    assert not idx.is_suppressed("test.py", 3, "SEC-002")


def test_js_style_suppression():
    idx = SuppressionIndex()
    lines = [
        "// backend-guard: ignore JS-001",
        "const data = fs.readFileSync('test');",
    ]
    idx.scan_file("server.js", lines)
    assert idx.is_suppressed("server.js", 2, "JS-001")


def test_block_suppression():
    idx = SuppressionIndex()
    lines = [
        "# backend-auditor: ignore-block ARCH-001",
        "from infra import db",
        "db.execute('SELECT 1')",
        "# backend-auditor: end-ignore-block",
        "from infra import raw",
    ]
    idx.scan_file("routes.py", lines)
    assert idx.is_suppressed("routes.py", 2, "ARCH-001")
    assert idx.is_suppressed("routes.py", 3, "ARCH-001")
    assert not idx.is_suppressed("routes.py", 5, "ARCH-001")


def test_file_level_suppression():
    idx = SuppressionIndex()
    lines = [
        "# backend-auditor: ignore-file",
        "line 1",
        "line 2",
    ]
    idx.scan_file("legacy.py", lines)
    assert idx.is_suppressed("legacy.py", 10, "ANY-RULE")

