"""The ML Client module.

It exports the MLClient class - the main entry point for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient (raw HTTP on main port)
    - .rest     -> RestApi (/v1/* on main port)
    - .manage   -> ManageApi (/manage/v2/* on port 8002)
    - .admin    -> AdminApi (/admin/v1/* on port 8001)
    - .parser   -> MLResponseParser
    - .documents, .eval, .logs -> high-level services
"""

from __future__ import annotations

import logging
from functools import cached_property
from types import TracebackType

from httpx import BasicAuth, DigestAuth, Response
from httpx_retries import Retry

from mlclient.api.admin_api import AdminApi
from mlclient.api.manage_api import ManageApi
from mlclient.api.rest_api import RestApi
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import DocumentsService
from mlclient.services.eval import EvalService
from mlclient.services.logs import LogsService

from .api_client import ApiClient
from .http_client import (
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    DEFAULT_RETRY_STRATEGY,
    RESTART_RETRY_STRATEGY,
    HttpClient,
)
from .restart_waiter import RestartWaiter

logger = logging.getLogger(__name__)


class MLClient:
    """Main entry point for MarkLogic interaction.

    Provides layered access:

    - ``ml.http.get("/endpoint")`` -- raw HTTP
    - ``ml.rest.eval.post(xquery="...")`` -- mid-level REST API (``/v1/*``)
    - ``ml.manage.databases.get_list()`` -- mid-level Management API (``/manage/v2/*``)
    - ``ml.admin.get_timestamp()`` -- mid-level Admin API (``/admin/v1/*``)
    - ``ml.rest.call(SomeApiCall())`` -- advanced: custom Call objects
    - ``ml.parser.parse(resp)`` -- manual parsing of raw responses
    - ``ml.documents.read("/doc.json")`` -- high-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- high-level, parsed results
    - ``ml.logs.get(log_type=...)`` -- high-level, parsed results

    Examples
    --------
    Low-level (raw HTTP) - returns raw multipart response:

    >>> from mlclient import MLClient
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8002,
    ...     "username": "admin",
    ...     "password": "admin",
    ... }
    >>> with MLClient(**config) as ml:
    ...     resp = ml.http.post(
    ...         "/v1/eval",
    ...         "xquery=xdmp:database()",
    ...         headers={"Content-Type": "application/x-www-form-urlencoded"},
    ...     )
    ...     resp.status_code
    200

    Mid-level REST API (``/v1/*``) - returns httpx.Response:

    >>> with MLClient(**config) as ml:
    ...     resp = ml.rest.eval.post(
    ...         xquery="xdmp:database() => xdmp:database-name()",
    ...     )
    ...     resp.status_code
    200

    Mid-level Management API (``/manage/v2/*``) - returns httpx.Response:

    >>> with MLClient(**config) as ml:
    ...     resp = ml.manage.databases.get_list()
    ...     resp.status_code
    200

    Mid-level Admin API (``/admin/v1/*``) - returns httpx.Response:

    >>> with MLClient(**config) as ml:
    ...     resp = ml.admin.get_timestamp()
    ...     resp.status_code
    200

    Response parsing:

    >>> from mlclient import MLClient
    >>> with MLClient(**config) as ml:
    ...     resp = ml.rest.eval.post(
    ...         xquery="xdmp:database() => xdmp:database-name()",
    ...     )
    ...     parsed = ml.parser.parse(resp)
    ...     print(parsed)
    App-Services

    High-level (services) - returns parsed Python objects:

    >>> with MLClient(**config) as ml:
    ...     result = ml.eval.xquery(
    ...         "xdmp:database() => xdmp:database-name()",
    ...     )
    ...     print(result)
    App-Services
    """

    def __init__(
        self,
        protocol: str = "http",
        host: str = "localhost",
        port: int = MARKLOGIC_MANAGE_API_PORT,
        auth_method: str = "basic",
        username: str = "admin",
        password: str = "admin",
        retry: Retry | None = None,
    ):
        """Initialize MLClient instance.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8002
            An App Service port
        auth_method : str, default "basic"
            An authorization method (basic / digest)
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        """
        self._http = HttpClient(
            protocol=protocol,
            host=host,
            port=port,
            auth_method=auth_method,
            username=username,
            password=password,
            retry=retry,
        )
        self._api_client = ApiClient(self._http)
        self._manage_http = None
        self._manage_api_client = None
        self._admin_http = None
        self._admin_api_client = None

    def __enter__(self):
        """Connect and return self for use as a context manager."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type,
        exc_val: BaseException,
        exc_tb: TracebackType,
    ):
        """Disconnect on context manager exit."""
        self.disconnect()

    @property
    def protocol(self) -> str:
        """Return the protocol (http/https)."""
        return self._http.protocol

    @property
    def host(self) -> str:
        """Return the host name."""
        return self._http.host

    @property
    def port(self) -> int:
        """Return the port number."""
        return self._http.port

    @property
    def auth_method(self) -> str:
        """Return the auth method."""
        return self._http.auth_method

    @property
    def username(self) -> str:
        """Return the username."""
        return self._http.username

    @property
    def password(self) -> str:
        """Return the password."""
        return self._http.password

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return self._http.base_url

    @property
    def http(self) -> HttpClient:
        """Raw HTTP access."""
        return self._http

    @cached_property
    def rest(self) -> RestApi:
        """REST API (``/v1/*``) - requires REST app server."""
        return RestApi(self._api_client)

    @cached_property
    def manage(self) -> ManageApi:
        """Management API (``/manage/v2/*``) - requires Manage server."""
        return ManageApi(self._get_manage_client())

    @cached_property
    def admin(self) -> AdminApi:
        """Admin API (``/admin/v1/*``) - requires Admin server (port 8001)."""
        return AdminApi(self._get_admin_client())

    @property
    def parser(self) -> type[MLResponseParser]:
        """Response parser for manual parsing of raw responses."""
        return MLResponseParser

    @cached_property
    def documents(self) -> DocumentsService:
        """High-level documents service."""
        return DocumentsService(self._api_client)

    @cached_property
    def eval(self) -> EvalService:
        """High-level eval service."""
        return EvalService(self._api_client)

    @cached_property
    def logs(self) -> LogsService:
        """High-level logs service."""
        return LogsService(self._get_manage_client())

    def connect(self):
        """Start an HTTP session."""
        self._http.connect()
        if self._manage_http is not None:
            self._manage_http.connect()
        if self._admin_http is not None:
            self._admin_http.connect()

    def disconnect(self):
        """Close an HTTP session."""
        self._http.disconnect()
        if self._manage_http is not None:
            self._manage_http.disconnect()
        if self._admin_http is not None:
            self._admin_http.disconnect()

    def is_connected(self) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._http.is_connected()

    def wait_for_restart(
        self,
        response: Response | None = None,
        *,
        timeout: float = 30.0,
        poll_interval: float = 0.25,
        retry: Retry | None = None,
    ) -> None:
        """Wait for MarkLogic readiness after a restart-signaling response.

        Parameters
        ----------
        response : Response | None
            Response from an operation that may have initiated a restart.
        timeout : float
            Maximum number of seconds to wait for readiness.
        poll_interval : float
            Delay between readiness probes.
        retry : Retry | None
            Retry strategy for readiness probes.
        """
        waiter = self._get_restart_waiter()
        waiter.wait_for_restart_completion(
            response,
            timeout=timeout,
            poll_interval=poll_interval,
            retry=retry or RESTART_RETRY_STRATEGY,
        )

    def _get_restart_waiter(self) -> RestartWaiter:
        auth_impl = BasicAuth if self._http.auth_method == "basic" else DigestAuth
        auth = auth_impl(self._http.username, self._http.password)
        return RestartWaiter(
            protocol=self._http.protocol,
            host=self._http.host,
            auth=auth,
            default_retry=DEFAULT_RETRY_STRATEGY,
        )

    def _get_manage_client(self) -> ApiClient:
        """Return ApiClient for manage API (always port 8002).

        The Management API is only available on the fixed Manage server
        port (8002). If the main client already uses port 8002, it is reused.
        Otherwise, a separate HttpClient is lazily created.
        """
        if self._http.port == MARKLOGIC_MANAGE_API_PORT:
            return self._api_client
        if self._manage_api_client is None:
            self._manage_http = self._create_secondary_http(
                MARKLOGIC_MANAGE_API_PORT,
            )
            self._manage_api_client = ApiClient(self._manage_http)
        return self._manage_api_client

    def _get_admin_client(self) -> ApiClient:
        """Return ApiClient for admin API (always port 8001).

        The Admin API is only available on the fixed Admin server port (8001).
        If the main client already uses port 8001, it is reused. Otherwise,
        a separate HttpClient is lazily created.
        """
        if self._http.port == MARKLOGIC_ADMIN_API_PORT:
            return self._api_client
        if self._admin_api_client is None:
            self._admin_http = self._create_secondary_http(MARKLOGIC_ADMIN_API_PORT)
            self._admin_api_client = ApiClient(self._admin_http)
        return self._admin_api_client

    def _create_secondary_http(self, port: int) -> HttpClient:
        """Create and optionally connect a secondary HttpClient."""
        http = HttpClient(
            protocol=self._http.protocol,
            host=self._http.host,
            port=port,
            auth_method=self._http.auth_method,
            username=self._http.username,
            password=self._http.password,
        )
        if self.is_connected():
            http.connect()
        return http
