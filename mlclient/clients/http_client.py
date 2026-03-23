"""The HTTP Client module.

It exports the HttpClient class for raw HTTP communication with MarkLogic.
"""

from __future__ import annotations

import logging
import ssl
from collections.abc import Mapping
from types import TracebackType

import httpx
from httpx import Auth, BasicAuth, Client, DigestAuth, HTTPTransport, Response
from httpx_retries import Retry, RetryTransport

from mlclient import constants as const
from mlclient.mimetypes import Mimetypes
from mlclient.models import DocumentType

from .restart_waiter import RestartWaiter

logger = logging.getLogger(__name__)

MARKLOGIC_REST_API_PORT = 8000
MARKLOGIC_ADMIN_API_PORT = 8001
MARKLOGIC_MANAGE_API_PORT = 8002

# Reuse a single SSL context across all clients. Without this, every
# HTTPTransport() call invokes ssl.SSLContext.load_verify_locations which
# re-reads the system CA bundle from disk (~60-120 ms each).
_SHARED_SSL_CONTEXT = ssl.create_default_context()

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


class HttpClient:
    """A low-level class used to send HTTP requests to a MarkLogic instance.

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
        """Initialize HttpClient instance.

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
        self.protocol: str = protocol
        self.host: str = host
        self.port: int = port
        self.auth_method: str = auth_method
        self.username: str = username
        self.password: str = password
        self.base_url: str = f"{protocol}://{host}:{port}"
        self._retry: Retry = retry or DEFAULT_RETRY_STRATEGY
        self._client: Client | None = None
        auth_impl = BasicAuth if auth_method == "basic" else DigestAuth
        self._auth: Auth = auth_impl(username, password)

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
        transport = HTTPTransport(verify=_SHARED_SSL_CONTEXT)
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

    def _prepare_request(
        self,
        params: dict | None = None,
        headers: dict | None = None,
        body: str | dict | None = None,
    ) -> dict:
        """Prepare a request details."""
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

    def _send_request(
        self,
        method: str,
        endpoint: str,
        request: dict,
    ) -> Response:
        """Send a request."""
        logger.info("Sending a request... %s %s", method.upper(), endpoint)

        url = self.base_url + endpoint
        if self.is_connected():
            return self._client.request(method, url, **request)

        logger.warning(
            "HttpClient is not connected -- "
            "A request will be sent in an ad-hoc initialized session (%s %s)",
            method.upper(),
            endpoint,
        )
        transport = httpx.HTTPTransport(verify=_SHARED_SSL_CONTEXT)
        with Client(
            transport=RetryTransport(transport=transport, retry=self._retry),
            follow_redirects=True,
        ) as client:
            return client.request(method, url, **request)

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
