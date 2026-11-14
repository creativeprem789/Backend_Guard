"""Unit tests for Model Context Protocol (MCP) server endpoints."""

from pathlib import Path

from auditor.integrations_external.mcp_server import McpServer


def test_mcp_detect_backend_stack(good_fastapi_dir: Path):
    server = McpServer()
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "detect_backend_stack",
        "params": {"path": str(good_fastapi_dir)},
    }
    resp = server.handle_request(req)
    assert resp["id"] == 1
    assert "result" in resp
    assert "Python" in str(resp["result"]["languages"])
    assert "FastAPI" in str(resp["result"]["frameworks"])


def test_mcp_get_rule_information():
    server = McpServer()
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "get_rule_information",
        "params": {"rule_id": "SEC-001"},
    }
    resp = server.handle_request(req)
    assert resp["id"] == 2
    assert resp["result"]["rule_id"] == "SEC-001"
    assert "security" in resp["result"]["category"].lower()


def test_mcp_generate_fix_suggestion():
    server = McpServer()
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "generate_fix_suggestion",
        "params": {"rule_id": "FASTAPI-001"},
    }
    resp = server.handle_request(req)
    assert resp["id"] == 3
    assert resp["result"]["rule_id"] == "FASTAPI-001"
    assert "Depends" in resp["result"]["suggested_fix"]
