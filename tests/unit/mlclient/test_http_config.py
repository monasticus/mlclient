from __future__ import annotations

import httpx
from httpx_retries import Retry

from mlclient.connection import CloudConfig, SSLConfig
from mlclient.http_config import HTTPConfig


def test_at_port_rebinds_non_cloud_connection():
    config = HTTPConfig.resolve(protocol="https", host="ml.example.com", port=8000)

    sibling = config.at_port(8002)

    assert sibling is not config
    assert sibling.port == 8002
    assert sibling.protocol == "https"
    assert sibling.host == "ml.example.com"


def test_at_port_preserves_auth_and_ssl():
    config = HTTPConfig.resolve(
        protocol="https",
        host="ml.example.com",
        auth="basic",
        username="reader",
        password="read123",
        ssl=SSLConfig(verify="/certs/ca.pem"),
    )

    sibling = config.at_port(8001)

    assert isinstance(sibling.auth, httpx.BasicAuth)
    assert sibling.ssl.verify == "/certs/ca.pem"


def test_at_port_on_cloud_returns_self():
    config = HTTPConfig.resolve(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )

    assert config.at_port(8002) is config


def test_at_port_carries_retry_strategy():
    strategy = Retry(total=3)
    config = HTTPConfig.resolve(host="ml.example.com", retry=strategy)

    assert config.at_port(8002).retry is strategy
