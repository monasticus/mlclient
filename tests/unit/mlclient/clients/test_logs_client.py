from __future__ import annotations

from pathlib import Path

import pytest
import responses

from mlclient.clients import LogsClient, LogType
from mlclient.exceptions import MarkLogicError
from tests.utils import MLResponseBuilder
from tests.utils import resources as resources_utils

ENDPOINT = "/manage/v2/logs"


@pytest.fixture(autouse=True)
def logs_client() -> LogsClient:
    return LogsClient()


@pytest.fixture(autouse=True)
def _setup_and_teardown(logs_client):
    logs_client.connect()

    yield

    logs_client.disconnect()


@responses.activate
def test_get_logs_no_such_host(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("host", "non-existing-host")
    builder.with_response_status(404)
    builder.with_response_body(
        {
            "errorResponse": {
                "statusCode": "404",
                "status": "Not Found",
                "messageCode": "XDMP-NOSUCHHOST",
                "message": 'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                "-- No such host non-existing-host",
            },
        },
    )
    builder.build_get()

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs(8002, host="non-existing-host")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHHOST) "
        'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
        "-- No such host non-existing-host"
    )
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_unauthorized(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_status(401)
    builder.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    builder.build_get()

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs()

    expected_error = "[401 Unauthorized] 401 Unauthorized"
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002)

    assert next(logs, None) is None


@responses.activate
def test_get_logs_without_port(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs()
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_logs_using_string_port(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs("8002")
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_task_server_logs(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "TaskServer_ErrorLog.txt")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs("TaskServer")
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_task_server_logs_using_int_port(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "TaskServer_ErrorLog.txt")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs(0)
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_error_logs(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs(8002)
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_error_logs_with_search_params(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("start", "2023-09-01T00:00:00")
    builder.with_request_param("end", "2023-09-01T23:59:00")
    builder.with_request_param("regex", "Log message")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        start_time="2023-09-01 00:00",
        end_time="2023-09-01 23:59",
        regex="Log message",
    )
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_error_logs_fully_customized(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("host", "some-host")
    builder.with_request_param("start", "2023-09-01T00:00:00")
    builder.with_request_param("end", "2023-09-01T23:59:00")
    builder.with_request_param("regex", "Log message")
    builder.with_response_body(
        builder.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        start_time="2023-09-01 00:00",
        end_time="2023-09-01 23:59",
        regex="Log message",
        host="some-host",
    )
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }
    assert logs[1] == {
        "timestamp": "2023-09-01T00:00:01Z",
        "level": "warning",
        "message": "Log message 2",
    }
    assert logs[2] == {
        "timestamp": "2023-09-01T00:00:02Z",
        "level": "error",
        "message": "Log message 3",
    }


@responses.activate
def test_get_error_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002)
    logs = list(logs)

    assert len(logs) == 0


@responses.activate
def test_get_access_logs(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.ACCESS)
    logs = list(logs)

    assert len(logs) == 2
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }


@responses.activate
def test_get_access_logs_with_search_params(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        log_type=LogType.ACCESS,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request",
    )
    logs = list(logs)

    assert len(logs) == 2
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }


@responses.activate
def test_get_access_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.non_error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.ACCESS)
    logs = list(logs)

    assert len(logs) == 0


@responses.activate
def test_get_request_logs(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.REQUEST)
    logs = list(logs)

    assert len(logs) == 2
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }


@responses.activate
def test_get_request_logs_with_search_params(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        log_type=LogType.REQUEST,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request",
    )
    logs = list(logs)

    assert len(logs) == 2
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }


@responses.activate
def test_get_request_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.non_error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.REQUEST)
    logs = list(logs)

    assert len(logs) == 0


@responses.activate
def test_get_audit_logs(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(log_type=LogType.AUDIT)
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }
    assert logs[2] == {
        "message": raw_logs[2],
    }


