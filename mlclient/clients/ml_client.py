"""The ML Client module (MLClient / AsyncMLClient).

Exports sync and async entry points for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient / AsyncHttpClient (raw HTTP on main port)
    - .rest     -> RestApi / AsyncRestApi (/v1/* on main port)
    - .manage   -> ManageApi / AsyncManageApi (/manage/v2/* on port 8002)
    - .admin    -> AdminApi / AsyncAdminApi (/admin/v1/* on port 8001)
    - .parser   -> MLResponseParser
    - .documents, .eval, .logs -> high-level services
"""

from __future__ import annotations

import logging
from functools import cached_property
from types import TracebackType

from httpx import BasicAuth, DigestAuth, Response
from httpx_retries import Retry

from mlclient.api.admin_api import AdminApi, AsyncAdminApi
from mlclient.api.manage_api import AsyncManageApi, ManageApi
from mlclient.api.rest_api import AsyncRestApi, RestApi
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import AsyncDocumentsService, DocumentsService
from mlclient.services.eval import AsyncEvalService, EvalService
from mlclient.services.logs import AsyncLogsService, LogsService

from .api_client import ApiClient, AsyncApiClient
from .http_client import (
    DEFAULT_RETRY_STRATEGY,
    MARKLOGIC_ADMIN_API_PORT,
    MARKLOGIC_MANAGE_API_PORT,
    RESTART_RETRY_STRATEGY,
    AsyncHttpClient,
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
        self._manage_http = None
        self._admin_http = None

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
    def http(self) -> HttpClient:
        """Raw HTTP access."""
        return self._http

    @cached_property
    def rest(self) -> RestApi:
        """REST API (``/v1/*``) - requires REST app server."""
        return RestApi(ApiClient(self._http))

    @cached_property
    def manage(self) -> ManageApi:
        """Management API (``/manage/v2/*``) - requires Manage server."""
        return ManageApi(ApiClient(self._get_manage_http()))

    @cached_property
    def admin(self) -> AdminApi:
        """Admin API (``/admin/v1/*``) - requires Admin server (port 8001)."""
        return AdminApi(ApiClient(self._get_admin_http()))

    @property
    def parser(self) -> type[MLResponseParser]:
        """Response parser for manual parsing of raw responses."""
        return MLResponseParser

    @cached_property
    def documents(self) -> DocumentsService:
        """High-level documents service."""
        return DocumentsService(ApiClient(self._http))

    @cached_property
    def eval(self) -> EvalService:
        """High-level eval service."""
        return EvalService(ApiClient(self._http))

    @cached_property
    def logs(self) -> LogsService:
        """High-level logs service."""
        return LogsService(ApiClient(self._get_manage_http()))

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

    def _get_manage_http(self) -> HttpClient:
        """Return HttpClient for manage API (always port 8002).

        The Management API is only available on the fixed Manage server
        port (8002). If the main client already uses port 8002, it is reused.
        Otherwise, a separate HttpClient is lazily created.
        """
        if self._http.port == MARKLOGIC_MANAGE_API_PORT:
            return self._http
        if self._manage_http is None:
            self._manage_http = self._create_secondary_http(
                MARKLOGIC_MANAGE_API_PORT,
            )
        return self._manage_http

    def _get_admin_http(self) -> HttpClient:
        """Return HttpClient for admin API (always port 8001).

        The Admin API is only available on the fixed Admin server port (8001).
        If the main client already uses port 8001, it is reused. Otherwise,
        a separate HttpClient is lazily created.
        """
        if self._http.port == MARKLOGIC_ADMIN_API_PORT:
            return self._http
        if self._admin_http is None:
            self._admin_http = self._create_secondary_http(MARKLOGIC_ADMIN_API_PORT)
        return self._admin_http

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


class AsyncMLClient:
    """Async entry point for MarkLogic interaction.

    Provides layered access (all methods are async):

    - ``ml.http.get("/endpoint")`` -- raw HTTP
    - ``ml.rest.eval.post(xquery="...")`` -- mid-level REST API (``/v1/*``)
    - ``ml.manage.databases.get_list()`` -- mid-level Management API
    - ``ml.admin.get_timestamp()`` -- mid-level Admin API (``/admin/v1/*``)
    - ``ml.rest.call(SomeApiCall())`` -- advanced: custom Call objects
    - ``ml.parser.parse(resp)`` -- manual parsing of raw responses
    - ``ml.documents.read("/doc.json")`` -- high-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- high-level, parsed results
    - ``ml.logs.get(log_type=...)`` -- high-level, parsed results
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
        """Initialize AsyncMLClient instance.

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
        http_kwargs = {
            "protocol": protocol,
            "host": host,
            "auth_method": auth_method,
            "username": username,
            "password": password,
            "retry": retry,
        }
        self._http = AsyncHttpClient(port=port, **http_kwargs)
        self._manage_http = (
            self._http
            if port == MARKLOGIC_MANAGE_API_PORT
            else AsyncHttpClient(port=MARKLOGIC_MANAGE_API_PORT, **http_kwargs)
        )
        self._admin_http = (
            self._http
            if port == MARKLOGIC_ADMIN_API_PORT
            else AsyncHttpClient(port=MARKLOGIC_ADMIN_API_PORT, **http_kwargs)
        )

    async def __aenter__(self):
        """Connect and return self for use as an async context manager."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type,
        exc_val: BaseException,
        exc_tb: TracebackType,
    ):
        """Disconnect on context manager exit."""
        await self.disconnect()

    @property
    def http(self) -> AsyncHttpClient:
        """Raw HTTP access."""
        return self._http

    @cached_property
    def rest(self) -> AsyncRestApi:
        """REST API (``/v1/*``) - requires REST app server."""
        return AsyncRestApi(AsyncApiClient(self._http))

    @cached_property
    def manage(self) -> AsyncManageApi:
        """Management API (``/manage/v2/*``) - requires Manage server."""
        return AsyncManageApi(AsyncApiClient(self._manage_http))

    @cached_property
    def admin(self) -> AsyncAdminApi:
        """Admin API (``/admin/v1/*``) - requires Admin server (port 8001)."""
        return AsyncAdminApi(AsyncApiClient(self._admin_http))

    @property
    def parser(self) -> type[MLResponseParser]:
        """Response parser for manual parsing of raw responses."""
        return MLResponseParser

    @cached_property
    def documents(self) -> AsyncDocumentsService:
        """High-level documents service."""
        return AsyncDocumentsService(AsyncApiClient(self._http))

    @cached_property
    def eval(self) -> AsyncEvalService:
        """High-level eval service."""
        return AsyncEvalService(AsyncApiClient(self._http))

    @cached_property
    def logs(self) -> AsyncLogsService:
        """High-level logs service."""
        return AsyncLogsService(AsyncApiClient(self._manage_http))

    async def connect(self):
        """Start an HTTP session."""
        await self._http.connect()
        if self._manage_http is not self._http:
            await self._manage_http.connect()
        if self._admin_http is not self._http:
            await self._admin_http.connect()

    async def disconnect(self):
        """Close an HTTP session."""
        await self._http.disconnect()
        if self._manage_http is not self._http:
            await self._manage_http.disconnect()
        if self._admin_http is not self._http:
            await self._admin_http.disconnect()

    def is_connected(self) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._http.is_connected()

    async def wait_for_restart(
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
        await waiter.async_wait_for_restart_completion(
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
