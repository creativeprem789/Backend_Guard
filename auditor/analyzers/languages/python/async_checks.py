"""Python asynchronous programming checks: blocking calls in async functions."""

from __future__ import annotations

import ast
from typing import List

from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_rule

BLOCKING_CALLS = {
    ("time", "sleep"): "asyncio.sleep()",
    ("requests", "get"): "httpx.AsyncClient or aiohttp",
    ("requests", "post"): "httpx.AsyncClient or aiohttp",
    ("requests", "put"): "httpx.AsyncClient or aiohttp",
    ("requests", "delete"): "httpx.AsyncClient or aiohttp",
    ("urllib", "request"): "httpx or aiohttp",
}


@register_rule
class SyncBlockingInAsyncRule(BaseRule):
    """Detects synchronous blocking operations inside async def functions."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="PY-ASYNC-001",
                title="Synchronous blocking call in async function",
                category=Category.ASYNC_CONCURRENCY,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="Synchronous blocking functions (such as time.sleep or requests.get) executed inside async def freeze the event loop.",
                impact="Completely blocks the single-threaded asyncio event loop, halting all concurrent requests and destroying backend throughput.",
                recommendation="Replace blocking synchronous calls with their non-blocking asynchronous equivalents.",
                suggested_fix="Replace with await asyncio.sleep() or an async HTTP client like httpx.",
                language="python",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call):
                            call_str = self._get_call_signature(child)
                            for (mod, fn), async_alt in BLOCKING_CALLS.items():
                                if f"{mod}.{fn}" in call_str or (
                                    mod in call_str and fn in call_str
                                ):
                                    rel_file = context.get_relative_path(py_file)
                                    findings.append(
                                        self.create_finding(
                                            file=rel_file,
                                            line=child.lineno,
                                            description=f"Blocking call '{call_str}()' invoked inside async function '{node.name}'. Use {async_alt} instead.",
                                            evidence=f"Call to {call_str}() at line {child.lineno} inside async def {node.name}",
                                        )
                                    )
        return findings

    @staticmethod
    def _get_call_signature(call_node: ast.Call) -> str:
        if isinstance(call_node.func, ast.Attribute):
            val_name = ""
            if isinstance(call_node.func.value, ast.Name):
                val_name = call_node.func.value.id
            elif isinstance(call_node.func.value, ast.Attribute):
                val_name = call_node.func.value.attr
            return f"{val_name}.{call_node.func.attr}"
        elif isinstance(call_node.func, ast.Name):
            return call_node.func.id
        return ""
