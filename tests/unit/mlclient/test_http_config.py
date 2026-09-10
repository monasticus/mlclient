from __future__ import annotations

import httpx
import pytest
from httpx_retries import Retry

from mlclient.connection import CloudConfig, SSLConfig
from mlclient.http_config import DEFAULT_RETRY_STRATEGY, HTTPConfig


def test_clone_rebinds_non_cloud_connection():
    config = HTTPConfig.resolve(protocol="https", host="ml.example.com", port=8000)

    sibling = config.clone(port=8002)

    assert sibling is not config
    assert sibling.port == 8002
    assert sibling.protocol == "https"
    assert sibling.host == "ml.example.com"


def test_clone_preserves_auth_and_ssl():
    config = HTTPConfig.resolve(
        protocol="https",
        host="ml.example.com",
        auth="basic",
        username="reader",
        password="read123",
        ssl=SSLConfig(verify="/certs/ca.pem"),
    )

    sibling = config.clone(port=8001)

    assert isinstance(sibling.auth, httpx.BasicAuth)
    assert sibling.ssl.verify == "/certs/ca.pem"


def test_clone_produces_a_fresh_auth_handler():
    config = HTTPConfig.resolve(host="ml.example.com", auth="digest")

    sibling = config.clone(port=8002)

    assert sibling.auth is not config.auth


def test_clone_overrides_arbitrary_fields():
    config = HTTPConfig.resolve(host="ml.example.com", username="admin")

    sibling = config.clone(host="other.example.com", username="reader")

    assert sibling.host == "other.example.com"
    assert sibling.username == "reader"
    assert config.host == "ml.example.com"


def test_clone_on_cloud_returns_self():
    config = HTTPConfig.resolve(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )

    assert config.clone(port=8002) is config


def test_clone_carries_retry_strategy():
    strategy = Retry(total=3)
    config = HTTPConfig.resolve(host="ml.example.com", retry=strategy)

    assert config.clone(port=8002).retry is strategy


@pytest.mark.parametrize("retry", [None, DEFAULT_RETRY_STRATEGY, Retry(total=0)])
def test_retry_retains_whether_it_was_explicit(retry):
    config = HTTPConfig.resolve(retry=retry)
    sibling = config.clone(port=8002)

    assert config.retry is (retry if retry is not None else DEFAULT_RETRY_STRATEGY)
    assert config.has_explicit_retry is (retry is not None)
    assert sibling.retry is config.retry
    assert sibling.has_explicit_retry is config.has_explicit_retry


def test_clone_can_restore_unspecified_retry():
    config = HTTPConfig.resolve(retry=Retry(total=0))

    sibling = config.clone(retry=None)

    assert sibling.retry is DEFAULT_RETRY_STRATEGY
    assert sibling.has_explicit_retry is False
    assert config.has_explicit_retry is True


def test_cloud_clone_applies_retry_without_changing_gateway():
    config = HTTPConfig.resolve(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )
    retry = Retry(total=0)

    sibling = config.clone(port=7997, retry=retry)

    assert sibling is not config
    assert sibling.base_url == config.base_url
    assert sibling.base_path == config.base_path
    assert sibling.retry is retry
    assert sibling.has_explicit_retry is True
    assert config.has_explicit_retry is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"host": "other.example.com"},
        {"port": 9999},
        {"protocol": "https"},
        {"auth": None},
        {"username": "other"},
        {"password": "other"},
        {"ssl": SSLConfig(verify=False), "protocol": "https"},
        {"retry": Retry(total=0)},
    ],
)
def test_session_sharing_rejects_different_settings(overrides):
    config = HTTPConfig.resolve()
    assert not config.can_share_session(config.clone(**overrides))


def test_session_sharing_matches_resolved_values():
    config = HTTPConfig.resolve(auth="basic")
    assert config.can_share_session(HTTPConfig.resolve(auth="basic"))
    assert config.can_share_session(config.clone())


def test_session_sharing_requires_same_custom_auth_and_retry():
    auth = httpx.BasicAuth("user", "pass")
    retry = Retry(total=2)
    config = HTTPConfig.resolve(auth=auth, retry=retry)
    assert config.can_share_session(config.clone())
    assert not config.can_share_session(
        config.clone(auth=httpx.BasicAuth("user", "pass")),
    )
    assert not config.can_share_session(config.clone(retry=Retry(total=2)))
