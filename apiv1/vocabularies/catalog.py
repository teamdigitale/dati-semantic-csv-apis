"""
API handlers for vocabularies endpoint.

This module implements handlers for serving controlled vocabularies
in RFC 9727 linkset format with filtering capabilities.
"""

import json
import logging
from typing import Any

from _generated.models import APICatalog, APIDistribution, Linkset
from common.utils import _get_database_or_fail
from connexion import request
from connexion.exceptions import BadRequestProblem
from pydantic import ValidationError

from tools.store import APIStore

LIMIT_DEFAULT = 20

log = logging.getLogger(__name__)


def get_status():
    """
    Get the status of the API.
    """
    return (
        {
            "status": 200,
            "title": "Vocabularies API is running",
            "type": "about:blank",
        },
        200,
        {"Content-Type": "application/json"},
    )


def _to_catalog_item(
    item: dict[str, Any],
    api_base_url: str,
    predecessor_base_url: str,
) -> APIDistribution | None:
    """
    Convert a dictionary item from _metadata
    containing agency_id, key_concept, vocabulary_uri
    to an APIDistribution model instance.
    """
    try:
        catalog = json.loads(item["catalog"])
        vocabulary_uri = item["vocabulary_uri"]
        api_url: str = "/".join(
            (
                api_base_url,
                "vocabularies",
                item["agency_id"],
                item["key_concept"],
            )
        )
        oas_url = "/".join((api_url, "openapi.yaml"))
        dist_dict: dict[str, Any] = {
            "href": api_url,
            "about": vocabulary_uri,
            "title": catalog["title"],
            "description": catalog["description"],
            "hreflang": catalog["hreflang"],
            "version": catalog["version"],
            "author": catalog["author"],
            "service-desc": [
                {"href": oas_url, "type": "application/openapi+yaml"}
            ],
            "service-meta": [
                {
                    "href": f"{vocabulary_uri}?output=application/ld+json",
                    "type": "application/ld+json",
                }
            ],
        }
        if predecessor_base_url:
            pre_url = "/".join(
                (predecessor_base_url, item["agency_id"], item["key_concept"])
            )
            dist_dict["predecessor-version"] = [{"href": pre_url}]
        return APIDistribution.model_validate(dist_dict)
    except (KeyError, json.JSONDecodeError, ValidationError) as e:
        log.exception(
            f"Skipping invalid catalog entry in database for agency_id={item['agency_id']} "
            f"and key_concept={item['key_concept']}: {e}"
        )
        return None


def _list_vocabularies_impl(
    q: str | None,
    title: str | None,
    author: str | None,
    hreflang: str | None,
    concept: str | None,
    limit: int,
    offset: int,
    kwargs: dict[str, Any],
    agency_id: str | None = None,
) -> tuple[dict[str, Any], int, dict[str, str]]:
    if kwargs:
        raise BadRequestProblem(detail=f"Unexpected query parameters: {kwargs}")

    limit = limit or LIMIT_DEFAULT

    db: APIStore = _get_database_or_fail()

    rows = db.search_metadata(
        query=q or "",
        agency_id=agency_id,
        author=author or "",
        hreflang=hreflang or "",
        title=title or "",
        key_concept=concept or "",
        limit=limit,
        offset=offset,
    )

    total_count: int = dict(rows[0]).get("total_count", 0) if rows else 0

    items: list[APIDistribution] = [
        item
        for x in rows
        if (
            item := _to_catalog_item(
                dict(x),
                request.state.api_base_url,
                request.state.predecessor_base_url,
            )
        )
        is not None
    ]

    catalog = APICatalog.model_validate(
        {
            "api-catalog": request.state.api_base_url,
            "anchor": request.state.api_base_url,
            "item": items,
            "total_count": total_count,
            "count": len(items),
            "limit": limit,
            "offset": offset,
        }
    )
    linkset = Linkset(linkset=[catalog])

    return (
        linkset.model_dump(by_alias=True, mode="json", exclude_none=True),
        200,
        {"Content-Type": "application/linkset+json"},
    )


def list_vocabularies(
    q: str | None = None,
    title: str | None = None,
    author: str | None = None,
    hreflang: str | None = None,
    concept: str | None = None,
    limit: int = LIMIT_DEFAULT,
    offset: int = 0,
    **kwargs: Any,
) -> tuple[dict[str, Any], int, dict[str, str]]:
    """
    Get vocabularies with optional filtering.

    Args:
        author: Filter by substring of the author URI.
        hreflang: Filter by language code.
        concept: Filter by substring of the key concept identifier.
        limit: Maximum number of items to return.
        offset: Number of items to skip before starting to collect the result set.

    Returns:
        Linkset dictionary with filtered items.
    """
    return _list_vocabularies_impl(
        q=q,
        title=title,
        author=author,
        hreflang=hreflang,
        concept=concept,
        limit=limit,
        offset=offset,
        kwargs=kwargs,
    )


def list_vocabularies_by_agency(
    agencyId: str,
    q: str | None = None,
    title: str | None = None,
    author: str | None = None,
    hreflang: str | None = None,
    concept: str | None = None,
    limit: int = LIMIT_DEFAULT,
    offset: int = 0,
    **kwargs: Any,
) -> tuple[dict[str, Any], int, dict[str, str]]:
    return _list_vocabularies_impl(
        q=q,
        title=title,
        author=author,
        hreflang=hreflang,
        concept=concept,
        limit=limit,
        offset=offset,
        kwargs=kwargs,
        agency_id=agencyId,
    )
