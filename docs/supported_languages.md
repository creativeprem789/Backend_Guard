# Supported Languages & Frameworks

Backend Guard is architected to scale across all backend technologies.

---

## Language Support Matrix

| Language | Status | Detected Manifests & Extensions | Included Analyzers |
|---|---|---|---|
| **Python** | ✅ Supported | `*.py`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `setup.py` | AST analysis, async blocking checks, type checks, import graph, mutable defaults, deserialization |
| **JavaScript** | ✅ Supported | `*.js`, `*.mjs`, `*.cjs`, `package.json` | Node.js AST parser, sync I/O in server, unhandled promises, eval safety, import graph |
| **TypeScript** | ✅ Supported | `*.ts`, `*.tsx`, `tsconfig.json` | Type checking, unsafe `any` detection, import graph, promise hygiene |
| **Java** | 📋 Planned v1.1 | `pom.xml`, `build.gradle`, `*.java` | Spring Boot DI, JPA N+1, exception handling |
| **Go** | 📋 Planned v1.1 | `go.mod`, `*.go` | Goroutine leak detection, Gin/Echo route design |
| **PHP** | 📋 Planned v1.2 | `composer.json`, `*.php` | Laravel Eloquent N+1, Symfony container |
| **C#** | 📋 Planned v1.2 | `*.csproj`, `*.sln`, `*.cs` | ASP.NET Core middleware, Entity Framework |
| **Rust** | 📋 Planned v1.3 | `Cargo.toml`, `*.rs` | Actix Web / Axum async safety, unwrap() in endpoints |

---

## Framework Support Matrix

### FastAPI (Python)
- Detection: `fastapi` in requirements/pyproject or `from fastapi import ...`
- Analyzers: Route boundary checks, direct raw SQL detection, response model validation, background task safety.

### Express.js (JavaScript / TypeScript)
- Detection: `"express"` in `package.json` or `require('express')` / `import express`
- Analyzers: Centralized 4-argument error middleware checks, async route error handling (connection hang prevention), middleware ordering.

### NestJS (TypeScript)
- Detection: `"@nestjs/core"` in `package.json` or `nest-cli.json`
- Analyzers: Service `@Injectable()` decoration, controller database isolation.

### Django (Python)
- Detection: `manage.py`, `settings.py`, or `django` in dependencies.
- Compatible with all universal architecture, database, security, and Python analyzers.

### Flask (Python)
- Detection: `Flask(__name__)` or `flask` in requirements.
- Compatible with all universal architecture, database, security, and Python analyzers.
