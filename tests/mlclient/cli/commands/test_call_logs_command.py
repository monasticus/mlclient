from __future__ import annotations

from pathlib import Path

import pytest
import responses
from cleo.testers.command_tester import CommandTester

from mlclient import MLConfiguration
from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import InvalidLogTypeError
from tests import tools
from tests.tools import MLResponseBuilder

ENDPOINT = "/manage/v2/logs"


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
def logs_list_items() -> list:
    return [
        {
            "uriref": f"{ENDPOINT}?filename=8001_AccessLog.txt&host=localhost",
            "nameref": "8001_AccessLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=8002_AccessLog_1.txt&host=localhost",
            "nameref": "8002_AccessLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=8001_RequestLog.txt&host=localhost",
            "nameref": "8001_RequestLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=8002_RequestLog_1.txt&host=localhost",
            "nameref": "8002_RequestLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=8001_ErrorLog.txt&host=localhost",
            "nameref": "8001_ErrorLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=8002_ErrorLog_1.txt&host=localhost",
            "nameref": "8002_ErrorLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_AccessLog.txt&host=localhost",
            "nameref": "TaskServer_AccessLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_AccessLog_1.txt&host=localhost",
            "nameref": "TaskServer_AccessLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_RequestLog.txt&host=localhost",
            "nameref": "TaskServer_RequestLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_RequestLog_1.txt&host=localhost",
            "nameref": "TaskServer_RequestLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_ErrorLog.txt&host=localhost",
            "nameref": "TaskServer_ErrorLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=TaskServer_ErrorLog_1.txt&host=localhost",
            "nameref": "TaskServer_ErrorLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=AccessLog.txt&host=localhost",
            "nameref": "AccessLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=AccessLog_1.txt&host=localhost",
            "nameref": "AccessLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=RequestLog.txt&host=localhost",
            "nameref": "RequestLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=RequestLog_1.txt&host=localhost",
            "nameref": "RequestLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=ErrorLog.txt&host=localhost",
            "nameref": "ErrorLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=ErrorLog_1.txt&host=localhost",
            "nameref": "ErrorLog_1.txt",
            "roleref": "localhost",
        },
        {
            "uriref": f"{ENDPOINT}?filename=AuditLog.txt&host=localhost",
            "nameref": "AuditLog.txt",
            "roleref": "localhost"},
        {
            "uriref": f"{ENDPOINT}?filename=AuditLog_1.txt&host=localhost",
            "nameref": "AuditLog_1.txt",
            "roleref": "localhost",
        },
    ]


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config):
    # Setup
    target = "mlclient.ml_config.MLConfiguration.from_environment"
    mocker.patch(target, return_value=ml_config)


@responses.activate
def test_command_call_logs_basic():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_basic_without_app_server():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") is None
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_basic_using_named_app_server():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8100_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_custom_rest_server():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_custom_log_type_error():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_custom_log_type_access():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.non_error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_custom_log_type_request():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.non_error_logs_body([]))
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
    assert tester.command.option("list") is False


def test_command_call_logs_custom_log_type_invalid():
    tester = _get_tester("call logs")
    with pytest.raises(InvalidLogTypeError) as err:
        tester.execute("-e test -a 8002 -l invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg


@responses.activate
def test_command_call_logs_from():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("start", "1970-01-01T00:00:00")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_to():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("end", "1984-01-01T00:00:00")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_regex():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("regex", "you-will-not-find-it")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_host():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("host", "some-host")
    builder.with_response_body(builder.error_logs_body([]))
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
    assert tester.command.option("list") is False


@responses.activate
def test_command_call_logs_list():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_body(builder.logs_list_body([]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test --list")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("rest-server") is None
    assert tester.command.option("app-server") is None
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is True


@responses.activate
def test_command_call_logs_output_for_error_logs():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
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
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.non_error_logs_body(logs))
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
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.non_error_logs_body(logs))
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
def test_command_call_logs_output_for_audit_logs():
    logs = [
        ("2023-09-04 01:01:01.111 event=server-restart; "
         "success=true; user=user; roles=admin"),
        ("2023-09-04 01:01:01.112 event=server-startup; "
         "success=true;"),
        ("2023-09-04 01:01:01.112 event=configuration-change; "
         "file=/data/MarkLogic/groups.xml; success=true;"),
    ]
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "AuditLog.txt")
    builder.with_response_body(builder.non_error_logs_body(logs))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -l audit")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("log-type") == "audit"

    expected_output_lines = [
        "Getting AuditLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@responses.activate
def test_command_call_logs_output_for_error_logs_without_app_port():
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "info", "Log message 2"),
        ("2023-09-01T00:00:02Z", "info", "Log message 3"),
    ]))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") is None
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: Log message 1",
        "<time>2023-09-01T00:00:01Z <log-level>INFO: Log message 2",
        "<time>2023-09-01T00:00:02Z <log-level>INFO: Log message 3",
    ]
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
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
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


@responses.activate
def test_command_call_output_of_logs_list(logs_list_items):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(builder.logs_list_body(logs_list_items))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test --list")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("list") is True

    expected_output_path = tools.get_test_resource_path(__file__, "output-full.txt")
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


@responses.activate
def test_command_call_output_of_logs_list_for_app_server(logs_list_items):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(builder.logs_list_body(logs_list_items))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a manage --list")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "manage"
    assert tester.command.option("list") is True

    expected_output_path = tools.get_test_resource_path(__file__, "output-server.txt")
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


@responses.activate
def test_command_call_output_of_logs_list_for_task_server(logs_list_items):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(builder.logs_list_body(logs_list_items))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 0 --list")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "0"
    assert tester.command.option("list") is True

    expected_output_path = tools.get_test_resource_path(__file__, "output-task.txt")
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


@responses.activate
def test_command_call_output_of_logs_list_empty(logs_list_items):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(builder.logs_list_body(logs_list_items))
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute("-e test -a 9999 --list")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("app-server") == "9999"
    assert tester.command.option("list") is True

    expected_output_path = tools.get_test_resource_path(__file__, "output-empty.txt")
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


def _get_tester(
        command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
