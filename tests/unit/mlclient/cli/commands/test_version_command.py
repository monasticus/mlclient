from __future__ import annotations

import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient import MLEnvironment
from mlclient.cli import MLCLIentApplication
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture(autouse=True)
def ml_config() -> MLEnvironment:
    config = {
        "app-name": "my-marklogic-app",
        "host": "localhost",
        "username": "admin",
        "password": "admin",
        "protocol": "http",
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
            },
        ],
    }
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    mocker.patch("mlclient.ml_environment.MLEnvironment.load", return_value=ml_config)


@respx.mock
def test_command_version_prints_dotted():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "12.0.1")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == "12.0.1\n"
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None


@respx.mock
def test_command_version_defaults_to_local_environment():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "12.0.1")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("")

    assert status == 0
    assert tester.command.option("environment") == "local"
    assert tester.io.fetch_output() == "12.0.1\n"


@respx.mock
def test_command_version_uses_custom_rest_server():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8100/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "12.0.1")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test -s content")

    assert status == 0
    assert tester.command.option("rest-server") == "content"
    assert tester.io.fetch_output() == "12.0.1\n"


@respx.mock
def test_command_version_falls_back_to_manage_when_eval_forbidden():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"version": "12.0.1"})
    ml_mocker.mock_get()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == "12.0.1\n"


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    command = app.find("version")
    return CommandTester(command)
