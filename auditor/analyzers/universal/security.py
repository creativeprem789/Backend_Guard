"""Security analysis: hardcoded secrets, SQL injection, command injection, CORS, and path traversal."""

from __future__ import annotations

import ast
import re
from typing import Dict, List

from auditor.core.analyzer import BaseAnalyzer
from auditor.core.context import AnalysisContext
from auditor.core.rule import BaseRule, RuleMetadata
from auditor.core.severity import Category, Confidence, Severity
from auditor.models import Finding
from auditor.registry import register_analyzer, register_rule

# High confidence secret patterns
SECRET_PATTERNS = [
    (
        re.compile(
            r"""(?:jwt[_-]?secret|secret[_-]?key|api[_-]?key|auth[_-]?token|password)\s*=\s*['"]([A-Za-z0-9_\-+=/]{16,})['"]""",
            re.IGNORECASE,
        ),
        "Generic hardcoded API secret / key",
    ),
    (
        re.compile(r"""['"](?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})['"]"""),
        "GitHub Personal Access Token",
    ),
    (re.compile(r"""['"]AKIA[0-9A-Z]{16}['"]"""), "AWS Access Key ID"),
    (re.compile(r"""['"]xox[baprs]-[0-9a-zA-Z]{10,48}['"]"""), "Slack API Token"),
]


