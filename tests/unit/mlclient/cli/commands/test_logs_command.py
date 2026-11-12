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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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
    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
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

    tester = _get_tester()
    tester.execute("-e test -s 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using Manage App-Server http://localhost:8002\n",
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

    tester = _get_tester()
    tester.execute("-e test -s 8002 -l access")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "access"

    expected_output_lines = [
        "Getting 8002_AccessLog.txt logs using Manage App-Server http://localhost:8002\n",
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

    tester = _get_tester()
    tester.execute("-e test -s 8002 -l request")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "request"

    expected_output_lines = [
        "Getting 8002_RequestLog.txt logs using Manage App-Server http://localhost:8002\n",
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

    tester = _get_tester()
    tester.execute("-e test -l audit")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("log-type") == "audit"

    expected_output_lines = [
        "Getting AuditLog.txt logs using Manage App-Server http://localhost:8002\n",
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

    tester = _get_tester()
    tester.execute("-e test")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") is None
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting ErrorLog.txt logs using Manage App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: Log message 1",
        "<time>2023-09-01T00:00:01Z <log-level>INFO: Log message 2",
        "<time>2023-09-01T00:00:02Z <log-level>INFO: Log message 3",
    ]
    assert command_output == "\n".join(expected_output_lines) + "\n"


@respx.mock
def test_command_logs_output_for_xml_logs():
    xml_log = (
        Path(
            resources_utils.get_test_resource_path(__file__, "error-log-entry.xml"),
        )
        .read_text()
        .rstrip("\n")
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", xml_log),
            ],
        ),
    )
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("-e test -s 8002")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test"
    assert tester.command.option("server") == "8002"
    assert tester.command.option("log-type") == "error"

    expected_output_lines = [
        "Getting 8002_ErrorLog.txt logs using Manage App-Server http://localhost:8002\n",
        "<time>2023-09-01T00:00:00Z <log-level>INFO: " + xml_log,
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

    tester = _get_tester()
    tester.execute(args)
    command_output = tester.io.fetch_output()

    expected_output_path = resources_utils.get_test_resource_path(__file__, output_path)
    expected_output = Path(expected_output_path).read_text()
    assert command_output == expected_output


@respx.mock
def test_command_logs_all_hosts():
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/hosts",
        params={"view": "default", "format": "json"},
    ).respond(200, json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]))
    for host, response_file in (
        ("ml_cluster_node1", "node1-error-logs.json"),
        ("ml_cluster_node2", "node2-error-logs.json"),
    ):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={"filename": "ErrorLog.txt", "format": "json", "host": host},
        ).respond(
            200,
            json=resources_utils.get_test_resource_json(__file__, response_file),
        )

    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts")
    command_output = tester.io.fetch_output()

    assert tester.command.option("environment") == "test-cluster"
    assert tester.command.option("log-type") == "error"
    assert tester.command.option("all-hosts") is True

    expected_output_lines = [
        "Getting error logs from every host using "
        "Manage App-Server http://ml_cluster_node1:8002\n",
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
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/hosts",
        params={"view": "default", "format": "json"},
    ).respond(200, json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]))
    for host, response_file in (
        ("ml_cluster_node1", "node1-error-logs.json"),
        ("ml_cluster_node2", "node2-error-logs.json"),
    ):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={"filename": "ErrorLog.txt", "format": "json", "host": host},
        ).respond(
            200,
            json=resources_utils.get_test_resource_json(__file__, response_file),
        )

    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts", decorated=True)
    command_output = tester.io.fetch_output()

    # First two palette entries, assigned by host order: colored parens
    # around an italic host name.
    assert "\x1b[38;5;208m(\x1b[3mml_cluster_node1\x1b[23m)\x1b[39m" in command_output
    assert "\x1b[38;5;38m(\x1b[3mml_cluster_node2\x1b[23m)\x1b[39m" in command_output


@respx.mock
def test_command_logs_all_hosts_omits_ansi_on_undecorated_output():
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/hosts",
        params={"view": "default", "format": "json"},
    ).respond(200, json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]))
    for host, response_file in (
        ("ml_cluster_node1", "node1-error-logs.json"),
        ("ml_cluster_node2", "node2-error-logs.json"),
    ):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={"filename": "ErrorLog.txt", "format": "json", "host": host},
        ).respond(
            200,
            json=resources_utils.get_test_resource_json(__file__, response_file),
        )

    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts", decorated=False)
    command_output = tester.io.fetch_output()

    assert "\x1b[" not in command_output
    assert "(ml_cluster_node1)" in command_output
    assert "(ml_cluster_node2)" in command_output


@respx.mock
def test_command_logs_all_hosts_warns_when_unfiltered_across_hosts():
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/hosts",
        params={"view": "default", "format": "json"},
    ).respond(200, json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]))
    for host, response_file in (
        ("ml_cluster_node1", "node1-error-logs.json"),
        ("ml_cluster_node2", "node2-error-logs.json"),
    ):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={"filename": "ErrorLog.txt", "format": "json", "host": host},
        ).respond(
            200,
            json=resources_utils.get_test_resource_json(__file__, response_file),
        )

    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts")

    error_output = tester.io.fetch_error()
    assert "unfiltered error logs from 2 hosts" in error_output
    assert "--from, --to or --regex" in error_output


