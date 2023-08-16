from mlclient import AuthMethod, MLConfiguration
from mlclient.ml_config import MLAppServerConfiguration

RESOURCES_PATH = "tests/resources/test-ml-config"


def test_from_file():
    path = f"{RESOURCES_PATH}/test-from-file.yaml"
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
    path = f"{RESOURCES_PATH}/test-from-file-default-values.yaml"
    config = MLConfiguration.from_file(path)
    assert config.model_dump() == {
        "app_name": "my-default-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
        "app_servers": [],
    }
    assert isinstance(config, MLConfiguration)
    assert all(isinstance(app_server_config, MLAppServerConfiguration)
               for app_server_config in config.app_servers)
