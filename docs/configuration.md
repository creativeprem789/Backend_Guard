# Backend Guard Configuration Guide

Backend Guard can be configured via a project-level file named `backend-auditor.toml` or `backend-guard.toml`.

To create a starting configuration:
```bash
backend-guard init .
```

---

## Configuration Reference

```toml
[general]
# Non-zero exit code (exit 1) if findings at or above this severity are detected
# Options: "critical", "high", "medium", "low", "info"
failure_threshold = "high"

# Minimum confidence required for a finding to be reported
# Options: "high", "medium", "low"
confidence_threshold = "low"

# Path to existing baseline file (relative to project root)
# baseline = "baseline.json"

[rules]
# Explicitly enable only a specific subset of rules (uncomment to activate whitelist)
# enable = ["ARCH-001", "SEC-001", "DB-001"]

# Disable specific rules completely
disable = [
    "LOG-002",  # Allow print() statements in this project
    "DUP-001"   # Disable code duplication scanner
]

[rules.severity]
# Override the default severity of individual rules
"API-001" = "low"
"CMPLX-001" = "low"

[exclusions]
# Directories to exclude from analysis
dirs = [
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "migrations",
    "docs",
    "generated"
]

# File names to exclude
files = [
    "package-lock.json",
    "poetry.lock"
]

# Whether to parse and respect rules in .gitignore
respect_gitignore = true

[complexity]
# Cyclomatic complexity threshold (McCabe metric)
max_cyclomatic_complexity = 15

# Maximum lines allowed per function definition
max_function_lines = 60

# Maximum lines allowed per source file
max_file_lines = 600

# Maximum control flow nesting depth before flagging arrow antipattern
max_nested_blocks = 4

[tools]
# External tools executed when running with --with-tools
ruff = true
eslint = true
mypy = true
bandit = true
pytest = true
```
