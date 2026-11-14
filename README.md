# 🛡️ Backend Guard

<div align="center">

**Universal Backend Codebase Auditor & Architecture Linter**

*Inspect backend architecture, catch silent production defects, enforce separation of concerns, and secure APIs across multiple languages and frameworks.*

[![Backend Guard CI](https://github.com/creativeprem789/Backend_Guard/actions/workflows/tests.yml/badge.svg)](https://github.com/creativeprem789/Backend_Guard/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Node.js: 18+](https://img.shields.io/badge/Node.js-18%2B-339933.svg?logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type Checked: mypy](https://img.shields.io/badge/types-mypy-blue.svg)](http://mypy-lang.org/)

[Features](#-features) •
[Why Backend Guard?](#-why-backend-guard) •
[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Auditing Your Backend](#-auditing-your-backend) •
[Rule Reference](#-rule-catalog) •
[AI & MCP Server](#-ai-coding-assistant-integration-mcp) •
[Configuration](#-configuration) •
[Documentation](#-documentation)

</div>

---

## 💡 What is Backend Guard?

**Backend Guard** is an extensible, open-source static analysis engine designed **exclusively for backend systems**.

While traditional linters check formatting and general style, Backend Guard evaluates **backend architecture, system reliability, data flow, concurrency safety, and production readiness**.

It answers questions linters ignore:
- ❌ Are HTTP route handlers directly executing database queries instead of delegating to a service/repository?
- ❌ Is a synchronous blocking call like `time.sleep()` or `fs.readFileSync` freezing the async event loop under high load?
- ❌ Are database queries executing inside a loop iteration creating severe **N+1 query** performance bottlenecks?
- ❌ Is an unhandled promise rejection in an Express route silently hanging client connections indefinitely?
- ❌ Are database transactions committing without explicit rollback handlers in exception paths?
- ❌ Is your backend missing health probes (`/health`), request timeouts, or pagination on collection endpoints?

---

## 🥊 Why Backend Guard?

| Feature | Standard Linters (Ruff, ESLint) | Security Scanners (Bandit, Snyk) | 🛡️ **Backend Guard** |
|---|:---:|:---:|:---:|
| Syntax & Formatting | ✅ | ❌ | ✅ |
| Known Vulnerability Scanning | ❌ | ✅ | ✅ |
| **Layer Boundary & Coupling (Presentation ➔ Infra)** | ❌ | ❌ | ✅ |
| **Async Event Loop Blocking Detections** | ❌ | ❌ | ✅ |
| **Database Transaction & N+1 Query Risks** | ❌ | ❌ | ✅ |
| **Framework Lifecycle Hygiene (FastAPI, Express, NestJS)** | ❌ | ❌ | ✅ |
| **API Pagination & HTTP Status Semantics** | ❌ | ❌ | ✅ |
| **Production Readiness (Health Probes, Graceful Shutdown)** | ❌ | ❌ | ✅ |
| **AI Coding Assistant Protocol (MCP Server Native)** | ❌ | ❌ | ✅ |
| **Strictly Read-Only Guarantee** | Varies | ✅ | ✅ |

---

## 🏗️ Architecture

Backend Guard employs a **language-independent core engine** coupled with specialized AST and framework analyzers:

```text
                            TARGET BACKEND CODEBASE
                                       │
                                       ▼
                             PROJECT DISCOVERY
                      (File tree, .gitignore, exclusions)
                                       │
                                       ▼
                             TECHNOLOGY DETECTION
                    (Python, JS, TS, FastAPI, Express, NestJS)
                                       │
                                       ▼
                             UNIVERSAL CORE ENGINE
               ┌───────────────────────┼───────────────────────┐
               ▼                       ▼                       ▼
       UNIVERSAL ANALYZERS     LANGUAGE ANALYZERS     FRAMEWORK ANALYZERS
       • Architecture          • Python (AST, async)  • FastAPI
       • SOLID Principles      • JavaScript (Node)    • Express.js
       • Security & Secrets    • TypeScript (strict)  • NestJS
       • Database & N+1                               • Django / Flask
       • Error Handling
       • Production Readiness
               │                       │                       │
               └───────────────────────┼───────────────────────┘
                                       │
                                       ▼
                               UNIFIED FINDINGS
                    (Fingerprinted, Suppressed, Baselines)
                                       │
               ┌───────────────────────┼───────────────────────┐
               ▼                       ▼                       ▼
        TERMINAL REPORT           JSON / SARIF             MARKDOWN
      (ANSI cards & fixes)     (GitHub CodeScan)       (PR Documentation)
                                       │
                                       ▼
                       AI CODING ASSISTANTS & CI/CD PIPELINES
                          (Model Context Protocol - MCP)
```

---

## 🚀 Supported Tech Stack

| Ecosystem | Status | Analyzed Frameworks | Key Checks |
|---|:---:|---|---|
| **Python** | ✅ Supported | **FastAPI**, **Django**, **Flask** | Blocking I/O in async def, mutable defaults, unsafe deserialization, DI validation, raw SQL in routes |
| **JavaScript** | ✅ Supported | **Express**, **NestJS** | Sync I/O on servers, unhandled promises, eval safety, missing 4-arg error middleware |
| **TypeScript** | ✅ Supported | **Express**, **NestJS** | Unsafe `any` type propagation, `@Injectable()` decoration, controller DB isolation |
| Java | 📋 Planned v1.1 | Spring Boot | Dependency injection lifecycle, JPA N+1 query patterns, transaction boundaries |
| Go | 📋 Planned v1.1 | Gin, Echo, Fiber | Goroutine leaks, unbuffered channel deadlocks, handler error propagation |
| PHP | 📋 Planned v1.2 | Laravel, Symfony | Eloquent eager-loading, container isolation, mass-assignment vulnerabilities |
| C# | 📋 Planned v1.2 | ASP.NET Core | Middleware ordering, Entity Framework DbContext concurrency |
| Rust | 📋 Planned v1.3 | Actix Web, Axum | Handler panic safety (`unwrap()`), async runtime blocking |

---

## 📦 Installation

### Option 1: Install from GitHub
```bash
git clone https://github.com/creativeprem789/Backend_Guard.git
cd Backend_Guard/backend-auditor
pip install -e .
```

### Option 2: Install via pip (once published on PyPI)
```bash
pip install backend-auditor
```

After installation, both `backend-guard` and `backend-auditor` CLI commands are available globally.

```bash
backend-guard --version
# Output: backend-guard 1.0.0
```

---

## ⚡ Quick Start

```bash
# 1. Audit your current backend directory
backend-guard audit .

# 2. Detect the technologies and frameworks in a project
backend-guard detect /path/to/backend

# 3. View all 42 supported backend audit rules
backend-guard rules

# 4. Generate a GitHub Flavored Markdown report for a Pull Request
backend-guard audit . --format markdown --output AUDIT.md

# 5. Output SARIF format for GitHub Code Scanning
backend-guard audit . --format sarif --output results.sarif
```

---

## 🔍 Auditing Your Backend

To audit any existing backend codebase, simply point `backend-guard` to your project folder:

```bash
backend-guard audit /path/to/my-project
```

### Sample Terminal Output

```text
============================================================================
 🛡️  BACKEND GUARD AUDIT REPORT - my-backend-service
============================================================================
  Root:       C:/Projects/my-backend-service
  Languages:  Python (high)
  Frameworks: FastAPI (high)
  Scanned:    34 files (5,420 lines of code) in 0.28s
----------------------------------------------------------------------------

  FINDINGS SUMMARY:
   Critical: 1  |  High: 3  |  Medium: 2  |  Low: 1  |  Info: 0

----------------------------------------------------------------------------
  DETAILED FINDINGS
----------------------------------------------------------------------------

 1. [CRITICAL] SEC-002: SQL injection risk from string formatting (high conf)
    Location: app/routers/orders.py:42
    Problem:  Database query constructed using Python f-string interpolation.
    Evidence: db.execute(f"SELECT * FROM orders WHERE id = '{order_id}'")
    Impact:   Attackers can bypass authorization or extract arbitrary database records.
    Fix:      Use parameterized queries with bind variables.
    Example:  cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))

 2. [HIGH] PY-ASYNC-001: Synchronous blocking call in async function (high conf)
    Location: app/services/notifier.py:18
    Problem:  Blocking call 'time.sleep()' invoked inside async function 'send_webhook'. Use asyncio.sleep() instead.
    Evidence: time.sleep(2)
    Impact:   Completely freezes the single-threaded asyncio event loop, halting all concurrent requests.
    Fix:      Replace with await asyncio.sleep(2).

 3. [HIGH] DB-001: Potential N+1 query pattern detected in loop (medium conf)
    Location: app/services/users.py:87
    Problem:  Database query 'db.get()' executed inside loop iteration.
    Evidence: Loop query at line 87
    Impact:   Multiplies database round-trips; an endpoint returning 100 items executes 101 queries.
    Fix:      Batch query IDs using .filter(Model.id.in_(ids)) outside the loop or use eager loading.

============================================================================
```

### Filtering Findings
```bash
# Only fail CI on critical and high severity findings
backend-guard audit . --fail-on high

# Only audit security-related rules
backend-guard audit . --category security

# Exclude generated code and migrations
backend-guard audit . --exclude migrations,generated,venv
```

---

## 🤖 AI Coding Assistant Integration (MCP)

Backend Guard includes a native **Model Context Protocol (MCP)** server over `stdio`. AI coding tools like **Cursor**, **Claude Desktop**, and **Antigravity** can inspect your backend, execute audits, and fetch fix suggestions dynamically.

### Start the MCP Server
```bash
backend-guard mcp
```

### Configure in Claude Desktop (`claude_desktop_config.json`) or Cursor
```json
{
  "mcpServers": {
    "backend-guard": {
      "command": "backend-guard",
      "args": ["mcp"]
    }
  }
}
```

### Supported MCP Operations
- `detect_backend_stack`: Inspects target codebase and returns detected frameworks, manifests, and file counts.
- `audit_backend`: Runs the full audit engine and returns structured JSON findings.
- `get_finding_details`: Fetches full impact, evidence, and remediation guidance for a specific finding.
- `get_rule_information`: Returns rule documentation and architecture rationale.
- `generate_fix_suggestion`: Returns concrete refactoring code snippets.

---

## 🚫 False-Positive Controls & Suppressions

Backend Guard is engineered to be developer-friendly. You can suppress individual findings directly in code:

### Python
```python
# Inline suppression
DUMMY_KEY = "test_key_1234567890"  # backend-auditor: ignore SEC-001 -- mock test key

# Block suppression
# backend-auditor: ignore-block ARCH-001
from app.infra import raw_db
raw_db.ping()
# backend-auditor: end-ignore-block

# File-level suppression
# backend-auditor: ignore-file
```

### JavaScript / TypeScript
```javascript
// Inline suppression
const data = fs.readFileSync('conf.json'); // backend-guard: ignore JS-001 -- startup only

// Block suppression
/* backend-guard: ignore-block JS-003 */
const res = eval(expr);
/* backend-guard: end-ignore-block */
```

### Baseline Snapshots for Legacy Codebases
Adopt Backend Guard on large existing codebases without breaking your build:
```bash
# 1. Snapshot all existing legacy findings
backend-guard baseline generate . -o baseline.json

# 2. Audit against baseline (only NEW defects fail the build)
backend-guard audit . --baseline baseline.json
```

---

## ⚙️ Configuration (`backend-auditor.toml`)

Initialize a configuration file:
```bash
backend-guard init .
```

`backend-auditor.toml`:
```toml
[general]
failure_threshold = "high"       # Exit code 1 if findings >= threshold (critical, high, medium, low)
confidence_threshold = "low"     # Minimum confidence level to report
# baseline = "baseline.json"

[rules]
# enable = ["ARCH-001", "SEC-001"] # Whitelist specific rules
disable = ["LOG-002"]             # Ignore specific rules

[rules.severity]
# Override default severities
"API-001" = "low"

[exclusions]
dirs = [
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "migrations"
]
files = []
respect_gitignore = true

[complexity]
max_cyclomatic_complexity = 15
max_function_lines = 60
max_file_lines = 600

[tools]
# External tools executed when running with --with-tools
ruff = true
eslint = true
mypy = true
bandit = true
pytest = true
```

---

## 📋 Rule Catalog

<details>
<summary><b>Click to expand the 42 implemented backend rules</b></summary>

### 1. Architecture (`architecture`)
- `ARCH-001` [HIGH]: Direct presentation to infrastructure coupling (route directly calling database).
- `ARCH-003` [HIGH]: Circular module dependency cycle detected.
- `DUP-001` [LOW]: Substantial code duplication across handlers/services.
- `FASTAPI-001` [HIGH]: Direct raw SQL execution inside route endpoint.
- `NEST-002` [HIGH]: Direct database access inside NestJS controller.

### 2. SOLID Principles (`solid`)
- `SOLID-001` [MEDIUM]: Single Responsibility Principle: God class detected (> 15 methods, > 250 lines).
- `SOLID-002` [LOW]: Open/Closed Principle: Excessive type-checking cascades (`isinstance` ladders).

### 3. Security (`security`)
- `SEC-001` [CRITICAL]: Hardcoded secret or API credential detected.
- `SEC-002` [CRITICAL]: SQL injection risk from string formatting/concatenation.
- `SEC-003` [HIGH]: Dangerous system command execution (`os.system`, `child_process.exec`).
- `SEC-004` [HIGH]: Insecure CORS wildcard origin with credentials enabled.
- `SEC-005` [HIGH]: Path traversal vulnerability risk in file operations.
- `PY-002` [CRITICAL]: Unsafe deserialization via `pickle` or `yaml.load` without SafeLoader.
- `JS-003` [CRITICAL]: Dangerous dynamic code evaluation (`eval()` or `new Function()`).

### 4. Async & Concurrency (`async_concurrency`)
- `PY-ASYNC-001` [HIGH]: Synchronous blocking call inside `async def` function.
- `JS-001` [HIGH]: Synchronous blocking I/O call in Node.js server (`fs.readFileSync`).

### 5. Database Engineering (`database`)
- `DB-001` [HIGH]: Potential N+1 query pattern detected in loop.
- `DB-002` [HIGH]: Database transaction commit without explicit rollback handler.

### 6. Error Handling (`error_handling`)
- `ERR-001` [HIGH]: Silent exception swallowing (`except: pass` or empty catch).
- `ERR-002` [MEDIUM]: Overly broad exception catching without re-raise (`except:` or `BaseException`).
- `ERR-003` [HIGH]: Internal stack trace or raw error leaked to client.
- `JS-002` [HIGH]: Unhandled promise rejection risk (`.then()` without `.catch()`).
- `EXPRESS-001` [HIGH]: Missing global 4-argument error handling middleware in Express.
- `EXPRESS-003` [HIGH]: Async Express route handler without error handling.

### 7. Complexity (`complexity`)
- `CMPLX-001` [MEDIUM]: Excessive cyclomatic complexity in function (> 15).
- `CMPLX-002` [LOW]: Function exceeds maximum line threshold (> 60 lines).
- `CMPLX-003` [MEDIUM]: Deeply nested control structures (Arrow antipattern > 4 levels).

### 8. API Design (`api_design`)
- `API-001` [MEDIUM]: Missing pagination on collection endpoint.
- `API-002` [LOW]: HTTP 200 OK returned with error payload.
- `FASTAPI-002` [LOW]: Missing `response_model` on mutating route endpoint.

### 9. Dependency Management (`dependency`)
- `DEP-002` [MEDIUM]: Unpinned dependency version in production manifest (`requirements.txt` / `package.json`).

### 10. Logging (`production_readiness`)
- `LOG-001` [HIGH]: Sensitive credential or auth token logged.
- `LOG-002` [LOW]: Raw stdout printing (`print()` / `console.log()`) instead of structured logger.

### 11. Production Readiness (`production_readiness`)
- `CONF-002` [HIGH]: Production debug mode hardcoded to True.
- `PROD-001` [LOW]: Missing health check or liveness endpoint (`/health`, `/healthz`).

### 12. Testing (`testing`)
- `TEST-001` [HIGH]: Missing automated test suite in non-trivial project.
- `TEST-002` [MEDIUM]: Vacuous test case containing no assertions.

### 13. Language & Framework Patterns (`patterns`, `typing`)
- `PY-001` [HIGH]: Dangerous mutable default argument (`def f(items=[])`).
- `PY-003` [LOW]: Wildcard import polluting namespace (`from module import *`).
- `PY-TYPE-001` [LOW]: Missing type annotations on public function.
- `TS-001` [LOW]: Excessive use of unsafe `any` type in TypeScript.
- `NEST-001` [HIGH]: Service class missing `@Injectable()` decorator.

</details>

---

## 🚦 Exit Codes

| Code | Meaning |
|:---:|---|
| `0` | Audit completed successfully; no blocking threshold exceeded. |
| `1` | Blocking findings detected (findings at or above configured `failure_threshold`). |
| `2` | Invalid usage or configuration error. |
| `3` | Audit incomplete because a required analysis stage failed. |

---

## 🔄 GitHub Actions CI Integration

Add `.github/workflows/audit.yml` to your repository:

```yaml
name: Backend Architecture Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Backend Guard
        run: |
          pip install git+https://github.com/creativeprem789/Backend_Guard.git#subdirectory=backend-auditor

      - name: Run Backend Guard Audit
        run: |
          backend-guard audit . --fail-on high --format github
```

---

## 📚 Documentation

For deeper details, consult the documentation in [`docs/`](docs/):
- [Architecture & Design Details](docs/architecture.md)
- [Rules Reference](docs/rules_reference.md)
- [Supported Languages & Frameworks](docs/supported_languages.md)
- [Configuration Reference](docs/configuration.md)
- [Integrations (MCP, CI/CD, External Tools)](docs/integrations.md)
- [False-Positive Management](docs/false_positives.md)
- [Contributing Guide](CONTRIBUTING.md)

---

## 🤝 Contributing

Contributions are welcomed! Check out [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to:
1. Add new language analyzers (Go, Java, Rust).
2. Add framework-specific rules (Spring Boot, Laravel, Gin).
3. Run the automated test suite (`pytest`) and linters (`ruff`, `mypy`).

---

## 📄 License

Backend Guard is open-source software licensed under the [MIT License](LICENSE).
