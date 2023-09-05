from __future__ import annotations

import urllib.parse

import pytest
import responses

from mlclient.clients import LogsClient, LogType
from mlclient.exceptions import MarkLogicError


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
    _setup_error_response(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "host": "non-existing-host",
        },
        {
            "errorResponse": {
                "statusCode": "404",
                "status": "Not Found",
                "messageCode": "XDMP-NOSUCHHOST",
                "message": 'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                           '-- No such host non-existing-host',
            },
        })

    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs(
            8002,
            host="non-existing-host")

    expected_error = ('[404 Not Found] (XDMP-NOSUCHHOST) '
                      'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                      '-- No such host non-existing-host')
    assert err.value.args[0] == expected_error


@responses.activate
def test_get_logs_empty(logs_client):
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [])

    logs = logs_client.get_logs(8002)

    assert next(logs, None) is None


@responses.activate
def test_get_logs_using_string_port(logs_client):
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
    _setup_responses(
        {
            "format": "json",
            "filename": "TaskServer_ErrorLog.txt",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
    _setup_responses(
        {
            "format": "json",
            "filename": "TaskServer_ErrorLog.txt",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "start": "2023-09-01T00:00:00",
            "end": "2023-09-01T23:59:00",
            "regex": "Log message",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_ErrorLog.txt",
            "host": "some-host",
            "start": "2023-09-01T00:00:00",
            "end": "2023-09-01T23:59:00",
            "regex": "Log message",
        },
        [
            ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
            ("2023-09-01T00:00:02Z", "error", "Log message 3"),
        ])

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
def test_get_access_logs(logs_client):
    raw_logs = [
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
        raw_logs,
        False)

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_AccessLog.txt",
        },
        raw_logs,
        False)

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_RequestLog.txt",
        },
        raw_logs,
        False)

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
    _setup_responses(
        {
            "format": "json",
            "filename": "8002_RequestLog.txt",
        },
        raw_logs,
        False)

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


def _setup_error_response(
        request_params: dict,
        response_body: dict,
):
    params = urllib.parse.urlencode(request_params).replace("%2B", "+")
    request_url = f"http://localhost:8002/manage/v2/logs?{params}"

    responses.get(
        request_url,
        json=response_body,
    )