@responses.activate
def test_get_audit_logs_with_search_params(logs_client):
    raw_logs = [
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
    builder.with_response_body(builder.non_error_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(
        log_type=LogType.AUDIT,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request",
    )
    logs = list(logs)

    assert len(logs) == 3
    assert logs[0] == {
        "message": raw_logs[0],
    }
    assert logs[1] == {
        "message": raw_logs[1],
    }
    assert logs[2] == {
        "message": raw_logs[2],
    }


@responses.activate
def test_get_audit_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "AuditLog.txt")
    builder.with_response_body(builder.non_error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(log_type=LogType.AUDIT)
    logs = list(logs)

    assert len(logs) == 0


@responses.activate
def test_get_logs_list_unauthorized(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(401)
    builder.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    builder.build_get()

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs_list()

    expected_error = "[401 Unauthorized] 401 Unauthorized"
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_list_no_such_host(logs_client):
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "no-such-host.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("host", "non-existing-host")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(404)
    builder.with_response_body(Path(response_body_path).read_bytes())
    builder.build_get()
    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs_list(host="non-existing-host")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHHOST) XDMP-NOSUCHHOST: "
        'xdmp:host("non-existing-host") -- No such host non-existing-host'
    )
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_list_empty(logs_client):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-no-logs.json",
    )
    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_body(response_body_json)
    builder.build_get()

    logs_list = logs_client.get_logs_list()

    assert logs_list == {
        "source": [],
        "parsed": [],
        "grouped": {},
    }


@responses.activate
def test_get_logs_list_from_single_node_cluster(logs_client):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )

    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(response_body_json)
    builder.build_get()

    logs_list = logs_client.get_logs_list()
    assert isinstance(logs_list, dict)

    source = logs_list["source"]
    assert isinstance(source, list)
    assert len(source) == 20

    parsed = logs_list["parsed"]
    assert isinstance(parsed, list)
    assert len(parsed) == 20

    grouped = logs_list["grouped"]
    assert isinstance(grouped, dict)
    assert len(grouped) == 1

    host_grouped = grouped["localhost"]
    assert isinstance(host_grouped, dict)
    assert len(host_grouped) == 4

    assert logs_list == {
        "source": response_body_json["log-default-list"]["list-items"]["list-item"],
        "parsed": [
            {
                "host": "localhost",
                "file-name": "8001_AccessLog.txt",
                "server": "8001",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "8002_AccessLog_1.txt",
                "server": "8002",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "8001_RequestLog.txt",
                "server": "8001",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "8002_RequestLog_1.txt",
                "server": "8002",
                "log-type": LogType.REQUEST,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "8001_ErrorLog.txt",
                "server": "8001",
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "8002_ErrorLog_1.txt",
                "server": "8002",
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_AccessLog.txt",
                "server": "TaskServer",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_AccessLog_1.txt",
                "server": "TaskServer",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_RequestLog.txt",
                "server": "TaskServer",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_RequestLog_1.txt",
                "server": "TaskServer",
                "log-type": LogType.REQUEST,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_ErrorLog.txt",
                "server": "TaskServer",
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "TaskServer_ErrorLog_1.txt",
                "server": "TaskServer",
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "AccessLog.txt",
                "server": None,
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "AccessLog_1.txt",
                "server": None,
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "RequestLog.txt",
                "server": None,
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "RequestLog_1.txt",
                "server": None,
                "log-type": LogType.REQUEST,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "ErrorLog.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "ErrorLog_1.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "localhost",
                "file-name": "AuditLog.txt",
                "server": None,
                "log-type": LogType.AUDIT,
                "days-ago": 0,
            },
            {
                "host": "localhost",
                "file-name": "AuditLog_1.txt",
                "server": None,
                "log-type": LogType.AUDIT,
                "days-ago": 1,
            },
        ],
        "grouped": {
            "localhost": {
                "8001": {
                    LogType.ACCESS: {
                        0: "8001_AccessLog.txt",
                    },
                    LogType.REQUEST: {
                        0: "8001_RequestLog.txt",
                    },
                    LogType.ERROR: {
                        0: "8001_ErrorLog.txt",
                    },
                },
                "8002": {
                    LogType.ACCESS: {
                        1: "8002_AccessLog_1.txt",
                    },
                    LogType.REQUEST: {
                        1: "8002_RequestLog_1.txt",
                    },
                    LogType.ERROR: {
                        1: "8002_ErrorLog_1.txt",
                    },
                },
                "TaskServer": {
                    LogType.ACCESS: {
                        0: "TaskServer_AccessLog.txt",
                        1: "TaskServer_AccessLog_1.txt",
                    },
                    LogType.REQUEST: {
                        0: "TaskServer_RequestLog.txt",
                        1: "TaskServer_RequestLog_1.txt",
                    },
                    LogType.ERROR: {
                        0: "TaskServer_ErrorLog.txt",
                        1: "TaskServer_ErrorLog_1.txt",
                    },
                },
                None: {
                    LogType.ACCESS: {
                        0: "AccessLog.txt",
                        1: "AccessLog_1.txt",
                    },
                    LogType.REQUEST: {
                        0: "RequestLog.txt",
                        1: "RequestLog_1.txt",
                    },
                    LogType.ERROR: {
                        0: "ErrorLog.txt",
                        1: "ErrorLog_1.txt",
                    },
                    LogType.AUDIT: {
                        0: "AuditLog.txt",
                        1: "AuditLog_1.txt",
                    },
                },
            },
        },
    }


