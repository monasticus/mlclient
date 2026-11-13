import logging
import shutil
from pathlib import Path

import httpx
import pytest

from mlclient import MLClient
from mlclient import _constants as constants
from mlclient.env import (
    MLEnvironment,
    MLServerConfig,
    find_mlclient_directory,
    find_mlclient_environment,
)
from mlclient.exceptions import (
    MLClientDirectoryNotFoundError,
    MLClientEnvironmentNotFoundError,
    NoSuchAppServerError,
)
from tests.utils import resources as resources_utils

_SCRIPT_DIR = Path(__file__).resolve().parent


def _server(identifier, port, auth, rest):
    return {
        "identifier": identifier,
        "port": port,
        "protocol": None,
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
        _server("app-services", None, None, rest=True),
        _server("admin", 8001, None, rest=False),
        _server("health", 7997, None, rest=False),
    ],
)

_DEFAULT_ENV_DUMP = _environment(
    "my-default-app",
    [
        _server("app-services", None, None, rest=True),
        _server("manage", 8002, None, rest=False),
        _server("admin", 8001, None, rest=False),
        _server("health", 7997, None, rest=False),
    ],
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


def test_find_mlclient_environment_returns_config_path():
    env_file_path = find_mlclient_environment("test")
    assert env_file_path.name == "mlclient-test.yaml"


def test_find_mlclient_environment_non_existing():
    with pytest.raises(MLClientEnvironmentNotFoundError) as err:
        find_mlclient_environment("non-existing")
    expected_msg = (
        "MLClient's environment configuration has not been found for [non-existing]!"
    )
    assert err.value.args[0] == expected_msg


def test_find_mlclient_directory_returns_directory():
    ml_client_dir = find_mlclient_directory(Path.cwd())
    assert ml_client_dir.name == constants.ML_CLIENT_DIR


def test_find_mlclient_directory_in_ancestor(monkeypatch):
    monkeypatch.chdir(_SCRIPT_DIR)

    ml_client_dir = find_mlclient_directory(Path.cwd())
    assert ml_client_dir.name == constants.ML_CLIENT_DIR


def test_find_mlclient_directory_non_existing(tmp_path, monkeypatch):
    start_dir = tmp_path / "project"
    start_dir.mkdir()
    home_dir = tmp_path / "home"
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    with pytest.raises(MLClientDirectoryNotFoundError) as err:
        find_mlclient_directory(start_dir)
    expected_msg = (
        f".mlclient directory has not been found in {start_dir} or any of its "
        f"parents (nor in {home_dir / '.mlclient'}). "
        "Run 'ml env init' or 'ml env init --global'."
    )
    assert err.value.args[0] == expected_msg


def test_find_mlclient_directory_falls_back_to_home(tmp_path, monkeypatch, caplog):
    start_dir = tmp_path / "project"
    start_dir.mkdir()
    home_dir = tmp_path / "home"
    (home_dir / ".mlclient").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    with caplog.at_level(logging.DEBUG, logger="mlclient.env"):
        ml_client_dir = find_mlclient_directory(start_dir)

    assert ml_client_dir == home_dir / ".mlclient"
    assert f"Using global configuration directory [{ml_client_dir}]" in caplog.text


def test_find_mlclient_directory_ignores_home_file_named_mlclient(
    tmp_path,
    monkeypatch,
):
    start_dir = tmp_path / "project"
    start_dir.mkdir()
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    (home_dir / ".mlclient").touch()
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    with pytest.raises(MLClientDirectoryNotFoundError):
        find_mlclient_directory(start_dir)


def test_find_mlclient_directory_prefers_ancestor_over_home(tmp_path, monkeypatch):
    project_dir = tmp_path / "project"
    start_dir = project_dir / "sub" / "dir"
    start_dir.mkdir(parents=True)
    (project_dir / ".mlclient").mkdir()
    home_dir = tmp_path / "home"
    (home_dir / ".mlclient").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: home_dir)

    ml_client_dir = find_mlclient_directory(start_dir)

    assert ml_client_dir == project_dir / ".mlclient"


