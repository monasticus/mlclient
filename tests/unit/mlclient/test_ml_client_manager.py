import pytest

from mlclient import MLClient, MLClientManager, MLProfile
from mlclient.clients import HttpClient
from mlclient.exceptions import NoRestServerConfiguredError, NotARestServerError


@pytest.fixture(autouse=True)
def ml_config() -> MLProfile:
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
    return MLProfile(**config)


@pytest.fixture(autouse=True)
def ml_config_no_rest() -> MLProfile:
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
    return MLProfile(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config, ml_config_no_rest):
    # Setup
    original_method = MLProfile.load

    def load_profile(profile_name: str):
        if profile_name == "test":
            return ml_config
        if profile_name == "test-no-rest":
            return ml_config_no_rest
        return original_method(profile_name)

    target = "mlclient.ml_profile.MLProfile.load"
    mocker.patch(target, side_effect=load_profile)


def test_properties():
    mgr = MLClientManager("test")

    assert mgr.profile_name == "test"

    expected_config = MLProfile.load("test")
    assert mgr.config.model_dump() == expected_config.model_dump()


def test_get_client_with_app_server_id():
    mgr = MLClientManager("test")
    with mgr.get_client("content") as client:
        assert isinstance(client, MLClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8100
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_client_default():
    mgr = MLClientManager("test")
    with mgr.get_client() as client:
        assert isinstance(client, MLClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_client_default_no_rest_servers_configured():
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLClientManager("test-no-rest").get_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] profile."
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
