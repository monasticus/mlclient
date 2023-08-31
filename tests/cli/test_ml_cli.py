from __future__ import annotations

import sys
import urllib.parse

import pytest
from cleo.testers.command_tester import CommandTester

import mlclient
from cli import main
from cli.ml_cli import MLCLIentApplication
from mlclient import MLManager, MLResponseParser
from mlclient.exceptions import InvalidLogTypeError
from tests import tools

test_helper = tools.TestHelper("test")


@pytest.fixture(scope="module", autouse=True)
def _setup_and_teardown():
    # Setup
    test_helper.setup_environment()

    yield

    # Teardown
    test_helper.clean_environment()


def test_main_sys_exit_1():
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 1


def test_main_sys_exit_0():
    sys.argv = ["ml"]
    with pytest.raises(SystemExit) as err:
        main()
    assert err.value.args[0] == 0


def test_app_properties():
    app = MLCLIentApplication()
    assert app.display_name == "MLCLIent"
    assert app.version == mlclient.__version__


def test_command_call_logs_basic():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })


def test_command_call_logs_custom_rest_server():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -s manage")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") == "manage"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })


def test_command_call_logs_custom_log_type_error():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l error")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })


def test_command_call_logs_custom_log_type_access():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l access")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "access"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_AccessLog.txt",
        })


def test_command_call_logs_custom_log_type_request():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l request")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "request"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_RequestLog.txt",
        })


def test_command_call_logs_custom_log_type_invalid():
    tester = _get_tester("call logs")
    with pytest.raises(InvalidLogTypeError) as err:
        tester.execute("-e test -p 8002 -l invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg


def test_command_call_logs_from():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -f 1970-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") == "1970-01-01"
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "start": "1970-01-01T00:00:00",
        })


def test_command_call_logs_to():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -t 1984-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") == "1984-01-01"
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "end": "1984-01-01T00:00:00",
        })


def test_command_call_logs_regex():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -r you-will-not-find-it")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") == "you-will-not-find-it"
    assert tester.command.option("host") is None

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "regex": "you-will-not-find-it",
        })


def test_command_call_logs_host():
    with MLManager("test").get_resources_client("manage") as client:
        resp = client.eval(xquery="xdmp:host() => xdmp:host-name()")
        host_name = MLResponseParser.parse(resp)

    tester = _get_tester("call logs")
    tester.execute(f"-e test -p 8002 -H {host_name}")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") == host_name

    _confirm_last_request(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "host": host_name,
        })


def test_command_call_logs_output_for_error_logs():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    init_log = "Getting [8002] error logs using REST App-Server http://localhost:8002"
    assert command_output.startswith(init_log)
    assert "<time>" in command_output
    assert "<log-level>" in command_output


def test_command_call_logs_output_for_access_logs():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l access")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "access"
    init_log = "Getting [8002] access logs using REST App-Server http://localhost:8002"
    assert command_output.startswith(init_log)
    assert "<time>" not in command_output
    assert "<log-level>" not in command_output


def test_command_call_logs_output_for_request_logs():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l request")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "request"
    init_log = "Getting [8002] request logs using REST App-Server http://localhost:8002"
    assert command_output.startswith(init_log)
    assert "<time>" not in command_output
    assert "<log-level>" not in command_output


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)


@pytest.mark.ml_access()
def _confirm_last_request(
        request_params: dict,
):
    params = urllib.parse.urlencode(request_params).replace("%2B", "+")
    request_url = f"/manage/v2/logs?{params}"

    rest_server_port = test_helper.config.provide_config("manage")["port"]
    test_helper.confirm_last_request(
        app_server_port=rest_server_port,
        request_method="GET",
        request_url=request_url)
