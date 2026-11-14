# Changelog

All notable changes to **Backend Guard (Universal Backend Auditor)** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-14

### Added
- **Core Architecture & Engine**:
  - Language-independent core engine coordinating discovery, rules, suppression, baselines, and reports.
  - Project scanner with automatic technology detection (languages and frameworks).
  - Dependency graph builder with automated layer classification (`presentation`, `service`, `repository`, `domain`, `infrastructure`) and cycle detection.
  - Granular suppression system supporting inline `# backend-auditor: ignore <RULE_ID>`, block suppressions, and file-level exclusions.
  - Baseline generator and validator for incremental adoption in large existing codebases.

- **Universal Rules (13 domains)**:
  - Architecture: Direct presentation-to-infrastructure coupling (`ARCH-001`), circular dependency cycles (`ARCH-003`), cross-module duplication (`DUP-001`).
  - SOLID Principles: God class detection (`SOLID-001`), type-switching cascades (`SOLID-002`).
  - Security: Hardcoded secrets and API keys (`SEC-001`), SQL injection risk in string formatting (`SEC-002`), dangerous system command execution (`SEC-003`), insecure CORS wildcard configuration with credentials (`SEC-004`), path traversal risk (`SEC-005`).
  - Complexity: Cyclomatic complexity threshold (`CMPLX-001`), function line length (`CMPLX-002`), deep nesting / arrow antipattern (`CMPLX-003`).
  - Database: N+1 query patterns inside loops (`DB-001`), transactions missing explicit rollback in error handlers (`DB-002`).
  - Error Handling: Silent exception swallowing (`ERR-001`), overly broad exception catching (`ERR-002`), raw stack trace leakage to clients (`ERR-003`).
  - API Design: Missing pagination on collection endpoints (`API-001`), HTTP 200 OK returned with error payloads (`API-002`).
  - Testing: Missing automated test suites (`TEST-001`), vacuous test cases lacking assertions (`TEST-002`).
  - Production Readiness: Missing health check endpoints (`PROD-001`), production debug mode enabled (`CONF-002`), unstructured printing to stdout (`LOG-002`).
  - Dependency Management: Unpinned dependencies in production manifests (`DEP-002`).

- **Python Language & Framework Analyzers**:
  - Python AST analysis: Synchronous blocking calls in `async def` (`PY-ASYNC-001`), mutable default arguments (`PY-001`), unsafe deserialization via `pickle` or `yaml.load` (`PY-002`), wildcard imports (`PY-003`), missing type annotations (`PY-TYPE-001`).
  - FastAPI Analyzer: Direct raw SQL in route endpoints (`FASTAPI-001`), missing `response_model` on mutating routes (`FASTAPI-002`).

- **JavaScript / TypeScript & Framework Analyzers**:
  - Node.js AST analysis bridge: Synchronous blocking I/O calls (`JS-001`), unhandled promise rejections (`JS-002`), dynamic `eval()` execution (`JS-003`), excessive `any` types (`TS-001`).
  - Express.js Analyzer: Missing global 4-argument error middleware (`EXPRESS-001`), async route handlers without error handling (`EXPRESS-003`).
  - NestJS Analyzer: Service classes missing `@Injectable()` (`NEST-001`), direct database access inside controllers (`NEST-002`).

- **Reporting Formats**:
  - Terminal reporter with formatted ANSI cards and summaries.
  - Standard JSON reporter for machine integration.
  - Detailed GitHub Flavored Markdown report generator.
  - OASIS SARIF v2.1.0 output for GitHub Code Scanning.

- **Integrations**:
  - Built-in JSON-RPC 2.0 Model Context Protocol (MCP) server over stdio for AI coding assistants.
  - GitHub Actions workflow generator and workflow annotation output (`::error`, `::warning`).
  - External tool runner wrappers for Ruff, ESLint, mypy, Bandit, and pytest.

