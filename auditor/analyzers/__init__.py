# ruff: noqa: F401, I001
"""Analyzer initialization and dynamic discovery loader."""

import auditor.analyzers.universal.architecture
import auditor.analyzers.universal.solid
import auditor.analyzers.universal.dependency
import auditor.analyzers.universal.complexity
import auditor.analyzers.universal.duplication
import auditor.analyzers.universal.security
import auditor.analyzers.universal.error_handling
import auditor.analyzers.universal.logging
import auditor.analyzers.universal.configuration
import auditor.analyzers.universal.database_design
import auditor.analyzers.universal.api_design
import auditor.analyzers.universal.testing
import auditor.analyzers.universal.production_readiness
import auditor.analyzers.languages.python.rules
import auditor.analyzers.languages.javascript.rules
import auditor.analyzers.languages.typescript.rules
import auditor.analyzers.frameworks.fastapi
import auditor.analyzers.frameworks.express
import auditor.analyzers.frameworks.nestjs


def ensure_analyzers_loaded() -> None:
    """Ensure all analyzer and rule modules are imported and registered."""
    pass
