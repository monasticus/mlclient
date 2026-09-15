"""The ML Client module (MLClient / AsyncMLClient).

Exports sync and async entry points for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient / AsyncHttpClient (raw HTTP on main port)
    - .rest     -> RestApi / AsyncRestApi (/v1/* on main port)
    - .manage   -> ManageApi / AsyncManageApi (/manage/v2/*, port 8002 by default)
    - .admin    -> AdminApi / AsyncAdminApi (/admin/v1/* on port 8001)
    - .healthcheck() -> HEAD / on the HealthCheck server (port 7997)
    - .parser   -> MLResponseParser
    - .documents, .eval -> higher-level services
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

from mlclient._options import UNSET
from mlclient.api.admin import AdminApi, AsyncAdminApi
from mlclient.api.manage import AsyncManageApi, ManageApi
from mlclient.api.rest import AsyncRestApi, RestApi
from mlclient.auth import AuthParam
from mlclient.clients._restart import _RestartWaiter
from mlclient.clients.api import ApiClient, AsyncApiClient
from mlclient.clients.http import _RESTART_RETRY_STRATEGY, AsyncHttpClient, HttpClient
from mlclient.connection import (
    MARKLOGIC_ADMIN_PORT,
    MARKLOGIC_HEALTHCHECK_PORT,
    MARKLOGIC_MANAGE_PORT,
    CloudConfig,
    SSLConfig,
)
from mlclient.exceptions import MarkLogicError
from mlclient.http import _HEALTH_TIMEOUT, NO_RETRY_STRATEGY, HTTPConfig
from mlclient.models.version import MarkLogicVersion
from mlclient.responses import MLResponseParser
from mlclient.services.documents import AsyncDocumentsService, DocumentsService
from mlclient.services.eval import AsyncEvalService, EvalService
from mlclient.services.transactions import (
    AsyncTransactionService,
    TransactionService,
    async_open_transaction,
    open_transaction,
)

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
    - ``ml.documents.read("/doc.json")`` -- higher-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- higher-level, parsed results
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

    Higher-level (services) - returns parsed Python objects:

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
        retry: Retry | int | None = None,
        limits: Limits | int | None = None,
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
        retry : Retry | int | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy; an int is shorthand for Retry(total=n)
        limits : httpx.Limits | int | None, default None
            Connection-pool limits; None defers to httpx's own default; an int
            is shorthand for httpx.Limits(max_connections=n)
        timeout : httpx.Timeout | float | None, default unset
            The request timeout. Unset uses DEFAULT_TIMEOUT (connect=5, read=60,
            write=60, pool=5 seconds). None disables every HTTP timeout. A number
            sets all four components to that many seconds. An httpx.Timeout fully
            overrides them without merging. The derived HealthCheck connection
            always uses _HEALTH_TIMEOUT, independent of this value
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
            no retries, _HEALTH_TIMEOUT) from the primary. Retry and timeout are
            resolved independently: an unspecified retry defaults to no retries
            and an unspecified timeout to _HEALTH_TIMEOUT, while an explicitly
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
            health_config.with_health_defaults()
            if health_config
            else self._http.config.clone(
                port=MARKLOGIC_HEALTHCHECK_PORT,
                auth=None,
                retry=NO_RETRY_STRATEGY,
                timeout=_HEALTH_TIMEOUT,
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
        """Raw HTTP access through the primary connection.

        Uses the main connection settings and returns raw httpx responses.
        Accessing this property sends no request; request methods open the
        session on demand. The client context manager owns its lifetime.

        Returns
        -------
        HttpClient
            The connection-bound API or service object.
        """
        return self._http

    @cached_property
    def rest(self) -> RestApi:
        """Client REST API on the primary connection (``/v1/*``).

        Requires a REST-enabled App Server. The wrapper is created once per
        client on first access; accessing it sends no request. Endpoint
        methods execute fresh requests and return raw httpx responses.

        Returns
        -------
        RestApi
            The connection-bound API or service object.
        """
        return RestApi(ApiClient(self._http))

    @cached_property
    def manage(self) -> ManageApi:
        """Management API on the configured Manage connection.

        Uses ``manage_config`` when supplied, otherwise the derived Manage
        connection (port 8002 by default). The wrapper is cached per client;
        its session opens on the first request, not when this property is read.

        Returns
        -------
        ManageApi
            The connection-bound API or service object.
        """
        return ManageApi(ApiClient(self._manage_http))

    @cached_property
    def admin(self) -> AdminApi:
        """Administration API on the configured Admin connection.

        Uses ``admin_config`` when supplied, otherwise the derived Admin
        connection (port 8001 by default). The wrapper is cached per client;
        its session opens on the first request, not when this property is read.

        Returns
        -------
        AdminApi
            The connection-bound API or service object.
        """
        return AdminApi(ApiClient(self._admin_http))

    def healthcheck(self, *, timeout=UNSET) -> bool:
        """Report whether the HealthCheck app server (port 7997 by default) is healthy.

        Sends a HEAD request to ``/`` on the HealthCheck connection.

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this probe. Unset uses the HealthCheck
            connection's timeout (five seconds per component by default). None
            disables every HTTP timeout; a number sets all four components to
            that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        bool
            True when the server answered 2xx, False when it answered 5xx

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        httpx.HTTPStatusError
            If the server answered with a 4xx status, which signals a
            misdirected request (the HealthCheck server takes no auth) rather
            than an unhealthy server
        """
        return _healthy_or_raise(self._health_http.head("/", timeout=timeout))

    @property
    def parser(self) -> type[MLResponseParser]:
        """Parse raw MarkLogic HTTP responses explicitly.

        Returns the parser class, not a parser instance. Call
        ``ml.parser.parse(response)`` for a response from the raw API.
        Parsing is local and performs no network requests.

        Returns
        -------
        type[MLResponseParser]
            The parser class.
        """
        return MLResponseParser

    @cached_property
    def documents(self) -> DocumentsService:
        """Read, write and delete documents as Python models.

        Uses the primary REST connection and returns parsed documents or
        metadata. The service is created once per client without network I/O.
        Each operation executes its own requests; document results are not cached.

        Returns
        -------
        DocumentsService
            The connection-bound API or service object.
        """
        return DocumentsService(self.rest)

    @cached_property
    def eval(self) -> EvalService:
        """Evaluate XQuery or JavaScript and parse the returned values.

        Uses the primary REST connection. The service is cached per client,
        not the query results: every evaluation sends a new request.
        Accessing this property alone performs no network I/O.

        Returns
        -------
        EvalService
            The connection-bound API or service object.
        """
        return EvalService(self.rest)

    @cached_property
    def version(self) -> MarkLogicVersion:
        """Complete MarkLogic version with four unpackable numeric parts.

        The first successful access performs network I/O and caches the value
        on this client instance. Later accesses do not contact the server, even
        after reconnecting; use a new client for a fresh server-version lookup.
        Failed lookups are not cached.

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

        Parameters
        ----------
        name : str | None, default None
            Optional server-side label; it is not the transaction identifier.
        time_limit : int | None, default None
            Server-side transaction lifetime in seconds. None uses the server
            default; this is independent of the HTTP timeout.
        database : str | None, default None
            Content database name or id. None uses the REST server's database.
        timeout : httpx.Timeout | float | None, default unset
            HTTP timeout for opening the transaction only. Unset inherits the
            connection setting; None disables the HTTP timeout.

        Returns
        -------
        TransactionService
            The newly opened transaction. Use its context manager to finish it;
            otherwise commit or roll it back explicitly. ``**txn`` forwards
            the transaction id and its database to content operations.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic rejects opening the transaction.
        """
        return open_transaction(
            ApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
            timeout=timeout,
        )

    def connect(self):
        """Open the primary local HTTP session.

        This allocates transport resources; it does not probe connectivity or
        authenticate with the server. Auxiliary sessions open on their first
        request. Prefer the client context manager for automatic cleanup.
        """
        self._http.connect()

    def disconnect(self):
        """Close the primary and auxiliary sessions owned by this client.

        Shared HTTP clients are closed once. Cached API/service wrappers are
        retained; a cached synchronous version value is not refreshed by closing
        or reopening the transport.
        """
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
            True if the primary local HTTP session is open; otherwise False.
            This does not probe the server or describe auxiliary session state.
            Use healthcheck() to probe the server.
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
            retry=retry or _RESTART_RETRY_STRATEGY,
        )

    def _get_restart_waiter(self) -> _RestartWaiter:
        return _RestartWaiter(self._http.config)

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
    - ``ml.documents.read("/doc.json")`` -- higher-level, parsed results
    - ``ml.eval.xquery("1+1")`` -- higher-level, parsed results
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
        retry: Retry | int | None = None,
        limits: Limits | int | None = None,
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
        retry : Retry | int | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy; an int is shorthand for Retry(total=n)
        limits : httpx.Limits | int | None, default None
            Connection-pool limits; None defers to httpx's own default; an int
            is shorthand for httpx.Limits(max_connections=n)
        timeout : httpx.Timeout | float | None, default unset
            The request timeout. Unset uses DEFAULT_TIMEOUT (connect=5, read=60,
            write=60, pool=5 seconds). None disables every HTTP timeout. A number
            sets all four components to that many seconds. An httpx.Timeout fully
            overrides them without merging. The derived HealthCheck connection
            always uses _HEALTH_TIMEOUT, independent of this value
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
            no retries, _HEALTH_TIMEOUT) from the primary. Retry and timeout are
            resolved independently: an unspecified retry defaults to no retries
            and an unspecified timeout to _HEALTH_TIMEOUT, while an explicitly
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
            health_config.with_health_defaults()
            if health_config
            else self._http.config.clone(
                port=MARKLOGIC_HEALTHCHECK_PORT,
                auth=None,
                retry=NO_RETRY_STRATEGY,
                timeout=_HEALTH_TIMEOUT,
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
        """Raw HTTP access through the primary connection.

        Uses the main connection settings and returns raw httpx responses.
        Accessing this property sends no request; request methods open the
        session on demand. The client context manager owns its lifetime.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncHttpClient
            The connection-bound API or service object.
        """
        return self._http

    @cached_property
    def rest(self) -> AsyncRestApi:
        """Client REST API on the primary connection (``/v1/*``).

        Requires a REST-enabled App Server. The wrapper is created once per
        client on first access; accessing it sends no request. Endpoint
        methods execute fresh requests and return raw httpx responses.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncRestApi
            The connection-bound API or service object.
        """
        return AsyncRestApi(AsyncApiClient(self._http))

    @cached_property
    def manage(self) -> AsyncManageApi:
        """Management API on the configured Manage connection.

        Uses ``manage_config`` when supplied, otherwise the derived Manage
        connection (port 8002 by default). The wrapper is cached per client;
        its session opens on the first request, not when this property is read.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncManageApi
            The connection-bound API or service object.
        """
        return AsyncManageApi(AsyncApiClient(self._manage_http))

    @cached_property
    def admin(self) -> AsyncAdminApi:
        """Administration API on the configured Admin connection.

        Uses ``admin_config`` when supplied, otherwise the derived Admin
        connection (port 8001 by default). The wrapper is cached per client;
        its session opens on the first request, not when this property is read.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncAdminApi
            The connection-bound API or service object.
        """
        return AsyncAdminApi(AsyncApiClient(self._admin_http))

    async def healthcheck(self, *, timeout=UNSET) -> bool:
        """Report whether the HealthCheck app server (port 7997 by default) is healthy.

        Sends a HEAD request to ``/`` on the HealthCheck connection.

        Parameters
        ----------
        timeout : httpx.Timeout | float | None, default unset
            A per-request timeout for this probe. Unset uses the HealthCheck
            connection's timeout (five seconds per component by default). None
            disables every HTTP timeout; a number sets all four components to
            that many seconds; an httpx.Timeout overrides them.

        Returns
        -------
        bool
            True when the server answered 2xx, False when it answered 5xx

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        httpx.HTTPStatusError
            If the server answered with a 4xx status, which signals a
            misdirected request (the HealthCheck server takes no auth) rather
            than an unhealthy server
        """
        return _healthy_or_raise(await self._health_http.head("/", timeout=timeout))

    @property
    def parser(self) -> type[MLResponseParser]:
        """Parse raw MarkLogic HTTP responses explicitly.

        Returns the parser class, not a parser instance. Call
        ``ml.parser.parse(response)`` for a response from the raw API.
        Parsing is local and performs no network requests.

        Returns
        -------
        type[MLResponseParser]
            The parser class.
        """
        return MLResponseParser

    @cached_property
    def documents(self) -> AsyncDocumentsService:
        """Read, write and delete documents as Python models.

        Uses the primary REST connection and returns parsed documents or
        metadata. The service is created once per client without network I/O.
        Each operation executes its own requests; document results are not cached.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncDocumentsService
            The connection-bound API or service object.
        """
        return AsyncDocumentsService(self.rest)

    @cached_property
    def eval(self) -> AsyncEvalService:
        """Evaluate XQuery or JavaScript and parse the returned values.

        Uses the primary REST connection. The service is cached per client,
        not the query results: every evaluation sends a new request.
        Accessing this property alone performs no network I/O.
        Access this property normally; asynchronous methods run when awaited.

        Returns
        -------
        AsyncEvalService
            The connection-bound API or service object.
        """
        return AsyncEvalService(self.rest)

    async def version(self) -> MarkLogicVersion:
        """Complete MarkLogic version with four unpackable numeric parts.

        Each ``await ml.version()`` performs a new lookup; no version value
        is cached by the asynchronous client.

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

        Parameters
        ----------
        name : str | None, default None
            Optional server-side label; it is not the transaction identifier.
        time_limit : int | None, default None
            Server-side transaction lifetime in seconds. None uses the server
            default; this is independent of the HTTP timeout.
        database : str | None, default None
            Content database name or id. None uses the REST server's database.
        timeout : httpx.Timeout | float | None, default unset
            HTTP timeout for opening the transaction only. Unset inherits the
            connection setting; None disables the HTTP timeout.

        Returns
        -------
        AsyncTransactionService
            The newly opened transaction. Use its context manager to finish it;
            otherwise commit or roll it back explicitly. ``**txn`` forwards
            the transaction id and its database to content operations.

        Raises
        ------
        httpx.TimeoutException
            If an HTTP connect, read, write or pool timeout expires after any
            configured retries are exhausted.
        MarkLogicError
            If MarkLogic rejects opening the transaction.
        """
        return await async_open_transaction(
            AsyncApiClient(self._http),
            name=name,
            time_limit=time_limit,
            database=database,
            timeout=timeout,
        )

    async def connect(self):
        """Open the primary local HTTP session.

        This allocates transport resources; it does not probe connectivity or
        authenticate with the server. Auxiliary sessions open on their first
        request. Prefer the client context manager for automatic cleanup.
        """
        await self._http.connect()

    async def disconnect(self):
        """Close the primary and auxiliary sessions owned by this client.

        Shared HTTP clients are closed once. Cached API/service wrappers are
        retained. Subsequent operations may open sessions again; use an async
        context manager to give their lifetime an explicit scope.
        """
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
            True if the primary local HTTP session is open; otherwise False.
            This does not probe the server or describe auxiliary session state.
            Use healthcheck() to probe the server.
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
            retry=retry or _RESTART_RETRY_STRATEGY,
        )

    def _get_restart_waiter(self) -> _RestartWaiter:
        return _RestartWaiter(self._http.config)


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


def _healthy_or_raise(response: Response) -> bool:
    """Turn a HealthCheck response into a healthy/unhealthy verdict.

    The HealthCheck server is unauthenticated and answers 200 when healthy; a
    5xx means it is up but not ready. A 4xx is never an unhealthy verdict but a
    misdirected request, so it is raised rather than silently read as False.
    """
    if response.is_client_error:
        response.raise_for_status()
    return response.is_success
