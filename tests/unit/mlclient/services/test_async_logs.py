from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
import respx

from mlclient.clients.api_client import AsyncApiClient
from mlclient.clients.http_client import AsyncHttpClient
from mlclient.exceptions import MarkLogicError
from mlclient.services.logs import AsyncLogsService, LogType
from tests.utils import resources as resources_utils
from tests.utils.ml_mockers import MLRespXMocker

ENDPOINT = "/manage/v2/logs"


@pytest_asyncio.fixture
async def svc():
    async with AsyncHttpClient(auth_method="digest") as http:
        yield AsyncLogsService(AsyncApiClient(http))


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_no_such_host(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("host", "non-existing-host")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
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
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError) as err:
        await svc.get(8002, host="non-existing-host")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHHOST) "
        'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
        "-- No such host non-existing-host"
    )
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_unauthorized(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "ErrorLog.txt")
    ml_mocker.with_response_code(401)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError) as err:
        await svc.get()

    expected_error = "[401 Unauthorized] 401 Unauthorized"
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_empty(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.error_logs_body([]))
    ml_mocker.mock_get()

    logs = await svc.get(8002)

    assert next(logs, None) is None


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_without_port(svc):
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
                ("2023-09-01T00:00:01Z", "warning", "Log message 2"),
                ("2023-09-01T00:00:02Z", "error", "Log message 3"),
            ],
        ),
    )
    ml_mocker.mock_get()

    logs = await svc.get()
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


@pytest.mark.asyncio
@respx.mock
async def test_get_task_server_logs(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "TaskServer_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ],
        ),
    )
    ml_mocker.mock_get()

    logs = await svc.get("TaskServer")
    logs = list(logs)

    assert len(logs) == 1
    assert logs[0] == {
        "timestamp": "2023-09-01T00:00:00Z",
        "level": "info",
        "message": "Log message 1",
    }


@pytest.mark.asyncio
@respx.mock
async def test_get_task_server_logs_using_int_port(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "TaskServer_ErrorLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ],
        ),
    )
    ml_mocker.mock_get()

    logs = await svc.get(0)
    logs = list(logs)

    assert len(logs) == 1


@pytest.mark.asyncio
@respx.mock
async def test_get_error_logs_with_search_params(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_ErrorLog.txt")
    ml_mocker.with_request_param("start", "2023-09-01T00:00:00")
    ml_mocker.with_request_param("end", "2023-09-01T23:59:00")
    ml_mocker.with_request_param("regex", "Log message")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        ml_mocker.error_logs_body(
            [
                ("2023-09-01T00:00:00Z", "info", "Log message 1"),
            ],
        ),
    )
    ml_mocker.mock_get()

    logs = await svc.get(
        8002,
        start_time="2023-09-01 00:00",
        end_time="2023-09-01 23:59",
        regex="Log message",
    )
    logs = list(logs)

    assert len(logs) == 1


@pytest.mark.asyncio
@respx.mock
async def test_get_access_logs(svc):
    raw_logs = [
        (
            "172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] "
            '"GET /manage/v2/logs HTTP/1.1" '
            '200 454 - "python-requests/2.31.0"'
        ),
        (
            "172.17.0.1 - - [01/Sep/2023:03:54:16 +0000] "
            '"GET /manage/v2/logs HTTP/1.1" '
            '401 104 - "python-requests/2.31.0"'
        ),
    ]
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_AccessLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(raw_logs))
    ml_mocker.mock_get()

    logs = await svc.get(8002, LogType.ACCESS)
    logs = list(logs)

    assert len(logs) == 2
    assert logs[0] == {"message": raw_logs[0]}
    assert logs[1] == {"message": raw_logs[1]}


@pytest.mark.asyncio
@respx.mock
async def test_get_access_logs_with_str_log_type(svc):
    raw_logs = [
        (
            "172.17.0.1 - admin [01/Sep/2023:03:54:16 +0000] "
            '"GET /manage/v2/logs HTTP/1.1" '
            '200 454 - "python-requests/2.31.0"'
        ),
    ]
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_AccessLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(raw_logs))
    ml_mocker.mock_get()

    logs = await svc.get(8002, "access")
    logs = list(logs)

    assert len(logs) == 1
    assert logs[0] == {"message": raw_logs[0]}


@pytest.mark.asyncio
@respx.mock
async def test_get_access_logs_empty(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_AccessLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body([]))
    ml_mocker.mock_get()

    logs = await svc.get(8002, LogType.ACCESS)
    logs = list(logs)

    assert len(logs) == 0


@pytest.mark.asyncio
@respx.mock
async def test_get_request_logs(svc):
    raw_logs = ['{"time":"2023-09-04T03:53:40Z", "url":"/manage/v2/logs"}']
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "8002_RequestLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(raw_logs))
    ml_mocker.mock_get()

    logs = await svc.get(8002, LogType.REQUEST)
    logs = list(logs)

    assert len(logs) == 1
    assert logs[0] == {"message": raw_logs[0]}


@pytest.mark.asyncio
@respx.mock
async def test_get_audit_logs(svc):
    raw_logs = [
        "2023-09-04 01:01:01.111 event=server-restart; success=true;",
    ]
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("filename", "AuditLog.txt")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(ml_mocker.non_error_logs_body(raw_logs))
    ml_mocker.mock_get()

    logs = await svc.get(log_type=LogType.AUDIT)
    logs = list(logs)

    assert len(logs) == 1
    assert logs[0] == {"message": raw_logs[0]}


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_list_unauthorized(svc):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(401)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(
        {
            "errorResponse": {
                "statusCode": 401,
                "status": "Unauthorized",
                "message": "401 Unauthorized",
            },
        },
    )
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError) as err:
        await svc.list()

    expected_error = "[401 Unauthorized] 401 Unauthorized"
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_list_no_such_host(svc):
    response_body_path = resources_utils.get_test_resource_path(
        __file__,
        "no-such-host.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/logs")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("host", "non-existing-host")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(404)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(Path(response_body_path).read_bytes())
    ml_mocker.mock_get()

    with pytest.raises(MarkLogicError) as err:
        await svc.list(host="non-existing-host")

    expected_error = (
        "[404 Not Found] (XDMP-NOSUCHHOST) XDMP-NOSUCHHOST: "
        'xdmp:host("non-existing-host") -- No such host non-existing-host'
    )
    assert err.value.args[0] == expected_error


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_list_empty(svc):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-no-logs.json",
    )
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(response_body_json)
    ml_mocker.mock_get()

    logs_list = await svc.list()

    assert logs_list == {
        "source": [],
        "parsed": [],
        "grouped": {},
    }


@pytest.mark.asyncio
@respx.mock
async def test_get_logs_list_from_single_node_cluster(svc):
    response_body_json = resources_utils.get_test_resource_json(
        __file__,
        "logs-list-response-single-node.json",
    )

    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(f"http://localhost:8002{ENDPOINT}")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json; charset=UTF-8")
    ml_mocker.with_response_body(response_body_json)
    ml_mocker.mock_get()

    logs_list = await svc.list()
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
