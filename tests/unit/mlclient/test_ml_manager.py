import pytest

from mlclient import MLClient, MLConfiguration, MLManager, MLResourcesClient
from mlclient.clients import EvalClient, LogsClient
from mlclient.exceptions import NoRestServerConfiguredError, NotARestServerError


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
    ml_manager = MLManager("test")

    assert ml_manager.environment_name == "test"

    expected_config = MLConfiguration.from_environment("test")
    assert ml_manager.config.model_dump() == expected_config.model_dump()


def test_get_client():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_client("content") as client:
        assert isinstance(client, MLClient)
        assert not isinstance(client, MLResourcesClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8100
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_resources_client():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_resources_client("content") as client:
        assert isinstance(client, MLResourcesClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8100
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_resources_client_default():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_resources_client() as client:
        assert isinstance(client, MLResourcesClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_resources_client_default_no_rest_servers_configured():
    # uses tests/resources/test-ml-manager/mlclient-test-no-rest.yaml copy
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLManager("test-no-rest").get_resources_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_resources_client_not_a_rest_server():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    with pytest.raises(NotARestServerError) as err:
        MLManager("test").get_resources_client("schemas")
    assert err.value.args[0] == "[schemas] App-Server is not configured as a REST one."


def test_get_logs_client():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_logs_client("manage") as client:
        assert isinstance(client, LogsClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_logs_client_default():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_logs_client() as client:
        assert isinstance(client, LogsClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_logs_client_default_no_rest_servers_configured():
    # uses tests/resources/test-ml-manager/mlclient-test-no-rest.yaml copy
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLManager("test-no-rest").get_logs_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_logs_client_not_a_rest_server():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    with pytest.raises(NotARestServerError) as err:
        MLManager("test").get_logs_client("schemas")
    assert err.value.args[0] == "[schemas] App-Server is not configured as a REST one."


def test_get_eval_client():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_eval_client("manage") as client:
        assert isinstance(client, EvalClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_eval_client_default():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    ml_manager = MLManager("test")
    with ml_manager.get_eval_client() as client:
        assert isinstance(client, EvalClient)
        assert client.protocol == "https"
        assert client.host == "localhost"
        assert client.port == 8002
        assert client.username == "my-marklogic-app-user"
        assert client.password == "my-marklogic-app-password"
        assert client.auth_method == "basic"
        assert client.is_connected()
    assert not client.is_connected()


def test_get_eval_client_default_no_rest_servers_configured():
    # uses tests/resources/test-ml-manager/mlclient-test-no-rest.yaml copy
    with pytest.raises(NoRestServerConfiguredError) as err:
        MLManager("test-no-rest").get_eval_client()
    assert err.value.args[0] == (
        "No REST server is configured for the [test-no-rest] environment."
    )


def test_get_eval_client_not_a_rest_server():
    # uses tests/resources/test-ml-manager/mlclient-test.yaml copy
    with pytest.raises(NotARestServerError) as err:
        MLManager("test").get_eval_client("schemas")
    assert err.value.args[0] == "[schemas] App-Server is not configured as a REST one."
