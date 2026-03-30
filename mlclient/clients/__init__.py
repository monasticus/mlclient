"""The ML Clients package.

This package contains the client hierarchy for MarkLogic interaction.

Exports:
    * MLClient - main entry point (composition with .http, .rest, etc.)
    * AsyncMLClient - async variant of MLClient
    * HttpClient - raw HTTP client
    * AsyncHttpClient - async variant of HttpClient
    * ApiClient - mid-level API client with call()
    * AsyncApiClient - async variant of ApiClient

Examples
--------
>>> from mlclient.clients import MLClient
>>> with MLClient() as ml:
...     resp = ml.manage.databases.get_list()
"""

from .api_client import ApiClient, AsyncApiClient
from .http_client import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    MARKLOGIC_REST_API_PORT,
    RESTART_RETRY_STRATEGY,
    AsyncHttpClient,
    HttpClient,
)
from .ml_client import AsyncMLClient, MLClient

__all__ = [
    "DEFAULT_RETRY_STRATEGY",
    "MARKLOGIC_ADMIN_API_PORT",
    "MARKLOGIC_MANAGE_API_PORT",
    "MARKLOGIC_REST_API_PORT",
    "RESTART_RETRY_STRATEGY",
    "ApiClient",
    "AsyncApiClient",
    "AsyncHttpClient",
    "AsyncMLClient",
    "HttpClient",
    "MLClient",
]
