from __future__ import annotations

import sys

import pytest
import urllib.parse
from cleo.testers.command_tester import CommandTester

import mlclient
from cli import main
from cli.ml_cli import MLCLIentApplication
from mlclient import MLManager, MLResponseParser
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

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server is None
    assert command_app_port == "8002"
    assert command_from is None
    assert command_to is None
    assert command_regex is None
    assert command_host is None
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })


def test_command_call_logs_custom_rest_server():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -s manage")

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server == "manage"
    assert command_app_port == "8002"
    assert command_from is None
    assert command_to is None
    assert command_regex is None
    assert command_host is None
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })


def test_command_call_logs_from():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -f 1970-01-01")

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server is None
    assert command_app_port == "8002"
    assert command_from == "1970-01-01"
    assert command_to is None
    assert command_regex is None
    assert command_host is None
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "start": "1970-01-01T00:00:00",
        })


def test_command_call_logs_to():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -t 1984-01-01")

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server is None
    assert command_app_port == "8002"
    assert command_from is None
    assert command_to == "1984-01-01"
    assert command_regex is None
    assert command_host is None
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "end": "1984-01-01T00:00:00",
        })


def test_command_call_logs_regex():
    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -r you-will-not-find-it")

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server is None
    assert command_app_port == "8002"
    assert command_from is None
    assert command_to is None
    assert command_regex == "you-will-not-find-it"
    assert command_host is None
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
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

    command_environment = tester.command.option("environment")
    command_rest_server = tester.command.option("rest-server")
    command_app_port = tester.command.option("app-port")
    command_from = tester.command.option("from")
    command_to = tester.command.option("to")
    command_regex = tester.command.option("regex")
    command_host = tester.command.option("host")

    assert command_environment == "test"
    assert command_rest_server is None
    assert command_app_port == "8002"
    assert command_from is None
    assert command_to is None
    assert command_regex is None
    assert command_host == host_name
    assert "Getting [8002] logs using REST App-Server http://localhost:8002" in tester.io.fetch_output()

    _confirm_last_request(
        command_rest_server,
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "host": host_name,
        })


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)


@pytest.mark.ml_access()
def _confirm_last_request(
        rest_server_id: str | None,
        request_params: dict,
):
    params = urllib.parse.urlencode(request_params).replace("%2B", "+")
    request_url = f"/manage/v2/logs?{params}"

    rest_server_port = test_helper.config.provide_config(rest_server_id or "manage")["port"]
    test_helper.confirm_last_request(
        app_server_port=rest_server_port,
        request_method="GET",
        request_url=request_url)
