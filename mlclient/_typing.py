"""Keyword-argument sets that functions in several modules accept as ``**kwargs``.

A function annotated with ``**kwargs: Unpack[HTTPConfigOverrides]`` lets a type
checker verify each keyword it forwards to an HTTP configuration or a client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    import httpx
    from httpx_retries import Retry

    from mlclient._options import UnsetType
    from mlclient.auth import AuthParam
    from mlclient.connection import CloudConfig, SSLConfig
    from mlclient.http import HTTPConfig


class HTTPConfigOverrides(TypedDict, total=False):
    """Settings that replace those of an HTTPConfig, as HTTPConfig.clone takes them."""

    protocol: str | UnsetType
    """HTTP protocol override."""
    host: str
    """Server hostname override."""
    port: int | UnsetType
    """Server port override."""
    auth: AuthParam | UnsetType
    """Authentication method override."""
    username: str
    """Authentication username override."""
    password: str
    """Authentication password override."""
    ssl: SSLConfig | None
    """TLS configuration override."""
    cloud: CloudConfig | None
    """Cloud connection configuration override."""
    retry: Retry | int | None
    """Retry policy override."""
    limits: httpx.Limits | int | None
    """Connection pool limits override."""
    timeout: httpx.Timeout | float | UnsetType | None
    """Request timeout override; None disables the timeout."""


class MLClientOptions(HTTPConfigOverrides, total=False):
    """HTTPConfig overrides plus the per-server configurations MLClient takes."""

    config: HTTPConfig | None
    """Base REST server configuration."""
    manage_config: HTTPConfig | None
    """Management server configuration."""
    admin_config: HTTPConfig | None
    """Administration server configuration."""
    health_config: HTTPConfig | None
    """Health check server configuration."""
