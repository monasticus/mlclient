"""The Connection module.

This module models the transport layer of a MarkLogic connection, separately
from authentication. It exports:

    * SSLConfig
        SSL/TLS settings: server certificate verification and an optional
        client certificate for mutual TLS.
    * CloudConfig
        MarkLogic Cloud settings: API key, base path and token duration.
    * ConnectionMode
        The resolved transport mode (HTTP, HTTPS, mutual TLS or Cloud).
    * resolve_connection
        Determine the connection mode from the supplied parameters.
    * get_ssl_context
        A cached SSL context factory shared across all clients.
"""

from __future__ import annotations

import logging
import ssl
from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from mlclient.auth import auth_method_name
from mlclient.exceptions import ConfigError

if TYPE_CHECKING:
    from mlclient.auth import AuthParam

logger = logging.getLogger(__name__)

CLOUD_PROTOCOL = "https"
CLOUD_PORT = 443
DEFAULT_PROTOCOL = "http"
DEFAULT_PORT = 8000


class _Unset:
    """Sentinel marking an unset argument.

    For ``auth`` it distinguishes "the caller did not choose a method" (so
    connection defaults apply) from an explicit ``auth="digest"`` (which keeps
    digest even alongside a client certificate, yielding double auth). For
    ``protocol`` and ``port`` it distinguishes an omitted value (auto-resolved
    for Cloud or mutual TLS) from an explicit one that conflicts and must error.
    """

    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()


class SSLConfig(BaseModel):
    """SSL/TLS connection configuration."""

    verify: Union[bool, str] = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None
    key_password: Optional[str] = None

    @property
    def has_client_cert(self) -> bool:
        """Whether a client certificate is configured (mutual TLS)."""
        return self.cert_file is not None


class CloudConfig(BaseModel):
    """MarkLogic Cloud connection configuration."""

    model_config = ConfigDict(populate_by_name=True)

    api_key: str = Field(alias="api-key")
    base_path: str = Field(alias="base-path")
    token_duration: int = Field(alias="token-duration", default=0)


class ConnectionMode(BaseModel):
    """A resolved transport mode for a MarkLogic connection."""

    protocol: str
    port: int
    ssl: Optional[SSLConfig] = None
    cloud: Optional[CloudConfig] = None

    @property
    def is_cloud(self) -> bool:
        """Whether this is a MarkLogic Cloud connection."""
        return self.cloud is not None

    @property
    def is_mutual_tls(self) -> bool:
        """Whether this connection presents a client certificate."""
        return self.ssl is not None and self.ssl.has_client_cert

    @property
    def is_https(self) -> bool:
        """Whether this connection uses TLS."""
        return self.protocol == "https"


def resolve_connection(
    protocol,
    port,
    ssl: SSLConfig | None,
    cloud: CloudConfig | None,
) -> ConnectionMode:
    """Determine the connection mode from the supplied parameters.

    Cloud forces HTTPS on port 443. A client certificate forces HTTPS. A plain
    ``https`` protocol yields a server-cert-only connection. Everything else is
    plain HTTP. Omitted protocol/port (UNSET) auto-resolve; an explicit value
    that conflicts with Cloud or mutual TLS raises ConfigError.

    Parameters
    ----------
    protocol : str | UNSET
        The requested protocol (http / https), or UNSET if omitted.
    port : int | UNSET
        The requested port, or UNSET if omitted.
    ssl : SSLConfig | None
        SSL/TLS configuration, if any.
    cloud : CloudConfig | None
        MarkLogic Cloud configuration, if any.

    Returns
    -------
    ConnectionMode
        The resolved transport mode.

    Raises
    ------
    ConfigError
        If an explicit protocol or port conflicts with Cloud or mutual TLS.
    """
    if cloud is not None:
        return _resolve_cloud_connection(protocol, port, ssl, cloud)
    if ssl is not None and ssl.has_client_cert:
        if protocol == "http":
            msg = "Mutual TLS requires HTTPS; remove protocol='http'."
            raise ConfigError(msg)
        return ConnectionMode(protocol="https", port=_concrete_port(port), ssl=ssl)
    if protocol == "https":
        return ConnectionMode(
            protocol="https",
            port=_concrete_port(port),
            ssl=ssl or SSLConfig(),
        )
    return ConnectionMode(protocol=DEFAULT_PROTOCOL, port=_concrete_port(port))


