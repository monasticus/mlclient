import httpx
import pytest
import respx
from httpx_retries import Retry

from mlclient import AsyncMLClient, MLClient, MLClientManager, MLEnvironment
from mlclient.clients import AsyncHttpClient, HttpClient
from mlclient.clients import http_client as http_client_module
from mlclient.connection import UNSET
from mlclient.clients.http_client import NO_RETRY_STRATEGY
from mlclient.http_config import DEFAULT_RETRY_STRATEGY, DEFAULT_TIMEOUT, HEALTH_TIMEOUT
from mlclient.exceptions import (
    NoRestServerConfiguredError,
    NoSuchAppServerError,
)
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture(autouse=True)
def ml_config() -> MLEnvironment:
    config = {
        "app-name": "my-marklogic-app",
        "host": "localhost",
        "username": "my-marklogic-app-user",
        "password": "my-marklogic-app-password",
        "protocol": "https",
        "app-servers": [
            {
                "id": "manage",
                "port": 8002,
                "auth": "basic",
                "rest": True,
            },
            {
                "id": "content",
                "port": 8100,
                "auth": "basic",
                "rest": True,
            },
            {
                "id": "modules",
                "port": 8101,
                "auth": "basic",
            },
            {
                "id": "schemas",
                "port": 8102,
                "auth": "basic",
            },
            {
                "id": "test",
                "port": 8103,
                "auth": "basic",
                "rest": True,
            },
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def ml_config_no_rest() -> MLEnvironment:
    config = {
        "app-name": "my-marklogic-app",
        "host": "localhost",
        "username": "my-marklogic-app-user",
        "password": "my-marklogic-app-password",
        "protocol": "https",
        "app-servers": [
            {
                "id": "app-services",
                "rest": False,
            },
            {
                "id": "manage",
                "port": 8002,
                "auth": "basic",
            },
            {
                "id": "content",
                "port": 8100,
                "auth": "basic",
            },
            {
                "id": "modules",
                "port": 8101,
                "auth": "basic",
            },
            {
                "id": "schemas",
                "port": 8102,
                "auth": "basic",
            },
            {
                "id": "test",
                "port": 8103,
                "auth": "basic",
            },
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config, ml_config_no_rest):
    # Setup
    original_method = MLEnvironment.load

    def load_env(env_name: str):
        if env_name == "test":
            return ml_config
        if env_name == "test-no-rest":
            return ml_config_no_rest
        return original_method(env_name)

    target = "mlclient.ml_environment.MLEnvironment.load"
    mocker.patch(target, side_effect=load_env)


def test_properties():
    mgr = MLClientManager("test")

    assert mgr.env_name == "test"

    expected_config = MLEnvironment.load("test")
    assert mgr.config.model_dump() == expected_config.model_dump()


@pytest.mark.parametrize(
    "factory",
    ["get_client", "get_async_client", "get_http_client", "get_async_http_client"],
)
def test_health_defaults_and_overrides_apply_to_every_factory(factory):
    manager = MLClientManager("test-no-rest")
    client = getattr(manager, factory)("health")
    http = client if isinstance(client, (HttpClient, AsyncHttpClient)) else client.http
    assert http.config.retry is NO_RETRY_STRATEGY
    assert http.config.auth is None
    assert http.config.port == 7997

    customized = getattr(manager, factory)("health", retry=DEFAULT_RETRY_STRATEGY)
    http = (
        customized
        if isinstance(customized, (HttpClient, AsyncHttpClient))
        else customized.http
    )
    assert http.config.retry is DEFAULT_RETRY_STRATEGY


def test_config_override_precedence_and_environment_isolation():
    retry = Retry(total=2)
    manager = MLClientManager("test", host="gateway.example.com", retry=retry)
    original = manager.config
    config = manager.get_config("content", port=9100, username="custom")
    assert config.host == "gateway.example.com"
    assert config.port == 9100
    assert config.username == "custom"
    assert config.retry is retry
    assert manager.get_config("health").retry is retry
    assert manager.get_config("health", retry=None).retry is NO_RETRY_STRATEGY
    assert manager.get_config("content", retry=None).retry is DEFAULT_RETRY_STRATEGY
    assert manager.get_config("content").port == 8100
    assert manager.config == original


def test_timeout_defaults_per_server_kind_without_manager_override():
    manager = MLClientManager("test")

    assert manager.get_config("content").timeout == DEFAULT_TIMEOUT
    assert not manager.get_config("content").has_explicit_timeout
    assert manager.get_config("health").timeout == HEALTH_TIMEOUT


def test_manager_timeout_applies_to_every_server_including_health():
    manager = MLClientManager("test", timeout=30)

    assert manager.get_config("content").timeout == httpx.Timeout(30.0)
    assert manager.get_config("health").timeout == httpx.Timeout(30.0)
    assert manager.get_config("health").has_explicit_timeout


def test_factory_call_timeout_overrides_manager_and_unset_inherits_it():
    manager = MLClientManager("test", timeout=30)

    assert manager.get_config("content", timeout=5).timeout == httpx.Timeout(5.0)
    assert manager.get_config("content", timeout=UNSET).timeout == httpx.Timeout(30.0)


def test_timeout_none_disables_at_manager_and_call_level():
    disabled_manager = MLClientManager("test", timeout=None)
    assert disabled_manager.get_config("content").timeout == httpx.Timeout(None)
    assert disabled_manager.get_config("health").timeout == httpx.Timeout(None)

    manager = MLClientManager("test", timeout=30)
    assert manager.get_config("content", timeout=None).timeout == httpx.Timeout(None)


def test_unknown_config_override_is_rejected():
    with pytest.raises(TypeError, match="unexpected keyword argument 'rety'"):
        MLClientManager("test").get_client("health", rety=Retry(total=0))


def test_get_client_with_app_server_id():
    mgr = MLClientManager("test")
    with mgr.get_client("content") as ml:
        assert isinstance(ml, MLClient)
        assert ml.http.config.protocol == "https"
        assert ml.http.config.host == "localhost"
        assert ml.http.config.port == 8100
        assert ml.http.config.username == "my-marklogic-app-user"
        assert ml.http.config.password == "my-marklogic-app-password"
        assert isinstance(ml.http.config.auth, httpx.BasicAuth)
        assert ml.is_connected()
    assert not ml.is_connected()


def test_get_client_default():
    mgr = MLClientManager("test")
    with mgr.get_client() as ml:
        assert isinstance(ml, MLClient)
        assert ml.http.config.protocol == "https"
        assert ml.http.config.host == "localhost"
        assert ml.http.config.port == 8002
        assert ml.http.config.username == "my-marklogic-app-user"
        assert ml.http.config.password == "my-marklogic-app-password"
        assert isinstance(ml.http.config.auth, httpx.BasicAuth)
        assert ml.is_connected()
    assert not ml.is_connected()


@respx.mock
def test_get_client_wires_env_manage_admin_and_health_servers():
    env = MLEnvironment(
        **{
            "app-name": "app",
            "host": "localhost",
            "app-servers": [
                {"id": "content", "port": 8100, "rest": True},
                {"id": "manage", "port": 9002},
                {"id": "admin", "port": 9001},
            ],
        },
    )
    mgr = MLClientManager("test")
    mgr.config = env

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:9002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:9001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    with mgr.get_client("content") as ml:
        assert ml.manage.databases.get_list().status_code == 200
        assert ml.admin.get_timestamp().status_code == 200
        assert ml.healthcheck() is True


@pytest.mark.asyncio
@respx.mock
async def test_get_async_client_wires_env_manage_admin_and_health_servers():
    env = MLEnvironment(
        **{
            "app-name": "app",
            "host": "localhost",
            "app-servers": [
                {"id": "content", "port": 8100, "rest": True},
                {"id": "manage", "port": 9002},
                {"id": "admin", "port": 9001},
            ],
        },
    )
    mgr = MLClientManager("test")
    mgr.config = env

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:9002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"database-default-list": {}})
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:9001/admin/v1/timestamp")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("text/plain")
    ml_mocker.with_response_body("2026-03-23T00:00:00")
    ml_mocker.mock_get()

    ml_mocker.with_url("http://localhost:7997/")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_head()

    async with mgr.get_async_client("content") as ml:
        assert (await ml.manage.databases.get_list()).status_code == 200
        assert (await ml.admin.get_timestamp()).status_code == 200
        assert await ml.healthcheck() is True


@respx.mock
def test_health_shares_session_and_preserves_other_endpoints(mocker):
    opened = mocker.spy(http_client_module, "Client")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://localhost:9997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    health_route = ml_mocker.mock_head()
    ml_mocker.with_url("https://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()
    manager = MLClientManager("test")

    with manager.get_client("health", port=9997) as ml:
        assert (ml.http.head("/")).status_code == 503
        assert ml.healthcheck() is False
        assert health_route.call_count == 2
        assert opened.call_count == 1
        ml.manage.databases.get_list()
        assert opened.call_count == 2


def test_get_client_default_no_rest_servers_configured():
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLClientManager("test-no-rest").get_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_client_non_rest_server():
    ml = MLClientManager("test").get_client("modules")
    assert ml.http.config.port == 8101


def test_get_client_unknown_app_server():
    mgr = MLClientManager("test")
    with pytest.raises(NoSuchAppServerError) as err:
        mgr.get_client("missing")
    assert err.value.args[0] == "There's no [missing] app server configuration!"


def test_get_http_client():
    mgr = MLClientManager("test")
    with mgr.get_http_client("content") as client:
        assert isinstance(client, HttpClient)
        assert client.config.protocol == "https"
        assert client.config.host == "localhost"
        assert client.config.port == 8100
        assert client.config.username == "my-marklogic-app-user"
        assert client.config.password == "my-marklogic-app-password"
        assert isinstance(client.config.auth, httpx.BasicAuth)


@pytest.mark.asyncio
async def test_get_async_client_with_app_server_id():
    mgr = MLClientManager("test")
    async with mgr.get_async_client("content") as ml:
        assert isinstance(ml, AsyncMLClient)
        assert ml.http.config.protocol == "https"
        assert ml.http.config.host == "localhost"
        assert ml.http.config.port == 8100
        assert ml.http.config.username == "my-marklogic-app-user"
        assert ml.http.config.password == "my-marklogic-app-password"
        assert isinstance(ml.http.config.auth, httpx.BasicAuth)
        assert ml.is_connected()
    assert not ml.is_connected()


@pytest.mark.asyncio
async def test_get_async_client_default():
    mgr = MLClientManager("test")
    async with mgr.get_async_client() as ml:
        assert isinstance(ml, AsyncMLClient)
        assert ml.http.config.protocol == "https"
        assert ml.http.config.host == "localhost"
        assert ml.http.config.port == 8002
        assert ml.http.config.username == "my-marklogic-app-user"
        assert ml.http.config.password == "my-marklogic-app-password"
        assert isinstance(ml.http.config.auth, httpx.BasicAuth)
        assert ml.is_connected()
    assert not ml.is_connected()


@pytest.mark.asyncio
@respx.mock
async def test_async_health_shares_session_and_preserves_other_endpoints(mocker):
    opened = mocker.spy(http_client_module, "AsyncClient")
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("https://localhost:9997/")
    ml_mocker.with_response_code(503)
    ml_mocker.with_empty_response_body()
    health_route = ml_mocker.mock_head()
    ml_mocker.with_url("https://localhost:8002/manage/v2/databases")
    ml_mocker.with_response_code(200)
    ml_mocker.with_empty_response_body()
    ml_mocker.mock_get()
    manager = MLClientManager("test")

    async with manager.get_async_client("health", port=9997) as ml:
        assert (await ml.http.head("/")).status_code == 503
        assert await ml.healthcheck() is False
        assert health_route.call_count == 2
        assert opened.call_count == 1
        await ml.manage.databases.get_list()
        assert opened.call_count == 2


def test_get_async_client_default_no_rest_servers_configured():
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLClientManager("test-no-rest").get_async_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_async_client_non_rest_server():
    ml = MLClientManager("test").get_async_client("modules")
    assert ml.http.config.port == 8101


def test_get_async_client_unknown_app_server():
    mgr = MLClientManager("test")
    with pytest.raises(NoSuchAppServerError) as err:
        mgr.get_async_client("missing")
    assert err.value.args[0] == "There's no [missing] app server configuration!"


def test_get_async_http_client():
    mgr = MLClientManager("test")
    ml = mgr.get_async_http_client("content")
    assert isinstance(ml, AsyncHttpClient)
    assert ml.config.protocol == "https"
    assert ml.config.host == "localhost"
    assert ml.config.port == 8100
    assert ml.config.username == "my-marklogic-app-user"
    assert ml.config.password == "my-marklogic-app-password"
    assert isinstance(ml.config.auth, httpx.BasicAuth)
