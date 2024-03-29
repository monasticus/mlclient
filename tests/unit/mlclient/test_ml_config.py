import os
import shutil
from pathlib import Path

import pytest

from mlclient import MLConfiguration, constants
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    NoSuchAppServerError,
)
from mlclient.ml_config import MLAppServerConfiguration
from tests.utils import resources as resources_utils

_SCRIPT_DIR = Path(__file__).resolve().parent


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    ml_client_dir = Path(constants.ML_CLIENT_DIR)
    if not ml_client_dir.exists() or not ml_client_dir.is_dir():
        ml_client_dir.mkdir()
    for file_name in resources_utils.list_resources(__file__):
        file_path = resources_utils.get_test_resource_path(__file__, file_name)
        shutil.copy(file_path, constants.ML_CLIENT_DIR)

    yield

    # Teardown
    for file_name in resources_utils.list_resources(__file__):
        Path(f"{constants.ML_CLIENT_DIR}/{file_name}").unlink()
    if ml_client_dir.exists() and not os.listdir(constants.ML_CLIENT_DIR):
        ml_client_dir.rmdir()


def test_from_file():
    path = resources_utils.get_test_resource_path(__file__, "mlclient-test.yaml")
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
                "auth_method": "basic",
                "rest": True,
            },
            {
                "identifier": "content",
                "port": 8100,
                "auth_method": "basic",
                "rest": True,
            },
            {
                "identifier": "modules",
                "port": 8101,
                "auth_method": "basic",
                "rest": False,
            },
            {
                "identifier": "schemas",
                "port": 8102,
                "auth_method": "basic",
                "rest": False,
            },
            {
                "identifier": "test",
                "port": 8103,
                "auth_method": "basic",
                "rest": True,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(
        isinstance(app_server_config, MLAppServerConfiguration)
        for app_server_config in config.app_servers
    )


def test_from_file_default_values():
    path = resources_utils.get_test_resource_path(
        __file__,
        "mlclient-test-default.yaml",
    )
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
                "auth_method": "digest",
                "rest": True,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(
        isinstance(app_server_config, MLAppServerConfiguration)
        for app_server_config in config.app_servers
    )


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
                "auth_method": "basic",
                "rest": True,
            },
            {
                "identifier": "content",
                "port": 8100,
                "auth_method": "basic",
                "rest": True,
            },
            {
                "identifier": "modules",
                "port": 8101,
                "auth_method": "basic",
                "rest": False,
            },
            {
                "identifier": "schemas",
                "port": 8102,
                "auth_method": "basic",
                "rest": False,
            },
            {
                "identifier": "test",
                "port": 8103,
                "auth_method": "basic",
                "rest": True,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(
        isinstance(app_server_config, MLAppServerConfiguration)
        for app_server_config in config.app_servers
    )


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
                "auth_method": "digest",
                "rest": True,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(
        isinstance(app_server_config, MLAppServerConfiguration)
        for app_server_config in config.app_servers
    )


def test_from_environment_non_existing():
    with pytest.raises(MLClientEnvironmentNotFoundError) as err:
        MLConfiguration.from_environment("non-existing")
    expected_msg = (
        "MLClient's configuration has not been found for the environment "
        "[non-existing]!"
    )
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg


def test_from_environment_in_child_directory():
    # Note: the test-default environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    curr_dir = Path.cwd()
    os.chdir(_SCRIPT_DIR)

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
                "auth_method": "digest",
                "rest": True,
            },
        ],
    }
    assert isinstance(config, MLConfiguration)
    assert all(
        isinstance(app_server_config, MLAppServerConfiguration)
        for app_server_config in config.app_servers
    )

    os.chdir(curr_dir)


def test_from_environment_in_parent_directory():
    # Note: the test-default environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    curr_dir = Path.cwd()
    os.chdir(Path(_SCRIPT_DIR).parent.parent.parent.parent)

    with pytest.raises(MLClientDirectoryNotFoundError) as err:
        MLConfiguration.from_environment("test-default")
    expected_msg = (
        ".mlclient directory has not been found in any of parent directories!"
    )
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg

    os.chdir(curr_dir)


def test_rest_servers():
    test_config = MLConfiguration.from_environment("test")
    default_config = MLConfiguration.from_environment("test-default")
    assert test_config.rest_servers == ["manage", "content", "test"]
    assert default_config.rest_servers == ["manage"]


def test_provide_config():
    config = MLConfiguration.from_environment("test")
    assert config.provide_config("manage") == {
        "protocol": "http",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "port": 8002,
        "auth_method": "basic",
    }


def test_provide_config_non_existing_server():
    config = MLConfiguration.from_environment("test")
    with pytest.raises(NoSuchAppServerError) as err:
        config.provide_config("non-existing")
    expected_msg = "There's no [non-existing] app server configuration!"
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg
