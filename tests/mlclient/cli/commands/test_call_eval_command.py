from __future__ import annotations

import urllib.parse

import pytest
import responses
from cleo.testers.command_tester import CommandTester
from requests_toolbelt import MultipartEncoder
from responses import matchers

from mlclient import MLConfiguration
from mlclient.cli.app import MLCLIentApplication
from mlclient.exceptions import WrongParametersError
from tests import tools


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
    code = ('xquery version "1.0"; '
            '""')
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
        ])

    file_path = tools.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None


@responses.activate
def test_command_call_eval_custom_rest_server():
    code = ('xquery version "1.0"; '
            '""')
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
        ])

    file_path = tools.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test -s manage {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") == "manage"
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None


@responses.activate
def test_command_call_eval_xquery_flag():
    code = ('xquery version "1.0"; '
            '""')
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
        ])

    tester = _get_tester("call eval")
    tester.execute(f"-e test -x '{code}'")

    assert tester.command.argument("code") == code
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("xquery") is True
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") is None


@responses.activate
def test_command_call_eval_javascript_flag():
    code = ('"use strict"; '
            '""')
    _setup_responses(
        request_body={"javascript": code},
        response_parts=[
            ("string", ""),
        ])

    tester = _get_tester("call eval")
    tester.execute(f"-e test -j '{code}'")

    assert tester.command.argument("code") == code
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is True
    assert tester.command.option("database") is None


def test_command_call_eval_mixed_xquery_and_javascript():
    code = ('xquery version "1.0"; '
            '""')

    tester = _get_tester("call eval")
    with pytest.raises(WrongParametersError) as err:
        tester.execute(f"-e test -x -j '{code}'")

    expected_msg = "You cannot include both the xquery and the javascript parameter!"
    assert err.value.args[0] == expected_msg


@responses.activate
def test_command_call_eval_custom_database():
    code = ('xquery version "1.0"; '
            '""')
    _setup_responses(
        request_params={
            "database": "custom-db"
        },
        request_body={"xquery": code},
        response_parts=[
            ("string", ""),
        ])

    file_path = tools.get_test_resource_path(__file__, "xquery-code.xqy")
    tester = _get_tester("call eval")
    tester.execute(f"-e test -d custom-db {file_path}")

    assert tester.command.argument("code") == file_path
    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("xquery") is False
    assert tester.command.option("javascript") is False
    assert tester.command.option("database") == "custom-db"


@responses.activate
def test_command_call_eval_output():
    code = ('xquery version "1.0"; '
            '('
            ' xs:dateTime("2023-08-09T01:01:01.001Z"),'
            ' 1,'
            ' "string-value",'
            ' element root {},'
            ' map:entry("key", "value")'
            ')')
    _setup_responses(
        request_body={"xquery": code},
        response_parts=[
            ("dateTime", "2023-08-09T01:01:01.001Z"),
            ("integer", "1"),
            ("string", "string-value"),
            ("element", "<root/>"),
            ("map", '{"key": "value"}'),
        ])

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


def _setup_responses(
        request_body: dict,
        response_parts: list[tuple[str, str]],
        request_params: dict | None = None,
):
    request_url = "http://localhost:8002/v1/eval"
    if request_params:
        params = urllib.parse.urlencode(request_params).replace("%2B", "+")
        request_url += f"?{params}"

    if len(response_parts) == 0:
        responses.post(
            request_url,
            body=b"",
            headers={"Content-Length": "0"},
            match=[matchers.urlencoded_params_matcher(request_body)],
        )
    else:
        fields = {}
        for i, item in enumerate(response_parts):
            name_disposition = f"name{i}"
            field_name = f"field{i}"
            field_value = item[1]
            x_primitive = item[0]
            headers = {"X-Primitive": x_primitive}
            if x_primitive in ["array", "map"]:
                content_type = "application/json"
            elif x_primitive in ["document", "element"]:
                content_type = "application/xml"
            else:
                content_type = "text/plain"
            fields[field_name] = (name_disposition, field_value, content_type, headers)
        multipart_body = MultipartEncoder(fields=fields)
        multipart_body_str = multipart_body.to_string()
        responses.post(
            request_url,
            body=multipart_body_str,
            content_type=f"multipart/mixed; boundary={multipart_body.boundary[2:]}",
            headers={
                "Content-Length": str(len(multipart_body_str)),
            },
            match=[matchers.urlencoded_params_matcher(request_body)],
        )


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