def test_find_mlclient_directory_relative_path_searches_above_cwd(
    tmp_path,
    monkeypatch,
):
    (tmp_path / ".mlclient").mkdir()
    (tmp_path / "project").mkdir()
    monkeypatch.chdir(tmp_path / "project")
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    ml_client_dir = find_mlclient_directory(Path())

    assert ml_client_dir == tmp_path / ".mlclient"


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
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")

    with pytest.raises(MLClientDirectoryNotFoundError) as err:
        MLEnvironment.load("test-default")
    actual_msg = err.value.args[0]
    assert actual_msg.startswith(
        f".mlclient directory has not been found in {tmp_path} or any of its parents",
    )


def test_rest_servers():
    test_config = MLEnvironment.load("test")
    default_config = MLEnvironment.load("test-default")
    assert test_config.rest_servers == ["manage", "content", "test", "app-services"]
    assert default_config.rest_servers == ["app-services"]


def test_provide_config():
    config = MLEnvironment.load("test")
    resolved = config.provide_config("manage")
    assert resolved.protocol == "http"
    assert resolved.host == "localhost"
    assert resolved.port == 8002
    assert resolved.username == "admin"
    assert resolved.password == "admin"
    assert isinstance(resolved.auth, httpx.BasicAuth)
    assert resolved.ssl is None
    assert resolved.cloud is None


def test_provide_config_non_existing_server():
    config = MLEnvironment.load("test")
    with pytest.raises(NoSuchAppServerError) as err:
        config.provide_config("non-existing")
    expected_msg = "There's no [non-existing] app server configuration!"
    actual_msg = err.value.args[0]
    assert actual_msg == expected_msg


def test_default_servers_present_when_user_defines_own():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "app-servers": [{"id": "content", "port": 8100, "rest": True}],
        },
    )
    identifiers = [server.identifier for server in config.app_servers]
    assert identifiers == ["content", "app-services", "manage", "admin", "health"]
    assert config.provide_config("manage").port == 8002
    assert config.provide_config("admin").port == 8001
    assert config.provide_config("health").port == 7997
    assert config.provide_config("health").auth is None


def test_app_name_defaults_to_none_when_omitted():
    config = MLEnvironment(
        **{"app-servers": [{"id": "content", "port": 8100, "rest": True}]},
    )
    assert config.app_name is None
    assert config.provide_config("content").port == 8100


def test_default_manage_and_admin_inherit_root_auth():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "basic",
            "app-servers": [{"id": "content", "port": 8100, "rest": True}],
        },
    )
    assert isinstance(config.provide_config("manage").auth, httpx.BasicAuth)
    assert isinstance(config.provide_config("admin").auth, httpx.BasicAuth)
    assert config.provide_config("health").auth is None


def test_user_server_overrides_default_of_same_id():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "app-servers": [{"id": "manage", "port": 8100, "rest": True}],
        },
    )
    identifiers = [server.identifier for server in config.app_servers]
    assert identifiers == ["manage", "app-services", "admin", "health"]
    assert config.provide_config("manage").port == 8100


def test_root_auth_inherited_when_server_omits_it():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "basic",
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert isinstance(config.provide_config("content").auth, httpx.BasicAuth)


def test_server_auth_overrides_root():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "digest",
            "app-servers": [{"id": "content", "port": 8100, "auth": "basic"}],
        },
    )
    assert isinstance(config.provide_config("content").auth, httpx.BasicAuth)


@pytest.mark.parametrize("auth", ["app", None])
def test_root_app_auth_resolves_to_none(auth):
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": auth,
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert config.auth is None
    assert config.provide_config("content").auth is None


@pytest.mark.parametrize("auth", ["app", None])
def test_server_app_auth_overrides_root(auth):
    config = MLEnvironment(
        **{
            "app-name": "app",
            "auth": "digest",
            "app-servers": [{"id": "content", "port": 8100, "auth": auth}],
        },
    )
    assert config.app_servers[0].auth is None
    assert config.provide_config("content").auth is None


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
    assert resolved.username == "root-user"
    assert resolved.password == "root-pass"


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
    assert config.provide_config("content").username == "reader"


def test_root_protocol_inherited_when_server_omits_it():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert config.provide_config("content").protocol == "https"


def test_server_protocol_overrides_root():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "http",
            "app-servers": [
                {"id": "secure", "port": 8010, "protocol": "https"},
            ],
        },
    )
    assert config.provide_config("secure").protocol == "https"


def test_root_ssl_inherited():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "ssl": {"verify": "/certs/ca.pem"},
            "app-servers": [{"id": "content", "port": 8100}],
        },
    )
    assert config.provide_config("content").ssl.verify == "/certs/ca.pem"


