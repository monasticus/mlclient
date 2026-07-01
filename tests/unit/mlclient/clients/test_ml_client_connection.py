from __future__ import annotations

import httpx
import pytest
import respx

from mlclient import MLClient
from mlclient.auth import AuthConfig
from mlclient.connection import CloudConfig, SSLConfig
from mlclient.exceptions import ConfigError

_PROBE_ENDPOINT = "/v1/documents"
_DIGEST_CHALLENGE = (
    'Digest realm="MarkLogic", qop="auth", '
    'nonce="dcd98b7102dd2f0e8b11d0f600bfb0c093", '
    'opaque="5ccc069c403ebaf9f0171e9517f40e41"'
)


def test_default_is_http_digest():
    ml = MLClient()
    assert ml.http.protocol == "http"
    assert ml.http.port == 8000
    assert ml.http.auth == "digest"
    request = _probe_request(ml, digest_challenge=True)
    assert request.headers["Authorization"].startswith("Digest ")


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


def test_explicit_certificate_string_with_mutual_tls():
    ml = MLClient(
        host="ml.example.com",
        port=8003,
        auth="certificate",
        ssl=SSLConfig(cert_file="/client.pem", key_file="/client-key.pem"),
    )
    assert ml.http.auth == "certificate"


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
    assert ml.http.auth == "digest"


def test_cloud_forces_https_443_and_internal_auth():
    ml = MLClient(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )
    assert ml.http.protocol == "https"
    assert ml.http.port == 443
    assert ml.http.base_path == "/ml/example/manage"

    request = _cloud_probe_request(ml)
    assert request.headers["Authorization"] == "Bearer tok-1"


def test_cloud_routes_manage_and_admin_through_the_single_connection():
    base = "https://x.marklogic.cloud:443"
    with respx.mock:
        respx.post(f"{base}/token").mock(
            return_value=httpx.Response(200, json={"access_token": "tok-1"}),
        )
        manage = respx.get(
            f"{base}/ml/example/manage/manage/v2/databases",
        ).mock(return_value=httpx.Response(200, json={"database-default-list": {}}))
        admin = respx.get(
            f"{base}/ml/example/manage/admin/v1/timestamp",
        ).mock(return_value=httpx.Response(200, text="2026-01-01T00:00:00"))

        with MLClient(
            host="x.marklogic.cloud",
            cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
        ) as ml:
            ml.manage.databases.get_list()
            ml.admin.get_timestamp()

    # Both tiers reach the single cloud host over HTTPS (port 443, which httpx
    # leaves implicit) rather than the on-premises manage/admin ports 8002/8001.
    for route in (manage, admin):
        request_url = route.calls.last.request.url
        assert request_url.host == "x.marklogic.cloud"
        assert request_url.scheme == "https"
        assert request_url.port is None


def test_oauth_auth_config():
    ml = MLClient(auth=AuthConfig(method="oauth", token="jwt-token"))
    request = _probe_request(ml)
    assert request.headers["Authorization"] == "Bearer jwt-token"


def test_application_level_auth_none():
    ml = MLClient(auth=None)
    request = _probe_request(ml)
    assert "Authorization" not in request.headers


def test_custom_httpx_auth_passthrough():
    ml = MLClient(auth=_HeaderAuth())
    request = _probe_request(ml)
    assert request.headers["X-Custom-Token"] == "custom"


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


class _HeaderAuth(httpx.Auth):
    def auth_flow(self, request: httpx.Request):
        request.headers["X-Custom-Token"] = "custom"
        yield request


def _probe_request(ml: MLClient, *, digest_challenge: bool = False) -> httpx.Request:
    """Return the request the client sends, captured against a mocked endpoint.

    Digest auth only sends its Authorization header after a 401 challenge, so the
    mocked endpoint replies with one before accepting the authorized retry.
    """
    url = f"{ml.http.base_url}{_PROBE_ENDPOINT}"
    with respx.mock:
        route = respx.get(url)
        if digest_challenge:
            route.side_effect = [
                httpx.Response(401, headers={"WWW-Authenticate": _DIGEST_CHALLENGE}),
                httpx.Response(200, text="ok"),
            ]
        else:
            route.mock(return_value=httpx.Response(200, text="ok"))
        with ml as client:
            client.http.get(_PROBE_ENDPOINT)
        return route.calls.last.request


def _cloud_probe_request(ml: MLClient) -> httpx.Request:
    """Return the authorized request a Cloud client sends after token exchange."""
    url = f"{ml.http.base_url}{ml.http.base_path}{_PROBE_ENDPOINT}"
    with respx.mock:
        respx.post(f"{ml.http.base_url}/token").mock(
            return_value=httpx.Response(200, json={"access_token": "tok-1"}),
        )
        route = respx.get(url).mock(return_value=httpx.Response(200, text="ok"))
        with ml as client:
            client.http.get(_PROBE_ENDPOINT)
        return route.calls.last.request
