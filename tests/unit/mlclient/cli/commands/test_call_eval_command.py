from __future__ import annotations

import pytest
import responses
from cleo.testers.command_tester import CommandTester

from mlclient import MLConfiguration
from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils


@pytest.fixture(autouse=True)
def ml_config() -> MLConfiguration:
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
    return MLConfiguration(**config)


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    # Setup
    target = "mlclient.ml_config.MLConfiguration.from_environment"
    mocker.patch(target, return_value=ml_config)


@responses.activate
def test_command_call_eval_basic():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


@responses.activate
def test_command_call_eval_custom_rest_server():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test -s manage {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") == "manage"
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


@responses.activate
def test_command_call_eval_with_vars():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_content_type("application/x-www-form-urlencoded")
    builder.with_request_body(
        {
            "xquery": code,
            "vars": '{"VARIABLE_1": "X", "VARIABLE_2": "Y"}',
        },
    )
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test {file_path} --var VARIABLE_1=X --var VARIABLE_2=Y")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == ["VARIABLE_1=X", "VARIABLE_2=Y"]
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


@responses.activate
def test_command_call_eval_xquery_flag():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    tester = _get_tester("call eval")
    tester.execute(f"-e test -x '{code}'")

    assert tester.command.argument("code") == code
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is True
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


@responses.activate
def test_command_call_eval_javascript_flag():
    code = '"use strict"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"javascript": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    tester = _get_tester("call eval")
    tester.execute(f"-e test -j '{code}'")

    assert tester.command.argument("code") == code
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is True
    assert tester.command.option("database") is None
    assert tester.command.option("txid") is None


def test_command_call_eval_mixed_xquery_and_javascript():
    code = 'xquery version "1.0"; ""'

    tester = _get_tester("call eval")
    with pytest.raises(WrongParametersError) as err:
        tester.execute(f"-e test -x -j '{code}'")

    expected_msg = "You cannot include both the xquery and the javascript parameter!"
    assert err.value.args[0] == expected_msg


@responses.activate
def test_command_call_eval_custom_database():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_param("database", "custom-db")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test -d custom-db {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") == "custom-db"
    assert tester.command.option("txid") is None


@responses.activate
def test_command_call_eval_custom_txid():
    code = 'xquery version "1.0"; ""'

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_param("txid", "transaction-id")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("string", "")
    builder.build_post()

    file_path = resources_utils.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test -t transaction-id {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("var") == []
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None
    assert tester.command.option("txid") == "transaction-id"


@responses.activate
def test_command_call_eval_output():
    code = (
        'xquery version "1.0"; '
        "("
        ' xs:dateTime("2023-08-09T01:01:01.001Z"),'
        " 1,"
        ' "string-value",'
        " element root {},"
        ' map:entry("key", "value")'
        ")"
    )

    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/v1/eval")
    builder.with_request_body({"xquery": code})
    builder.with_response_body_multipart_mixed()
    builder.with_response_body_part("dateTime", "2023-08-09T01:01:01.001Z")
    builder.with_response_body_part("integer", "1")
    builder.with_response_body_part("string", "string-value")
    builder.with_response_body_part("element", "<root/>")
    builder.with_response_body_part("map", '{"key": "value"}')
    builder.build_post()

    tester = _get_tester("call eval")
    tester.execute(f"-e test -x '{code}'")
    command_output = tester.io.fetch_output()

    assert tester.command.argument("code") == code
    assert tester.command.option("environment") == "test"
    assert tester.command.option("xquery") is True

    expected_output_lines = [
        "Evaluating code using REST App-Server http://localhost:8002\n",
        "2023-08-09T01:01:01.001Z",
        "1",
        "string-value",
        "<root/>",
        '{"key": "value"}',
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


def _get_tester(
    command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
