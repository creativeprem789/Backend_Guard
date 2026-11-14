"""Command-line interface for Universal Backend Auditor (Backend Guard)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from auditor import __tool_name__, __version__
from auditor.baselines import Baseline
from auditor.config import Config
from auditor.core.severity import Category, Confidence, Severity
from auditor.discovery import ProjectScanner
from auditor.engine import AuditEngine
from auditor.integrations_external.github_actions import GitHubActionsAnnotation
from auditor.integrations_external.mcp_server import McpServer
from auditor.registry import RuleRegistry
from auditor.reporting.json_report import JsonReporter
from auditor.reporting.markdown_report import MarkdownReporter
from auditor.reporting.sarif_report import SarifReporter
from auditor.reporting.terminal import TerminalReporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="backend-guard",
        description="Universal Backend Codebase Auditor: static architecture, security, and quality analysis.",
    )
    parser.add_argument("--version", action="version", version=f"{__tool_name__} {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Auditor command")

    # Command: audit
    p_audit = subparsers.add_parser("audit", help="Audit a backend codebase")
    p_audit.add_argument(
        "path", nargs="?", default=".", help="Target project root directory (default: .)"
    )
    p_audit.add_argument(
        "--format",
        choices=["terminal", "json", "markdown", "sarif", "github"],
        default="terminal",
        help="Output format",
    )
    p_audit.add_argument("--output", "-o", help="Write report output to specified file")
    p_audit.add_argument(
        "--severity",
        "-s",
        help="Filter minimum finding severity (info, low, medium, high, critical)",
    )
    p_audit.add_argument("--confidence", "-c", help="Filter minimum confidence (low, medium, high)")
    p_audit.add_argument("--category", help="Filter findings by category")
    p_audit.add_argument("--exclude", help="Comma-separated directories to exclude")
    p_audit.add_argument(
        "--with-tools",
        action="store_true",
        help="Execute available external tools (ruff, eslint, mypy, bandit, pytest)",
    )
    p_audit.add_argument("--baseline", help="Path to baseline file to suppress legacy findings")
    p_audit.add_argument(
        "--fail-on", help="Severity threshold triggering non-zero exit code (default: high)"
    )
    p_audit.add_argument("--config", help="Path to custom backend-auditor.toml config file")

    # Command: detect
    p_detect = subparsers.add_parser(
        "detect", help="Detect backend languages, frameworks, and manifests"
    )
    p_detect.add_argument("path", nargs="?", default=".", help="Target directory (default: .)")

    # Command: rules
    p_rules = subparsers.add_parser("rules", help="List all supported backend audit rules")
    p_rules.add_argument("--category", help="Filter rules by category")
    p_rules.add_argument("--severity", help="Filter rules by severity")

    # Command: languages
    subparsers.add_parser("languages", help="Show supported language and framework matrix")

    # Command: baseline
    p_baseline = subparsers.add_parser("baseline", help="Manage audit baselines")
    base_sub = p_baseline.add_subparsers(dest="baseline_command")
    p_base_gen = base_sub.add_parser("generate", help="Generate a baseline from current findings")
    p_base_gen.add_argument("path", nargs="?", default=".", help="Target project directory")
    p_base_gen.add_argument(
        "--output", "-o", default="baseline.json", help="Output baseline file path"
    )

    # Command: init
    p_init = subparsers.add_parser(
        "init", help="Create a default backend-auditor.toml configuration"
    )
    p_init.add_argument("path", nargs="?", default=".", help="Target directory (default: .)")

    # Command: mcp
    subparsers.add_parser("mcp", help="Run Model Context Protocol (MCP) server over stdio")

    return parser


def cmd_audit(args: argparse.Namespace) -> int:
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        return 2

    # Load configuration
    cfg_file = Path(args.config).resolve() if args.config else None
    config = Config.load(target_path, cfg_file)

    # CLI Overrides
    if args.with_tools:
        config.with_tools = True
    if args.exclude:
        for d in args.exclude.split(","):
            if d.strip():
                config.exclude_dirs.add(d.strip())
    if args.baseline:
        config.baseline_file = Path(args.baseline).resolve()
    if args.confidence:
        config.confidence_threshold = Confidence.from_str(args.confidence)
    if args.fail_on:
        config.failure_threshold = Severity.from_str(args.fail_on)

    # Run audit
    engine = AuditEngine(target_path, config)
    result = engine.run()

    # Apply command-line filters
    if args.severity:
        min_sev = Severity.from_str(args.severity)
        result.findings = [f for f in result.findings if f.severity.is_at_least(min_sev)]
    if args.category:
        cat = Category.from_str(args.category)
        result.findings = [f for f in result.findings if f.category == cat]

    # Generate output
    output_str = ""
    fmt = args.format.lower()
    if fmt == "json":
        output_str = JsonReporter.generate(result)
    elif fmt == "markdown":
        output_str = MarkdownReporter.generate(result)
    elif fmt == "sarif":
        output_str = SarifReporter.generate(result)
    elif fmt == "github":
        GitHubActionsAnnotation.print_annotations(result)
        return 0
    else:  # terminal
        TerminalReporter.render(result)

    # Write output to file if requested
    if args.output and output_str:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_str, encoding="utf-8")
        sys.stdout.write(f"Report written to: {out_path}\n")
    elif output_str and fmt != "terminal":
        sys.stdout.write(output_str + "\n")

    # Check incomplete stage failure (code 3)
    if not result.is_complete and result.failed_analyzers:
        sys.stderr.write("Audit incomplete because one or more analyzer stages crashed.\n")
        return 3

    # Check blocking threshold (code 1)
    fail_threshold = config.failure_threshold
    has_blocking = any(f.severity.is_at_least(fail_threshold) for f in result.findings)
    if has_blocking:
        return 1

    return 0


def cmd_detect(args: argparse.Namespace) -> int:
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path '{target_path}' does not exist.\n")
        return 2

    config = Config.load(target_path)
    scanner = ProjectScanner(target_path, config)
    p = scanner.scan()

    sys.stdout.write(f"\nTechnology Detection for: {p.root_path}\n")
    sys.stdout.write("=" * 60 + "\n")
    sys.stdout.write("Languages:\n")
    if p.detected_languages:
        for k, v in p.detected_languages.items():
            sys.stdout.write(f"  • {v.name} (confidence: {v.confidence.value})\n")
            for ev in v.evidence:
                sys.stdout.write(f"      - {ev}\n")
    else:
        sys.stdout.write("  None detected\n")

    sys.stdout.write("\nFrameworks:\n")
    if p.detected_frameworks:
        for k, v in p.detected_frameworks.items():
            sys.stdout.write(f"  • {v.name} (confidence: {v.confidence.value})\n")
            for ev in v.evidence:
                sys.stdout.write(f"      - {ev}\n")
    else:
        sys.stdout.write("  None detected\n")

    sys.stdout.write(f"\nFiles scanned: {len(p.files)} | Total lines: {p.total_lines:,}\n\n")
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    rules = RuleRegistry.all_rules()
    if args.category:
        cat = Category.from_str(args.category)
        rules = [r for r in rules if r.category == cat]
    if args.severity:
        sev = Severity.from_str(args.severity)
        rules = [r for r in rules if r.severity.is_at_least(sev)]

    sys.stdout.write(f"\nSupported Audit Rules ({len(rules)} total):\n")
    sys.stdout.write("=" * 76 + "\n")
    for r in sorted(rules, key=lambda x: (x.category.value, x.rule_id)):
        sys.stdout.write(f"[{r.severity.value.upper():8}] {r.rule_id:14} {r.title}\n")
        sys.stdout.write(f"           Category: {r.category.value}\n")
        if r.metadata.language or r.metadata.framework:
            sys.stdout.write(
                f"           Scope: language={r.metadata.language or '*'}, framework={r.metadata.framework or '*'}\n"
            )
        sys.stdout.write(f"           Description: {r.metadata.description}\n\n")
    return 0


def cmd_languages(args: argparse.Namespace) -> int:
    sys.stdout.write("""
