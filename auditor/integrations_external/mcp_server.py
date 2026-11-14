"""Model Context Protocol (MCP) server for AI coding assistants."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from auditor.config import Config
from auditor.discovery import ProjectScanner
from auditor.engine import AuditEngine
from auditor.models import AuditResult
from auditor.registry import RuleRegistry


class McpServer:
    """Standard JSON-RPC 2.0 stdio MCP server for Backend Guard."""

    def __init__(self) -> None:
        self.last_result: Optional[AuditResult] = None

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        handler = getattr(self, f"rpc_{method}", None)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        try:
            result = handler(params)
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": str(exc)},
            }

    def rpc_detect_backend_stack(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect target directory and detect language, frameworks, and manifests."""
        path = Path(params.get("path", ".")).resolve()
        config = Config.load(path)
        scanner = ProjectScanner(path, config)
        project_info = scanner.scan()
        return project_info.to_dict()

    def rpc_audit_backend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute audit on target backend codebase."""
        path = Path(params.get("path", ".")).resolve()
        config = Config.load(path)
        if "with_tools" in params:
            config.with_tools = bool(params["with_tools"])
        engine = AuditEngine(path, config)
        result = engine.run()
        self.last_result = result
        return result.to_dict()

    def rpc_get_finding_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve detailed information about a finding by rule_id or index."""
        rule_id = params.get("rule_id")
        index = params.get("index")

        if not self.last_result:
            return {"error": "No recent audit result available. Run audit_backend first."}

        findings = self.last_result.findings
        if index is not None and 0 <= index < len(findings):
            return findings[index].to_dict()

        if rule_id:
            matches = [f.to_dict() for f in findings if f.rule_id == rule_id]
            return {"matches": matches}

        return {"error": "Must provide rule_id or valid index."}

    def rpc_get_rule_information(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query metadata and remediation guidance for a specific rule ID."""
        rule_id = params.get("rule_id", "")
        rule = RuleRegistry.get(rule_id)
        if not rule:
            return {"error": f"Rule not found: {rule_id}"}
        return rule.metadata.to_dict()

    def rpc_generate_fix_suggestion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Return suggested code fix and architectural recommendations for a rule."""
        rule_id = params.get("rule_id", "")
        rule = RuleRegistry.get(rule_id)
        if not rule:
            return {"error": f"Rule not found: {rule_id}"}
        return {
            "rule_id": rule_id,
            "title": rule.title,
            "recommendation": rule.metadata.recommendation,
            "suggested_fix": rule.metadata.suggested_fix,
            "autofix_available": rule.metadata.autofix_available,
        }

    def run_stdio(self) -> None:
        """Run JSON-RPC loop over standard input / output."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception:
                pass


if __name__ == "__main__":
    McpServer().run_stdio()
