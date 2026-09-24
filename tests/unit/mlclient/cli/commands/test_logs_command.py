from __future__ import annotations

import asyncio
import re
from pathlib import Path

import httpx
import pytest
import respx
from cleo.testers.command_tester import CommandTester

from mlclient import AsyncMLClient
from mlclient.cli import MLCLIentApplication
from mlclient.env import MLEnvironment
from mlclient.exceptions import (
    InvalidLogTypeError,
    MarkLogicError,
    WrongParametersError,
)
from mlclient.http import NO_RETRY_STRATEGY
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

ENDPOINT = "/manage/v2/logs"


@pytest.fixture(autouse=True)
def ml_config_single_node() -> MLEnvironment:
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
def ml_config_cluster() -> MLEnvironment:
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
    return MLEnvironment(**config)


@pytest.fixture(autouse=True)
def logs_list_response() -> dict:
    return resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )


@pytest.fixture(autouse=True)
def _setup(mocker, ml_config_single_node, ml_config_cluster):
    # Setup
    original_method = MLEnvironment.load

    def load_env(env_name: str):
        if env_name == "test":
            return ml_config_single_node
        if env_name == "test-cluster":
            return ml_config_cluster
        return original_method(env_name)

    target = "mlclient.env.MLEnvironment.load"
    mocker.patch(target, side_effect=load_env)


@respx.mock
def test_command_logs_basic():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_basic_without_app_server():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") is None
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_basic_using_named_app_server():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8100_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s content")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "content"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_custom_log_type_error():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -l error")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_custom_log_type_access():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_AccessLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -l access")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "access"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_custom_log_type_request():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_RequestLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -l request")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "request"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


def test_command_logs_custom_log_type_invalid():
    tester = _get_tester("logs")
    with pytest.raises(InvalidLogTypeError) as err:
        tester.execute("-e test -s 8002 -l invalid")

    expected_msg = "Invalid log type! Allowed values are: error, access, request."
    assert err.value.args[0] == expected_msg


@respx.mock
def test_command_logs_from():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("start", "1970-01-01T00:00:00")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -f 1970-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") == "1970-01-01"
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_to():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("end", "1984-01-01T00:00:00")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -t 1984-01-01")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") == "1984-01-01"
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_regex():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("regex", "you-will-not-find-it")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -r you-will-not-find-it")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") == "you-will-not-find-it"
    assert tester.command.option("host") is None
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_host():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("host", "some-host")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -H some-host")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") == "some-host"
    assert tester.command.option("list") is False


@respx.mock
def test_command_logs_list():
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(response_body_json)
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test --list")

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") is None
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("from") is None
    assert tester.command.option("to") is None
    assert tester.command.option("regex") is None
    assert tester.command.option("host") is None
    assert tester.command.option("list") is True


