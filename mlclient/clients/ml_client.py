"""The ML Client module (MLClient / AsyncMLClient).

Exports sync and async entry points for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient / AsyncHttpClient (raw HTTP on main port)
    - .rest     -> RestApi / AsyncRestApi (/v1/* on main port)
    - .manage   -> ManageApi / AsyncManageApi (/manage/v2/*, always port 8002)
    - .admin    -> AdminApi / AsyncAdminApi (/admin/v1/* on port 8001)
    - .healthcheck() -> HEAD / on the HealthCheck server (port 7997)
    - .parser   -> MLResponseParser
    - .documents, .eval, .logs -> high-level services
    - .transaction() -> open a scoped transaction (context manager)
"""

from __future__ import annotations

import logging
from contextlib import suppress
from functools import cached_property
from types import TracebackType
from xml.etree import ElementTree

from httpx import Limits, RequestError, Response
from httpx_retries import Retry

from mlclient.api.admin_api import AdminApi, AsyncAdminApi
from mlclient.api.manage_api import AsyncManageApi, ManageApi
from mlclient.api.rest_api import AsyncRestApi, RestApi
from mlclient.auth import AuthParam
from mlclient.connection import UNSET, CloudConfig, SSLConfig
from mlclient.exceptions import MarkLogicError
from mlclient.http_config import HEALTH_TIMEOUT, HTTPConfig
from mlclient.ml_response_parser import MLResponseParser
from mlclient.models.version import MarkLogicVersion
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
    MARKLOGIC_ADMIN_PORT,
    MARKLOGIC_HEALTHCHECK_PORT,
    MARKLOGIC_MANAGE_PORT,
    NO_RETRY_STRATEGY,
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
    - ``ml.healthcheck()`` -- HEAD ``/`` on the HealthCheck server (port 7997)
    - ``ml.rest.call(SomeApiCall())`` -- advanced: custom Call objects
    - ``ml.parser.parse(resp)`` -- manual parsing of raw responses
    - ``ml.documents.read("/doc.json")`` -- high-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- high-level, parsed results
    - ``ml.logs.get(log_type=...)`` -- high-level, parsed results
    - ``ml.version`` -- complete MarkLogic version with four numeric parts
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
        limits: Limits | None = None,
        timeout=UNSET,
        *,
        config: HTTPConfig | None = None,
        manage_config: HTTPConfig | None = None,
        admin_config: HTTPConfig | None = None,
        health_config: HTTPConfig | None = None,
    ):
        """Initialize MLClient instance.

        The connection parameters describe the primary connection. The Manage
        (8002), Admin (8001) and HealthCheck (7997) connections are derived from it
        by default; pass ``manage_config`` / ``admin_config`` / ``health_config``
        only to point them at a different host, credentials or port. The derived
        HealthCheck connection targets port 7997 with no authentication.

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
        limits : httpx.Limits | None, default None
            Connection-pool limits; None defers to httpx's own default
        timeout : httpx.Timeout | float | None, default unset
            The request timeout. Unset uses DEFAULT_TIMEOUT (connect=5, read=60,
            write=60, pool=5 seconds). None disables every HTTP timeout. A number
            sets all four components to that many seconds. An httpx.Timeout fully
            overrides them without merging. The derived HealthCheck connection
            always uses HEALTH_TIMEOUT, independent of this value
        config : HTTPConfig | None, default None
            An already-resolved primary configuration; when given, the
            connection parameters above are ignored
        manage_config : HTTPConfig | None, default None
            An already-resolved Manage configuration; when given, it is used
            instead of deriving the Manage connection from the primary
        admin_config : HTTPConfig | None, default None
            An already-resolved Admin configuration; when given, it is used
            instead of deriving the Admin connection from the primary
        health_config : HTTPConfig | None, default None
            An already-resolved HealthCheck configuration; when given, it is used
            instead of deriving the HealthCheck connection (port 7997, no auth,
            no retries, HEALTH_TIMEOUT) from the primary. Retry and timeout are
            resolved independently: an unspecified retry defaults to no retries
            and an unspecified timeout to HEALTH_TIMEOUT, while an explicitly
            supplied retry strategy or timeout (including None to disable it) is
            preserved
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
            limits=limits,
            timeout=timeout,
            config=config,
        )
        self._manage_http = self._secondary_http(
            manage_config or self._http.config.clone(port=MARKLOGIC_MANAGE_PORT),
        )
        self._admin_http = self._secondary_http(
            admin_config or self._http.config.clone(port=MARKLOGIC_ADMIN_PORT),
        )
        self._health_http = self._secondary_http(
            _resolve_health_config(health_config)
            if health_config
            else self._http.config.clone(
                port=MARKLOGIC_HEALTHCHECK_PORT,
                auth=None,
                retry=NO_RETRY_STRATEGY,
                timeout=HEALTH_TIMEOUT,
            ),
        )

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
        return ManageApi(ApiClient(self._manage_http))

    @cached_property
    def admin(self) -> AdminApi:
        """Admin API (``/admin/v1/*``) - requires Admin server (port 8001)."""
        return AdminApi(ApiClient(self._admin_http))

    def healthcheck(self, *, timeout=UNSET) -> bool:
        """Report whether the HealthCheck app server (port 7997) is healthy.

        Sends a HEAD request to ``/`` on the HealthCheck connection.

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this probe. Unset uses the HealthCheck
            connection's timeout (HEALTH_TIMEOUT unless overridden). None
            disables every HTTP timeout; a number sets all four components to
            that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        bool
            True when the server answered 2xx, False when it answered 5xx

        Raises
        ------
        httpx.HTTPStatusError
            If the server answered with a 4xx status, which signals a
            misdirected request (the HealthCheck server takes no auth) rather
            than an unhealthy server
        """
        return _healthy_or_raise(self._health_http.head("/", timeout=timeout))

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
        return LogsService(ApiClient(self._manage_http))

    @cached_property
    def version(self) -> MarkLogicVersion:
        """Complete MarkLogic version with four unpackable numeric parts.

        Resolved from ``xdmp:version()``. When the connecting user lacks the
        eval privilege the query fails; the Manage and Admin server-config
        endpoints are then tried in turn. If every source fails the eval error
        is re-raised. A connection error propagates from the eval attempt --
        auxiliary servers are not queried for eval transport failures.
        Unavailable or malformed fallback responses are skipped.

        Returns
        -------
        MarkLogicVersion
            The full server version. ``parts`` always contains four components,
            with None for missing components; ``str()`` preserves the full version.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error and no fallback source succeeds
        RequestError
            If the eval request fails at the HTTP transport level
        ValueError
            If the eval result is not a recognizable version string
        """
        try:
            return MarkLogicVersion(self.eval.xquery("xdmp:version()"))
        except MarkLogicError:
            version = self._version_from_secondaries()
            if version is not None:
                return version
            raise

    def _version_from_secondaries(self) -> MarkLogicVersion | None:
        """Read the version from the Manage then the Admin server.

        Returns
        -------
        MarkLogicVersion | None
            The first usable version, or None when both endpoints fail.
            HTTP errors, transport failures and malformed responses are skipped.
        """
        with suppress(RequestError, ValueError, KeyError, TypeError):
            manage = self._manage_http.get(
                "/manage/v2/properties",
                headers={"Accept": "application/json"},
            )
            if manage.is_success:
                return MarkLogicVersion(manage.json()["version"])
        with suppress(RequestError, ValueError, ElementTree.ParseError):
            admin = self.admin.get_server_config()
            if admin.is_success:
                return MarkLogicVersion(_admin_config_version(admin.text))
        return None

    def transaction(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
        timeout=UNSET,
    ) -> TransactionService:
        """Open a multi-statement transaction and return a service scoped to it.

        Use as a context manager to commit on a clean exit and roll back on error:

        >>> with ml.transaction(database="my-db") as txn:  # doctest: +SKIP
        ...     ml.eval.xquery("...", **txn)

        ``timeout`` bounds only the HTTP request that opens the transaction:
        unset uses the client's configured timeout, None disables every HTTP
        timeout, a number sets all four components to that many seconds, and an
        httpx.Timeout overrides them. It is unrelated to ``time_limit``, the
        server-side lifetime of the transaction. Subsequent operations
        (status/commit/rollback and content ops run with ``**txn``) accept their
        own ``timeout``.
        """
        return open_transaction(
            ApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
            timeout=timeout,
        )

    def connect(self):
        """Start the primary session; auxiliary sessions open on first request."""
        self._http.connect()

    def disconnect(self):
        """Close all sessions owned by this client."""
        for http in {
            self._http,
            self._manage_http,
            self._admin_http,
            self._health_http,
        }:
            http.disconnect()

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

    def _secondary_http(self, config: HTTPConfig) -> HttpClient:
        """Reuse the primary session when its complete configuration matches."""
        if self._http.config.can_share_session(config):
            return self._http
        return HttpClient(config=config, session_owner=self._http)


class AsyncMLClient:
    """Async entry point for MarkLogic interaction.

    Provides layered access (all methods are async):

    - ``ml.http.get("/endpoint")`` -- raw HTTP
    - ``ml.rest.eval.post(xquery="...")`` -- mid-level REST API (``/v1/*``)
    - ``ml.manage.databases.get_list()`` -- mid-level Management API
    - ``ml.admin.get_timestamp()`` -- mid-level Admin API (``/admin/v1/*``)
    - ``ml.healthcheck()`` -- HEAD ``/`` on the HealthCheck server (port 7997)
    - ``ml.rest.call(SomeApiCall())`` -- advanced: custom Call objects
    - ``ml.parser.parse(resp)`` -- manual parsing of raw responses
    - ``ml.documents.read("/doc.json")`` -- high-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- high-level, parsed results
    - ``ml.logs.get(log_type=...)`` -- high-level, parsed results
    - ``await ml.version()`` -- complete MarkLogic version with four numeric parts
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
        limits: Limits | None = None,
        timeout=UNSET,
        *,
        config: HTTPConfig | None = None,
        manage_config: HTTPConfig | None = None,
        admin_config: HTTPConfig | None = None,
        health_config: HTTPConfig | None = None,
    ):
        """Initialize AsyncMLClient instance.

        The connection parameters describe the primary connection. The Manage
        (8002), Admin (8001) and HealthCheck (7997) connections are derived from it
        by default; pass ``manage_config`` / ``admin_config`` / ``health_config``
        only to point them at a different host, credentials or port. The derived
        HealthCheck connection targets port 7997 with no authentication.

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
        limits : httpx.Limits | None, default None
            Connection-pool limits; None defers to httpx's own default
        timeout : httpx.Timeout | float | None, default unset
            The request timeout. Unset uses DEFAULT_TIMEOUT (connect=5, read=60,
            write=60, pool=5 seconds). None disables every HTTP timeout. A number
            sets all four components to that many seconds. An httpx.Timeout fully
            overrides them without merging. The derived HealthCheck connection
            always uses HEALTH_TIMEOUT, independent of this value
        config : HTTPConfig | None, default None
            An already-resolved primary configuration; when given, the
            connection parameters above are ignored
        manage_config : HTTPConfig | None, default None
            An already-resolved Manage configuration; when given, it is used
            instead of deriving the Manage connection from the primary
        admin_config : HTTPConfig | None, default None
            An already-resolved Admin configuration; when given, it is used
            instead of deriving the Admin connection from the primary
        health_config : HTTPConfig | None, default None
            An already-resolved HealthCheck configuration; when given, it is used
            instead of deriving the HealthCheck connection (port 7997, no auth,
            no retries, HEALTH_TIMEOUT) from the primary. Retry and timeout are
            resolved independently: an unspecified retry defaults to no retries
            and an unspecified timeout to HEALTH_TIMEOUT, while an explicitly
            supplied retry strategy or timeout (including None to disable it) is
            preserved
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
            limits=limits,
            timeout=timeout,
            config=config,
        )
        self._manage_http = self._secondary_http(
            manage_config or self._http.config.clone(port=MARKLOGIC_MANAGE_PORT),
        )
        self._admin_http = self._secondary_http(
            admin_config or self._http.config.clone(port=MARKLOGIC_ADMIN_PORT),
        )
        self._health_http = self._secondary_http(
            _resolve_health_config(health_config)
            if health_config
            else self._http.config.clone(
                port=MARKLOGIC_HEALTHCHECK_PORT,
                auth=None,
                retry=NO_RETRY_STRATEGY,
                timeout=HEALTH_TIMEOUT,
            ),
        )

    def _secondary_http(self, config: HTTPConfig) -> AsyncHttpClient:
        """Reuse the primary session when its complete configuration matches."""
        if self._http.config.can_share_session(config):
            return self._http
        return AsyncHttpClient(config=config, session_owner=self._http)

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

    async def healthcheck(self, *, timeout=UNSET) -> bool:
        """Report whether the HealthCheck app server (port 7997) is healthy.

        Sends a HEAD request to ``/`` on the HealthCheck connection.

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this probe. Unset uses the HealthCheck
            connection's timeout (HEALTH_TIMEOUT unless overridden). None
            disables every HTTP timeout; a number sets all four components to
            that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        bool
            True when the server answered 2xx, False when it answered 5xx

        Raises
        ------
        httpx.HTTPStatusError
            If the server answered with a 4xx status, which signals a
            misdirected request (the HealthCheck server takes no auth) rather
            than an unhealthy server
        """
        return _healthy_or_raise(await self._health_http.head("/", timeout=timeout))

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

    async def version(self) -> MarkLogicVersion:
        """Complete MarkLogic version with four unpackable numeric parts.

        Resolved from ``xdmp:version()``. When the connecting user lacks the
        eval privilege the query fails; the Manage and Admin server-config
        endpoints are then tried in turn. If every source fails the eval error
        is re-raised. A connection error propagates from the eval attempt --
        auxiliary servers are not queried for eval transport failures.
        Unavailable or malformed fallback responses are skipped.

        Returns
        -------
        MarkLogicVersion
            The full server version. ``parts`` always contains four components,
            with None for missing components; ``str()`` preserves the full version.

        Raises
        ------
        MarkLogicError
            If MarkLogic returns an error and no fallback source succeeds
        RequestError
            If the eval request fails at the HTTP transport level
        ValueError
            If the eval result is not a recognizable version string
        """
        try:
            return MarkLogicVersion(await self.eval.xquery("xdmp:version()"))
        except MarkLogicError:
            version = await self._version_from_secondaries()
            if version is not None:
                return version
            raise

    async def _version_from_secondaries(self) -> MarkLogicVersion | None:
        """Read the version from the Manage then the Admin server.

        Returns
        -------
        MarkLogicVersion | None
            The first usable version, or None when both endpoints fail.
            HTTP errors, transport failures and malformed responses are skipped.
        """
        with suppress(RequestError, ValueError, KeyError, TypeError):
            manage = await self._manage_http.get(
                "/manage/v2/properties",
                headers={"Accept": "application/json"},
            )
            if manage.is_success:
                return MarkLogicVersion(manage.json()["version"])
        with suppress(RequestError, ValueError, ElementTree.ParseError):
            admin = await self.admin.get_server_config()
            if admin.is_success:
                return MarkLogicVersion(_admin_config_version(admin.text))
        return None

    async def transaction(
        self,
        *,
        name: str | None = None,
        time_limit: int | None = None,
        database: str | None = None,
        timeout=UNSET,
    ) -> AsyncTransactionService:
        """Open a multi-statement transaction and return a service scoped to it.

        Use as an async context manager to commit on a clean exit and roll back
        on error:

        >>> async with await ml.transaction(database="my-db") as txn:  # doctest: +SKIP
        ...     await ml.eval.xquery("...", **txn)

        ``timeout`` bounds only the HTTP request that opens the transaction:
        unset uses the client's configured timeout, None disables every HTTP
        timeout, a number sets all four components to that many seconds, and an
        httpx.Timeout overrides them. It is unrelated to ``time_limit``, the
        server-side lifetime of the transaction. Subsequent operations
        (status/commit/rollback and content ops run with ``**txn``) accept their
        own ``timeout``.
        """
        return await async_open_transaction(
            AsyncApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
            timeout=timeout,
        )

    async def connect(self):
        """Start the primary session; auxiliary sessions open on first request."""
        await self._http.connect()

    async def disconnect(self):
        """Close all sessions owned by this client."""
        for http in {
            self._http,
            self._manage_http,
            self._admin_http,
            self._health_http,
        }:
            await http.disconnect()

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


def _admin_config_version(server_config: str) -> str | None:
    """Extract the host version from an Admin server-config XML document.

    Parameters
    ----------
    server_config : str
        XML returned by the Admin server-config endpoint

    Returns
    -------
    str | None
        Version text, or None if the host version element is absent or empty

    Raises
    ------
    ElementTree.ParseError
        If the response is not well-formed XML
    """
    return ElementTree.fromstring(server_config).findtext("{*}version")


def _resolve_health_config(config: HTTPConfig) -> HTTPConfig:
    """Default an injected health config's unset retry and timeout independently.

    An unspecified retry falls back to NO_RETRY_STRATEGY and an unspecified
    timeout to HEALTH_TIMEOUT. An explicit value for either - including a
    timeout of None to disable it - is preserved.
    """
    overrides = {}
    if not config.has_explicit_retry:
        overrides["retry"] = NO_RETRY_STRATEGY
    if not config.has_explicit_timeout:
        overrides["timeout"] = HEALTH_TIMEOUT
    return config.clone(**overrides) if overrides else config


def _healthy_or_raise(response: Response) -> bool:
    """Turn a HealthCheck response into a healthy/unhealthy verdict.

    The HealthCheck server is unauthenticated and answers 200 when healthy; a
    5xx means it is up but not ready. A 4xx is never an unhealthy verdict but a
    misdirected request, so it is raised rather than silently read as False.
    """
    if response.is_client_error:
        response.raise_for_status()
    return response.is_success
