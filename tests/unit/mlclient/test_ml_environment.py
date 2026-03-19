import pytest

from mlclient import MLClient, MLConfiguration, MLEnvironment
from mlclient.exceptions import NoRestServerConfiguredError


@pytest.fixture(autouse=True)
def ml_config() -> MLConfiguration:
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
    return MLConfiguration(**config)


@pytest.fixture(autouse=True)
def ml_config_no_rest() -> MLConfiguration:
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
    return MLConfiguration(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config, ml_config_no_rest):
    # Setup
    original_method = MLConfiguration.from_environment

    def config_from_environment(environment_name: str):
        if environment_name == "test":
            return ml_config
        if environment_name == "test-no-rest":
            return ml_config_no_rest
        return original_method(environment_name)

    target = "mlclient.ml_config.MLConfiguration.from_environment"
    mocker.patch(target, side_effect=config_from_environment)


def test_properties():
    ml_env = MLEnvironment("test")

    assert ml_env.environment_name == "test"

    expected_config = MLConfiguration.from_environment("test")
    assert ml_env.config.model_dump() == expected_config.model_dump()


def test_get_client_with_app_server_id():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_env = MLEnvironment("test")
    with ml_env.get_client("content") as client:
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
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_env = MLEnvironment("test")
    with ml_env.get_client() as client:
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
    # uses tests/resources/test-ml-manager/mlclient-test-no-rest.yaml copy
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLEnvironment("test-no-rest").get_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_client_any_server():
    # get_client() with explicit ID works for any server, not just REST
    ml_env = MLEnvironment("test")
    with ml_env.get_client("schemas") as client:
        assert isinstance(client, MLClient)
        assert client.port == 8102
