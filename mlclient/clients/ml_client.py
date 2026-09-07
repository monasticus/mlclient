"""The ML Client module (MLClient / AsyncMLClient).

Exports sync and async entry points for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient / AsyncHttpClient (raw HTTP on main port)
    - .rest     -> RestApi / AsyncRestApi (/v1/* on main port)
    - .manage   -> ManageApi / AsyncManageApi (/manage/v2/*, always port 8002)
    - .admin    -> AdminApi / AsyncAdminApi (/admin/v1/* on port 8001)
    - .parser   -> MLResponseParser
    - .documents, .eval, .logs -> high-level services
    - .transaction() -> open a scoped transaction (context manager)
"""

from __future__ import annotations

import logging
from functools import cached_property
from types import TracebackType

from httpx import Response
from httpx_retries import Retry

from mlclient.api.admin_api import AdminApi, AsyncAdminApi
from mlclient.api.manage_api import AsyncManageApi, ManageApi
from mlclient.api.rest_api import AsyncRestApi, RestApi
from mlclient.auth import AuthParam
from mlclient.connection import UNSET, CloudConfig, SSLConfig
from mlclient.http_config import HTTPConfig
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import AsyncDocumentsService, DocumentsService
from mlclient.services.eval import AsyncEvalService, EvalService
from mlclient.services.logs import AsyncLogsService, LogsService
from mlclient.services.transactions import (
    AsyncTransactionService,
    TransactionService,
    async_open_transaction,
    open_transaction,
)

