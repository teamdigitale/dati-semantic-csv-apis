"""
Vocabulary Data API application using Connexion.

This module provides a spec-first API for serving controlled vocabulary data items.
"""

import contextlib
import logging
import sqlite3
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import starlette.convertors
import yaml
from common.cache_control_middleware import (
    CacheControlResponseHeaderMiddleware,
)
from common.errors import (
    handle_exception,
    handle_not_implemented,
    handle_problem_safe,
)
from common.printable_parameters_middleware import (
    PrintableParametersMiddleware,
)
from connexion import AsyncApp, ConnexionMiddleware
from connexion.exceptions import ProblemException
from connexion.middleware.main import MiddlewarePosition
from connexion.options import SwaggerUIOptions
from starlette.middleware.cors import CORSMiddleware

from tools.store import APIStore


class _NonEmptyPathConvertor(starlette.convertors.Convertor):
    """Override Starlette's default path convertor (.*) to require at least one character.

    Without this, a trailing slash in e.g. GET /vocabularies/inail/agente_causale/
    is matched as {itemId:path} with itemId='' and then rejected with 400 by
    schema validation instead of routing correctly to the listing endpoint.
    """

    regex = ".+"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


starlette.convertors.CONVERTOR_TYPES["path"] = _NonEmptyPathConvertor()


@dataclass
class Config:
    API_BASE_URL: str
    HARVEST_DB: str
    CACHE_CONTROL_MAX_AGE: int = 3600
    PREDECESSOR_BASE_URL: str = ""
    CORS_ORIGINS: list[str] | None = None
    SWAGGER_UI: bool = False


# Configure logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def load_dataset_handler(
    api_base_url: str,
    harvest_db: str,
    app: ConnexionMiddleware,
    predecessor_base_url: str = "",
) -> AsyncIterator[dict[str, Any]]:
    """
    Load the vocabulary dataset at startup
    and makes it available via request.state in all handlers.

    Args:
        api_base_url: Base URL for the API.
        harvest_db: Local path to the harvest.db SQLite file.
        app: The ConnexionMiddleware application instance.

    Yields:
        Dictionary containing the application state (vocabulary_items).
    """
    logger.info("Application startup: loading vocabulary dataset")
    vocabulary_items = None
    assert harvest_db

    # Load base OAS spec once for use in show_vocabulary_spec
    with open(Path(__file__).parent / "openapi.yaml") as f:
        base_spec = yaml.safe_load(f)

    # Open a single read-only APIStore instance reused across requests.
    harvest_database: APIStore = APIStore(
        harvest_db,
        read_only=True,
    )

    # Update the FTS table.
    # harvest_database.create_fts_table()

    harvest_database.connect()
    logger.info("Opened harvest DB connection: %s", harvest_db)

    logger.info("Application startup complete")

    yield {
        "vocabulary_items": vocabulary_items,
        "harvest_db": harvest_database,
        "base_spec": base_spec,
        "api_base_url": api_base_url,
        "predecessor_base_url": predecessor_base_url,
    }

    logger.info("Application shutdown")
    if harvest_database:
        harvest_database.close()


def create_app(config: Config | None = None) -> AsyncApp:
    """
    Create and configure the Connexion application.

        harvest_db = config.get("HARVEST_DB")
    This function sets up the API application, including loading the OpenAPI
    specification and configuring the lifespan handler.

    Args:
        config: Configuration dictionary with API_BASE_URL and VOCABULARY_DATAFILE.
                vocabulary_datafile, api_base_url, harvest_db, app
    Returns:
        The configured AsyncApp instance.
    """
    if config is None:
        config = Config(
            API_BASE_URL="http://localhost:8080",
            HARVEST_DB="harvest.db",
        )
    assert config is not None, "Config must be provided to create_app"

    api_base_url = config.API_BASE_URL or "http://localhost:8080"

    app: AsyncApp = AsyncApp(
        import_name=__name__,
        specification_dir=str(Path(__file__).parent),
        lifespan=lambda app: load_dataset_handler(
            api_base_url,
            harvest_db=config.HARVEST_DB,
            app=app,
            predecessor_base_url=config.PREDECESSOR_BASE_URL,
        ),
        swagger_ui_options=SwaggerUIOptions(swagger_ui=config.SWAGGER_UI),
    )
    app.add_api(
        "openapi.yaml",
        strict_validation=True,
    )
    # Ensure that request parameters are safe (e.g., for logging, ..)
    app.add_middleware(
        PrintableParametersMiddleware,
        position=MiddlewarePosition.BEFORE_CONTEXT,
    )
    app.add_middleware(
        CacheControlResponseHeaderMiddleware.factory(
            max_age=config.CACHE_CONTROL_MAX_AGE
        ),
        position=MiddlewarePosition.BEFORE_CONTEXT,
    )

    app.add_middleware(
        CORSMiddleware,
        # BEFORE_ROUTING ensures CORS headers are added even
        #  for 3xx responses.
        position=MiddlewarePosition.BEFORE_ROUTING,
        allow_origins=config.CORS_ORIGINS or [],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # Register exception handler for generic exceptions
    app.add_error_handler(NotImplementedError, handle_not_implemented)
    app.add_error_handler(501, handle_not_implemented)
    app.add_error_handler(500, handle_exception)
    app.add_error_handler(Exception, handle_exception)

    # Specific sql Handlers.
    app.add_error_handler(sqlite3.OperationalError, handle_exception)
    app.add_error_handler(sqlite3.DatabaseError, handle_exception)

    app.add_error_handler(ProblemException, handle_problem_safe)

    #
    # We use assertion errors to track unexpected conditions
    #   that are elsewhere tested. These should be
    #   logged and fixed in the code.
    #
    app.add_error_handler(AssertionError, handle_exception)

    return app
