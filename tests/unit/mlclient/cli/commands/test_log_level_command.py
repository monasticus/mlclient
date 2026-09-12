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
def test_command_log_level_shows_group_file_level_by_default():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "info")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Default\nFile Log Level: info\n"


@pytest.mark.parametrize(
    "options", ["--type system --group Analyzer", "-t system -g Analyzer"],
)
@respx.mock
def test_command_log_level_shows_group_system_level(options):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "debug")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute(f"-e test {options}")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Analyzer\nSystem Log Level: debug\n"


@pytest.mark.parametrize("connection", ["content", "8100"])
@respx.mock
def test_command_log_level_shows_app_server_line_when_server_targeted(connection):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8100/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "warning")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute(f"-e test -c {connection} -s App-Services")

    assert status == 0
    assert tester.io.fetch_output() == (
        "Group: Default\nApp Server: App-Services\nFile Log Level: warning\n"
    )


@respx.mock
def test_command_log_level_sets_level_and_prints_same_block():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "error")
    ml_mocker.mock_post()

    tester = _get_tester()
    status = tester.execute("-e test error")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Default\nFile Log Level: error\n"


@respx.mock
def test_command_log_level_falls_back_to_manage_when_eval_forbidden():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    ml_mocker.mock_post()

    ml_mocker.with_url("http://localhost:8002/manage/v2/groups/Default/properties")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"file-log-level": "notice"})
    ml_mocker.mock_get()

    tester = _get_tester()
    status = tester.execute("-e test")

    assert status == 0
    assert tester.io.fetch_output() == "Group: Default\nFile Log Level: notice\n"


@respx.mock
def test_command_log_level_styles_names_bold_and_level_coloured():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "info")
    ml_mocker.mock_post()

    tester = _get_tester()
    tester.execute("-e test --server App-Services", decorated=True)

    output = tester.io.fetch_output()
    assert "Group: \x1b[1mDefault\x1b[22m" in output
    assert "App Server: \x1b[1mApp-Services\x1b[22m" in output
    assert "\x1b[92;1minfo\x1b[39;22m" in output


@respx.mock
def test_command_log_level_colours_extended_palette_level():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "notice")
    ml_mocker.mock_post()

    tester = _get_tester()
    tester.execute("-e test", decorated=True)

    output = tester.io.fetch_output()
    assert "\x1b[33;1mnotice\x1b[39;22m" in output


def test_command_log_level_rejects_system_level_for_app_server():
    tester = _get_tester()
    status = tester.execute("-e test --type system --server App-Services")

    assert status == 1
    assert "system log level" in tester.io.fetch_error()


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    command = app.find("log-level")
    return CommandTester(command)


@respx.mock
def test_command_preserves_literal_names_and_unknown_levels():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("string", "future-level")
    ml_mocker.mock_post()

    tester = _get_tester()
    assert tester.execute('-e test --group "<info>Default</info>"') == 0
    assert tester.io.fetch_output() == (
        "Group: <info>Default</info>\nFile Log Level: future-level\n"
    )
