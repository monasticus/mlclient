from __future__ import annotations

import pytest
import responses

from mlclient.clients import LogsClient, LogType
from mlclient.exceptions import MarkLogicError
from tests.tools import MLResponseBuilder


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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("host", "non-existing-host")
    builder.with_response_body({
        "errorResponse": {
            "statusCode": "404",
            "status": "Not Found",
            "messageCode": "XDMP-NOSUCHHOST",
            "message": 'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                       '-- No such host non-existing-host',
        },
    })
    builder.build_get()

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs(
            8002,
            host="non-existing-host")

    expected_error = ('[404 Not Found] (XDMP-NOSUCHHOST) '
                      'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                      '-- No such host non-existing-host')
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_unauthorized(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_content_type("application/json; charset=utf-8")
    builder.with_response_status(401)
    builder.with_response_body({
        "errorResponse": {
            "statusCode": 401,
            "status": "Unauthorized",
            "message": "401 Unauthorized",
        },
    })
    builder.build_get()

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs()

    expected_error = "[401 Unauthorized] 401 Unauthorized"
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_empty(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002)

    assert next(logs, None) is None


@responses.activate
def test_get_logs_without_port(logs_client):
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "ErrorLog.txt")
    builder.with_response_content_type("application/json; charset=UTF-8")
    builder.with_response_header("Content-type", "application/json; charset=UTF-8")
    builder.with_response_status(200)
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "TaskServer_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "TaskServer_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("start", "2023-09-01T00:00:00")
    builder.with_request_param("end", "2023-09-01T23:59:00")
    builder.with_request_param("regex", "Log message")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        start_time="2023-09-01 00:00",
        end_time="2023-09-01 23:59",
        regex="Log message")
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_ErrorLog.txt")
    builder.with_request_param("host", "some-host")
    builder.with_request_param("start", "2023-09-01T00:00:00")
    builder.with_request_param("end", "2023-09-01T23:59:00")
    builder.with_request_param("regex", "Log message")
    builder.with_response_body(builder.error_logs_body([
        ("2023-09-01T00:00:00Z", "info", "Log message 1"),
        ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
        ("2023-09-01T00:00:02Z", "error", "Log message 3"),
    ]))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        start_time="2023-09-01 00:00",
        end_time="2023-09-01 23:59",
        regex="Log message",
        host="some-host")
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
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
        ('172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_AccessLog.txt HTTP/1.1" '
         '200 454 - "python-requests/2.31.0"'),
        ('172.17.0.1 - - [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_ErrorLog.txt HTTP/1.1" '
         '401 104 - "python-requests/2.31.0"'),
    ]
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body(raw_logs))
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
        ('172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_AccessLog.txt HTTP/1.1" '
         '200 454 - "python-requests/2.31.0"'),
        ('172.17.0.1 - - [01/Sep/2023:03:54:16 +0000] '
         '"GET /manage/v2/logs?format=json&filename=8002_ErrorLog.txt HTTP/1.1" '
         '401 104 - "python-requests/2.31.0"'),
    ]
    builder = MLResponseBuilder()
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        log_type=LogType.ACCESS,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request")
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_AccessLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.ACCESS)
    logs = list(logs)

    assert len(logs) == 0


@responses.activate
def test_get_request_logs(logs_client):
    raw_logs = [
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
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body(raw_logs))
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
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body(raw_logs))
    builder.build_get()

    logs = logs_client.get_logs(
        8002,
        log_type=LogType.REQUEST,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request")
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
    builder.with_base_url("http://localhost:8002/manage/v2/logs")
    builder.with_request_param("format", "json")
    builder.with_request_param("filename", "8002_RequestLog.txt")
    builder.with_response_body(builder.access_or_request_logs_body([]))
    builder.build_get()

    logs = logs_client.get_logs(8002, log_type=LogType.REQUEST)
    logs = list(logs)

    assert len(logs) == 0
