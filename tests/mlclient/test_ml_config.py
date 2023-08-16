import os
import shutil
from pathlib import Path

import pytest

from mlclient import AuthMethod, MLConfiguration, constants
from mlclient.ml_config import MLAppServerConfiguration

RESOURCES_PATH = "tests/resources/test-ml-config"


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    ml_client_dir = Path(constants.ML_CLIENT_PATH)
    if not ml_client_dir.exists() or not ml_client_dir.is_dir():
        ml_client_dir.mkdir()
    for file_name in os.listdir(RESOURCES_PATH):
        shutil.copy(f"{RESOURCES_PATH}/{file_name}", constants.ML_CLIENT_PATH)

    yield

    # Teardown
    for file_name in os.listdir(RESOURCES_PATH):
        Path(f"{constants.ML_CLIENT_PATH}/{file_name}").unlink()
    if ml_client_dir.exists() and not os.listdir(constants.ML_CLIENT_PATH):
        ml_client_dir.rmdir()


def test_from_file():
    path = f"{RESOURCES_PATH}/mlclient-test.yaml"
    config = MLConfiguration.from_file(path)
    assert config.model_dump() == {
        "app_name": "my-marklogic-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app_servers": [
            {
                "identifier": "manage",
                "port": 8002,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "content",
                "port": 8100,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "modules",
                "port": 8101,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "schemas",
                "port": 8102,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "test",
                "port": 8103,
                "auth": AuthMethod.BASIC,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(isinstance(app_server_config, MLAppServerConfiguration)
               for app_server_config in config.app_servers)


def test_from_file_default_values():
    path = f"{RESOURCES_PATH}/mlclient-test-default.yaml"
    config = MLConfiguration.from_file(path)
    assert config.model_dump() == {
        "app_name": "my-default-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app_servers": [
            {
                "identifier": "manage",
                "port": 8002,
                "auth": AuthMethod.DIGEST,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(isinstance(app_server_config, MLAppServerConfiguration)
               for app_server_config in config.app_servers)


def test_from_environment():
    # Note: the test environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    config = MLConfiguration.from_environment("test")
    assert config.model_dump() == {
        "app_name": "my-marklogic-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app_servers": [
            {
                "identifier": "manage",
                "port": 8002,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "content",
                "port": 8100,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "modules",
                "port": 8101,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "schemas",
                "port": 8102,
                "auth": AuthMethod.BASIC,
            },
            {
                "identifier": "test",
                "port": 8103,
                "auth": AuthMethod.BASIC,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(isinstance(app_server_config, MLAppServerConfiguration)
               for app_server_config in config.app_servers)


def test_from_environment_default():
    # Note: the test-default environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    config = MLConfiguration.from_environment("test-default")
    assert config.model_dump() == {
        "app_name": "my-default-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app_servers": [
            {
                "identifier": "manage",
                "port": 8002,
                "auth": AuthMethod.DIGEST,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(isinstance(app_server_config, MLAppServerConfiguration)
               for app_server_config in config.app_servers)