def test_server_ssl_merges_client_cert_over_root_verify():
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
                        "cert_file": "/certs/client.pem",
                        "key_file": "/certs/client-key.pem",
                    },
                },
            ],
        },
    )
    resolved_ssl = config.provide_config("secure").ssl
    assert resolved_ssl.cert_file == "/certs/client.pem"
    assert resolved_ssl.key_file == "/certs/client-key.pem"
    assert resolved_ssl.verify == "/certs/root-ca.pem"


def test_server_ssl_overrides_root_verify():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "ssl": {"verify": "/certs/root-ca.pem"},
            "app-servers": [
                {
                    "id": "secure",
                    "port": 8010,
                    "ssl": {"verify": "/certs/other-ca.pem"},
                },
            ],
        },
    )
    assert config.provide_config("secure").ssl.verify == "/certs/other-ca.pem"


def test_server_ssl_used_when_root_has_no_ssl():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "app-servers": [
                {
                    "id": "secure",
                    "port": 8010,
                    "ssl": {
                        "cert_file": "/certs/client.pem",
                        "key_file": "/certs/client-key.pem",
                    },
                },
            ],
        },
    )
    resolved_ssl = config.provide_config("secure").ssl
    assert resolved_ssl.cert_file == "/certs/client.pem"
    assert resolved_ssl.verify is True


def test_server_ssl_can_disable_root_verify():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "ssl": {"verify": "/certs/root-ca.pem"},
            "app-servers": [
                {"id": "secure", "port": 8010, "ssl": {"verify": False}},
            ],
        },
    )
    assert config.provide_config("secure").ssl.verify is False


def test_complex_auth_resolved_as_certificate():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "protocol": "https",
            "app-servers": [
                {
                    "id": "secure",
                    "port": 8010,
                    "auth": {"method": "certificate"},
                    "ssl": {
                        "cert_file": "/certs/client.pem",
                        "key_file": "/certs/client-key.pem",
                    },
                },
            ],
        },
    )
    resolved = config.provide_config("secure")
    assert resolved.protocol == "https"
    assert resolved.connection.is_mutual_tls
    assert resolved.auth is None


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
    assert resolved.cloud.api_key == "mk-1"
    assert resolved.cloud.base_path == "/ml/x/manage"


def test_cloud_environment_needs_no_app_servers_or_port():
    config = MLEnvironment(
        **{
            "app-name": "app",
            "host": "x.marklogic.cloud",
            "cloud": {"api-key": "mk-1", "base-path": "/ml/x"},
        },
    )
    resolved = config.provide_config("app-services")
    assert resolved.port == 443
    ml = MLClient(config=resolved)
    assert ml.http.config.port == 443


def test_no_root_auth_defaults_to_digest():
    config = MLEnvironment(
        **{"app-name": "app", "app-servers": [{"id": "content", "port": 8100}]},
    )
    assert isinstance(config.provide_config("content").auth, httpx.DigestAuth)


@pytest.mark.parametrize(
    "settings",
    [
        {},
        {"auth": "app"},
        {"protocol": "https", "ssl": {"verify": False}},
        {"username": "alice", "app-servers": [{"id": "content", "username": "bob"}]},
    ],
)
def test_provide_config_dict_match_client_configuration(settings):
    environment = MLEnvironment.model_validate(
        {
            "app-servers": [{"id": "content"}],
            **settings,
        },
    )

    inherited = environment.provide_config_dict("content")
    resolved = environment.provide_config("content")

    for field in ("host", "port", "protocol", "username", "password", "ssl", "cloud"):
        assert inherited[field] == getattr(resolved, field)
    assert inherited["auth"] == resolved.auth_method


def test_provide_config_dict_are_independent_of_environment():
    environment = MLEnvironment.model_validate(
        {
            "protocol": "https",
            "ssl": {"verify": "root-ca.pem"},
            "auth": {"method": "oauth", "token": "original-token"},
        },
    )

    inherited = environment.provide_config_dict("app-services")
    inherited["ssl"].verify = False
    inherited["auth"].token = "replacement-token"
    inherited["host"] = "other.example.com"

    later = environment.provide_config_dict("app-services")
    assert later["ssl"].verify == "root-ca.pem"
    assert later["auth"].token == "original-token"
    assert later["host"] == "localhost"