@register_rule
class HardcodedSecretsRule(BaseRule):
    """Detects hardcoded secrets, tokens, and API credentials."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SEC-001",
                title="Hardcoded secret or credential detected",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                description="Sensitive credentials, secret keys, or authentication tokens are hardcoded directly in source code.",
                impact="Source code leaks expose credentials to all repository viewers, leading to unauthorized infrastructure access or data compromise.",
                recommendation="Store secrets in environment variables or a dedicated secrets manager (e.g., Vault, AWS Secrets Manager).",
                suggested_fix="Replace hardcoded string with os.environ.get('SECRET_KEY') or a configuration loader.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        for f in source_files:
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                clean = line.strip()
                if clean.startswith(("#", "//", "/*", "*")):
                    continue
                for pat, label in SECRET_PATTERNS:
                    if pat.search(line):
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=idx,
                                description=f"Potential {label} hardcoded in source code.",
                                evidence=re.sub(r"[a-zA-Z0-9]{8,}", "********", clean),
                            )
                        )
                        break
        return findings


@register_rule
class SqlInjectionRule(BaseRule):
    """Detects SQL queries built via string interpolation or concatenation."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SEC-002",
                title="SQL injection risk from string formatting",
                category=Category.SECURITY,
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                description="Database queries constructed using string concatenation, f-strings, or %-formatting are vulnerable to SQL injection.",
                impact="Attackers can bypass authentication, read unauthorized database records, or modify/drop entire tables.",
                recommendation="Use parameterized queries or ORM query builders with bind variables.",
                suggested_fix="Pass parameters as separate tuple/dict arguments: cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # Check Python files via AST
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            # Track variable names assigned to f-strings or binary ops in file
            vulnerable_vars: Dict[str, int] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    val = node.value
                    is_interpolated = False
                    if isinstance(val, ast.JoinedStr):
                        is_interpolated = True
                    elif isinstance(val, ast.BinOp) and isinstance(val.op, (ast.Add, ast.Mod)):
                        is_interpolated = True

                    if is_interpolated:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                vulnerable_vars[target.id] = node.lineno

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for .execute(...) or .raw(...) calls
                    func_name = ""
                    if isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    elif isinstance(node.func, ast.Name):
                        func_name = node.func.id

                    if func_name in ("execute", "raw", "executescript") and node.args:
                        first_arg = node.args[0]
                        # Check f-strings
                        if isinstance(first_arg, ast.JoinedStr):
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description="Database query constructed using Python f-string interpolation.",
                                    evidence="db.execute(f'... {variable} ...')",
                                )
                            )
                        # Check string concatenation or % formatting
                        elif isinstance(first_arg, ast.BinOp):
                            if isinstance(first_arg.op, (ast.Add, ast.Mod)):
                                rel_file = context.get_relative_path(py_file)
                                findings.append(
                                    self.create_finding(
                                        file=rel_file,
                                        line=node.lineno,
                                        description="Database query constructed using string concatenation or % formatting.",
                                        evidence="db.execute('SELECT ...' + var)",
                                    )
                                )
                        # Check variable pointing to interpolated query
                        elif isinstance(first_arg, ast.Name) and first_arg.id in vulnerable_vars:
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description=f"Database query '{first_arg.id}' was constructed via string interpolation/concatenation.",
                                    evidence=f"db.{func_name}({first_arg.id})",
                                )
                            )

        # Check JS/TS files for query string interpolation
        for f in context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        ):
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                if re.search(
                    r"""\.(?:query|execute)\s*\(\s*`\s*(?:SELECT|INSERT|UPDATE|DELETE).*\$\{""",
                    line,
                    re.IGNORECASE,
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Database query constructed via template literal interpolation.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_rule
class CommandInjectionRule(BaseRule):
    """Detects dangerous system command execution."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SEC-003",
                title="Dangerous system command execution",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="System shell commands executed with shell=True, os.system, or exec with dynamic user input.",
                impact="Remote code execution allowing attackers to take full control of host or container environment.",
                recommendation="Use subprocess.run() with a list of arguments and shell=False. Never pass raw user input into a shell.",
                suggested_fix="Use subprocess.run(['cmd', arg], shell=False, check=True)",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []

        # Python checks
        for py_file in context.get_files_for_language("python"):
            tree = context.get_python_ast(py_file)
            if not tree:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # os.system(cmd)
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                            rel_file = context.get_relative_path(py_file)
                            findings.append(
                                self.create_finding(
                                    file=rel_file,
                                    line=node.lineno,
                                    description="os.system() used for command execution; vulnerable to command injection.",
                                    evidence="os.system(...)",
                                )
                            )
                    # subprocess.call / Popen with shell=True
                    if isinstance(node.func, ast.Attribute) and node.func.attr in (
                        "call",
                        "Popen",
                        "run",
                        "check_output",
                    ):
                        for kw in node.keywords:
                            if (
                                kw.arg == "shell"
                                and isinstance(kw.value, ast.Constant)
                                and kw.value.value is True
                            ):
                                rel_file = context.get_relative_path(py_file)
                                findings.append(
                                    self.create_finding(
                                        file=rel_file,
                                        line=node.lineno,
                                        description=f"subprocess.{node.func.attr} called with shell=True.",
                                        evidence="shell=True",
                                    )
                                )

        # JS/TS checks
        for f in context.get_files_for_language("javascript") + context.get_files_for_language(
            "typescript"
        ):
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                if re.search(r"""\bchild_process\.exec\s*\(|execSync\s*\(""", line):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="child_process.exec/execSync invoked; invokes a system shell and risks command injection.",
                            evidence=line.strip(),
                        )
                    )
        return findings


@register_rule
class InsecureCorsRule(BaseRule):
    """Detects overly permissive CORS configuration."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SEC-004",
                title="Insecure CORS wildcard origin with credentials",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                description="CORS middleware allows wildcard origin '*' while permitting credentials or allowing arbitrary origins.",
                impact="Cross-origin attackers can make authenticated requests from malicious sites and extract user data.",
                recommendation="Specify explicit allowed origins rather than wildcard '*' or reflect arbitrary Request headers.",
                suggested_fix="Define an explicit whitelist of approved frontend domains for allow_origins.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        source_files = (
            context.get_files_for_language("python")
            + context.get_files_for_language("javascript")
            + context.get_files_for_language("typescript")
        )

        for f in source_files:
            lines = context.get_lines(f)
            rel_file = context.get_relative_path(f)
            for idx, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith(("#", "//", "/*", "*")):
                    continue
                clean_lower = stripped.lower()
                # Check Python CORSMiddleware
                if (
                    "allow_origins" in clean_lower
                    and ("['*']" in clean_lower or '["*"]' in clean_lower)
                    and "allow_credentials=true" in clean_lower
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Insecure CORS: wildcard origins combined with allow_credentials=True.",
                            evidence=stripped,
                        )
                    )
                # Check Express cors({ origin: '*', credentials: true })
                if (
                    "cors(" in clean_lower
                    and "origin" in clean_lower
                    and "*" in clean_lower
                    and "credentials" in clean_lower
                    and "true" in clean_lower
                ):
                    findings.append(
                        self.create_finding(
                            file=rel_file,
                            line=idx,
                            description="Insecure Express CORS: wildcard origin combined with credentials enabled.",
                            evidence=stripped,
                        )
                    )
        return findings


@register_rule
class PathTraversalRule(BaseRule):
    """Detects unvalidated user paths passed to filesystem calls."""

    def __init__(self) -> None:
        super().__init__(
            RuleMetadata(
                rule_id="SEC-005",
                title="Path traversal vulnerability risk",
                category=Category.SECURITY,
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                description="File operations access paths constructed with direct user input or unvalidated filename concatenation.",
                impact="Attackers can read sensitive system files (e.g. /etc/passwd or .env) or write files to arbitrary locations.",
                recommendation="Validate path using os.path.abspath and ensure it remains inside an allowed base directory.",
                suggested_fix="Verify that the canonical path starts with the allowed root directory.",
            )
        )

    def evaluate(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for py_file in context.get_files_for_language("python"):
            lines = context.get_lines(py_file)
            rel_file = context.get_relative_path(py_file)
            for idx, line in enumerate(lines, start=1):
                if re.search(
                    r"""send_file\s*\(\s*(?:request\.|req\.|f["']|.*(?:filename|path)\b)""", line
                ):
                    if "os.path.abspath" not in line and "safe_join" not in line:
                        findings.append(
                            self.create_finding(
                                file=rel_file,
                                line=idx,
                                description="send_file / file access using raw request parameters without path validation.",
                                evidence=line.strip(),
                            )
                        )
        return findings


@register_analyzer
class UniversalSecurityAnalyzer(BaseAnalyzer):
    name = "universal-security"
    description = (
        "Analyzes high-impact security vulnerabilities: secrets, SQLi, command execution, and CORS"
    )
    category = Category.SECURITY

    def get_rules(self) -> List[BaseRule]:
        return [
            HardcodedSecretsRule(),
            SqlInjectionRule(),
            CommandInjectionRule(),
            InsecureCorsRule(),
            PathTraversalRule(),
        ]

    def analyze(self, context: AnalysisContext) -> List[Finding]:
        findings: List[Finding] = []
        for rule in self.get_rules():
            if context.config.is_rule_enabled(rule.rule_id):
                findings.extend(rule.evaluate(context))
        return findings