Backend Guard Supported Language & Framework Matrix:
============================================================================
Language       Status      Tested Frameworks
----------------------------------------------------------------------------
Python         Supported   FastAPI, Django, Flask
JavaScript     Supported   Express, NestJS
TypeScript     Supported   Express, NestJS
Java           Planned     Spring Boot (planned for v1.1)
Go             Planned     Gin, Echo, Fiber (planned for v1.1)
PHP            Planned     Laravel, Symfony (planned for v1.2)
C#             Planned     ASP.NET Core (planned for v1.2)
Rust           Planned     Actix Web, Axum (planned for v1.3)
============================================================================
""")
    return 0


def cmd_baseline(args: argparse.Namespace) -> int:
    if args.baseline_command == "generate":
        target_path = Path(args.path).resolve()
        config = Config.load(target_path)
        engine = AuditEngine(target_path, config)
        result = engine.run()
        out_file = Path(args.output).resolve()
        Baseline.save(result.findings, out_file)
        sys.stdout.write(f"Baseline saved to '{out_file}' with {len(result.findings)} findings.\n")
        return 0
    sys.stderr.write("Invalid baseline command. Use 'baseline generate'.\n")
    return 2


def cmd_init(args: argparse.Namespace) -> int:
    target_path = Path(args.path).resolve()
    target_file = target_path / "backend-auditor.toml"
    if target_file.exists():
        sys.stderr.write(f"Configuration file already exists: {target_file}\n")
        return 1

    sample_config = """# Backend Guard Configuration File
# Documentation: https://github.com/backend-guard/backend-auditor

[general]
failure_threshold = "high"       # Exit code 1 on findings >= this severity
confidence_threshold = "low"     # Minimum confidence level to report
# baseline = "baseline.json"

[rules]
# enable = ["ARCH-001", "SEC-001"]
disable = []

[rules.severity]
# Override default severities
# "API-001" = "low"

[exclusions]
dirs = [
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "migrations"
]
files = []
respect_gitignore = true

[complexity]
max_cyclomatic_complexity = 15
max_function_lines = 60
max_file_lines = 600

[tools]
ruff = true
eslint = true
mypy = true
bandit = true
pytest = true
"""
    target_file.write_text(sample_config, encoding="utf-8")
    sys.stdout.write(f"Initialized configuration at: {target_file}\n")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "audit":
        return cmd_audit(args)
    elif args.command == "detect":
        return cmd_detect(args)
    elif args.command == "rules":
        return cmd_rules(args)
    elif args.command == "languages":
        return cmd_languages(args)
    elif args.command == "baseline":
        return cmd_baseline(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "mcp":
        McpServer().run_stdio()
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
