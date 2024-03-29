from __future__ import annotations

import re
from pathlib import Path

import pytest
import responses
from cleo.testers.command_tester import CommandTester

from mlclient import MLConfiguration
from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import InvalidLogTypeError
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils

ENDPOINT = "/manage/v2/logs"


@pytest.fixture(autouse=True)
def ml_config_single_node() -> MLConfiguration:
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
def ml_config_cluster() -> MLConfiguration:
    config = {
        "app-name": "my-marklogic-app",
        "host": "ml_cluster_node1",
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
def logs_list_response() -> dict:
    return resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config_single_node, ml_config_cluster):
    # Setup
    original_method = MLConfiguration.from_environment

    def config_from_environment(environment_name: str):
        if environment_name == "test":
            return ml_config_single_node
        if environment_name == "test-cluster":
            return ml_config_cluster
        return original_method(environment_name)

    target = "mlclient.ml_config.MLConfiguration.from_environment"
    mocker.patch(target, side_effect=config_from_environment)


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
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_body(response_body_json)
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
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "info", "Log message 2"),
                ("2023-09-01T00:00:02Z", "info", "Log message 3"),
            ],
        ),
    )
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
        (
            "172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] "
            '"GET /manage/v2/logs?format=json&filename=8002_AccessLog.txt HTTP/1.1" '
            '200 454 - "python-requests/2.31.0"'
        ),
        (
            "172.17.0.1 - - [01/Sep/2023:03:54:16 +0000] "
            '"GET /manage/v2/logs?format=json&filename=8002_ErrorLog.txt HTTP/1.1" '
            '401 104 - "python-requests/2.31.0"'
        ),
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
        (
            "{"
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
            "}"
        ),
        (
            "{"
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
            "}"
        ),
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
        (
            "2023-09-04 01:01:01.111 event=server-restart; "
            "success=true; user=user; roles=admin"
        ),
        ("2023-09-04 01:01:01.112 event=server-startup; success=true;"),
        (
            "2023-09-04 01:01:01.112 event=configuration-change; "
            "file=/data/MarkLogic/groups.xml; success=true;"
        ),
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
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "info", "Log message 2"),
                ("2023-09-01T00:00:02Z", "info", "Log message 3"),
            ],
        ),
    )
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
        (
            "<error:error "
            'xsi:schemaLocation="http://marklogic.com/xdmp/error error.xsd" '
            'xmlns:error="http://marklogic.com/xdmp/error" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        ),
        "  <error:code>XDMP-CAST</error:code>",
        "  <error:name>err:FORG0001</error:name>",
        "  <error:xquery-version>1.0</error:xquery-version>",
        "  <error:message>Invalid cast</error:message>",
        (
            "  <error:format-string>XDMP-CAST: (err:FORG0001) xs:date($date) "
            '-- Invalid cast: "Asasdas" cast as xs:date</error:format-string>'
        ),
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
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "\n".join(xml_log_lines)),
            ],
        ),
    )
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
@pytest.mark.parametrize(
    ("args", "host", "response_path", "output_path"),
    [
        (  # single node - logs list
            "-e test --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-full.txt",
        ),
        (  # single node - logs list for a specific app server
            "-e test -a manage --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-server.txt",
        ),
        (  # single node - logs list for a host
            "-e test -H localhost --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-full.txt",
        ),
        (  # single node - logs list for a host and a specific app server
            "-e test -H localhost -a manage --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-server.txt",
        ),
        (  # cluster - logs list for all hosts with logs
            "-e test-cluster --list",
            "ml_cluster_node1",
            "logs-list-response-cluster.json",
            "output-cluster-full.txt",
        ),
        (  # cluster - logs list for a specific app server
            "-e test-cluster -a manage --list",
            "ml_cluster_node1",
            "logs-list-response-cluster.json",
            "output-cluster-server.txt",
        ),
        (  # cluster - logs list for a host
            "-e test-cluster -H ml_cluster_node2 --list",
            "ml_cluster_node1",
            "logs-list-response-cluster-logs-from-single-node.json",
            "output-cluster-host.txt",
        ),
        (  # cluster - logs list for a host and a specific app server
            "-e test-cluster -H ml_cluster_node2 -a manage --list",
            "ml_cluster_node1",
            "logs-list-response-cluster-logs-from-single-node.json",
            "output-cluster-host-and-server.txt",
        ),
        (  # task server log files
            "-e test -a 0 --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-task.txt",
        ),
        (  # no log files
            "-e test --list",
            "localhost",
            "logs-list-response-no-logs.json",
            "output-single-node-empty.txt",
        ),
        (  # no corresponding log files
            "-e test -a 9999 --list",
            "localhost",
            "logs-list-response-single-node.json",
            "output-single-node-empty.txt",
        ),
    ],
)
def test_command_call_output_of_logs_list(args, host, response_path, output_path):
    host_param_match = re.search(r"-H\s+(\S+)", args)
    host_param = host_param_match.group(1) if host_param_match else None

    logs_list_response = resources_utils.get_test_resource_json(__file__, response_path)
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://{host}:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("host", host_param)
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(logs_list_response)
    builder.build_get()

    tester = _get_tester("call logs")
    tester.execute(args)
    command_output = tester.io.fetch_output()

    expected_output_path = resources_utils.get_test_resource_path(__file__, output_path)
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


def _get_tester(
    command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
