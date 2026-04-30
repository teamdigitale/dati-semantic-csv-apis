import contextlib
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import yaml
from starlette.testclient import TestClient
from vocabularies.app import Config

TESTDIR = Path(__file__).parent
DATADIR = TESTDIR / "data"
ATECO_OAS = DATADIR / "ateco-2025.oas3.yaml"
ATECO_SPEC = yaml.safe_load(ATECO_OAS.read_text())
APIDIR: Path = TESTDIR.parent / "vocabularies"
OPENAPI_SPEC_PATH = APIDIR / "openapi.yaml"


def check_substructure(
    expected: Any, actual: Any, path: str = "root"
) -> list[tuple[str, str]]:
    """Return (path, issue) pairs where expected is not a substructure of actual."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [
                (
                    path,
                    f"expected dict, got {type(actual).__name__}: {actual!r}",
                )
            ]
        issues = []
        for k, v in expected.items():
            if k not in actual:
                issues.append((f"{path}.{k}", "key missing from actual"))
            else:
                issues.extend(check_substructure(v, actual[k], f"{path}.{k}"))
        return issues
    elif isinstance(expected, list):
        if not isinstance(actual, list):
            return [
                (
                    path,
                    f"expected list, got {type(actual).__name__}: {actual!r}",
                )
            ]
        used: set[int] = set()
        issues = []
        for i, exp_item in enumerate(expected):
            best_j, best_issues = None, None
            for j, act_item in enumerate(actual):
                if j in used:
                    continue
                item_issues = check_substructure(
                    exp_item, act_item, f"{path}[{i}]"
                )
                if not item_issues:
                    best_j, best_issues = j, []
                    break
                if best_issues is None or len(item_issues) < len(best_issues):
                    best_j, best_issues = j, item_issues
            if not best_issues and best_j is not None:
                used.add(best_j)
            elif best_issues:
                issues.extend(best_issues)
            else:
                issues.append(
                    (f"{path}[{i}]", f"no match in actual for {exp_item!r}")
                )
        return issues
    else:
        if expected != actual:
            return [(path, f"expected {expected!r}, got {actual!r}")]
        return []


def _config(harvest_db: str) -> Config:
    return Config(
        API_BASE_URL="https://schema.gov.it/api/vocabularies/v1/",
        PREDECESSOR_BASE_URL="https://old.example.com",
        HARVEST_DB=harvest_db,
    )


@contextlib.contextmanager
def log_records() -> Iterator[list[str]]:
    """Fixture to capture log records during tests."""
    records = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    handler = ListHandler()
    logger = logging.getLogger()  # Root logger captures all logs
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    yield records
    logger.removeHandler(handler)


class Latin1Headers(httpx.Headers):
    """Header container that defaults to latin1 for RFC9110 compatibility tests."""

    def __init__(
        self,
        headers: Any = None,
        encoding: str = "latin1",
    ):
        if not isinstance(headers, (dict, list, type(None))):
            headers.encoding = "latin1"
        super().__init__(headers=headers, encoding="latin1")


@contextlib.contextmanager
def client_harness(
    creator: Any,
    config: Any,
) -> Iterator[tuple[TestClient, list[str]]]:
    """Fixture to create and yield the ASGI app with the given config."""
    with log_records() as logs:
        app = creator(config)
        # Patch it in this scope so all request header merges use latin1.
        with patch("httpx._models.Headers", Latin1Headers):
            with app.test_client() as client:
                client._headers.encoding = "latin1"
                yield client, logs