@respx.mock
def test_command_logs_all_hosts_no_warning_when_filtered():
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/hosts",
        params={"view": "default", "format": "json"},
    ).respond(200, json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]))
    for host, response_file in (
        ("ml_cluster_node1", "node1-error-logs.json"),
        ("ml_cluster_node2", "node2-error-logs.json"),
    ):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={
                "filename": "ErrorLog.txt",
                "format": "json",
                "host": host,
                "regex": "node",
            },
        ).respond(
            200,
            json=resources_utils.get_test_resource_json(__file__, response_file),
        )

    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts --regex node")

    assert "may return a large volume" not in tester.io.fetch_error()


def test_command_logs_all_hosts_rejects_non_error_log_type():
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as err:
        tester.execute("-e test-cluster --all-hosts -l access")

    expected_msg = "The --all-hosts option supports the error log type only"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("option", ["--host node1", "--list"])
@respx.mock
def test_command_logs_all_hosts_rejects_conflicting_options(option):
    tester = _get_tester()
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
        _get_tester().execute("-e test-cluster --all-hosts")


@respx.mock
def test_command_logs_all_hosts_handles_empty_host_list():
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json={"host-default-list": {"list-items": {"list-count": {"value": 0}}}},
    )
    tester = _get_tester()
    tester.execute("-e test-cluster --all-hosts")
    assert tester.status_code == 0
    assert tester.io.fetch_error() == ""


@respx.mock
def test_command_logs_all_hosts_orders_instants_and_preserves_messages():
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={
            "filename": "ErrorLog.txt",
            "format": "json",
            "host": "ml_cluster_node1",
        },
    ).respond(
        200,
        json=resources_utils.get_test_resource_json(__file__, "node1-offset-logs.json"),
    )
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={
            "filename": "ErrorLog.txt",
            "format": "json",
            "host": "ml_cluster_node2",
        },
    ).respond(
        200,
        json=resources_utils.get_test_resource_json(__file__, "node2-offset-logs.json"),
    )
    tester = _get_tester()
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
    tester = _get_tester()
    tester.execute(
        f"-e test-cluster --all-hosts -s {server} "
        "--from 2023-09-01 --to 2023-09-02 --regex needle",
    )
    assert all(route.call_count == 1 for route in routes)
    assert tester.io.fetch_error() == ""


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        (httpx.ReadTimeout("Host unavailable"), "Host unavailable"),
        (httpx.ReadTimeout(""), "ReadTimeout"),
        (httpx.ConnectError("Connection refused"), "Connection refused"),
    ],
)
@respx.mock
def test_command_logs_all_hosts_reports_transport_error(mocker, failure, reason):
    mocker.patch("mlclient.http.DEFAULT_RETRY_STRATEGY", NO_RETRY_STRATEGY)
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1"]),
    )
    respx.get("http://ml_cluster_node1:8002/manage/v2/logs").mock(
        side_effect=failure,
    )
    tester = _get_tester()
    assert tester.execute("-e test-cluster --all-hosts") == 1
    assert tester.io.fetch_error() == (
        f"\nLogs are incomplete; missing hosts:\n  ml_cluster_node1: {reason}\n"
    )
    assert "<log-level>" not in tester.io.fetch_output()


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
            msg = "Invalid host response"
            raise ValueError(msg)
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
    tester = _get_tester()
    with pytest.raises(ValueError, match=r"^Invalid host response$") as error:
        tester.execute("-e test-cluster --all-hosts")
    assert str(error.value) == "Invalid host response"
    assert events == ["cancelled", "disconnect"]
    assert "<log-level>" not in tester.io.fetch_output()


@respx.mock
def test_command_logs_all_hosts_returns_available_logs_when_host_is_offline():
    params = {
        "filename": "ErrorLog.txt",
        "format": "json",
        "start": "2026-11-11T00:00:00",
        "regex": "Starting MarkLogic Server",
    }
    available = resources_utils.get_test_resource_json(
        __file__, "ml_cluster_node1-starting-logs.json",
    )
    offline = resources_utils.get_test_resource_json(__file__, "host-offline.json")
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node3"]),
    )
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={**params, "host": "ml_cluster_node1"},
    ).respond(200, json=available)
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={**params, "host": "ml_cluster_node3"},
    ).respond(500, json=offline)
    tester = _get_tester()

    status = tester.execute(
        "-e test-cluster --all-hosts --from 2026-11-11 "
        '--regex "Starting MarkLogic Server"',
    )

    assert status == 1
    output = resources_utils.get_test_resource_path(
        __file__, "output-partial-cluster.txt",
    )
    errors = resources_utils.get_test_resource_path(
        __file__, "output-missing-host-offline.txt",
    )
    assert tester.io.fetch_output() == Path(output).read_text()
    assert tester.io.fetch_error() == Path(errors).read_text()


