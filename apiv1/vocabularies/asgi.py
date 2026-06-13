"""
ASGI entry point for production deployment with uvicorn.

Usage:
    uvicorn vocabularies.asgi:application --host 0.0.0.0 --port 8080
"""

import os
from typing import Literal, cast

from . import Config, create_app

_config = Config(
    API_BASE_URL=os.environ.get("API_BASE_URL", "http://localhost:8080").rstrip(
        "/"
    ),
    HARVEST_DB=os.environ.get("HARVEST_DB", "harvest.db"),
    CACHE_CONTROL_MAX_AGE=int(os.environ.get("CACHE_CONTROL_MAX_AGE", 3600)),
    PREDECESSOR_BASE_URL=os.environ.get("PREDECESSOR_BASE_URL", "").rstrip("/"),
    CORS_ORIGINS=[
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "").split(",")
        if o.strip()
    ]
    or None,
    SWAGGER_UI=os.environ.get("SWAGGER_UI", "").lower() == "true",
    SERVERS_URL_OVERRIDE=cast(
        Literal["FALSE", "BASE_URL", "PATH_ONLY"],
        os.environ.get("SERVERS_URL_OVERRIDE", "FALSE"),
    ),
)

application = create_app(config=_config)
