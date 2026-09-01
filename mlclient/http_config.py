"""The HTTP Configuration module.

This module exposes a single facade over the connection and authentication
layers: :class:`HTTPConfig`. A client resolves one HTTPConfig up front and then
carries it as the sole source of communication details - the base URL, the SSL
verification setting, the URL builder and the ready httpx auth handler.

HTTPConfig sits above the two focused layers it composes and does not replace
them:

    * ``mlclient.connection`` decides the transport mode (HTTP, HTTPS, mutual
      TLS or Cloud) and validates connection/auth combinations.
    * ``mlclient.auth`` turns an auth descriptor into an httpx.Auth handler.

The facade owns the order those steps run in, so a client no longer wires the
connection and auth functions together by hand.
"""

from __future__ import annotations

import ssl

import httpx
from httpx_retries import Retry

from mlclient.auth import AuthParam
from mlclient.connection import (
    UNSET,
    CloudConfig,
    ConnectionMode,
    SSLConfig,
    build_connection_auth,
    default_auth,
    resolve_connection,
    transport_verify,
    validate_config,
)

DEFAULT_RETRY_STRATEGY = Retry(
    total=5,
    backoff_factor=0.5,
)


class HTTPConfig:
    """Resolved connection and authentication details for a MarkLogic client.

    The single point a client reads its communication details from. It pairs
    the resolved transport mode with the ready httpx auth handler, so callers
    ask for ``base_url``, ``transport_verify()`` or ``auth`` rather than
    reconstructing them from loose parameters.

    ``auth`` is the built httpx.Auth handler applied to each request. The
    descriptor it was built from (a shortcut string, an AuthConfig, a custom
    handler or None) is retained internally so an independent variant can be
    derived via :meth:`clone`.
    """

    def __init__(
        self,
        connection: ConnectionMode,
        host: str,
        auth_method: AuthParam,
        auth: httpx.Auth | None,
        username: str,
        password: str,
        retry: Retry,
    ):
        """Initialize HTTPConfig from already-resolved parts.

        Prefer :meth:`resolve`, which runs the connection and auth layers to
        produce these parts. This initializer only stores them.
        """
        self._connection = connection
        self._host = host
        self._auth_method = auth_method
        self._auth = auth
        self._username = username
        self._password = password
        self._retry = retry

    @classmethod
    def resolve(
        cls,
        *,
        protocol=UNSET,
        host: str = "localhost",
        port=UNSET,
        auth: AuthParam = UNSET,
        username: str = "admin",
        password: str = "admin",
        ssl: SSLConfig | None = None,
        cloud: CloudConfig | None = None,
        retry: Retry | None = None,
    ) -> HTTPConfig:
        """Resolve connection and auth parameters into an HTTPConfig.

        Runs the connection layer (transport mode, defaulting, validation) and
        the auth layer (handler construction) in order, raising ConfigError on
        an unsupported connection/auth combination.

        Parameters
        ----------
        protocol : str | UNSET
            The requested protocol (http / https), or UNSET to auto-resolve.
        host : str, default "localhost"
            A host name.
        port : int | UNSET
            The requested port, or UNSET to auto-resolve.
        auth : str | httpx.Auth | AuthConfig | None | UNSET
            The auth descriptor, or UNSET to apply the connection default.
        username : str, default "admin"
            A username for credential-based methods.
        password : str, default "admin"
            A password for credential-based methods.
        ssl : SSLConfig | None, default None
            SSL/TLS configuration.
        cloud : CloudConfig | None, default None
            MarkLogic Cloud configuration.
        retry : Retry | None, default DEFAULT_RETRY_STRATEGY
            The retry strategy for transport creation.

        Returns
        -------
        HTTPConfig
            The resolved configuration.
        """
        connection = resolve_connection(protocol, port, ssl, cloud)
        auth_method = default_auth(auth, connection)
        validate_config(connection, auth_method)
        base_url = cls._build_base_url(connection.protocol, host, connection.port)
        auth = build_connection_auth(
            connection,
            auth_method,
            username,
            password,
            base_url,
        )
        return cls(
            connection,
            host,
            auth_method,
            auth,
            username,
            password,
            retry or DEFAULT_RETRY_STRATEGY,
        )

    @property
    def connection(self) -> ConnectionMode:
        """The resolved transport mode."""
        return self._connection

    @property
    def protocol(self) -> str:
        """The connection protocol (http / https)."""
        return self._connection.protocol

    @property
    def host(self) -> str:
        """The host name."""
        return self._host

    @property
    def port(self) -> int:
        """The connection port."""
        return self._connection.port

    @property
    def username(self) -> str:
        """The username for credential-based methods."""
        return self._username

    @property
    def password(self) -> str:
        """The password for credential-based methods."""
        return self._password

    @property
    def ssl(self) -> SSLConfig | None:
        """The SSL/TLS configuration, if any."""
        return self._connection.ssl

    @property
    def cloud(self) -> CloudConfig | None:
        """The MarkLogic Cloud configuration, if any."""
        return self._connection.cloud

    @property
    def base_path(self) -> str | None:
        """The URL prefix prepended to every endpoint (MarkLogic Cloud)."""
        return self._connection.cloud.base_path if self._connection.cloud else None

    @property
    def base_url(self) -> str:
        """The base URL built from protocol, host and port."""
        return self._build_base_url(self.protocol, self._host, self.port)

    @property
    def auth(self) -> httpx.Auth | None:
        """The httpx auth handler applied to each request, or None."""
        return self._auth

    @property
    def retry(self) -> Retry:
        """The retry strategy for transport creation."""
        return self._retry

    def transport_verify(self) -> ssl.SSLContext | bool:
        """Return the SSL verification setting for transport creation."""
        return transport_verify(self._connection)

    def build_url(self, endpoint: str) -> str:
        """Build a full request URL, applying the Cloud base path if present."""
        base_path = self.base_path
        if base_path:
            endpoint = f"/{base_path.strip('/')}/{endpoint.lstrip('/')}"
        return self.base_url + endpoint

    def clone(self, **overrides) -> HTTPConfig:
        """Return an independent config, overriding the given fields.

        Accepts any resolve() parameter (``port``, ``host``, ``auth``, ...);
        unspecified fields keep this config's values. The result is produced by
        a fresh resolve(), so it carries its own httpx.Auth handler and shares
        no mutable state with this instance - safe to hand to a separate client.

        Fixed-port siblings (Admin on 8001, Manage on 8002) use
        ``config.clone(port=...)``. Cloud routes every tier through its single
        port-443 connection, so a Cloud config yields itself unchanged.
        """
        if self._connection.is_cloud:
            return self
        base = {
            "protocol": self.protocol,
            "host": self._host,
            "port": self.port,
            "auth": self._auth_method,
            "username": self._username,
            "password": self._password,
            "ssl": self._connection.ssl,
            "cloud": self._connection.cloud,
            "retry": self._retry,
        }
        return self.resolve(**{**base, **overrides})

    @staticmethod
    def _build_base_url(protocol: str, host: str, port: int) -> str:
        """Build a base URL from its parts."""
        return f"{protocol}://{host}:{port}"
