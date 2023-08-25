import os
import shutil
from pathlib import Path

import pytest

from mlclient import (MLClient, MLConfiguration, MLManager, MLResourcesClient,
                      constants)
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

