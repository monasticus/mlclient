from mlclient import AuthMethod, MLConfiguration

RESOURCES_PATH = "tests/resources/test-ml-config"


def test_from_file():
    path = f"{RESOURCES_PATH}/test-from-file.yaml"
    config = MLConfiguration.from_file(path)
    assert config.app_name == "my-marklogic-app"
    assert config.host == "localhost"
    assert config.username == "admin"
    assert config.password == "admin"
    assert config.protocol == "http"
    assert len(config.app_servers) == 5
    assert config.app_servers[0].model_dump() == {
        "identifier": "manage",
        "port": 8002,
        "auth": AuthMethod.BASIC,
    }
    assert config.app_servers[1].model_dump() == {
        "identifier": "content",
        "port": 8100,
        "auth": AuthMethod.BASIC,
    }
    assert config.app_servers[2].model_dump() == {
        "identifier": "modules",
        "port": 8101,
        "auth": AuthMethod.BASIC,
    }
    assert config.app_servers[3].model_dump() == {
        "identifier": "schemas",
        "port": 8102,
        "auth": AuthMethod.BASIC,
    }
    assert config.app_servers[4].model_dump() == {
        "identifier": "test",
        "port": 8103,
        "auth": AuthMethod.BASIC,
    }
