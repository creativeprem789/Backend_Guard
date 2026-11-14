# 🛡️ Backend Guard Audit Report: python_fastapi

> Audited on `2026-11-14T07:37:32.837353+00:00` in `0.03` seconds.

## 📊 Executive Summary

| Metric | Value |
| --- | --- |
| **Target Codebase** | `C:\Users\PREM\Desktop\BackendGaurd\backend-auditor\tests\fixtures\bad_projects\python_fastapi` |
| **Total Files** | 2 |
| **Total Lines of Code** | 47 |
| **Detected Languages** | Python |
| **Detected Frameworks** | FastAPI |
| **Total Findings** | **11** |
| **Audit Status** | ✅ Complete |

### Findings by Severity

- 🔴 **Critical**: 2
- 🟠 **High**: 5
- 🟡 **Medium**: 3
- 🔵 **Low**: 1
- ⚪ **Info**: 0

## 🔍 Findings Summary Table

| # | Severity | Rule ID | Title | Location |
|---|---|---|---|---|
| 1 | 🔴 Critical | `SEC-001` | Hardcoded secret or credential detected | `app/main.py:6` |
| 2 | 🔴 Critical | `SEC-002` | SQL injection risk from string formatting | `app/main.py:37` |
| 3 | 🟠 High | `CONF-002` | Production debug mode hardcoded to True | `app/main.py:9` |
| 4 | 🟠 High | `PY-ASYNC-001` | Synchronous blocking call in async function | `app/main.py:33` |
| 5 | 🟠 High | `FASTAPI-001` | Direct raw SQL execution inside route endpoint | `app/main.py:37` |
| 6 | 🟠 High | `ERR-001` | Silent exception swallowing | `app/main.py:43` |
| 7 | 🟠 High | `DB-001` | Potential N+1 query pattern detected in loop | `app/main.py:42` |
| 8 | 🟡 Medium | `DEP-002` | Unpinned dependency version in production manifest | `requirements.txt:1` |
| 9 | 🟡 Medium | `DEP-002` | Unpinned dependency version in production manifest | `requirements.txt:2` |
| 10 | 🟡 Medium | `DEP-002` | Unpinned dependency version in production manifest | `requirements.txt:3` |
| 11 | 🔵 Low | `PROD-001` | Missing health check or liveness endpoint | `.:1` |

## 🛠️ Detailed Findings and Actionable Fixes

### 1. [CRITICAL] SEC-001: Hardcoded secret or credential detected
- **File**: `app/main.py` (Line 6)
- **Category**: `security`
- **Confidence**: `high`

**Description**:
Potential Generic hardcoded API secret / key hardcoded in source code.

**Evidence**:
```
JWT_SECRET = "********"
```

**Architectural / Runtime Impact**:
Source code leaks expose credentials to all repository viewers, leading to unauthorized infrastructure access or data compromise.

**Recommendation**:
Store secrets in environment variables or a dedicated secrets manager (e.g., Vault, AWS Secrets Manager).

**Suggested Fix / Example**:
```
Replace hardcoded string with os.environ.get('SECRET_KEY') or a configuration loader.
```

---

### 2. [CRITICAL] SEC-002: SQL injection risk from string formatting
- **File**: `app/main.py` (Line 37)
- **Category**: `security`
- **Confidence**: `high`

**Description**:
Database query 'query' was constructed via string interpolation/concatenation.

**Evidence**:
```
db.execute(query)
```

**Architectural / Runtime Impact**:
Attackers can bypass authentication, read unauthorized database records, or modify/drop entire tables.

**Recommendation**:
Use parameterized queries or ORM query builders with bind variables.

**Suggested Fix / Example**:
```
Pass parameters as separate tuple/dict arguments: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
```

---

### 3. [HIGH] CONF-002: Production debug mode hardcoded to True
- **File**: `app/main.py` (Line 9)
- **Category**: `production_readiness`
- **Confidence**: `high`

**Description**:
debug=True explicitly passed to framework call.

**Evidence**:
```
debug=True
```

**Architectural / Runtime Impact**:
Debug mode in production exposes interactive web shells, stack traces, and detailed system internals to external users.

**Recommendation**:
Read debug configuration exclusively from environment variables with a default of False in production.

**Suggested Fix / Example**:
```
debug = os.getenv('DEBUG', 'false').lower() == 'true'
```

---

### 4. [HIGH] PY-ASYNC-001: Synchronous blocking call in async function
- **File**: `app/main.py` (Line 33)
- **Category**: `async_concurrency`
- **Confidence**: `high`

**Description**:
Blocking call 'time.sleep()' invoked inside async function 'get_user'. Use asyncio.sleep() instead.

**Evidence**:
```
Call to time.sleep() at line 33 inside async def get_user
```

**Architectural / Runtime Impact**:
Completely blocks the single-threaded asyncio event loop, halting all concurrent requests and destroying backend throughput.

**Recommendation**:
Replace blocking synchronous calls with their non-blocking asynchronous equivalents.

**Suggested Fix / Example**:
```
Replace with await asyncio.sleep() or an async HTTP client like httpx.
```

