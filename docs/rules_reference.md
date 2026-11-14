# Backend Guard Rules Reference

This document provides a comprehensive reference for all rules implemented in Backend Guard v1.0.0.

---

## 1. Architecture (`architecture`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `ARCH-001` | HIGH | HIGH | **Direct presentation to infrastructure coupling**: Route handlers directly importing database or infrastructure drivers without service/repository abstraction. |
| `ARCH-003` | HIGH | HIGH | **Circular module dependency cycle detected**: Recursive circular import loop detected between two or more modules. |
| `DUP-001` | LOW | MEDIUM | **Substantial code block duplication across modules**: Identical code blocks of 8+ lines duplicated across disparate backend files. |
| `FASTAPI-001` | HIGH | HIGH | **Direct raw SQL execution inside route endpoint**: FastAPI endpoint executes raw SQL queries directly instead of delegating to a repository. |
| `NEST-002` | HIGH | HIGH | **Direct database access inside NestJS controller**: Controller executes database calls directly rather than using an injected service. |

---

## 2. SOLID Principles (`solid`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `SOLID-001` | MEDIUM | MEDIUM | **Single Responsibility Principle: God class detected**: Class contains >15 methods and spans >250 lines, indicating multiple mixed responsibilities. |
| `SOLID-002` | LOW | MEDIUM | **Open/Closed Principle: Type-checking cascade detected**: Long ladder of `isinstance` / `typeof` checks instead of polymorphic dispatch or Strategy pattern. |

---

## 3. Security (`security`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `SEC-001` | CRITICAL | HIGH | **Hardcoded secret or credential detected**: API keys, JWT secrets, passwords, or cloud tokens hardcoded in source code. |
| `SEC-002` | CRITICAL | HIGH | **SQL injection risk from string formatting**: Database queries constructed via f-strings, `%` formatting, or string concatenation. |
| `SEC-003` | HIGH | HIGH | **Dangerous system command execution**: Unvalidated shell commands executed via `os.system` or `child_process.exec`. |
| `SEC-004` | HIGH | HIGH | **Insecure CORS wildcard origin with credentials**: CORS allows `*` origin with credentials enabled. |
| `SEC-005` | HIGH | MEDIUM | **Path traversal vulnerability risk**: Direct concatenation of user input into filesystem operations without canonical path validation. |
| `PY-002` | CRITICAL | HIGH | **Unsafe deserialization via pickle or raw yaml.load**: Untrusted payloads deserialized with `pickle.loads` or `yaml.load` without SafeLoader. |
| `JS-003` | CRITICAL | HIGH | **Dangerous dynamic code evaluation (eval / Function)**: Executing dynamic code strings via `eval()` or `new Function()`. |

---

## 4. Async & Concurrency (`async_concurrency`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `PY-ASYNC-001` | HIGH | HIGH | **Synchronous blocking call in async function**: Calls like `time.sleep()` or synchronous `requests.get()` inside `async def` freezing the event loop. |
| `JS-001` | HIGH | HIGH | **Synchronous blocking I/O call in Node.js server**: Calls like `fs.readFileSync` or `crypto.pbkdf2Sync` stalling concurrent requests on the event loop. |

---

## 5. Database Engineering (`database`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `DB-001` | HIGH | MEDIUM | **Potential N+1 query pattern detected in loop**: Database lookups or ORM queries executed inside loop iterations. |
| `DB-002` | HIGH | HIGH | **Database transaction without explicit rollback on error**: Transaction `commit()` in try block without matching `rollback()` in error handlers. |

---

## 6. Error Handling (`error_handling`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `ERR-001` | HIGH | HIGH | **Silent exception swallowing**: Catching exceptions with empty body or `pass`, hiding runtime failures completely. |
| `ERR-002` | MEDIUM | HIGH | **Overly broad exception catching without re-raise**: Catching bare `except:` or `BaseException` at low abstraction levels. |
| `ERR-003` | HIGH | MEDIUM | **Internal stack trace or raw error leaked to client**: Returning raw tracebacks or exception messages in HTTP API response payloads. |
| `JS-002` | HIGH | MEDIUM | **Unhandled promise rejection risk**: Promise `.then()` without `.catch()` handler. |
| `EXPRESS-001` | HIGH | HIGH | **Missing global error handling middleware in Express**: Express app lacking a 4-parameter `(err, req, res, next)` error handler. |
| `EXPRESS-003` | HIGH | HIGH | **Async Express route handler without error handling**: Async route handler without try/catch or async handler wrapper hanging client sockets on rejection. |

---

## 7. Complexity (`complexity`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `CMPLX-001` | MEDIUM | HIGH | **Excessive cyclomatic complexity in function**: McCabe cyclomatic complexity exceeds configured threshold (> 15). |
| `CMPLX-002` | LOW | HIGH | **Function exceeds maximum line threshold**: Function length exceeds configured threshold (> 60 lines). |
| `CMPLX-003` | MEDIUM | HIGH | **Deeply nested control structures (Arrow antipattern)**: Nested control blocks exceed maximum depth (> 4). |

---

## 8. API Design (`api_design`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `API-001` | MEDIUM | MEDIUM | **Missing pagination on collection endpoint**: List endpoint queries unbounded collections with `.all()` without limit/offset arguments. |
| `API-002` | LOW | HIGH | **HTTP 200 OK returned with error payload**: Returning 200 OK while sending an error or failure response payload. |
| `FASTAPI-002` | LOW | HIGH | **Missing response_model on route endpoint**: Mutating POST/PUT endpoint lacks `response_model`, bypassing schema filtering. |

---

## 9. Dependency Management (`dependency`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `DEP-002` | MEDIUM | HIGH | **Unpinned dependency version in production manifest**: Wildcard `*` or unconstrained dependencies in `requirements.txt` or `package.json`. |

---

## 10. Logging (`production_readiness` & `security`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `LOG-001` | HIGH | MEDIUM | **Sensitive credential or token logged**: Passwords, tokens, or authorization headers interpolated into log calls. |
| `LOG-002` | LOW | HIGH | **Raw stdout printing instead of structured logger**: Using `print()` or `console.log()` in backend services instead of structured logging. |

---

## 11. Configuration & Production Readiness (`production_readiness`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `CONF-002` | HIGH | HIGH | **Production debug mode hardcoded to True**: `debug=True` explicitly passed to framework or settings. |
| `PROD-001` | LOW | MEDIUM | **Missing health check or liveness endpoint**: Backend web service defines routes but has no `/health` or `/healthz` probe. |

---

## 12. Testing (`testing`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `TEST-001` | HIGH | HIGH | **Missing automated test suite**: Project contains backend source code but zero test files were detected. |
| `TEST-002` | MEDIUM | HIGH | **Vacuous test case with no assertions**: Test function contains zero `assert` statements. |

---

## 13. Language & Framework Specific (`patterns`, `typing`)

| Rule ID | Severity | Confidence | Title & Description |
|---|---|---|---|
| `PY-001` | HIGH | HIGH | **Dangerous mutable default argument**: Using mutable default values (`items=[]`) that leak state across calls. |
| `PY-003` | LOW | HIGH | **Wildcard import polluting namespace**: `from module import *` obscuring scope. |
| `PY-TYPE-001` | LOW | MEDIUM | **Missing type annotations on public function**: Public service or router function lacking parameter or return type annotations. |
| `TS-001` | LOW | HIGH | **Excessive use of unsafe 'any' type**: Explicit `any` annotations bypassing TypeScript type guarantees. |
| `NEST-001` | HIGH | HIGH | **Service class missing @Injectable() decorator**: NestJS service lacking `@Injectable()` decorator. |