@respx.mock
def test_command_logs_output_for_error_logs():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "info", "Log message 2"),
                ("2023-09-01T00:00:02Z", "info", "Log message 3"),
            ],
        ),
    )
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: Log message 1",
        "<time>2023-09-01T00:00:01Z <log-level>INFO: Log message 2",
        "<time>2023-09-01T00:00:02Z <log-level>INFO: Log message 3",
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_access_logs():
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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_AccessLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(logs))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -l access")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "access"

    expected_output_lines = [
        "Getting 8002_AccessLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_request_logs():
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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_RequestLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(logs))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002 -l request")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "request"

    expected_output_lines = [
        "Getting 8002_RequestLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_audit_logs():
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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "AuditLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(logs))
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -l audit")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("log-type") == "audit"

    expected_output_lines = [
        "Getting AuditLog.txt logs using REST App-Server http://localhost:8002\n",
    ]
    expected_output_lines.extend(logs)
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_error_logs_without_app_port():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "info", "Log message 2"),
                ("2023-09-01T00:00:02Z", "info", "Log message 3"),
            ],
        ),
    )
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") is None
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: Log message 1",
        "<time>2023-09-01T00:00:01Z <log-level>INFO: Log message 2",
        "<time>2023-09-01T00:00:02Z <log-level>INFO: Log message 3",
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_xml_logs():
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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "\n".join(xml_log_lines)),
            ],
        ),
    )
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute("-e test -s 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using REST App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: " + "\n".join(xml_log_lines),
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
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
            "-e test -s manage --list",
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
            "-e test -H localhost -s manage --list",
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
            "-e test-cluster -s manage --list",
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
            "-e test-cluster -H ml_cluster_node2 -s manage --list",
            "ml_cluster_node1",
            "logs-list-response-cluster-logs-from-single-node.json",
            "output-cluster-host-and-server.txt",
        ),
        (  # task server log files
            "-e test -s 0 --list",
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
            "-e test -s 9999 --list",
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
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://{host}:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("host", host_param)
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(logs_list_response)
    ml_mocker.mock_get()

    tester = _get_tester("logs")
    tester.execute(args)
    command_output = tester.io.fetch_output()

    expected_output_path = resources_utils.get_test_resource_path(__file__, output_path)
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


@respx.mock
def test_command_logs_all_hosts():
    _mock_two_node_error_logs()

    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test-cluster"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("all-hosts") is True

    expected_output_lines = [
        "Getting error logs from every host using "
        "REST App-Server http://ml_cluster_node1:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO (ml_cluster_node1): "
        "node1 message A",
        "<time>2023-09-01T00:00:01Z <log-level>INFO (ml_cluster_node2): "
        "node2 message A",
        "<time>2023-09-01T00:00:02Z <log-level>WARNING (ml_cluster_node1): "
        "node1 message B",
        "<time>2023-09-01T00:00:03Z <log-level>ERROR (ml_cluster_node2): "
        "node2 message B",
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_all_hosts_colors_hosts_on_decorated_output():
    _mock_two_node_error_logs()

    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts", decorated=True)
    command_output = tester.io.fetch_output()

    # First two palette entries, assigned by host order: colored parens
    # around an italic host name.
    assert "\x1b[38;5;208m(\x1b[3mml_cluster_node1\x1b[23m)\x1b[39m" in command_output
    assert "\x1b[38;5;38m(\x1b[3mml_cluster_node2\x1b[23m)\x1b[39m" in command_output


@respx.mock
def test_command_logs_all_hosts_omits_ansi_on_undecorated_output():
    _mock_two_node_error_logs()

    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts", decorated=False)
    command_output = tester.io.fetch_output()

    assert "\x1b[" not in command_output
    assert "(ml_cluster_node1)" in command_output
    assert "(ml_cluster_node2)" in command_output


@respx.mock
def test_command_logs_all_hosts_warns_when_unfiltered_across_hosts():
    _mock_two_node_error_logs()

    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts")

    error_output = tester.io.fetch_error()
    assert "unfiltered error logs from 2 hosts" in error_output
    assert "--from, --to or --regex" in error_output


@respx.mock
def test_command_logs_all_hosts_no_warning_when_filtered():
    _mock_two_node_error_logs()

    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts --regex node")

    assert "may return a large volume" not in tester.io.fetch_error()


def test_command_logs_all_hosts_rejects_non_error_log_type():
    tester = _get_tester("logs")
    with pytest.raises(WrongParametersError) as err:
        tester.execute("-e test-cluster --all-hosts -l access")

    expected_msg = "The --all-hosts option supports the error log type only"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("option", ["--host node1", "--list"])
@respx.mock
def test_command_logs_all_hosts_rejects_conflicting_options(option):
    tester = _get_tester("logs")
    with pytest.raises(WrongParametersError, match="cannot be combined"):
        tester.execute(f"-e test-cluster --all-hosts {option}")
    assert not respx.calls


@respx.mock
def test_command_logs_all_hosts_reports_host_discovery_error():
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        403,
        json={
            "errorResponse": {
                "statusCode": 403,
                "status": "Forbidden",
                "messageCode": "SEC-PRIV",
                "message": "Insufficient privileges",
            },
        },
    )
    with pytest.raises(MarkLogicError, match="Insufficient privileges"):
        _get_tester("logs").execute("-e test-cluster --all-hosts")


@respx.mock
def test_command_logs_all_hosts_handles_empty_host_list():
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json={"host-default-list": {"list-items": {"list-count": {"value": 0}}}},
    )
    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts")
    assert tester.status_code == 0
    assert tester.io.fetch_error() == ""


@respx.mock
def test_command_logs_all_hosts_orders_instants_and_preserves_messages():
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    _mock_host_error_logs(
        "ml_cluster_node1",
        [
            ("2023-09-01T00:00:00.1Z", "info", "third"),
            ("2023-09-01T00:00:00Z", "info", "<info>second</info>"),
        ],
    )
    _mock_host_error_logs(
        "ml_cluster_node2",
        [
            ("2023-09-01T01:00:00.2+01:00", "info", "fourth"),
            ("2023-09-01T00:30:00+01:00", "info", "first"),
        ],
    )
    tester = _get_tester("logs")
    tester.execute("-e test-cluster --all-hosts")
    messages = [
        line.rsplit(": ", 1)[1]
        for line in tester.io.fetch_output().splitlines()
        if "<log-level>" in line
    ]
    assert messages == ["first", "<info>second</info>", "third", "fourth"]