---

### 5. [HIGH] FASTAPI-001: Direct raw SQL execution inside route endpoint
- **File**: `app/main.py` (Line 37)
- **Category**: `architecture`
- **Confidence**: `high`

**Description**:
Raw SQL execution inside route 'get_user'.

**Evidence**:
```
db.execute(...) in @router endpoint
```

**Architectural / Runtime Impact**:
Violates separation of concerns, mixes HTTP transport with database schemas, and makes unit testing endpoints difficult.

**Recommendation**:
Move database queries into a dedicated repository or service class injected via Depends().

**Suggested Fix / Example**:
```
Create a UserRepository and inject it into the route handler via Depends(get_user_repo).
```

---

### 6. [HIGH] ERR-001: Silent exception swallowing
- **File**: `app/main.py` (Line 43)
- **Category**: `error_handling`
- **Confidence**: `high`

**Description**:
Exception caught and swallowed silently with 'pass'.

**Evidence**:
```
except ...: pass
```

**Architectural / Runtime Impact**:
Critical bugs, database corruptions, and network timeouts are hidden, making production debugging almost impossible.

**Recommendation**:
Always log the exception with stack trace or re-raise it.

**Suggested Fix / Example**:
```
Log the exception with logger.exception('Context description') or re-raise.
```

---

### 7. [HIGH] DB-001: Potential N+1 query pattern detected in loop
- **File**: `app/main.py` (Line 42)
- **Category**: `database`
- **Confidence**: `medium`

**Description**:
Database query 'db.get()' executed inside loop iteration.

**Evidence**:
```
Loop query at line 42
```

**Architectural / Runtime Impact**:
Drastically multiplies database latency and round-trips; an endpoint returning 100 items executes 101 queries.

**Recommendation**:
Use eager loading (e.g., joinedload, selectinload) or fetch records in a single batched IN query.

**Suggested Fix / Example**:
```
Batch query IDs using .filter(Model.id.in_(ids)) outside the loop or use eager loading.
```

---

### 8. [MEDIUM] DEP-002: Unpinned dependency version in production manifest
- **File**: `requirements.txt` (Line 1)
- **Category**: `dependency`
- **Confidence**: `high`

**Description**:
Dependency 'fastapi' is completely unpinned without version constraints.

**Evidence**:
```
fastapi
```

**Architectural / Runtime Impact**:
Builds are non-deterministic; upstream minor or major breaking updates can cause production outages without notice.

**Recommendation**:
Pin dependencies to specific or compatible version ranges (e.g., package==1.2.3 or package~=1.2.0).

**Suggested Fix / Example**:
```
Specify exact or compatible version specifiers in the dependency manifest.
```

---

### 9. [MEDIUM] DEP-002: Unpinned dependency version in production manifest
- **File**: `requirements.txt` (Line 2)
- **Category**: `dependency`
- **Confidence**: `high`

**Description**:
Dependency 'uvicorn' is completely unpinned without version constraints.

**Evidence**:
```
uvicorn
```

**Architectural / Runtime Impact**:
Builds are non-deterministic; upstream minor or major breaking updates can cause production outages without notice.

**Recommendation**:
Pin dependencies to specific or compatible version ranges (e.g., package==1.2.3 or package~=1.2.0).

**Suggested Fix / Example**:
```
Specify exact or compatible version specifiers in the dependency manifest.
```

---

### 10. [MEDIUM] DEP-002: Unpinned dependency version in production manifest
- **File**: `requirements.txt` (Line 3)
- **Category**: `dependency`
- **Confidence**: `high`

**Description**:
Dependency 'sqlalchemy==*' is completely unpinned without version constraints.

**Evidence**:
```
sqlalchemy==*
```

**Architectural / Runtime Impact**:
Builds are non-deterministic; upstream minor or major breaking updates can cause production outages without notice.

**Recommendation**:
Pin dependencies to specific or compatible version ranges (e.g., package==1.2.3 or package~=1.2.0).

**Suggested Fix / Example**:
```
Specify exact or compatible version specifiers in the dependency manifest.
```

---

### 11. [LOW] PROD-001: Missing health check or liveness endpoint
- **File**: `.` (Line 1)
- **Category**: `production_readiness`
- **Confidence**: `medium`

**Description**:
No standard health probe endpoint (/health or /healthz) discovered in backend API.

**Evidence**:
```
No health route found across project files
```

**Architectural / Runtime Impact**:
Container orchestrators (Kubernetes, AWS ECS) and load balancers cannot monitor container liveness or readiness.

**Recommendation**:
Expose a lightweight GET /health or /healthz route that checks database connectivity and returns 200 OK.

**Suggested Fix / Example**:
```
Add @app.get('/health') returning {'status': 'healthy'}.
```

---

## ℹ️ Analysis Scope and Limitations

- Static analysis evaluates code structure, patterns, and known defect signatures.
- Dynamic runtime behavior, infrastructure configurations, and cloud deployment states must be verified independently.
- False positives can be managed using inline `# backend-auditor: ignore <RULE_ID>` comments or baseline files.