@responses.activate
def test_get_logs_list_from_multiple_nodes_cluster(logs_client):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-cluster.json",
    )

    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(response_body_json)
    builder.build_get()

    logs_list = logs_client.get_logs_list()
    assert isinstance(logs_list, dict)

    source = logs_list["source"]
    assert isinstance(source, list)
    assert len(source) == 18

    parsed = logs_list["parsed"]
    assert isinstance(parsed, list)
    assert len(parsed) == 18

    grouped = logs_list["grouped"]
    assert isinstance(grouped, dict)
    assert len(grouped) == 3

    host1_grouped = grouped["ml_cluster_node1"]
    assert isinstance(host1_grouped, dict)
    assert len(host1_grouped) == 4

    host2_grouped = grouped["ml_cluster_node2"]
    assert isinstance(host2_grouped, dict)
    assert len(host2_grouped) == 4

    host3_grouped = grouped["ml_cluster_node3"]
    assert isinstance(host3_grouped, dict)
    assert len(host3_grouped) == 4

    assert logs_list == {
        "source": response_body_json["log-default-list"]["list-items"]["list-item"],
        "parsed": [
            {
                "host": "ml_cluster_node3",
                "file-name": "8000_AccessLog.txt",
                "server": "8000",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8001_AccessLog_1.txt",
                "server": "8001",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8002_AccessLog.txt",
                "server": "8002",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8002_RequestLog.txt",
                "server": "8002",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "ErrorLog_1.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "ErrorLog.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "8000_AccessLog.txt",
                "server": "8000",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "8001_AccessLog_1.txt",
                "server": "8001",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "8002_AccessLog.txt",
                "server": "8002",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "8002_RequestLog.txt",
                "server": "8002",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "ErrorLog_1.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node2",
                "file-name": "ErrorLog.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "8000_AccessLog.txt",
                "server": "8000",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "8001_AccessLog_1.txt",
                "server": "8001",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "8002_AccessLog.txt",
                "server": "8002",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "8002_RequestLog.txt",
                "server": "8002",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "ErrorLog_1.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node1",
                "file-name": "ErrorLog.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
        ],
        "grouped": {
            "ml_cluster_node1": {
                "8000": {
                    LogType.ACCESS: {
                        0: "8000_AccessLog.txt",
                    },
                },
                "8001": {
                    LogType.ACCESS: {
                        1: "8001_AccessLog_1.txt",
                    },
                },
                "8002": {
                    LogType.ACCESS: {
                        0: "8002_AccessLog.txt",
                    },
                    LogType.REQUEST: {
                        0: "8002_RequestLog.txt",
                    },
                },
                None: {
                    LogType.ERROR: {
                        0: "ErrorLog.txt",
                        1: "ErrorLog_1.txt",
                    },
                },
            },
            "ml_cluster_node2": {
                "8000": {
                    LogType.ACCESS: {
                        0: "8000_AccessLog.txt",
                    },
                },
                "8001": {
                    LogType.ACCESS: {
                        1: "8001_AccessLog_1.txt",
                    },
                },
                "8002": {
                    LogType.ACCESS: {
                        0: "8002_AccessLog.txt",
                    },
                    LogType.REQUEST: {
                        0: "8002_RequestLog.txt",
                    },
                },
                None: {
                    LogType.ERROR: {
                        0: "ErrorLog.txt",
                        1: "ErrorLog_1.txt",
                    },
                },
            },
            "ml_cluster_node3": {
                "8000": {
                    LogType.ACCESS: {
                        0: "8000_AccessLog.txt",
                    },
                },
                "8001": {
                    LogType.ACCESS: {
                        1: "8001_AccessLog_1.txt",
                    },
                },
                "8002": {
                    LogType.ACCESS: {
                        0: "8002_AccessLog.txt",
                    },
                    LogType.REQUEST: {
                        0: "8002_RequestLog.txt",
                    },
                },
                None: {
                    LogType.ERROR: {
                        0: "ErrorLog.txt",
                        1: "ErrorLog_1.txt",
                    },
                },
            },
        },
    }


@responses.activate
def test_get_logs_list_from_multiple_nodes_cluster_for_single_host(logs_client):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-cluster-one-node-only.json",
    )

    builder = MLResponseBuilder()
    builder.with_base_url(f"http://localhost:8002{ENDPOINT}")
    builder.with_request_param("format", "json")
    builder.with_request_param("host", "ml_cluster_node3")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(response_body_json)
    builder.build_get()

    logs_list = logs_client.get_logs_list(host="ml_cluster_node3")
    assert isinstance(logs_list, dict)

    source = logs_list["source"]
    assert isinstance(source, list)
    assert len(source) == 6

    parsed = logs_list["parsed"]
    assert isinstance(parsed, list)
    assert len(parsed) == 6

    grouped = logs_list["grouped"]
    assert isinstance(grouped, dict)
    assert len(grouped) == 1

    host_grouped = grouped["ml_cluster_node3"]
    assert isinstance(host_grouped, dict)
    assert len(host_grouped) == 4

    assert logs_list == {
        "source": response_body_json["log-default-list"]["list-items"]["list-item"],
        "parsed": [
            {
                "host": "ml_cluster_node3",
                "file-name": "8000_AccessLog.txt",
                "server": "8000",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8001_AccessLog_1.txt",
                "server": "8001",
                "log-type": LogType.ACCESS,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8002_AccessLog.txt",
                "server": "8002",
                "log-type": LogType.ACCESS,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "8002_RequestLog.txt",
                "server": "8002",
                "log-type": LogType.REQUEST,
                "days-ago": 0,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "ErrorLog_1.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 1,
            },
            {
                "host": "ml_cluster_node3",
                "file-name": "ErrorLog.txt",
                "server": None,
                "log-type": LogType.ERROR,
                "days-ago": 0,
            },
        ],
        "grouped": {
            "ml_cluster_node3": {
                "8000": {
                    LogType.ACCESS: {
                        0: "8000_AccessLog.txt",
                    },
                },
                "8001": {
                    LogType.ACCESS: {
                        1: "8001_AccessLog_1.txt",
                    },
                },
                "8002": {
                    LogType.ACCESS: {
                        0: "8002_AccessLog.txt",
                    },
                    LogType.REQUEST: {
                        0: "8002_RequestLog.txt",
                    },
                },
                None: {
                    LogType.ERROR: {
                        0: "ErrorLog.txt",
                        1: "ErrorLog_1.txt",
                    },
                },
            },
        },
    }
