# Managing False Positives & Baselines

A reliable auditor must earn developer trust. Backend Guard offers four primary mechanisms to control false positives without compromising codebase security:

---

## 1. Inline Code Suppressions

Suppress individual findings using inline or leading comments:

### Python
```python
# Inline suppression
DUMMY_KEY = "test_key_123456789012"  # backend-auditor: ignore SEC-001 -- mock test fixture


# Suppression on preceding line (applies to next line)
# backend-auditor: ignore PY-001
def add_item(item, items=[]):
    pass
```

### JavaScript & TypeScript
```javascript
// Inline suppression
const data = fs.readFileSync('config.json'); // backend-guard: ignore JS-001 -- sync startup config only
```

---

## 2. Block & File Suppressions

### Block Suppression
```python
# backend-auditor: ignore-block ARCH-001
from app.infra import raw_db

raw_db.ping()
# backend-auditor: end-ignore-block
```

### File-Level Suppression
To exclude an entire file from a specific rule or all rules:
```python
# backend-auditor: ignore-file
```
Or for a specific rule:
```python
# backend-auditor: ignore-file ARCH-001, SEC-001
```

---

## 3. Baseline Snapshots for Legacy Codebases

When introducing Backend Guard to an existing production codebase, legacy warnings can overwhelm developers. Use a baseline file to suppress existing findings while catching any new regressions:

```bash
# 1. Snapshot all existing findings into baseline.json
backend-guard baseline generate . -o baseline.json

# 2. Run future audits against the baseline
backend-guard audit . --baseline baseline.json
```
Findings matching an entry in `baseline.json` are excluded from the exit code failure threshold.

---

## 4. Configuration Disables & Severity Overrides

In `backend-auditor.toml`:
```toml
[rules]
disable = ["LOG-002"]  # Disable rule globally

[rules.severity]
"API-001" = "low"     # Demote rule so it never fails CI
```
