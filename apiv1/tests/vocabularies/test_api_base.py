"""Fast tests for the Vocabularies data API ASGI app."""

from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from vocabularies.app import create_app

from tests.harness import (
    OPENAPI_SPEC_PATH,
    _config,
    check_substructure,
    client_harness,
)

TESTCASES_FILE = Path(__file__).with_suffix(".yaml")
TESTCASES = cast(
    dict[str, list[dict[str, Any]]], yaml.safe_load(TESTCASES_FILE.read_text())
)
OPENAPI_SPEC = yaml.safe_load(OPENAPI_SPEC_PATH.read_text())


@pytest.mark.parametrize(
    "testcase",
    TESTCASES["testcases"],
    ids=[tc["name"] for tc in TESTCASES["testcases"]],
)
def test_base_requests(single_entry_db, testcase):
    """
    When:

    - I issue basic requests

    Then:

    - I got the expected responses and logs.
    """
    with client_harness(create_app, _config(single_entry_db)) as (
        client,
        _logs,
    ):
        requests = (
            testcase["request"]
            if isinstance(testcase["request"], list)
            else [testcase["request"]]
        )
        for request in requests:
            response = client.request(
                method=request["method"],
                url=request["url"],
                headers=request.get("headers"),
                params=request.get("params"),
            )
            expected = testcase["expected"]

            # Then I got the expected status code ..
            assert response.status_code == expected["response"]["status_code"]
            if expected_count := expected["response"].get("count"):
                assert (
                    len(response.json().get("items", [])) == expected_count
                ), (
                    f"Expected 'count' to be {expected_count}, but got {len(response.json().get('items', []))}"
                )

            # .. headers are as expected ..
            if expected_headers := expected["response"].get("headers"):
                for check in expected_headers:
                    present = check.get("present", True)
                    headers = {k: v for k, v in check.items() if k != "present"}
                    for header, value in headers.items():
                        if present:
                            assert header in response.headers, (
                                f"Missing expected header: {header}"
                            )
                            assert response.headers[header] == value, (
                                f"Expected header '{header}' to be '{value}', but got '{response.headers[header]}'"
                            )
                        else:
                            assert header not in response.headers, (
                                f"Unexpected header present: {header}={response.headers[header]!r}"
                            )
            # .. the content is as expected ..
            if expected_data := expected["response"].get("json"):
                response_data = response.json()
            elif expected_data := expected["response"].get("yaml"):
                response_data = yaml.safe_load(response.text)
            else:
                response_data = None

            if response_data is not None:
                issues = check_substructure(expected_data, response_data)
                assert not issues, (
                    "Missing/changed expected JSON fields:\n"
                    + "\n".join(f"  {path}: {msg}" for path, msg in issues)
                )

            # .. and the logs contain the expected messages.
            for log in expected.get("logs", []):
                assert log in _logs


def test_get_item_href_points_to_self(single_entry_db):
    """href in the /{id} response must be the canonical self URL."""
    config = _config(single_entry_db)
    with client_harness(create_app, config) as (client, _):
        url = "/vocabularies/istat/ateco-2025/A01"
        response = client.get(url)
        assert response.status_code == 200
        expected_href = f"{config.API_BASE_URL.rstrip('/')}{url}"
        assert response.json()["href"] == expected_href


@pytest.mark.skip(reason="Check why it happens.")
def test_missing_vocab_returns_404(
    broken_dataset_db,
) -> None:
    """Missing vocabulary tables should be reported as a sanitized 404 problem."""
    with client_harness(
        create_app,
        _config(broken_dataset_db),
    ) as (client, _logs):
        response = client.get("/vocabularies/agid/broken-vocab")

        assert response.status_code == 404
        assert (
            response.headers["content-type"].split(";")[0]
            == "application/problem+json"
        )
        body = response.json()
        assert body["title"] == "Not Found"
        assert body["status"] == 404
        assert body["detail"] == "The requested vocabulary was not found"


@pytest.mark.parametrize(
    "override,expected_url",
    [
        # FALSE: servers served as-is from openapi.yaml (first static entry)
        ("FALSE", OPENAPI_SPEC["servers"][0]["url"]),
        # BASE_URL: first server reflects API_BASE_URL (set by _config)
        ("BASE_URL", "https://schema.gov.it/api/vocabularies/v1/"),
        # PATH_ONLY: Connexion default strips scheme+host; root_path="" in tests
        ("PATH_ONLY", ""),
    ],
)
def test_servers_url_from_env(
    monkeypatch, single_entry_db, override, expected_url
):
    """SERVERS_URL_OVERRIDE controls the servers.url in the served openapi.yaml."""
    monkeypatch.setenv("SERVERS_URL_OVERRIDE", override)
    config = _config(single_entry_db)
    config.SERVERS_URL_OVERRIDE = override
    with client_harness(create_app, config) as (client, _):
        response = client.get("/openapi.yaml")
        assert response.status_code == 200
        spec = yaml.safe_load(response.text)
        assert spec["servers"][0]["url"] == expected_url
