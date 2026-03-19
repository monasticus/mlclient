"""The ML Client module.

It exports the MLClient class - the main entry point for MarkLogic interaction
using a layered composition architecture:
    - .http     -> HttpClient (raw HTTP)
    - .rest     -> RestApi (/v1/* endpoints)
    - .manage   -> ManageApi (/manage/v2/* endpoints)
    - .parser   -> MLResponseParser
    - .documents, .eval, .logs -> high-level services
"""

from __future__ import annotations

from functools import cached_property
from types import TracebackType

from httpx import Response
from httpx_retries import Retry

from mlclient.api.manage_api import ManageApi
from mlclient.api.rest_api import RestApi
from mlclient.ml_response_parser import MLResponseParser
from mlclient.services.documents import DocumentsService
from mlclient.services.eval import EvalService
from mlclient.services.logs import LogsService

from .http_client import (
    MARKLOGIC_MANAGE_API_PORT,
    HttpClient,
)
from .rest_client import RestClient


class MLClient:
    """Main entry point for MarkLogic interaction.

    Provides layered access:
    - ml.http.get("/endpoint")              # raw HTTP
    - ml.rest.eval.post(xquery="...")       # mid-level REST API (/v1/*)
    - ml.manage.databases.get_list()        # mid-level Management API (/manage/v2/*)
    - ml.rest.call(SomeRestCall())          # advanced: custom Call objects
    - ml.parser.parse(resp)                 # manual parsing of raw responses
    - ml.documents.read("/doc.json")        # high-level, parsed results
    - ml.eval.xquery("1+1")                # high-level, parsed results
    - ml.logs.get(log_type=...)             # high-level, parsed results

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth_method : str
        an authorization method (basic / digest)
    username : str
        a username
    password : str
        a password
    base_url : str
        a base url built based on the protocol, the host name and the port

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
    ...         headers={"Content-Type": "..."},
    ...         body="xquery=xdmp:database()",
    ...     )
    ...     resp.status_code
    200

    Mid-level REST API (/v1/*) - returns httpx.Response:

    >>> with MLClient(**config) as ml:
    ...     resp = ml.rest.eval.post(
    ...         xquery="xdmp:database() => xdmp:database-name()",
    ...     )
    ...     resp.status_code
    200

    Mid-level Management API (/manage/v2/*) - returns httpx.Response:

    >>> with MLClient(**config) as ml:
    ...     resp = ml.manage.databases.get_list()
    ...     resp.status_code
    200

    Response parsing:

    >>> from mlclient import MLClient, MLResponseParser
    >>> with MLClient(**config) as ml:
    ...     resp = ml.rest.eval.post(
    ...         xquery="xdmp:database() => xdmp:database-name()",
    ...     )
    ...     parsed = MLResponseParser.parse(resp)
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
        manage_port: int | None = None,
    ):
        self._http = HttpClient(
            protocol=protocol,
            host=host,
            port=port,
            auth_method=auth_method,
            username=username,
            password=password,
            retry=retry,
        )
        self._rest_client = RestClient(self._http)
        self._manage_port = manage_port
        self._manage_http = None
        self._manage_rest_client = None

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
        """REST API (/v1/*) - requires REST app server."""
        return RestApi(self._rest_client)

    @cached_property
    def manage(self) -> ManageApi:
        """Management API (/manage/v2/*) - requires Manage server."""
        return ManageApi(self._get_manage_client())

    @property
    def parser(self) -> type[MLResponseParser]:
        """Response parser for manual parsing of raw responses."""
        return MLResponseParser

    @cached_property
    def documents(self) -> DocumentsService:
        """High-level documents service."""
        return DocumentsService(self._rest_client)

    @cached_property
    def eval(self) -> EvalService:
        """High-level eval service."""
        return EvalService(self._rest_client)

    @cached_property
    def logs(self) -> LogsService:
        """High-level logs service."""
        return LogsService(self._get_manage_client())

    def connect(self):
        """Start an HTTP session."""
        self._http.connect()
        if self._manage_http is not None:
            self._manage_http.connect()

    def disconnect(self):
        """Close an HTTP session."""
        self._http.disconnect()
        if self._manage_http is not None:
            self._manage_http.disconnect()

    def is_connected(self) -> bool:
        """Return a connection status."""
        return self._http.is_connected()

    def wait_for_restart(
        self,
        response: Response | None = None,
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
        self._http.wait_for_restart_completion(response, timeout, poll_interval, retry)

    def _get_manage_client(self) -> RestClient:
        """Return RestClient for manage API (lazy init if separate port)."""
        if self._manage_port is None or self._manage_port == self._http.port:
            return self._rest_client
        if self._manage_rest_client is None:
            self._manage_http = HttpClient(
                protocol=self._http.protocol,
                host=self._http.host,
                port=self._manage_port,
                auth_method=self._http.auth_method,
                username=self._http.username,
                password=self._http.password,
            )
            if self.is_connected():
                self._manage_http.connect()
            self._manage_rest_client = RestClient(self._manage_http)
        return self._manage_rest_client
