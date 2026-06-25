"""The HTTP Client module (HttpClient / AsyncHttpClient).

Exports sync and async HTTP clients for raw communication with MarkLogic.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from types import TracebackType

import httpx
from httpx import AsyncClient, AsyncHTTPTransport, Auth, Client, HTTPTransport, Response
from httpx_retries import Retry, RetryTransport

from mlclient import constants as const
from mlclient.auth import AuthParam, MarkLogicCloudAuth, build_auth
from mlclient.connection import (
    UNSET,
    CloudConfig,
    SSLConfig,
    default_auth,
    get_ssl_context,
    resolve_connection,
    validate_config,
)
from mlclient.mimetypes import Mimetypes
from mlclient.models import DocumentType

from .restart_waiter import RestartWaiter

logger = logging.getLogger(__name__)

MARKLOGIC_REST_API_PORT = 8000
MARKLOGIC_ADMIN_API_PORT = 8001
MARKLOGIC_MANAGE_API_PORT = 8002

DEFAULT_RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=0.5,
)
RESTART_RETRY_STRATEGY = Retry(
    total=12,
    allowed_methods=["GET"],
    status_forcelist=[
        httpx.codes.BAD_GATEWAY,
        httpx.codes.SERVICE_UNAVAILABLE,
        httpx.codes.GATEWAY_TIMEOUT,
    ],
    retry_on_exceptions=[
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    ],
    backoff_factor=1.0,
)


class HttpClientBase:
    """Shared base for sync and async HTTP clients.

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth : str | httpx.Auth | AuthConfig | None
        an authentication method
    username : str
        a username
    password : str
        a password
    ssl : SSLConfig | None
        SSL/TLS configuration
    cloud : CloudConfig | None
        MarkLogic Cloud configuration
    base_path : str | None
        a URL prefix prepended to every endpoint (MarkLogic Cloud)
    base_url : str
        a base url built based on the protocol, the host name and the port
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
    ):
        """Initialize HttpClientBase instance.

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
            SSL/TLS configuration
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        """
        connection = resolve_connection(protocol, port, ssl, cloud)
        auth = default_auth(auth, connection)
        validate_config(connection, auth)

        self.connection = connection
        self.protocol: str = connection.protocol
        self.host: str = host
        self.port: int = connection.port
        self.auth: AuthParam = auth
        self.username: str = username
        self.password: str = password
        self.ssl: SSLConfig | None = connection.ssl
        self.cloud: CloudConfig | None = connection.cloud
        self.base_path: str | None = cloud.base_path if cloud else None
        self.base_url: str = f"{self.protocol}://{host}:{self.port}"
        self._retry: Retry = retry or DEFAULT_RETRY_STRATEGY
        self._auth: Auth | None = self._build_auth()

    def _build_auth(self) -> Auth | None:
        """Build the httpx auth handler for this connection."""
        if self.connection.is_cloud:
            return MarkLogicCloudAuth(
                base_url=self.base_url,
                api_key=self.cloud.api_key,
                token_duration=self.cloud.token_duration,
                verify=self._verify(),
            )
        return build_auth(self.auth, self.username, self.password)

    def _verify(self):
        """Return the SSL verification setting for transport creation.

        Returns a shared SSL context, or ``False`` when verification is
        explicitly disabled (httpx interprets ``verify=False`` as no checks).
        """
        context = get_ssl_context(self.ssl or SSLConfig())
        return context if context is not None else False

    def _build_url(self, endpoint: str) -> str:
        """Build a full request URL, applying the Cloud base path if present."""
        if self.base_path:
            endpoint = f"/{self.base_path.strip('/')}/{endpoint.lstrip('/')}"
        return self.base_url + endpoint

    def _prepare_request(
        self,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> dict:
        """Prepare request details."""
        request = {
            "params": params or {},
            "headers": headers or {},
            "auth": self._auth,
        }
        if body is not None:
            content_type = (headers or {}).get(const.HEADER_NAME_CONTENT_TYPE)
            doc_type = Mimetypes.get_doc_type(content_type) if content_type else None
            if doc_type == DocumentType.JSON:
                request["json"] = body
            elif isinstance(body, Mapping):
                request["data"] = body
            else:
                request["content"] = body

        logger.debug(
            "Request details: %s",
            " ".join(
                f"{k} [{v if k != 'auth' else v.__class__.__name__}]"
                for k, v in request.items()
            ),
        )
        return request

    @classmethod
    def _log_response(
        cls,
        method: str,
        endpoint: str,
        response: Response,
    ):
        """Log response details and restart warning, if applicable."""
        logger.debug("Response retrieved")
        logger.fine(cls._format_http_response(response))

        if RestartWaiter.is_restart_response(response):
            logger.warning(
                "MarkLogic accepted %s %s and initiated a restart; "
                "Location [%s]. Wait for restart completion before "
                "sending follow-up requests",
                method,
                endpoint,
                response.headers.get("Location"),
            )

    @staticmethod
    def _format_http_response(
        response: Response,
    ) -> str:
        """Format an HTTP response in a protocol-like representation."""
        reason_phrase = httpx.codes.get_reason_phrase(response.status_code)
        start_line = f"HTTP/1.1 {response.status_code} {reason_phrase}"
        headers = "\n".join(f"{name}: {val}" for name, val in response.headers.items())
        if response.text:
            return f"{start_line}\n{headers}\n\n{response.text}"
        return f"{start_line}\n{headers}"


class HttpClient(HttpClientBase):
    """A low-level class used to send HTTP requests to a MarkLogic instance.

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth : str | httpx.Auth | AuthConfig | None
        an authentication method
    username : str
        a username
    password : str
        a password
    base_url : str
        a base url built based on the protocol, the host name and the port
    """

    def __init__(self, **kwargs):
        """Initialize HttpClient instance.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8000
            An App Service port
        auth : str | httpx.Auth | AuthConfig | None, default "digest"
            An authentication method
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        ssl : SSLConfig | None, default None
            SSL/TLS configuration
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        """
        super().__init__(**kwargs)
        self._client: Client | None = None

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

    def connect(self):
        """Start an HTTP session."""
        logger.debug("Initiating a connection with %s", self.base_url)
        transport = HTTPTransport(verify=self._verify())
        self._client = Client(
            transport=RetryTransport(transport=transport, retry=self._retry),
            follow_redirects=True,
        )

    def disconnect(self):
        """Close an HTTP session."""
        if self._client:
            logger.debug("Closing a connection")
            self._client.close()
            self._client = None

    def is_connected(self) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._client is not None

    def get(
        self,
        endpoint: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a GET request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a POST request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("POST", endpoint, body, params=params, headers=headers)

    def put(
        self,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a PUT request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("PUT", endpoint, body, params=params, headers=headers)

    def delete(
        self,
        endpoint: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send a DELETE request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return self.request("DELETE", endpoint, params=params, headers=headers)

    def request(
        self,
        method: str,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an HTTP request.

        Parameters
        ----------
        method : str
            An HTTP request method
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        request = self._prepare_request(params, headers, body)
        resp = self._send_request(method, endpoint, request)
        self._log_response(method, endpoint, resp)
        return resp

    def _send_request(
        self,
        method: str,
        endpoint: str,
        request: dict,
    ) -> Response:
        """Send a request."""
        logger.info("Sending a request... %s %s", method.upper(), endpoint)

        url = self._build_url(endpoint)
        if self.is_connected():
            return self._client.request(method, url, **request)

        logger.warning(
            "HttpClient is not connected -- "
            "A request will be sent in an ad-hoc initialized session (%s %s)",
            method.upper(),
            endpoint,
        )
        transport = HTTPTransport(verify=self._verify())
        with Client(
            transport=RetryTransport(transport=transport, retry=self._retry),
            follow_redirects=True,
        ) as client:
            return client.request(method, url, **request)


class AsyncHttpClient(HttpClientBase):
    """An async low-level class used to send HTTP requests to a MarkLogic instance.

    Attributes
    ----------
    protocol : str
        a protocol used for HTTP requests (http / https)
    host : str
        a host name
    port : int
        an App Service port
    auth : str | httpx.Auth | AuthConfig | None
        an authentication method
    username : str
        a username
    password : str
        a password
    base_url : str
        a base url built based on the protocol, the host name and the port
    """

    def __init__(self, **kwargs):
        """Initialize AsyncHttpClient instance.

        Parameters
        ----------
        protocol : str, default "http"
            A protocol used for HTTP requests (http / https)
        host : str, default "localhost"
            A host name
        port : int, default 8000
            An App Service port
        auth : str | httpx.Auth | AuthConfig | None, default "digest"
            An authentication method
        username : str, default "admin"
            A username
        password : str, default "admin"
            A password
        ssl : SSLConfig | None, default None
            SSL/TLS configuration
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration
        retry : Retry | None, default Retry(total=5, backoff_factor=0.5)
            A retry strategy
        """
        super().__init__(**kwargs)
        self._client: AsyncClient | None = None

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
        """Disconnect on async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Start an async HTTP session."""
        logger.debug("Initiating a connection with %s", self.base_url)
        transport = AsyncHTTPTransport(verify=self._verify())
        self._client = AsyncClient(
            transport=RetryTransport(transport=transport, retry=self._retry),
            follow_redirects=True,
        )

    async def disconnect(self):
        """Close an async HTTP session."""
        if self._client:
            logger.debug("Closing a connection")
            await self._client.aclose()
            self._client = None

    def is_connected(self) -> bool:
        """Return a connection status.

        Returns
        -------
        bool
            True if the client has started a connection; otherwise False
        """
        return self._client is not None

    async def get(
        self,
        endpoint: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an async GET request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return await self.request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an async POST request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return await self.request(
            "POST",
            endpoint,
            body,
            params=params,
            headers=headers,
        )

    async def put(
        self,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an async PUT request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return await self.request(
            "PUT",
            endpoint,
            body,
            params=params,
            headers=headers,
        )

    async def delete(
        self,
        endpoint: str,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an async DELETE request.

        Parameters
        ----------
        endpoint : str
            A REST endpoint to call
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        return await self.request("DELETE", endpoint, params=params, headers=headers)

    async def request(
        self,
        method: str,
        endpoint: str,
        body: str | dict | None = None,
        *,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Response:
        """Send an async HTTP request.

        Parameters
        ----------
        method : str
            An HTTP request method
        endpoint : str
            A REST endpoint to call
        body : str | dict | None
            A request body
        params : dict | None
            Request parameters
        headers : dict | None
            Request headers

        Returns
        -------
        Response
            An HTTP response
        """
        request = self._prepare_request(params, headers, body)
        resp = await self._send_request(method, endpoint, request)
        self._log_response(method, endpoint, resp)
        return resp

    async def _send_request(
        self,
        method: str,
        endpoint: str,
        request: dict,
    ) -> Response:
        """Send a request asynchronously."""
        logger.info("Sending a request... %s %s", method.upper(), endpoint)

        url = self._build_url(endpoint)
        if self.is_connected():
            return await self._client.request(method, url, **request)

        logger.warning(
            "AsyncHttpClient is not connected -- "
            "A request will be sent in an ad-hoc initialized session (%s %s)",
            method.upper(),
            endpoint,
        )
        transport = AsyncHTTPTransport(verify=self._verify())
        async with AsyncClient(
            transport=RetryTransport(transport=transport, retry=self._retry),
            follow_redirects=True,
        ) as client:
            return await client.request(method, url, **request)
