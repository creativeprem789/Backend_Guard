# 🛡️ Backend Guard Audit Case Study: GPT-Researcher (18k+ ⭐ AI Agent Backend)

> **Audited by**: [Backend Guard v1.0.0](https://pypi.org/project/backend-guard/)  
> **Target Codebase**: [`assafelovic/gpt-researcher`](https://github.com/assafelovic/gpt-researcher) (Autonomous AI Research Agent)  
> **Audited Date**: November 2026  
> **Scan Duration**: 75.4 seconds across 924 files (60,294 lines of code)

---

## 📊 Executive Summary

| Metric | Measurement |
|---|---|
| **Repository** | `assafelovic/gpt-researcher` |
| **Domain** | Autonomous Multi-Agent AI Research System |
| **Tech Stack** | Python, FastAPI, WebSockets, Next.js / TypeScript |
| **Total Lines Scanned** | 60,294 LOC |
| **Files Analyzed** | 924 files |
| **Total Findings** | **811** (1 Critical, 48 High, 106 Medium, 656 Low) |
| **False Positive Suppression** | Enabled (Context-aware AST verification) |

---

## 🚨 Top 5 High-Impact Production Defects Discovered

### 1. 🔴 CRITICAL: Unsafe Object Deserialization via `pickle` (`PY-002`)
- **Location**: `gpt_researcher/scraper/browser/browser.py:140`
- **Issue**: Use of raw `pickle.load()` on scraped browser session state.
- **Why It Matters in Production**: In an AI agent system that browses arbitrary internet URLs, unpickling untrusted binary streams allows arbitrary code execution (RCE) on the host server.
- **Recommended Fix**: Serialize session cookies and browser storage using encrypted JSON or strict schema validation (`pydantic`).

---

### 2. 🟠 HIGH: Event-Loop Freezing Synchronous I/O in `async def` (`PY-ASYNC-001`)
- **Location**: `gpt_researcher/llm_provider/image/modelslab_image_generator.py:219`
- **Issue**: Calling blocking synchronous network/file I/O directly inside an asynchronous coroutine (`async def generate(...)`).
- **Why It Matters in Production**: In high-concurrency FastAPI/asyncio servers, a synchronous network delay blocks the single-threaded event loop, stalling all simultaneous WebSocket clients and background research agents.
- **Recommended Fix**: Offload blocking I/O using `await asyncio.to_thread(sync_func)` or switch to native asynchronous clients like `httpx.AsyncClient`.

---

### 3. 🟠 HIGH: Cross-Agent State Pollution via Mutable Default Arguments (`PY-001`)
- **Location**: `backend/report_type/detailed_report/detailed_report.py:16`, `backend/server/websocket_manager.py:101`, `gpt_researcher/agent.py:475`
- **Issue**: Function definitions using mutable collections as defaults (e.g., `def __init__(self, headers={}, items=[])`).
- **Why It Matters in Production**: Python instantiates default arguments only once at module load time. When multiple concurrent research agents or WebSocket sessions modify the list/dict, state leaks across different user sessions, causing phantom research context leaks.
- **Recommended Fix**:
  ```python
  # Instead of:
  def __init__(self, headers: dict = {}):
      self.headers = headers


  # Use defensive sentinel:
  def __init__(self, headers: Optional[dict] = None):
      self.headers = headers if headers is not None else {}
  ```

---

### 4. 🟠 HIGH: Silent Exception Swallowing (`ERR-001`)
- **Location**: `backend/server/websocket_manager.py:98`, `gpt_researcher/retrievers/mcp/retriever.py:260`
- **Issue**: Empty `try ... except: pass` blocks around WebSocket disconnects and MCP tool calls.
- **Why It Matters in Production**: Silent exception swallowing masks network drops, rate limits, and broken MCP connections. The agent keeps waiting indefinitely for tools without informing the client why the run stalled.
- **Recommended Fix**: Log the caught exception with structured context (`logger.exception("WebSocket disconnected unexpectedly")`) and emit clean failure events.

---

### 5. 🟠 HIGH: Raw Internal Stack Traces Leaked to Client Responses (`ERR-003`)
- **Location**: `backend/server/app.py:308`, `backend/chat/chat.py:115`
- **Issue**: Returning unformatted internal exceptions and traceback strings directly in the JSON response payload.
- **Why It Matters in Production**: Exposes internal file paths, module structures, and sensitive runtime environment details to public API clients.
- **Recommended Fix**: Intercept errors with a global exception handler and return standardized error objects:
  ```json
  {
    "error": "Failed to process research prompt",
    "request_id": "req_847294",
    "status": 500
  }
  ```

---

## 📈 Maintainability & Complexity Breakdown

- **Cyclomatic Complexity (`CMPLX-001`)**: 14 functions exhibited cyclomatic complexity > 15 (peaking in `gpt_researcher/skills/researcher.py` and `backend/server/server_utils.py`).
- **Arrow Antipattern Nesting (`CMPLX-003`)**: 22 deep nesting chains exceeded 5 levels of indentation.
- **Unpinned Dependencies (`DEP-002`)**: Multiple sub-manifests (`deep_agents/requirements.txt`, `multi_agents/requirements.txt`) lacked pinned version constraints, risking non-deterministic deployment failures.
- **Missing API Response Models (`FASTAPI-002`)**: 8 mutating endpoints in `backend/server/app.py` did not declare `response_model`, leaving response schemas unvalidated.

---

## 💡 How to Run This Audit on Any Backend

Install Backend Guard directly from PyPI:

```bash
pip install backend-guard
```

Run an audit on any repository:

```bash
# Terminal output with actionable fixes
backend-guard audit /path/to/backend

# Export full Markdown report
backend-guard audit /path/to/backend --format markdown -o AUDIT_REPORT.md

# Export SARIF for GitHub Code Scanning
backend-guard audit /path/to/backend --format sarif -o results.sarif
```

