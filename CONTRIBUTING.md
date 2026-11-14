# Contributing to Backend Guard (Universal Backend Auditor)

Thank you for your interest in contributing to **Backend Guard**!

Backend Guard is designed to be a high-precision, production-grade static analysis and architecture auditor exclusively for backend codebases across multiple languages and frameworks.

---

## Architecture Overview

```text
Backend Codebase -> Discovery & Detection -> Engine -> Analyzers -> Reporting (Terminal/JSON/Markdown/SARIF)
                                                                 -> MCP Server (AI Assistants)
```

1. **Language-Independent Core**: Core engine (`auditor/engine.py`), dependency graph (`auditor/core/dependency_graph.py`), suppression engine (`auditor/suppressions.py`), and baseline engine (`auditor/baselines.py`) contain no framework-specific logic.
2. **Standard Finding Model**: Every rule emits standard `Finding` objects (`auditor/models.py`) with rule_id, title, category, severity, confidence, recommendation, and suggested fix.
3. **Pluggable Analyzers**: Analyzers subclass `BaseAnalyzer` and register rules via `@register_rule` and `@register_analyzer`.

---

## Adding a New Rule

1. Pick an appropriate category: `architecture`, `solid`, `patterns`, `database`, `api_design`, `security`, `error_handling`, `performance`, `testing`, `production_readiness`, `dependency`, `complexity`, `typing`, `async_concurrency`.
2. Implement your rule subclassing `BaseRule` (`auditor/core/rule.py`).
3. Define static metadata (`rule_id`, `title`, `severity`, `confidence`, `impact`, `recommendation`, `suggested_fix`).
4. Implement `evaluate(context: AnalysisContext) -> List[Finding]`.
5. Decorate with `@register_rule`.
6. Add unit tests covering positive (defective), negative (clean), and edge-case samples in `tests/`.

---

## Adding a New Language Analyzer

To add a new language (e.g. Go, Java, Rust):

1. Create a module directory under `auditor/analyzers/languages/<language>/`.
2. Implement a parser or AST extractor bridge (if using external runtime binaries, execute with subprocess timeouts and graceful fallback).
3. Populate the project `DependencyGraph` with module imports.
4. Implement language-specific rules in `rules.py`.
5. Register the analyzer class with `@register_analyzer`.
6. Register the file extensions in `auditor/discovery.py`.
7. Add automated tests in `tests/languages/<language>/`.

---

## Adding a New Framework Analyzer

1. Create a package under `auditor/analyzers/frameworks/<framework>/`.
2. Subclass `BaseAnalyzer` and specify `framework = "<framework_name>"`.
3. Framework rules will automatically only execute when that framework is detected in the project discovery phase.
4. Add tests and fixtures under `tests/frameworks/<framework>/`.

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/backend-guard/backend-auditor.git
cd backend-auditor

# Install in editable mode with development dependencies
pip install -e .[dev]

# Run tests
pytest tests -v

# Run Ruff linter
ruff check .

# Run Mypy type checker
mypy auditor
```

---

## Code Standards

- **Strictly Read-Only**: The auditor must never mutate audited codebases.
- **Low False-Positive Tolerance**: Do not report heuristic hints as confirmed critical bugs. Clearly differentiate `confidence=high` from `confidence=low`.
- **Actionable Guidance**: Every finding must include why it matters (`impact`), how to resolve it (`recommendation`), and an example fix (`suggested_fix`).
- **Suppression Support**: All rules must honor `# backend-auditor: ignore <RULE_ID>` and `// backend-guard: ignore <RULE_ID>`.
