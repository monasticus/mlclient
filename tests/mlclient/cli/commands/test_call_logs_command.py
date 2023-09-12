from __future__ import annotations

import urllib.parse

import pytest
import responses
from cleo.testers.command_tester import CommandTester

from mlclient import MLConfiguration
from mlclient.cli.app import MLCLIentApplication
from mlclient.exceptions import InvalidLogTypeError
from tests.tools import MLResponseBuilder


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
def test_command_call_logs_basic():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_basic_using_named_app_server():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8100_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a content")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "content"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_custom_rest_server():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -s manage")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") == "manage"
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_custom_log_type_error():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -l error")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_custom_log_type_access():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_AccessLog.txt")
    builder.with_response_body({"logfile": {"message": "\n".join([])}})
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -l access")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "access"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_custom_log_type_request():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_RequestLog.txt")
    builder.with_response_body({"logfile": {"message": "\n".join([])}})
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -l request")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "request"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


def test_command_call_logs_custom_log_type_invalid():
    tester = _get_tester("call logs")
    with pytest.raises(InvalidLogTypeError) as err:
        tester.execute("-e test -a 8002 -l invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg


@responses.activate
def test_command_call_logs_from():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_param("start", "1970-01-01T00:00:00")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -f 1970-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") == "1970-01-01"
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_to():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_param("end", "1984-01-01T00:00:00")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -t 1984-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") == "1984-01-01"
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_regex():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_param("regex", "you-will-not-find-it")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -r you-will-not-find-it")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") == "you-will-not-find-it"
    assert tester.command.option("host") is None


@responses.activate
def test_command_call_logs_host():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_param("host", "some-host")
    builder.with_response_body(_get_error_logs_response_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -H some-host")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") == "some-host"


@responses.activate
def test_command_call_logs_output_for_error_logs():
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "info", "Log message 2"),
        ("2023-09-01T00:00:02Z", "info", "Log message 3"),
    ]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "8002"
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
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_AccessLog.txt")
    builder.with_response_body({"logfile": {"message": "\n".join(logs)}})
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -l access")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "8002"
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
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_RequestLog.txt")
    builder.with_response_body({"logfile": {"message": "\n".join(logs)}})
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002 -l request")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "request"

    expected_output_lines = [
        "Getting 8002_RequestLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@responses.activate
def test_command_call_logs_output_for_xml_logs():
    xml_log_lines = [
        ('<error:error '
         'xsi:schemaLocation="http://marklogic.com/xdmp/error error.xsd" '
         'xmlns:error="http://marklogic.com/xdmp/error" '
         'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'),
        "  <error:code>XDMP-CAST</error:code>",
        "  <error:name>err:FORG0001</error:name>",
        "  <error:xquery-version>1.0</error:xquery-version>",
        "  <error:message>Invalid cast</error:message>",
        ('  <error:format-string>XDMP-CAST: (err:FORG0001) xs:date($date) '
         '-- Invalid cast: "Asasdas" cast as xs:date</error:format-string>'),
        "  <error:retryable>false</error:retryable>",
        "  <error:expr>xs:date($date)</error:expr>",
        "  <error:data>",
        '    <error:datum>"Asasdas"</error:datum>',
        "    <error:datum>xs:date</error:datum>",
        "  </error:data>",
        "  <error:stack>",
        "    <error:frame>",
        "      <error:uri>/MarkLogic/functx/functx-1.0-nodoc-2007-01.xqy</error:uri>",
        "      <error:line>345</error:line>",
        "      <error:column>19</error:column>",
        '      <error:operation>functx:day-of-week("Asasdas")</error:operation>',
        "      <error:variables>",
        "        <error:variable>",
        '          <error:name xmlns="http://www.functx.com">date</error:name>',
        '          <error:value>"Asasdas"</error:value>',
        "        </error:variable>",
        "      </error:variables>",
        "      <error:xquery-version>1.0</error:xquery-version>",
        "    </error:frame>",
        "    <error:frame>",
        "      <error:line>8</error:line>",
        "      <error:column>0</error:column>",
        "      <error:operation>function() as item()*()</error:operation>",
        "      <error:xquery-version>1.0-ml</error:xquery-version>",
        "    </error:frame>",
        "    <error:frame>",
        "      <error:uri>/</error:uri>",
        "      <error:xquery-version>1.0-ml</error:xquery-version>",
        "    </error:frame>",
        "  </error:stack>",
        "</error:error>",
    ]
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_param("format", "json")
    builder.with_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(_get_error_logs_response_body([
        ("2023-09-01T00:00:00Z", "info", "\n".join(xml_log_lines)),
    ]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: " + "\n".join(xml_log_lines),
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)


def _get_error_logs_response_body(
        logs: list[tuple],
):
    return {
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