@pytest.mark.parametrize(
    ("status_code", "response_file", "output_file"),
    [
        (503, "http-error-without-details.json", "output-missing-host-http.txt"),
        (403, "host-forbidden.json", "output-missing-host-forbidden.txt"),
    ],
)
@respx.mock
def test_command_logs_all_hosts_reports_http_error(
    mocker,
    status_code,
    response_file,
    output_file,
):
    mocker.patch("mlclient.http.DEFAULT_RETRY_STRATEGY", NO_RETRY_STRATEGY)
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node3"]),
    )
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={"host": "ml_cluster_node3"},
    ).respond(
        status_code,
        json=resources_utils.get_test_resource_json(__file__, response_file),
    )
    tester = _get_tester()

    status = tester.execute(
        "-e test-cluster --all-hosts --from 2026-11-11 "
        '--regex "Starting MarkLogic Server"',
    )

    assert status == 1
    assert (
        tester.io.fetch_error()
        == Path(
            resources_utils.get_test_resource_path(__file__, output_file),
        ).read_text()
    )
    assert "<log-level>" not in tester.io.fetch_output()


@respx.mock
def test_command_logs_all_hosts_waits_for_remaining_reads_after_timeout(mocker):
    mocker.patch("mlclient.http.DEFAULT_RETRY_STRATEGY", NO_RETRY_STRATEGY)
    failed = asyncio.Event()
    completed = []

    async def fail(_request):
        failed.set()
        msg = "Host unavailable"
        raise httpx.ReadTimeout(msg)

    async def finish(_request):
        await failed.wait()
        await asyncio.sleep(0)
        completed.append("ml_cluster_node2")
        return httpx.Response(200, json={"logfile": {}})

    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["ml_cluster_node1", "ml_cluster_node2"]),
    )
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={"host": "ml_cluster_node1"},
    ).mock(side_effect=fail)
    respx.get(
        "http://ml_cluster_node1:8002/manage/v2/logs",
        params={"host": "ml_cluster_node2"},
    ).mock(side_effect=finish)
    tester = _get_tester()

    status = tester.execute("-e test-cluster --all-hosts --regex missing")

    assert status == 1
    assert completed == ["ml_cluster_node2"]
    assert tester.io.fetch_error() == (
        "\nLogs are incomplete; missing hosts:\n  ml_cluster_node1: Host unavailable\n"
    )


@pytest.mark.parametrize("decorated", [False, True])
@respx.mock
def test_command_logs_all_hosts_reports_multiple_missing_hosts_literally(decorated):
    respx.get("http://ml_cluster_node1:8002/manage/v2/hosts").respond(
        200,
        json=_hosts_body(["<info>host1</info>", "host2"]),
    )
    for host in ("<info>host1</info>", "host2"):
        respx.get(
            "http://ml_cluster_node1:8002/manage/v2/logs",
            params={"host": host},
        ).respond(
            403,
            json={"errorResponse": {"message": "<info>Missing role</info>"}},
        )
    tester = _get_tester()
    assert (
        tester.execute(
            "-e test-cluster --all-hosts --regex needle",
            decorated=decorated,
        )
        == 1
    )
    errors = tester.io.fetch_error()
    assert "<info>host1</info>" in errors
    assert "host2" in errors
    assert errors.count("<info>Missing role</info>") == 2
    assert "Logs are incomplete; missing hosts:" in errors
    assert "<log-level>" not in tester.io.fetch_output()


@respx.mock
def test_command_logs_reloads_environment_between_invocations(mocker):
    for host in ("first.example.com", "second.example.com"):
        environment = MLEnvironment(
            **{
                "app-name": "logs-test",
                "host": host,
                "username": "admin",
                "password": "admin",
                "protocol": "http",
                "app-servers": [
                    {"id": "manage", "port": 8002, "auth": "basic", "rest": True},
                ],
            },
        )
        mocker.patch("mlclient.env.MLEnvironment.load", return_value=environment)
        route = respx.get(f"http://{host}:8002/manage/v2/logs").respond(
            200,
            json={"logfile": {}},
        )
        tester = _get_tester()

        assert tester.execute("-e reload-config --regex missing") == 0
        assert route.call_count == 1


@respx.mock
def test_command_logs_list_links_use_manage_connection(mocker, logs_list_response):
    environment = MLEnvironment(
        **{
            "app-name": "logs-test",
            "host": "localhost",
            "username": "admin",
            "password": "admin",
            "protocol": "http",
            "app-servers": [
                {"id": "app-services", "port": 8000, "auth": "basic", "rest": True},
                {"id": "manage", "port": 8123, "auth": "basic"},
            ],
        },
    )
    mocker.patch("mlclient.env.MLEnvironment.load", return_value=environment)
    respx.get("http://localhost:8123/manage/v2/logs").respond(
        200,
        json=logs_list_response,
    )
    tester = _get_tester()

    assert tester.execute("-e separate-manage --list") == 0
    output = tester.io.fetch_output()
    assert "http://localhost:8123/manage/v2/logs?filename=ErrorLog.txt" in output
    assert "http://localhost:8000" not in output


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


def _get_tester() -> CommandTester:
    """Returns a command tester."""
    app = MLCLIentApplication()
    command = app.find("logs")
    return CommandTester(command)
