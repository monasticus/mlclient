import pytest

from mlclient import AsyncMLClient, MLClient, MLClientManager, MLEnvironment
from mlclient.clients import AsyncHttpClient, HttpClient
from mlclient.exceptions import NoRestServerConfiguredError, NotARestServerError


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


def test_get_client_with_app_server_id():
    mgr = MLClientManager("test")
    with mgr.get_client("content") as ml:
        assert isinstance(ml, MLClient)
        assert ml.http.protocol == "https"
        assert ml.http.host == "localhost"
        assert ml.http.port == 8100
        assert ml.http.username == "my-marklogic-app-user"
        assert ml.http.password == "my-marklogic-app-password"
        assert ml.http.auth_method == "basic"
        assert ml.is_connected()
    assert not ml.is_connected()


def test_get_client_default():
    mgr = MLClientManager("test")
    with mgr.get_client() as ml:
        assert isinstance(ml, MLClient)
        assert ml.http.protocol == "https"
        assert ml.http.host == "localhost"
        assert ml.http.port == 8002
        assert ml.http.username == "my-marklogic-app-user"
        assert ml.http.password == "my-marklogic-app-password"
        assert ml.http.auth_method == "basic"
        assert ml.is_connected()
    assert not ml.is_connected()


def test_get_client_default_no_rest_servers_configured():
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLClientManager("test-no-rest").get_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_client_not_a_rest_server():
    mgr = MLClientManager("test")
    with pytest.raises(NotARestServerError) as err:
        mgr.get_client("modules")
    assert err.value.args[0] == (
        "[modules] App-Server is not configured as a REST one."
    )


def test_get_http_client():
    mgr = MLClientManager("test")
    with mgr.get_http_client("content") as client:
        assert isinstance(client, HttpClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8100
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"


@pytest.mark.asyncio
async def test_get_async_client_with_app_server_id():
    mgr = MLClientManager("test")
    async with mgr.get_async_client("content") as ml:
        assert isinstance(ml, AsyncMLClient)
        assert ml.http.protocol == "https"
        assert ml.http.host == "localhost"
        assert ml.http.port == 8100
        assert ml.http.username == "my-marklogic-app-user"
        assert ml.http.password == "my-marklogic-app-password"
        assert ml.http.auth_method == "basic"
        assert ml.is_connected()
    assert not ml.is_connected()


@pytest.mark.asyncio
async def test_get_async_client_default():
    mgr = MLClientManager("test")
    async with mgr.get_async_client() as ml:
        assert isinstance(ml, AsyncMLClient)
        assert ml.http.protocol == "https"
        assert ml.http.host == "localhost"
        assert ml.http.port == 8002
        assert ml.http.username == "my-marklogic-app-user"
        assert ml.http.password == "my-marklogic-app-password"
        assert ml.http.auth_method == "basic"
        assert ml.is_connected()
    assert not ml.is_connected()


def test_get_async_client_default_no_rest_servers_configured():
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLClientManager("test-no-rest").get_async_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_async_client_not_a_rest_server():
    mgr = MLClientManager("test")
    with pytest.raises(NotARestServerError) as err:
        mgr.get_async_client("modules")
    assert err.value.args[0] == (
        "[modules] App-Server is not configured as a REST one."
    )


def test_get_async_http_client():
    mgr = MLClientManager("test")
    ml = mgr.get_async_http_client("content")
    assert isinstance(ml, AsyncHttpClient)
    assert ml.protocol == "https"
    assert ml.host == "localhost"
    assert ml.port == 8100
    assert ml.username == "my-marklogic-app-user"
    assert ml.password == "my-marklogic-app-password"
    assert ml.auth_method == "basic"
