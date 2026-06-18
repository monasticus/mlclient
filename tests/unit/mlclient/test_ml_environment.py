import shutil
from pathlib import Path

import pytest

from mlclient import MLClient, MLEnvironment, constants
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    NoSuchAppServerError,
)
from mlclient.ml_environment import MLServerConfig
from tests.utils import resources as resources_utils

_SCRIPT_DIR = Path(__file__).resolve().parent


def _server(identifier, port, auth, rest):
    return {
        "identifier": identifier,
        "port": port,
        "auth": auth,
        "username": None,
        "password": None,
        "ssl": None,
        "rest": rest,
    }


def _environment(app_name, app_servers):
    return {
        "app_name": app_name,
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "auth": "digest",
        "ssl": None,
        "cloud": None,
        "app_servers": app_servers,
    }


_TEST_ENV_DUMP = _environment(
    "my-marklogic-app",
    [
        _server("manage", 8002, "basic", rest=True),
        _server("content", 8100, "basic", rest=True),
        _server("modules", 8101, "basic", rest=False),
        _server("schemas", 8102, "basic", rest=False),
        _server("test", 8103, "basic", rest=True),
    ],
)

_DEFAULT_ENV_DUMP = _environment(
    "my-default-app",
    [_server("app-services", None, None, rest=True)],
)


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
    if ml_client_dir.exists() and not list(Path(constants.ML_CLIENT_DIR).iterdir()):
        ml_client_dir.rmdir()


def test_load_file():
    path = resources_utils.get_test_resource_path(__file__, "mlclient-test.yaml")
    config = MLEnvironment.load_file(path)
    assert config.model_dump() == _TEST_ENV_DUMP
    assert isinstance(config, MLEnvironment)
    assert all(
        isinstance(app_server_config, MLServerConfig)
        for app_server_config in config.app_servers
    )


def test_load_file_default_values():
    path = resources_utils.get_test_resource_path(
        __file__,
        "mlclient-test-default.yaml",
    )
    config = MLEnvironment.load_file(path)
    assert config.model_dump() == _DEFAULT_ENV_DUMP
    assert isinstance(config, MLEnvironment)
    assert all(
        isinstance(app_server_config, MLServerConfig)
        for app_server_config in config.app_servers
    )


def test_load():
    # Note: the test environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    config = MLEnvironment.load("test")
    assert config.model_dump() == _TEST_ENV_DUMP
    assert isinstance(config, MLEnvironment)
    assert all(
        isinstance(app_server_config, MLServerConfig)
        for app_server_config in config.app_servers
    )


def test_load_default():
    # Note: the test-default environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    config = MLEnvironment.load("test-default")
    assert config.model_dump() == _DEFAULT_ENV_DUMP
    assert isinstance(config, MLEnvironment)
    assert all(
        isinstance(app_server_config, MLServerConfig)
        for app_server_config in config.app_servers
    )


def test_load_non_existing():
    with pytest.raises(MLClientEnvironmentNotFoundError) as err:
        MLEnvironment.load("non-existing")
    expected_msg = (
        "MLClient's environment configuration has not been found for [non-existing]!"
    )
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg


def test_load_in_child_directory(monkeypatch):
    # Note: the test-default environment configuration is copied from the test resources
    # to .mlclient directory in a setup step
    monkeypatch.chdir(_SCRIPT_DIR)

    config = MLEnvironment.load("test-default")
    assert config.model_dump() == _DEFAULT_ENV_DUMP
    assert isinstance(config, MLEnvironment)
    assert all(
        isinstance(app_server_config, MLServerConfig)
        for app_server_config in config.app_servers
    )


def test_load_in_parent_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with pytest.raises(MLClientDirectoryNotFoundError) as err:
        MLEnvironment.load("test-default")
    expected_msg = (
        ".mlclient directory has not been found in any of parent directories!"
    )
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg


def test_rest_servers():
    test_config = MLEnvironment.load("test")
    default_config = MLEnvironment.load("test-default")
    assert test_config.rest_servers == ["manage", "content", "test"]
    assert default_config.rest_servers == ["app-services"]


def test_provide_config():
    config = MLEnvironment.load("test")
    assert config.provide_config("manage") == {
        "protocol": "http",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "auth": "basic",
        "ssl": None,
        "cloud": None,
        "port": 8002,
    }


def test_provide_config_non_existing_server():
    config = MLEnvironment.load("test")
    with pytest.raises(NoSuchAppServerError) as err:
        config.provide_config("non-existing")
    expected_msg = "There's no [non-existing] app server configuration!"
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg


def test_root_auth_inherited_when_server_omits_it():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "basic",
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert config.provide_config("content")["auth"] == "basic"


def test_server_auth_overrides_root():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "digest",
            "app-servers": [{"id": "content", "port": 8100, "auth": "basic"}],
        },
    )
    assert config.provide_config("content")["auth"] == "basic"


def test_root_credentials_inherited():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "username": "root-user",
            "password": "root-pass",
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    resolved = config.provide_config("content")
    assert resolved["username"] == "root-user"
    assert resolved["password"] == "root-pass"


def test_server_credentials_override_root():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "username": "root-user",
            "app-servers": [
                {"id": "content", "port": 8100, "username": "reader"},
            ],
        },
    )
    assert config.provide_config("content")["username"] == "reader"


def test_root_ssl_inherited():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "ssl": {"verify": "/certs/ca.pem"},
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert config.provide_config("content")["ssl"].verify == "/certs/ca.pem"


def test_server_ssl_replaces_root():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "ssl": {"verify": "/certs/root-ca.pem"},
            "app-servers": [
                {
                    "id": "secure",
                    "port": 8010,
                    "ssl": {
                        "verify": "/certs/ca.pem",
                        "cert_file": "/certs/client.pem",
                        "key_file": "/certs/client-key.pem",
                    },
                },
            ],
        },
    )
    resolved_ssl = config.provide_config("secure")["ssl"]
    assert resolved_ssl.cert_file == "/certs/client.pem"


def test_complex_auth_parsed_as_auth_config():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "app-servers": [
                {"id": "secure", "port": 8010, "auth": {"method": "certificate"}},
            ],
        },
    )
    assert config.provide_config("secure")["auth"].method == "certificate"


def test_cloud_config_in_provide_config():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "host": "x.marklogic.cloud",
            "cloud": {"api-key": "mk-1", "base-path": "/ml/x/manage"},
            "app-servers": [{"id": "content", "port": 443, "rest": True}],
        },
    )
    resolved = config.provide_config("content")
    assert resolved["cloud"].api_key == "mk-1"
    assert resolved["cloud"].base_path == "/ml/x/manage"


def test_cloud_environment_needs_no_app_servers_or_port():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "host": "x.marklogic.cloud",
            "cloud": {"api-key": "mk-1", "base-path": "/ml/x"},
        },
    )
    resolved = config.provide_config("app-services")
    assert "port" not in resolved
    ml = MLClient(**resolved)
    assert ml.http.port == 443


def test_no_root_auth_defaults_to_digest():
    config = MLEnvironment(
        **{"app-name": "app", "app-servers": [{"id": "content", "port": 8100}]},
    )
    assert config.provide_config("content")["auth"] == "digest"
