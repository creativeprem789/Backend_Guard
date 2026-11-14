# 🛡️ Backend Guard (Universal Backend Auditor)

> **A production-grade, extensible, open-source static analysis and architecture auditing tool designed exclusively for backend codebases.**

[![CI](https://github.com/backend-guard/backend-auditor/actions/workflows/tests.yml/badge.svg)](https://github.com/backend-guard/backend-auditor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)](https://python.org)
[![Node: 18+](https://img.shields.io/badge/Node-18%2B-green.svg)](https://nodejs.org)

---

## 💡 Why Backend Guard?

Most static analysis tools focus on either general syntax formatting (e.g. ESLint, Ruff) or low-level security vulnerabilities (e.g. Bandit, Semgrep). Ordinary linters cannot answer critical backend architectural questions:

- *Are HTTP route handlers directly querying the database instead of through a service or repository layer?*
- *Is there a blocking synchronous `time.sleep()` or `fs.readFileSync` freezing an async event loop?*
- *Are database queries executing inside a loop iteration causing an N+1 query performance cliff?*
- *Is an unhandled promise rejection in an Express endpoint going to hang client sockets until timeout?*
- *Are database transaction commits lacking explicit rollback blocks in error paths?*
- *Is the codebase missing health probes, graceful shutdown handling, or pagination on collection endpoints?*

**Backend Guard** evaluates backend architectures, domain boundaries, security hygiene, database transaction safety, and production readiness across multiple programming languages and frameworks.

---

## 🧭 Architecture & Design

Backend Guard is designed around a **language-independent core** with pluggable language and framework analyzers:

```text
                    BACKEND CODEBASE
                            |
                            v
                  PROJECT DISCOVERY
                            |
                            v
                  TECHNOLOGY DETECTION
                            |
                            v
                   UNIVERSAL CORE ENGINE
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
      UNIVERSAL       LANGUAGE          FRAMEWORK
      ANALYZERS       ANALYZERS         ANALYZERS
            |               |               |
            v               v               v
      Architecture     Python / JS      FastAPI /
      Security         TypeScript       Express /
      Maintainability  Java / Go (plan) NestJS /
      Dependencies     PHP / C# (plan)  Spring (plan)
            |               |               |
            +---------------+---------------+
                            |
                            v
                   UNIFIED FINDINGS
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
           TERMINAL       JSON/SARIF     MARKDOWN
              |             |             |
              +-------------+-------------+
                            |
                            v
                 AI CODING TOOL / CI/CD (MCP Server)
```

---

## 🚀 Supported Ecosystems

| Language | Status | Analyzed Frameworks | Test Suite |
|---|---|---|---|
| **Python** | ✅ Supported | **FastAPI**, **Django**, **Flask** | 100% Automated |
| **JavaScript** | ✅ Supported | **Express**, **NestJS** | 100% Automated |
| **TypeScript** | ✅ Supported | **Express**, **NestJS** | 100% Automated |
| Java | 📋 Planned v1.1 | Spring Boot | Planned |
| Go | 📋 Planned v1.1 | Gin, Echo, Fiber | Planned |
| PHP | 📋 Planned v1.2 | Laravel, Symfony | Planned |
| C# | 📋 Planned v1.2 | ASP.NET Core | Planned |
| Rust | 📋 Planned v1.3 | Actix Web, Axum | Planned |

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/backend-guard/backend-auditor.git
cd backend-auditor

# Install with pip
pip install .

# Or install in editable development mode
pip install -e ".[dev]"
```

Both `backend-guard` and `backend-auditor` CLI executables are installed on your PATH.

---

## 🛠️ Quick Start & CLI Usage

### 1. Audit a backend project
```bash
# Audit the current project (terminal output)
backend-guard audit .

# Audit an external project
backend-guard audit /path/to/my-backend

# Generate a detailed Markdown report
backend-guard audit . --format markdown --output AUDIT.md

# Generate structured JSON for AI coding assistants
backend-guard audit . --format json --output audit.json

# Generate standard SARIF for GitHub Code Scanning
backend-guard audit . --format sarif --output results.sarif
```

### 2. Technology & Stack Detection
```bash
backend-guard detect .
```
Outputs detected languages, frameworks, manifests, and lines of code with confidence metrics.

### 3. Filter Findings
```bash
# Filter by minimum severity (critical, high, medium, low, info)
backend-guard audit . --severity high

# Filter by category
backend-guard audit . --category security

# Exclude specific directories
backend-guard audit . --exclude migrations,generated,legacy
```

### 4. Baseline Support for Legacy Repositories
Adopt Backend Guard on large existing codebases without breaking CI:
```bash
# Snapshot existing findings into a baseline file
backend-guard baseline generate . -o baseline.json

# Run audit against baseline (only new findings will be reported or fail the build)
backend-guard audit . --baseline baseline.json
```

### 5. Initialize Configuration
```bash
backend-guard init .
```
Creates a default `backend-auditor.toml` in your project root.

### 6. View All Supported Rules
```bash
backend-guard rules
backend-guard rules --category architecture
```

---

## 🤖 AI Coding Assistant & MCP Server Integration

Backend Guard features a built-in **Model Context Protocol (MCP)** server over stdio for seamless integration with Cursor, Claude Desktop, Antigravity, and other AI coding tools.

### Launching the MCP Server
```bash
backend-guard mcp
```

### Supported MCP Tool Operations
- `detect_backend_stack`: Inspects target codebase, detects languages and frameworks.
- `audit_backend`: Executes a full audit and returns unified findings in structured JSON.
- `get_finding_details`: Fetches full impact, evidence, and remediation advice for an issue.
- `get_rule_information`: Retrieves static rule metadata and best practice documentation.
- `generate_fix_suggestion`: Returns concrete code refactor snippets and fix examples.

### Example Cursor / Claude Desktop MCP Configuration (`claude_desktop_config.json`)
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

---

## ⚙️ Configuration (`backend-auditor.toml`)

Backend Guard works out of the box with zero configuration, but can be fully customized:

```toml
[general]
failure_threshold = "high"       # Exit code 1 on findings >= threshold (critical, high, medium, low)
confidence_threshold = "low"     # Minimum confidence level to report
# baseline = "baseline.json"

[rules]
# enable = ["ARCH-001", "SEC-001"] # If set, only these rules run
disable = ["LOG-002"]             # Exclude specific rules

[rules.severity]
# Override rule severities
"API-001" = "low"

[exclusions]
dirs = [
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "migrations",
    "tests/fixtures"
]
files = []
respect_gitignore = true

[complexity]
max_cyclomatic_complexity = 15
max_function_lines = 60
max_file_lines = 600

[tools]
# Run optional external tools with --with-tools flag
ruff = true
eslint = true
mypy = true
bandit = true
pytest = true
```

---

## 🚫 False-Positive Control & Suppressions

Backend Guard is designed to be trusted by engineers. You can suppress individual findings directly in source code:

### Python
```python
# Inline suppression
SECRET_KEY = "dummy-local-key"  # backend-auditor: ignore SEC-001 -- mock test key

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

---

## 🚦 Exit Codes

- `0`: Audit completed successfully; no blocking threshold exceeded.
- `1`: Audit completed, but blocking findings were detected (at or above configured `failure_threshold`).
- `2`: Invalid CLI arguments or configuration error.
- `3`: Audit incomplete because a required analysis stage crashed.

---

## 🛡️ Security & Read-Only Guarantee

Backend Guard is **strictly read-only**. It never writes to, modifies, or mutates the audited source code.

*Disclaimer: Backend Guard performs static architecture and pattern analysis. It cannot guarantee the absence of all vulnerabilities. Dynamic penetration testing and runtime verification remain essential.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
