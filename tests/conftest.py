"""Pytest configuration and shared fixtures for Backend Guard test suite."""

import sys
from pathlib import Path

import pytest

# Ensure auditor is on sys.path
AUDITOR_ROOT = Path(__file__).parent.parent.resolve()
if str(AUDITOR_ROOT) not in sys.path:
    sys.path.insert(0, str(AUDITOR_ROOT))

from auditor.config import Config  # noqa: E402
from auditor.core.context import AnalysisContext  # noqa: E402
from auditor.discovery import ProjectScanner  # noqa: E402


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def good_fastapi_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "good_projects" / "python_fastapi"


@pytest.fixture
def bad_fastapi_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "bad_projects" / "python_fastapi"


@pytest.fixture
def good_express_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "good_projects" / "node_express"


@pytest.fixture
def bad_express_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "bad_projects" / "node_express"


@pytest.fixture
def good_nestjs_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "good_projects" / "typescript_backend"


@pytest.fixture
def bad_nestjs_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "bad_projects" / "typescript_backend"


@pytest.fixture
def default_config() -> Config:
    return Config.default()


@pytest.fixture
def make_context():
    def _make(root_path: Path, config: Config | None = None) -> AnalysisContext:
        cfg = config or Config.default()
        scanner = ProjectScanner(root_path, cfg)
        pinfo = scanner.scan()
        return AnalysisContext(pinfo, cfg)

    return _make
