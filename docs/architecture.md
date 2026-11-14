# Architecture of Backend Guard

Backend Guard is engineered around the principle of **language-independent core orchestration** paired with **specialized language and framework analyzers**.

```text
+-------------------------------------------------------------+
|                     Project Scanner                         |
|   - File discovery respecting .gitignore & exclusions       |
|   - Language heuristics (Python, JS, TS, Java, Go, etc.)    |
|   - Framework detection (FastAPI, Express, NestJS, etc.)    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                    Analysis Context                         |
|   - File content & line caching                             |
|   - AST caches (Python standard AST, Node.js AST bridge)    |
|   - Cross-module DependencyGraph & Layer Classifications    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Audit Engine                            |
|   - Inline & file-level suppression indexing                |
|   - Universal analyzers (Architecture, SOLID, Security, DB) |
|   - Language analyzers (Python, JavaScript, TypeScript)     |
|   - Framework analyzers (FastAPI, Express, NestJS)          |
|   - Optional external tool integrations (Ruff, ESLint, etc.)|
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                 Unified Findings Pipeline                   |
|   - Confidence and severity filtering                       |
|   - Baseline snapshot exclusion                             |
|   - Deduplication & deterministic sorting                   |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                    Reporting Engine                         |
|   - Terminal (ANSI cards and tables)                        |
|   - Machine JSON                                            |
|   - GitHub-Flavored Markdown                                |
|   - OASIS SARIF v2.1.0 for GitHub Code Scanning             |
|   - JSON-RPC 2.0 MCP Server for AI coding agents            |
+-------------------------------------------------------------+
```

## Layer Boundary Analysis

The `DependencyGraph` automatically classifies source modules into architectural layers based on path tokens:
- **Presentation Layer**: `routers`, `controllers`, `endpoints`, `handlers`, `views`
- **Service Layer**: `services`, `usecases`, `business`
- **Repository Layer**: `repositories`, `dao`, `queries`
- **Domain Layer**: `models`, `entities`, `schemas`, `domain`
- **Infrastructure Layer**: `infra`, `database`, `db`, `adapters`, `clients`

It detects:
1. **Direct Presentation to Infrastructure Coupling (`ARCH-001`)**: Route handlers that import raw database connections or infrastructure drivers directly, bypassing domain abstraction.
2. **Circular Dependencies (`ARCH-003`)**: Direct or multi-hop recursive import cycles across modules.
3. **Domain Layer Leaks**: Domain entities importing outwards to infrastructure or delivery mechanisms.
