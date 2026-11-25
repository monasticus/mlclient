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
    host: str
    port: int | UnsetType
    auth: AuthParam | UnsetType
    username: str
    password: str
    ssl: SSLConfig | None
    cloud: CloudConfig | None
    retry: Retry | int | None
    limits: httpx.Limits | int | None
    timeout: httpx.Timeout | float | UnsetType | None


class MLClientOptions(HTTPConfigOverrides, total=False):
    """HTTPConfig overrides plus the per-server configurations MLClient takes."""

    config: HTTPConfig | None
    manage_config: HTTPConfig | None
    admin_config: HTTPConfig | None
    health_config: HTTPConfig | None
