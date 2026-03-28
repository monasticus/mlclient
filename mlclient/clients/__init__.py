"""The ML Clients package.

This package contains the client hierarchy for MarkLogic interaction.

Exports:
    * MLClient - main entry point (composition with .http, .rest, etc.)
    * HttpClient - raw HTTP client
    * ApiClient - mid-level API client with call()

Examples
--------
>>> from mlclient.clients import MLClient
>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_list()
"""

from .api_client import ApiClient
from .http_client import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    MARKLOGIC_REST_API_PORT,
    RESTART_RETRY_STRATEGY,
    HttpClient,
)
from .ml_client import MLClient

__all__ = [
    "DEFAULT_RETRY_STRATEGY",
    "MARKLOGIC_ADMIN_API_PORT",
    "MARKLOGIC_MANAGE_API_PORT",
    "MARKLOGIC_REST_API_PORT",
    "RESTART_RETRY_STRATEGY",
    "ApiClient",
    "HttpClient",
    "MLClient",
]