from .api_client import ApiClient, AsyncApiClient
from .http_client import (
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
    - ``ml.transaction(database=...)`` -- open a scoped transaction (context manager)

    Examples
    --------
    Low-level (raw HTTP) - returns raw multipart response:

    >>> from mlclient import MLClient
    >>> config = {
    ...     "host": "localhost",
    ...     "port": 8000,
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
        protocol=UNSET,
        host: str = "localhost",
        port=UNSET,
        auth: AuthParam = UNSET,
        username: str = "admin",
        password: str = "admin",
        ssl: SSLConfig | None = None,
        cloud: CloudConfig | None = None,
        retry: Retry | None = None,
        *,
        config: HTTPConfig | None = None,
        manage_config: HTTPConfig | None = None,
        admin_config: HTTPConfig | None = None,
    ):
        """Initialize MLClient instance.

        The connection parameters describe the primary connection. The Manage
        (8002) and Admin (8001) connections are derived from it by default; pass
        ``manage_config`` / ``admin_config`` only to point them at a different
        host, credentials or port.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8000
            An App Service port
        auth : str | httpx.Auth | AuthConfig | None, default "digest"
            An authentication method: a string shortcut ("basic", "digest",
            "digestbasic", "certificate", "kerberos"), an AuthConfig, a custom
            httpx.Auth, or None
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        ssl : SSLConfig | None, default None
            SSL/TLS configuration; a client certificate forces HTTPS and
            defaults the auth method to "certificate"
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration; forces HTTPS on port 443 and handles
            authentication via the API key
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        config : HTTPConfig | None, default None
            An already-resolved primary configuration; when given, the
            connection parameters above are ignored
        manage_config : HTTPConfig | None, default None
            An already-resolved Manage configuration; when given, it is used
            instead of deriving the Manage connection from the primary
        admin_config : HTTPConfig | None, default None
            An already-resolved Admin configuration; when given, it is used
            instead of deriving the Admin connection from the primary
        """
        self._http = HttpClient(
            protocol=protocol,
            host=host,
            port=port,
            auth=auth,
            username=username,
            password=password,
            ssl=ssl,
            cloud=cloud,
            retry=retry,
            config=config,
        )
        self._manage_http = HttpClient(config=manage_config) if manage_config else None
        self._admin_http = HttpClient(config=admin_config) if admin_config else None

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

    def transaction(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
    ) -> TransactionService:
        """Open a multi-statement transaction and return a service scoped to it.

        Use as a context manager to commit on a clean exit and roll back on error:

        >>> with ml.transaction(database="my-db") as txn:  # doctest: +SKIP
        ...     ml.eval.xquery("...", **txn)
        """
        return open_transaction(
            ApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
        )

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
        return RestartWaiter(self._http.config)

    def _get_manage_http(self) -> HttpClient:
        """Return HttpClient for manage API (always port 8002).

        The Management API is only available on the fixed Manage server
        port (8002). An injected Manage configuration is used as-is; otherwise
        the main client is reused when it already targets port 8002 or runs on
        Cloud (every API routes through the single port-443 connection), and a
        separate HttpClient is lazily created in the remaining case.
        """
        if self._manage_http is not None:
            return self._manage_http
        config = self._http.config
        if config.cloud is not None or config.port == MARKLOGIC_MANAGE_API_PORT:
            return self._http
        self._manage_http = self._create_secondary_http(MARKLOGIC_MANAGE_API_PORT)
        return self._manage_http

    def _get_admin_http(self) -> HttpClient:
        """Return HttpClient for admin API (always port 8001).

        The Admin API is only available on the fixed Admin server port (8001).
        An injected Admin configuration is used as-is; otherwise the main client
        is reused when it already targets port 8001 or runs on Cloud (every API
        routes through the single port-443 connection), and a separate
        HttpClient is lazily created in the remaining case.
        """
        if self._admin_http is not None:
            return self._admin_http
        config = self._http.config
        if config.cloud is not None or config.port == MARKLOGIC_ADMIN_API_PORT:
            return self._http
        self._admin_http = self._create_secondary_http(MARKLOGIC_ADMIN_API_PORT)
        return self._admin_http

    def _create_secondary_http(self, port: int) -> HttpClient:
        """Create and optionally connect a secondary HttpClient."""
        http = HttpClient(config=self._http.config.clone(port=port))
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
    - ``ml.transaction(database=...)`` -- open a scoped transaction (context manager)
    """

    def __init__(
        self,
        protocol=UNSET,
        host: str = "localhost",
        port=UNSET,
        auth: AuthParam = UNSET,
        username: str = "admin",
        password: str = "admin",
        ssl: SSLConfig | None = None,
        cloud: CloudConfig | None = None,
        retry: Retry | None = None,
        *,
        config: HTTPConfig | None = None,
        manage_config: HTTPConfig | None = None,
        admin_config: HTTPConfig | None = None,
    ):
        """Initialize AsyncMLClient instance.

        The connection parameters describe the primary connection. The Manage
        (8002) and Admin (8001) connections are derived from it by default; pass
        ``manage_config`` / ``admin_config`` only to point them at a different
        host, credentials or port.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8000
            An App Service port
        auth : str | httpx.Auth | AuthConfig | None, default "digest"
            An authentication method: a string shortcut ("basic", "digest",
            "digestbasic", "certificate", "kerberos"), an AuthConfig, a custom
            httpx.Auth, or None
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        ssl : SSLConfig | None, default None
            SSL/TLS configuration; a client certificate forces HTTPS and
            defaults the auth method to "certificate"
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration; forces HTTPS on port 443 and handles
            authentication via the API key
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        config : HTTPConfig | None, default None
            An already-resolved primary configuration; when given, the
            connection parameters above are ignored
        manage_config : HTTPConfig | None, default None
            An already-resolved Manage configuration; when given, it is used
            instead of deriving the Manage connection from the primary
        admin_config : HTTPConfig | None, default None
            An already-resolved Admin configuration; when given, it is used
            instead of deriving the Admin connection from the primary
        """
        self._http = AsyncHttpClient(
            protocol=protocol,
            host=host,
            port=port,
            auth=auth,
            username=username,
            password=password,
            ssl=ssl,
            cloud=cloud,
            retry=retry,
            config=config,
        )
        self._manage_http = (
            AsyncHttpClient(config=manage_config)
            if manage_config
            else self._create_secondary_async_http(MARKLOGIC_MANAGE_API_PORT)
        )
        self._admin_http = (
            AsyncHttpClient(config=admin_config)
            if admin_config
            else self._create_secondary_async_http(MARKLOGIC_ADMIN_API_PORT)
        )

    def _create_secondary_async_http(
        self,
        port: int,
    ) -> AsyncHttpClient:
        """Return a fixed-port client, reusing the main one when it fits.

        Cloud connections route every API through the single port-443
        connection via base_path, so the main client is reused. The main client
        is also reused when it already targets the requested fixed port.
        """
        config = self._http.config
        if config.cloud is not None or config.port == port:
            return self._http
        return AsyncHttpClient(config=config.clone(port=port))

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

    async def transaction(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
    ) -> AsyncTransactionService:
        """Open a multi-statement transaction and return a service scoped to it.

        Use as an async context manager to commit on a clean exit and roll back
        on error:

        >>> async with await ml.transaction(database="my-db") as txn:  # doctest: +SKIP
        ...     await ml.eval.xquery("...", **txn)
        """
        return await async_open_transaction(
            AsyncApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
        )

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
        return RestartWaiter(self._http.config)
