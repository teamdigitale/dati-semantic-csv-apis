"""
Tests for the show_vocabulary_spec endpoint.
"""

import yaml
from vocabularies.app import create_app

from tests.harness import ATECO_SPEC, _config, client_harness


def test_show_vocabulary_spec(single_entry_db):
    """Returns 200 with merged OAS spec in application/openapi+yaml."""
    with client_harness(
        create_app,
        _config(single_entry_db),
    ) as (client, _logs):
        response = client.get("/vocabularies/istat/ateco-2025/openapi.yaml")

        assert response.status_code == 200
        assert "application/openapi+yaml" in response.headers["content-type"]

        spec = yaml.safe_load(response.text)
        assert spec["info"]["title"] == ATECO_SPEC["info"]["title"]
        returned_item = spec["components"]["schemas"]["Item"]
        stored_item = ATECO_SPEC["components"]["schemas"]["Item"]

        # href: null is injected at serve time; verify the rest of the schema is unchanged.
        context = returned_item.pop("x-jsonld-context")
        assert context["href"] is None
        context.pop("href")

        parent_context = context["parent"]["@context"]
        assert parent_context["href"] is None
        parent_context.pop("href")

        vocab_context = context["vocab"]["@context"]
        assert vocab_context["href"] is None
        vocab_context.pop("href")

        # The vocabulary-specific server URL should have been appended.
        server_urls = [s["url"] for s in spec.get("servers", [])]
        assert any("istat/ateco-2025" in url for url in server_urls)
        stored_context = stored_item.pop("x-jsonld-context")
        assert returned_item == stored_item
        assert context == stored_context


def test_show_vocabulary_spec_not_found(single_entry_db):
    """Returns 404 when the vocabulary is not in the database."""
    with client_harness(
        create_app,
        _config(single_entry_db),
    ) as (client, _logs):
        response = client.get("/vocabularies/istat/nonexistent/openapi.yaml")

        assert response.status_code == 404
