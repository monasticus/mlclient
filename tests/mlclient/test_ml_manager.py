import os
import shutil
from pathlib import Path

import pytest

from mlclient import (MLClient, MLConfiguration, MLManager, MLResourcesClient,
                      constants)
from mlclient.clients import LogsClient
from mlclient.exceptions import NotARestServerError, NoRestServerConfiguredError
from tests import tools


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    ml_client_dir = Path(constants.ML_CLIENT_DIR)
    if not ml_client_dir.exists() or not ml_client_dir.is_dir():
        ml_client_dir.mkdir()
    for file_name in tools.list_resources(__file__):
        file_path = tools.get_test_resource_path(__file__, file_name)
        shutil.copy(file_path, constants.ML_CLIENT_DIR)

    yield

    # Teardown
    for file_name in tools.list_resources(__file__):
        Path(f"{constants.ML_CLIENT_DIR}/{file_name}").unlink()
    if ml_client_dir.exists() and not os.listdir(constants.ML_CLIENT_DIR):
        ml_client_dir.rmdir()


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
    assert err.value.args[0] == ("No REST server is configured for the [test-no-rest] "
                                 "environment.")


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

