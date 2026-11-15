"""Project discovery, file scanning, and technology detection."""

from __future__ import annotations

import fnmatch
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from auditor.config import Config
from auditor.core.severity import Confidence
from auditor.models import ProjectInfo, TechnologyDetection

logger = logging.getLogger(__name__)

LANGUAGE_EXTENSIONS: Dict[str, Set[str]] = {
    "python": {".py", ".pyw"},
    "javascript": {".js", ".mjs", ".cjs", ".jsx"},
    "typescript": {".ts", ".tsx"},
    "java": {".java"},
    "go": {".go"},
    "php": {".php"},
    "csharp": {".cs"},
    "rust": {".rs"},
    "sql": {".sql"},
}


class ProjectScanner:
    """Scans filesystem to discover files and classify technologies."""

    def __init__(self, root_path: Path, config: Config) -> None:
        self.root_path = root_path.resolve()
        self.config = config
        self.gitignore_patterns: List[str] = self._load_gitignore()

    def _safe_read_text(self, path: Path, max_chars: Optional[int] = None) -> str:
        """Safely read text file with fallback, logging any access errors."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read(max_chars) if max_chars is not None else f.read()
        except (OSError, UnicodeDecodeError) as exc:
            logger.debug("Could not read %s: %s", path, exc)
            return ""

    def _load_gitignore(self) -> List[str]:
        if not self.config.respect_gitignore:
            return []
        gi = self.root_path / ".gitignore"
        patterns: List[str] = []
        if gi.is_file():
            content = self._safe_read_text(gi)
            for line in content.splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    patterns.append(stripped)
        return patterns

    def is_ignored(self, path: Path) -> bool:
        """Check if path is in exclude dirs, exclude files, or gitignore."""
        # Check against exclude_dirs relative to project root
        try:
            rel_parts = path.resolve().relative_to(self.root_path).parts
        except ValueError:
            rel_parts = path.parts

        for part in rel_parts:
            if part in self.config.exclude_dirs:
                return True

        if path.is_file() and path.name in self.config.exclude_files:
            return True

        # Check gitignore
        if self.gitignore_patterns:
            try:
                rel = str(path.relative_to(self.root_path)).replace("\\", "/")
                for pattern in self.gitignore_patterns:
                    clean_pattern = pattern.rstrip("/")
                    if fnmatch.fnmatch(rel, clean_pattern) or fnmatch.fnmatch(
                        path.name, clean_pattern
                    ):
                        return True
                    if rel == clean_pattern or rel.startswith(clean_pattern + "/"):
                        return True
                    if fnmatch.fnmatch(rel, clean_pattern + "/*"):
                        return True
            except ValueError:
                return False

        return False

    def scan(self) -> ProjectInfo:
        """Scan project directory and discover files, languages, and frameworks."""
        files: List[Path] = []
        files_by_lang: Dict[str, List[Path]] = {}
        total_lines = 0

        # Discover all eligible files
        for item in self.root_path.rglob("*"):
            try:
                if not item.is_file():
                    continue
                if self.is_ignored(item):
                    continue
            except (OSError, PermissionError):
                continue

            files.append(item)
            ext = item.suffix.lower()

            for lang, exts in LANGUAGE_EXTENSIONS.items():
                if ext in exts:
                    files_by_lang.setdefault(lang, []).append(item)
                    break

            # Count lines for source files
            if ext in {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".php", ".cs", ".rs"}:
                try:
                    with open(item, "rb") as f:
                        total_lines += sum(1 for _ in f)
                except (OSError, PermissionError) as exc:
                    logger.debug("Failed counting lines in %s: %s", item, exc)

        # Technology detection
        languages = self._detect_languages(files_by_lang, files)
        frameworks = self._detect_frameworks(files, languages)

        project_name = self.root_path.name
        pkg_json = self.root_path / "package.json"
        try:
            if pkg_json.is_file():
                with open(pkg_json, "r", encoding="utf-8") as f:
                    pj = json.load(f)
                    if "name" in pj and isinstance(pj["name"], str):
                        project_name = pj["name"]
        except (json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed reading package.json for project name: %s", exc)

        return ProjectInfo(
            root_path=self.root_path,
            name=project_name,
            detected_languages=languages,
            detected_frameworks=frameworks,
            files=files,
            files_by_language=files_by_lang,
            total_lines=total_lines,
        )

    def _detect_languages(
        self, files_by_lang: Dict[str, List[Path]], all_files: List[Path]
    ) -> Dict[str, TechnologyDetection]:
        detected: Dict[str, TechnologyDetection] = {}

        # Python
        py_files = files_by_lang.get("python", [])
        py_manifests = [
            f
            for f in all_files
            if f.name in ("pyproject.toml", "requirements.txt", "Pipfile", "setup.py")
        ]
        if py_files or py_manifests:
            evidence = [f"{len(py_files)} Python source files"]
            for m in py_manifests[:3]:
                evidence.append(f"manifest: {m.name}")
            detected["python"] = TechnologyDetection(
                name="Python",
                kind="language",
                confidence=Confidence.HIGH if py_files else Confidence.MEDIUM,
                evidence=evidence,
            )

        # TypeScript
        ts_files = files_by_lang.get("typescript", [])
        ts_configs = [f for f in all_files if f.name.startswith("tsconfig")]
        if ts_files or ts_configs:
            evidence = [f"{len(ts_files)} TypeScript source files"]
            for tc in ts_configs:
                evidence.append(f"config: {tc.name}")
            detected["typescript"] = TechnologyDetection(
                name="TypeScript",
                kind="language",
                confidence=Confidence.HIGH if ts_files else Confidence.MEDIUM,
                evidence=evidence,
            )

        # JavaScript
        js_files = files_by_lang.get("javascript", [])
        pkg_files = [f for f in all_files if f.name == "package.json"]
        if js_files or (pkg_files and "typescript" not in detected):
            evidence = [f"{len(js_files)} JavaScript source files"]
            if pkg_files:
                evidence.append("package.json present")
            detected["javascript"] = TechnologyDetection(
                name="JavaScript",
                kind="language",
                confidence=Confidence.HIGH if js_files else Confidence.MEDIUM,
                evidence=evidence,
            )

        # Java
        java_files = files_by_lang.get("java", [])
        java_manifests = [
            f for f in all_files if f.name in ("pom.xml", "build.gradle", "build.gradle.kts")
        ]
        if java_files or java_manifests:
            detected["java"] = TechnologyDetection(
                name="Java",
                kind="language",
                confidence=Confidence.HIGH if java_files else Confidence.MEDIUM,
                evidence=[f"{len(java_files)} Java source files"]
                + [f.name for f in java_manifests],
            )

        # Go
        go_files = files_by_lang.get("go", [])
        go_mods = [f for f in all_files if f.name == "go.mod"]
        if go_files or go_mods:
            detected["go"] = TechnologyDetection(
                name="Go",
                kind="language",
                confidence=Confidence.HIGH if go_files else Confidence.MEDIUM,
                evidence=[f"{len(go_files)} Go source files"] + [f.name for f in go_mods],
            )

        # PHP
        php_files = files_by_lang.get("php", [])
        php_manifests = [f for f in all_files if f.name == "composer.json"]
        if php_files or php_manifests:
            detected["php"] = TechnologyDetection(
                name="PHP",
                kind="language",
                confidence=Confidence.HIGH if php_files else Confidence.MEDIUM,
                evidence=[f"{len(php_files)} PHP source files"],
            )

        # C#
        cs_files = files_by_lang.get("csharp", [])
        cs_manifests = [f for f in all_files if f.suffix in (".csproj", ".sln")]
        if cs_files or cs_manifests:
            detected["csharp"] = TechnologyDetection(
                name="C#",
                kind="language",
                confidence=Confidence.HIGH if cs_files else Confidence.MEDIUM,
                evidence=[f"{len(cs_files)} C# source files"],
            )

        # Rust
        rs_files = files_by_lang.get("rust", [])
        cargo_files = [f for f in all_files if f.name == "Cargo.toml"]
        if rs_files or cargo_files:
            detected["rust"] = TechnologyDetection(
                name="Rust",
                kind="language",
                confidence=Confidence.HIGH if rs_files else Confidence.MEDIUM,
                evidence=[f"{len(rs_files)} Rust source files"],
            )

        return detected

    def _detect_frameworks(
        self, all_files: List[Path], languages: Dict[str, TechnologyDetection]
    ) -> Dict[str, TechnologyDetection]:
        frameworks: Dict[str, TechnologyDetection] = {}

        # Content samples from package manifests
        package_json_content = ""
        requirements_content = ""
        pyproject_content = ""

        for f in all_files:
            if f.name == "package.json":
                package_json_content = self._safe_read_text(f).lower()
            elif f.name in ("requirements.txt", "Pipfile"):
                requirements_content += "\n" + self._safe_read_text(f).lower()
            elif f.name == "pyproject.toml":
                pyproject_content = self._safe_read_text(f).lower()

        # FastAPI detection
        fastapi_evidence: List[str] = []
        if "fastapi" in requirements_content or "fastapi" in pyproject_content:
            fastapi_evidence.append("fastapi declared in dependencies")

        for f in all_files:
            if f.suffix == ".py":
                sample = self._safe_read_text(f, max_chars=3000)
                if "import fastapi" in sample or "from fastapi import" in sample:
                    fastapi_evidence.append(f"FastAPI import in {f.name}")
                    break

        if fastapi_evidence:
            frameworks["fastapi"] = TechnologyDetection(
                name="FastAPI",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=fastapi_evidence,
            )

        # Django detection
        django_evidence: List[str] = []
        if any(f.name == "manage.py" for f in all_files):
            django_evidence.append("manage.py present")
        if "django" in requirements_content or "django" in pyproject_content:
            django_evidence.append("django declared in dependencies")

        for f in all_files:
            if f.suffix == ".py":
                sample = self._safe_read_text(f, max_chars=2000)
                if "from django" in sample or "import django" in sample:
                    django_evidence.append(f"Django import in {f.name}")
                    break

        if django_evidence:
            frameworks["django"] = TechnologyDetection(
                name="Django",
                kind="framework",
                confidence=Confidence.HIGH if len(django_evidence) > 1 else Confidence.MEDIUM,
                evidence=django_evidence,
            )

        # Flask detection
        flask_evidence: List[str] = []
        if "flask" in requirements_content or "flask" in pyproject_content:
            flask_evidence.append("flask declared in dependencies")
        for f in all_files:
            if f.suffix == ".py":
                sample = self._safe_read_text(f, max_chars=2000)
                if "from flask import" in sample or "import flask" in sample:
                    flask_evidence.append(f"Flask import in {f.name}")
                    break
        if flask_evidence:
            frameworks["flask"] = TechnologyDetection(
                name="Flask",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=flask_evidence,
            )

        # Express detection
        express_evidence: List[str] = []
        if '"express"' in package_json_content:
            express_evidence.append("express in package.json")
        for f in all_files:
            if f.suffix in (".js", ".ts", ".mjs"):
                sample = self._safe_read_text(f, max_chars=2000)
                if (
                    "require('express')" in sample
                    or 'require("express")' in sample
                    or "from 'express'" in sample
                    or 'from "express"' in sample
                ):
                    express_evidence.append(f"express import in {f.name}")
                    break
        if express_evidence:
            frameworks["express"] = TechnologyDetection(
                name="Express",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=express_evidence,
            )

        # NestJS detection
        nest_evidence: List[str] = []
        if any(f.name == "nest-cli.json" for f in all_files):
            nest_evidence.append("nest-cli.json present")
        if '"@nestjs/core"' in package_json_content or '"@nestjs/common"' in package_json_content:
            nest_evidence.append("@nestjs in package.json dependencies")
        if nest_evidence:
            frameworks["nestjs"] = TechnologyDetection(
                name="NestJS",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=nest_evidence,
            )

        # Spring Boot detection
        spring_evidence: List[str] = []
        for f in all_files:
            if f.name in ("pom.xml", "build.gradle", "build.gradle.kts"):
                txt = self._safe_read_text(f)
                if "spring-boot" in txt:
                    spring_evidence.append(f"spring-boot in {f.name}")
                    break
            elif f.suffix == ".java":
                txt = self._safe_read_text(f, max_chars=2000)
                if "SpringBootApplication" in txt:
                    spring_evidence.append(f"@SpringBootApplication in {f.name}")
                    break
        if spring_evidence:
            frameworks["spring"] = TechnologyDetection(
                name="Spring Boot",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=spring_evidence,
            )

        # Laravel detection
        laravel_evidence: List[str] = []
        if any(f.name == "artisan" for f in all_files):
            laravel_evidence.append("artisan CLI present")
        for f in all_files:
            if f.name == "composer.json":
                txt = self._safe_read_text(f)
                if "laravel/framework" in txt:
                    laravel_evidence.append("laravel/framework in composer.json")
        if laravel_evidence:
            frameworks["laravel"] = TechnologyDetection(
                name="Laravel",
                kind="framework",
                confidence=Confidence.HIGH,
                evidence=laravel_evidence,
            )

        return frameworks
