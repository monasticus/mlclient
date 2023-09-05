from __future__ import annotations

import urllib.parse

import pytest
import responses
from cleo.testers.command_tester import CommandTester

from cli.app import MLCLIentApplication
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


@responses.activate
def test_command_call_logs_basic():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [])

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


@responses.activate
def test_command_call_logs_custom_rest_server():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [])

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


@responses.activate
def test_command_call_logs_custom_log_type_error():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [])

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


@responses.activate
def test_command_call_logs_custom_log_type_access():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_AccessLog.txt",
        },
        [],
        False)

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


@responses.activate
def test_command_call_logs_custom_log_type_request():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_RequestLog.txt",
        },
        [],
        False)

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


def test_command_call_logs_custom_log_type_invalid():
    tester = _get_tester("call logs")
    with pytest.raises(InvalidLogTypeError) as err:
        tester.execute("-e test -p 8002 -l invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg


@responses.activate
def test_command_call_logs_from():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "start": "1970-01-01T00:00:00",
        },
        [])

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


@responses.activate
def test_command_call_logs_to():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "end": "1984-01-01T00:00:00",
        },
        [])

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


@responses.activate
def test_command_call_logs_regex():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "regex": "you-will-not-find-it",
        },
        [])

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


@responses.activate
def test_command_call_logs_host():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "host": "some-host",
        },
        [])

    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -H some-host")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") == "some-host"


@responses.activate
def test_command_call_logs_output_for_error_logs():
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "info", "Log message 2"),
            ("2023-09-01T00:00:02Z", "info", "Log message 3"),
        ])

    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: Log message 1",
        "<time>2023-09-01T00:00:01Z <log-level>INFO: Log message 2",
        "<time>2023-09-01T00:00:02Z <log-level>INFO: Log message 3",
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@responses.activate
def test_command_call_logs_output_for_access_logs():
    logs = [
        ('172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_AccessLog.txt HTTP/1.1" '
         '200 454 - "python-requests/2.31.0"'),
        ('172.17.0.1 - - [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_ErrorLog.txt HTTP/1.1" '
         '401 104 - "python-requests/2.31.0"'),
    ]
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_AccessLog.txt",
        },
        logs,
        False)

    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l access")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "access"

    expected_output_lines = [
        "Getting 8002_AccessLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@responses.activate
def test_command_call_logs_output_for_request_logs():
    logs = [
        ('{'
         '"time":"2023-09-04T03:53:40Z", '
         '"url":"/manage/v2/logs?format=json&filename=8002_RequestLog.txt", '
         '"user":"admin", '
         '"elapsedTime":1.788074, '
         '"requests":1, '
         '"valueCacheHits":5347, '
         '"valueCacheMisses":349287, '
         '"regexpCacheHits":5279, '
         '"regexpCacheMisses":12, '
         '"fsProgramCacheMisses":1, '
         '"fsMainModuleSequenceCacheMisses":1, '
         '"fsLibraryModuleCacheMisses":226, '
         '"compileTime":0.801934, '
         '"runTime":0.950788'
         '}'),
        ('{'
         '"time":"2023-09-04T03:56:59Z", '
         '"url":"/manage/v2/forests", '
         '"user":"admin", '
         '"elapsedTime":1.265614, '
         '"requests":1, '
         '"inMemoryListHits":6, '
         '"expandedTreeCacheHits":2, '
         '"valueCacheHits":5142, '
         '"valueCacheMisses":4545, '
         '"regexpCacheHits":327, '
         '"regexpCacheMisses":11, '
         '"fragmentsAdded":1, '
         '"fragmentsDeleted":1, '
         '"fsProgramCacheHits":3, '
         '"fsProgramCacheMisses":6, '
         '"writeLocks":1, '
         '"lockTime":0.000003, '
         '"compileTime":0.00072, '
         '"commitTime":0.000252, '
         '"runTime":1.265031, '
         '"indexingTime":0.000687'
         '}'),
    ]
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_RequestLog.txt",
        },
        logs,
        False)

    tester = _get_tester("call logs")
    tester.execute("-e test -p 8002 -l request")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-port") == "8002"
    assert tester.command.option("log-type") == "request"

    expected_output_lines = [
        "Getting 8002_RequestLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)


def _setup_responses(
        request_params: dict,
        logs: list[tuple | str],
        error_logs: bool = True,
):
    params = urllib.parse.urlencode(request_params).replace("%2B", "+")
    request_url = f"http://localhost:8002/manage/v2/logs?{params}"

    if error_logs:
        response_json = {
            "logfile": {
                "log": [
                    {
                        "timestamp": log_tuple[0],
                        "level": log_tuple[1],
                        "message": log_tuple[2],
                    }
                    for log_tuple in logs
                ],
            },
        }
    else:
        response_json = {"logfile": {"message": "\n".join(logs)}}

    responses.get(
        request_url,
        json=response_json,
    )