def _resolve_cloud_connection(
    protocol,
    port,
    ssl: SSLConfig | None,
    cloud: CloudConfig,
) -> ConnectionMode:
    """Resolve a Cloud connection, rejecting conflicting protocol/port."""
    if protocol not in (UNSET, CLOUD_PROTOCOL):
        msg = f"Cloud connection requires HTTPS; remove protocol={protocol!r}."
        raise ConfigError(msg)
    if port not in (UNSET, CLOUD_PORT):
        msg = f"Cloud connection requires port {CLOUD_PORT}; remove port={port!r}."
        raise ConfigError(msg)
    return ConnectionMode(
        protocol=CLOUD_PROTOCOL,
        port=CLOUD_PORT,
        ssl=ssl,
        cloud=cloud,
    )


def _concrete_port(port) -> int:
    """Return the requested port, or the default when omitted."""
    return DEFAULT_PORT if isinstance(port, _Unset) else port


def default_auth(
    auth: AuthParam | _Unset,
    connection: ConnectionMode,
) -> AuthParam:
    """Resolve the default auth method for a connection when none was chosen.

    A Cloud connection handles auth internally, so it resolves to None. A
    mutual-TLS connection with no chosen auth defaults to certificate auth.
    Otherwise the default is digest, mirroring MarkLogic.

    Parameters
    ----------
    auth : str | httpx.Auth | AuthConfig | None | UNSET
        The chosen auth, or UNSET when the caller did not choose one.
    connection : ConnectionMode
        The resolved transport mode.

    Returns
    -------
    str | httpx.Auth | AuthConfig | None
        The effective auth parameter.
    """
    if not isinstance(auth, _Unset):
        return auth
    if connection.is_cloud:
        return None
    if connection.is_mutual_tls:
        return "certificate"
    return "digest"


def validate_config(
    connection: ConnectionMode,
    auth: AuthParam,
) -> None:
    """Reject invalid connection and authentication combinations.

    Invariants are enforced here, at client creation, rather than at request
    time. Combinations that are valid but risky (basic auth over plain HTTP)
    log a warning instead of raising.

    Parameters
    ----------
    connection : ConnectionMode
        The resolved transport mode.
    auth : str | httpx.Auth | AuthConfig | None
        The auth parameter being validated.

    Raises
    ------
    ConfigError
        If the combination is one MarkLogic cannot support.
    """
    method = auth_method_name(auth)

    if connection.is_cloud:
        _validate_cloud_connection(connection, auth)
        return

    if method == "certificate" and not connection.is_mutual_tls:
        msg = (
            "Certificate authentication requires HTTPS with a client "
            "certificate. Provide ssl=SSLConfig(cert_file=..., key_file=...)."
        )
        raise ConfigError(msg)

    if method == "basic" and not connection.is_https:
        logger.warning(
            "Basic auth over HTTP sends credentials in cleartext. "
            "Consider using HTTPS or digest auth.",
        )


def _validate_cloud_connection(
    connection: ConnectionMode,
    auth: AuthParam,
) -> None:
    """Reject invalid configuration for a MarkLogic Cloud connection."""
    if auth is not None:
        msg = (
            "Cloud connection handles authentication via API key. "
            "Do not set 'auth', 'username', or 'password'."
        )
        raise ConfigError(msg)
    if connection.is_mutual_tls:
        msg = "Cloud connection does not use client certificates."
        raise ConfigError(msg)


def get_ssl_context(ssl_config: SSLConfig) -> ssl.SSLContext | None:
    """Return a cached SSL context for the given SSL configuration.

    Returns ``None`` when verification is disabled, deferring to httpx's own
    ``verify=False`` handling. Caching avoids re-reading the system CA bundle
    from disk (~60-120 ms) on every transport creation.

    Parameters
    ----------
    ssl_config : SSLConfig
        SSL/TLS configuration: server verification and an optional client
        certificate for mutual TLS.

    Returns
    -------
    ssl.SSLContext | None
        A configured SSL context, or None when verification is disabled.
    """
    if ssl_config.verify is False:
        return None
    return _build_ssl_context(
        ssl_config.verify,
        ssl_config.cert_file,
        ssl_config.key_file,
        ssl_config.key_password,
    )


@lru_cache(maxsize=8)
def _build_ssl_context(
    verify: bool | str,
    cert_file: str | None,
    key_file: str | None,
    key_password: str | None,
) -> ssl.SSLContext:
    """Build an SSL context, cached by its hashable arguments.

    Kept separate from get_ssl_context because lru_cache requires hashable
    arguments and SSLConfig (a pydantic model) is not hashable.
    """
    if isinstance(verify, str):
        context = ssl.create_default_context(cafile=verify)
    else:
        context = ssl.create_default_context()
    if cert_file:
        context.load_cert_chain(cert_file, key_file, key_password)
    return context
