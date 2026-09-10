from __future__ import annotations

import httpx
import pytest
from httpx_retries import Retry

from mlclient.connection import UNSET, CloudConfig, SSLConfig
from mlclient.http_config import (
    DEFAULT_RETRY_STRATEGY,
    DEFAULT_TIMEOUT,
    HEALTH_TIMEOUT,
    NO_RETRY_STRATEGY,
    HTTPConfig,
)


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


def test_clone_carries_limits():
    limits = httpx.Limits(max_connections=5)
    config = HTTPConfig.resolve(host="ml.example.com", limits=limits)

    assert config.clone(port=8002).limits == limits


def test_unset_limits_defers_to_httpx():
    config = HTTPConfig.resolve()

    assert config.limits is None
    assert "limits" not in config.transport_options()


def test_explicit_limits_reach_the_transport():
    limits = httpx.Limits(max_connections=5)
    config = HTTPConfig.resolve(limits=limits)

    assert config.transport_options()["limits"] == limits


def test_clone_can_restore_unspecified_limits():
    config = HTTPConfig.resolve(limits=httpx.Limits(max_connections=5))

    sibling = config.clone(limits=None)

    assert sibling.limits is None
    assert config.limits is not None


def test_cloud_clone_applies_limits_without_changing_gateway():
    config = HTTPConfig.resolve(
        host="x.marklogic.cloud",
        cloud=CloudConfig(api_key="mk-1", base_path="/ml/example/manage"),
    )
    limits = httpx.Limits(max_connections=5)

    sibling = config.clone(port=7997, limits=limits)

    assert sibling.base_url == config.base_url
    assert sibling.limits == limits
    assert config.limits is None


def test_clone_carries_timeout():
    timeout = httpx.Timeout(1.0)
    config = HTTPConfig.resolve(host="ml.example.com", timeout=timeout)

    assert config.clone(port=8002).timeout == timeout


def test_timeout_resolves_default_when_unset():
    config = HTTPConfig.resolve()

    assert config.timeout == DEFAULT_TIMEOUT
    assert not config.has_explicit_timeout
    assert config.clone(port=8002).timeout == DEFAULT_TIMEOUT


def test_timeout_none_disables_every_component():
    config = HTTPConfig.resolve(timeout=None)

    assert config.has_explicit_timeout
    assert config.timeout == httpx.Timeout(None)
    assert config.clone(port=8002).timeout == httpx.Timeout(None)


@pytest.mark.parametrize("timeout", [30, 30.0, httpx.Timeout(30.0)])
def test_number_sets_all_four_components(timeout):
    config = HTTPConfig.resolve(timeout=timeout)

    assert config.has_explicit_timeout
    assert config.timeout == httpx.Timeout(30.0)


def test_timeout_configuration_is_isolated_from_input_and_clones():
    supplied = httpx.Timeout(30)
    config = HTTPConfig.resolve(timeout=supplied)
    clone = config.clone()
    supplied.read = 1
    config.timeout.write = 2

    assert config.timeout == httpx.Timeout(30)
    assert clone.timeout == httpx.Timeout(30)


def test_default_timeout_cannot_be_mutated_through_configuration():
    before = httpx.Timeout(DEFAULT_TIMEOUT)
    config = HTTPConfig.resolve()
    config.timeout.read = 1

    assert before == DEFAULT_TIMEOUT
    assert HTTPConfig.resolve().timeout == before


def test_limits_configuration_is_isolated_from_input_and_transport_options():
    limits = httpx.Limits(max_connections=5)
    config = HTTPConfig.resolve(limits=limits)
    clone = config.clone()
    limits.max_connections = 1
    config.limits.max_connections = 2
    config.transport_options()["limits"].max_connections = 3

    assert config.limits == httpx.Limits(max_connections=5)
    assert clone.limits == httpx.Limits(max_connections=5)


def test_clone_can_restore_unspecified_timeout():
    config = HTTPConfig.resolve(timeout=httpx.Timeout(1.0))

    sibling = config.clone(timeout=UNSET)

    assert sibling.timeout == DEFAULT_TIMEOUT
    assert not sibling.has_explicit_timeout


@pytest.mark.parametrize("timeout", [UNSET, None, 17])
@pytest.mark.parametrize("retry", [None, DEFAULT_RETRY_STRATEGY, Retry(total=2)])
def test_health_defaults_resolve_retry_and_timeout_independently(timeout, retry):
    config = HTTPConfig.resolve(timeout=timeout, retry=retry)
    health = config.with_health_defaults()

    assert health.retry is (NO_RETRY_STRATEGY if retry is None else retry)
    assert health.timeout == (
        HEALTH_TIMEOUT if timeout is UNSET else httpx.Timeout(timeout)
    )
    assert config.has_explicit_timeout is (timeout is not UNSET)
    assert config.has_explicit_retry is (retry is not None)
    health.timeout.read = 100
    assert httpx.Timeout(5) == HEALTH_TIMEOUT


@pytest.mark.parametrize(
    "overrides",
    [
        {"max_connections": 10},
        {"max_keepalive_connections": 3},
        {"keepalive_expiry": 30},
    ],
)
def test_session_sharing_rejects_a_difference_in_any_limit(overrides):
    values = {
        "max_connections": 5,
        "max_keepalive_connections": 2,
        "keepalive_expiry": 5,
    }
    config = HTTPConfig.resolve(limits=httpx.Limits(**values))
    other = HTTPConfig.resolve(limits=httpx.Limits(**{**values, **overrides}))

    assert not config.can_share_session(other)


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
        {"limits": httpx.Limits(max_connections=5)},
        {"timeout": httpx.Timeout(1.0)},
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


def test_session_sharing_compares_limits_values():
    limits = httpx.Limits(max_connections=5)
    config = HTTPConfig.resolve(limits=limits)
    assert config.can_share_session(config.clone())
    assert config.can_share_session(
        config.clone(limits=httpx.Limits(max_connections=5)),
    )


def test_session_sharing_compares_effective_timeout_components():
    config = HTTPConfig.resolve(timeout=httpx.Timeout(1.0))
    assert config.can_share_session(config.clone())
    assert config.can_share_session(config.clone(timeout=httpx.Timeout(1.0)))
    assert config.can_share_session(config.clone(timeout=1.0))
    assert not config.can_share_session(config.clone(timeout=httpx.Timeout(2.0)))
    assert not config.can_share_session(
        config.clone(timeout=httpx.Timeout(connect=1.0, read=1.0, write=1.0, pool=2.0)),
    )


def test_session_sharing_disabled_is_not_bounded():
    disabled = HTTPConfig.resolve(timeout=None)
    assert disabled.can_share_session(HTTPConfig.resolve(timeout=None))
    assert not disabled.can_share_session(HTTPConfig.resolve())


def test_session_sharing_ignores_timeout_explicitness_when_values_match():
    explicit_default = HTTPConfig.resolve(timeout=DEFAULT_TIMEOUT)
    assert explicit_default.can_share_session(HTTPConfig.resolve())


def test_session_sharing_shares_default_timeout():
    config = HTTPConfig.resolve()
    assert config.can_share_session(HTTPConfig.resolve())
