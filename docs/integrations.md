# Tool & AI Assistant Integrations

Backend Guard integrates seamlessly into developer workflows, CI/CD pipelines, and AI coding assistants.

---

## 1. AI Coding Assistants via Model Context Protocol (MCP)

Backend Guard provides a native **Model Context Protocol (MCP)** server over standard input/output. This enables AI assistants (Claude Desktop, Cursor, Antigravity, etc.) to inspect backend architecture, trigger audits, and fetch fix suggestions dynamically.

### Running MCP Server
```bash
backend-guard mcp
```

### Supported MCP Methods
- `detect_backend_stack`: Returns detected languages, frameworks, lines of code, and project manifests.
- `audit_backend`: Runs the full audit engine on the specified directory and returns structured findings.
- `get_finding_details`: Fetches full details for a finding.
- `get_rule_information`: Retrieves rule documentation and impact rationale.
- `generate_fix_suggestion`: Returns actionable code fix examples.

### Example Configuration for Claude Desktop / Cursor (`claude_desktop_config.json`)
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

## 2. GitHub Actions Integration

Backend Guard can emit native GitHub Actions annotations or standard SARIF v2.1.0 payloads for GitHub Code Scanning:

### Example `.github/workflows/audit.yml`
```yaml
name: Backend Architecture Audit

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Backend Guard
        run: pip install backend-auditor
      - name: Run Backend Guard Audit
        run: backend-guard audit . --format github --fail-on high
```

### SARIF Upload for GitHub Security Tab
```yaml
      - name: Generate SARIF
        run: backend-guard audit . --format sarif --output results.sarif
      - name: Upload SARIF report
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

---

## 3. External Tool Orchestration

When invoked with `--with-tools`, Backend Guard safely executes installed static analysis tools and incorporates their findings into the unified report:
- **Ruff**: Fast Python linting and code quality
- **ESLint**: JavaScript and TypeScript linting
- **mypy**: Python static type checking
- **Bandit**: Python security scanner
- **pytest**: Automated test discovery and health