@pytest.mark.parametrize(
    ("server", "filename"),
    [
        ("content", "8100_ErrorLog.txt"),
        ("8002", "8002_ErrorLog.txt"),
        ("0", "TaskServer_ErrorLog.txt"),
    ],
)
@respx.mock
def test_command_logs_all_hosts_forwards_filters_and_server(server, filename):
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    routes = [
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={
                "host": host,
                "filename": filename,
                "format": "json",
                "start": "2023-09-01T00:00:00",
                "end": "2023-09-02T00:00:00",
                "regex": "needle",
            },
        ).respond(200, json={"logfile": {}})
        for host in ("ml_cluster_node1", "ml_cluster_node2")
    ]
    tester = _get_tester("logs")
    tester.execute(
        f"-e test-cluster --all-hosts -s {server} "
        "--from 2023-09-01 --to 2023-09-02 --regex needle",
    )
    assert all(route.call_count == 1 for route in routes)
    assert tester.io.fetch_error() == ""


@respx.mock
def test_command_logs_all_hosts_propagates_host_timeout(mocker):
    mocker.patch("mlclient.http.DEFAULT_RETRY_STRATEGY", NO_RETRY_STRATEGY)
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1"]),
    )
    respx.get("http://ml_cluster_node1:8002/manage/v2/logs").mock(
        side_effect=httpx.ReadTimeout("Host unavailable"),
    )
    with pytest.raises(httpx.ReadTimeout):
        _get_tester("logs").execute("-e test-cluster --all-hosts")


@respx.mock
def test_command_logs_all_hosts_cancels_reads_before_disconnect(mocker):
    started = asyncio.Event()
    events = []
    disconnect = AsyncMLClient.disconnect

    async def record_disconnect(client):
        events.append("disconnect")
        await disconnect(client)

    async def read_logs(request):
        if request.url.params["host"] == "ml_cluster_node1":
            await started.wait()
            return httpx.Response(403, json={"errorResponse": {"message": "Denied"}})
        started.set()
        try:
            await asyncio.Future()
        finally:
            events.append("cancelled")

    mocker.patch.object(AsyncMLClient, "disconnect", record_disconnect)
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    respx.get("http://ml_cluster_node1:8002/manage/v2/logs").mock(side_effect=read_logs)
    tester = _get_tester("logs")
    with pytest.raises(MarkLogicError, match="Denied"):
        tester.execute("-e test-cluster --all-hosts")
    assert events == ["cancelled", "disconnect"]
    assert "<log-level>" not in tester.io.fetch_output()


def _mock_two_node_error_logs():
    hosts_mocker = MLRespXMocker(use_router=False)
    hosts_mocker.with_url("http://ml_cluster_node1:8002/manage/v2/hosts")
    hosts_mocker.with_request_param("format", "json")
    hosts_mocker.with_response_code(200)
    hosts_mocker.with_response_content_type("application/json; charset=UTF-8")
    hosts_mocker.with_response_body(
        _hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    hosts_mocker.mock_get()

    _mock_host_error_logs(
        "ml_cluster_node1",
        [
            ("2023-09-01T00:00:00Z", "info", "node1 message A"),
            ("2023-09-01T00:00:02Z", "warning", "node1 message B"),
        ],
    )
    _mock_host_error_logs(
        "ml_cluster_node2",
        [
            ("2023-09-01T00:00:01Z", "info", "node2 message A"),
            ("2023-09-01T00:00:03Z", "error", "node2 message B"),
        ],
    )


def _mock_host_error_logs(
    host: str,
    logs: list[tuple],
):
    mocker = MLRespXMocker(use_router=False)
    mocker.with_url(f"http://ml_cluster_node1:8002{ENDPOINT}")
    mocker.with_request_param("format", "json")
    mocker.with_request_param("filename", "ErrorLog.txt")
    mocker.with_request_param("host", host)
    mocker.with_response_code(200)
    mocker.with_response_content_type("application/json; charset=UTF-8")
    mocker.with_response_body(mocker.error_logs_body(logs))
    mocker.mock_get()


def _hosts_body(
    hosts: list[str],
) -> dict:
    return {
        "host-default-list": {
            "list-items": {
                "list-item": [{"nameref": host} for host in hosts],
            },
        },
    }


def _get_tester(
    command_name: str,
):
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find(command_name)
    return CommandTester(command)
