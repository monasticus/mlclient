from __future__ import annotations

import httpx
import pytest

from mlclient import MLClient
from mlclient.auth import AuthConfig, MarkLogicCloudAuth
from mlclient.connection import CloudConfig, SSLConfig
from mlclient.exceptions import ConfigError


def test_default_is_http_digest():
    ml = MLClient()
    assert ml.http.protocol == "http"
    assert ml.http.port == 8000
    assert ml.http.auth == "digest"
    assert isinstance(ml.http._auth, httpx.DigestAuth)


def test_https_server_cert_only():
    ml = MLClient(protocol="https", port=8003)
    assert ml.http.protocol == "https"
    assert ml.http.ssl is not None
    assert not ml.http.connection.is_mutual_tls


def test_client_cert_infers_certificate_auth():
    ml = MLClient(
        host="ml.example.com",
        port=8003,
        ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
    )
    assert ml.http.protocol == "https"
    assert ml.http.auth == "certificate"
    assert ml.http._auth is None


def test_explicit_certificate_string_with_mutual_tls():
    ml = MLClient(
        host="ml.example.com",
        port=8003,
        auth="certificate",
        ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
    )
    assert ml.http.auth == "certificate"
    assert ml.http._auth is None


def test_certificate_string_without_client_cert_raises():
    with pytest.raises(ConfigError):
        MLClient(auth="certificate")


def test_client_cert_with_explicit_digest_is_double_auth():
    ml = MLClient(
        host="ml.example.com",
        port=8003,
        auth="digest",
        ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
    )
    assert ml.http.protocol == "https"
    assert isinstance(ml.http._auth, httpx.DigestAuth)


def test_cloud_forces_https_443_and_internal_auth():
    ml = MLClient(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )
    assert ml.http.protocol == "https"
    assert ml.http.port == 443
    assert ml.http.base_path == "/ml/example/manage"
    assert isinstance(ml.http._auth, MarkLogicCloudAuth)


def test_cloud_reuses_main_client_for_manage_and_admin():
    ml = MLClient(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )
    assert ml._get_manage_http() is ml.http
    assert ml._get_admin_http() is ml.http


def test_oauth_auth_config():
    ml = MLClient(auth=AuthConfig(method="oauth", token="jwt-token"))
    assert ml.http._auth.__class__.__name__ == "OAuthBearerAuth"


def test_application_level_auth_none():
    ml = MLClient(auth=None)
    assert ml.http._auth is None


def test_custom_httpx_auth_passthrough():
    custom = httpx.BasicAuth("u", "p")
    ml = MLClient(auth=custom)
    assert ml.http._auth is custom


def test_cloud_with_explicit_auth_raises():
    with pytest.raises(ConfigError):
        MLClient(
            host="x.marklogic.cloud",
            cloud=CloudConfig(api_key="mk-1", base_path="/p"),
            auth="digest",
        )


def test_cloud_with_http_raises():
    with pytest.raises(ConfigError):
        MLClient(
            host="x.marklogic.cloud",
            protocol="http",
            cloud=CloudConfig(api_key="mk-1", base_path="/p"),
        )


def test_cloud_with_custom_port_raises():
    with pytest.raises(ConfigError):
        MLClient(
            host="x.marklogic.cloud",
            port=8002,
            cloud=CloudConfig(api_key="mk-1", base_path="/p"),
        )


def test_certificate_auth_without_client_cert_raises():
    with pytest.raises(ConfigError):
        MLClient(auth=AuthConfig(method="certificate"))


def test_client_cert_over_http_raises():
    with pytest.raises(ConfigError):
        MLClient(
            protocol="http",
            ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
        )
