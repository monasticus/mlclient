import datetime
import urllib.parse

import pytest

from mlclient import MLManager, MLResponseParser
from mlclient.clients import LogsClient, LogType
from mlclient.exceptions import MarkLogicError
from tests import tools

test_helper = tools.TestHelper("test")


@pytest.fixture(scope="module", autouse=True)
def _module_setup_and_teardown():
    test_helper.setup_environment()
    with MLManager("test").get_resources_client("manage") as client:
        for i in range(10):
            client.eval(xquery=f'xdmp:log("Test request {i+1}", "error")')

    yield

    test_helper.clean_environment()


@pytest.fixture(autouse=True)
def logs_client() -> LogsClient:
    return LogsClient(auth_method="digest")


@pytest.fixture(autouse=True)
def _setup_and_teardown(logs_client):
    logs_client.connect()

    yield

    logs_client.disconnect()


@pytest.mark.ml_access()
def test_get_logs_no_such_host(logs_client):
    with pytest.raises(MarkLogicError) as err:
        logs_client.get_logs(
            8002,
            host="non-existing-host")
    expected_error = ('[404 Not Found] (XDMP-NOSUCHHOST) '
                      'XDMP-NOSUCHHOST: xdmp:host("non-existing-host") '
                      '-- No such host non-existing-host')
    assert err.value.args[0] == expected_error


@pytest.mark.ml_access()
def test_get_logs_empty(logs_client):
    logs = logs_client.get_logs(8002, regex="non-existing-log-line")

    _confirm_last_request({
        "format": "json",
        "filename": "8002_ErrorLog.txt",
        "regex": "non-existing-log-line",
    })
    assert next(logs, None) is None


@pytest.mark.ml_access()
def test_get_error_logs(logs_client):
    logs = logs_client.get_logs(8002)

    _confirm_last_request({
        "format": "json",
        "filename": "8002_ErrorLog.txt",
    })
    log = next(logs)
    assert "message" in log
    assert "timestamp" in log
    assert "level" in log


@pytest.mark.ml_access()
def test_get_error_logs_with_search_params(logs_client):
    logs = logs_client.get_logs(
        8002,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request")

    _confirm_last_request({
        "format": "json",
        "filename": "8002_ErrorLog.txt",
        "start": f"{datetime.date.today()}T00:00:00",
        "end": f"{datetime.date.today()}T23:59:59",
        "regex": "Test+request",
    })
    logs = list(logs)
    assert len(logs) % 10 == 0
    log = logs[0]
    assert "message" in log
    assert "timestamp" in log
    assert "level" in log


@pytest.mark.ml_access()
def test_get_error_logs_fully_customized(logs_client):
    with MLManager("test").get_resources_client("manage") as client:
        resp = client.eval(xquery="xdmp:host() => xdmp:host-name()")
        host_name = MLResponseParser.parse(resp)

    logs = logs_client.get_logs(
        8002,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request",
        host=host_name)

    _confirm_last_request({
        "format": "json",
        "filename": "8002_ErrorLog.txt",
        "host": host_name,
        "start": f"{datetime.date.today()}T00:00:00",
        "end": f"{datetime.date.today()}T23:59:59",
        "regex": "Test+request",
    })
    logs = list(logs)
    assert len(logs) % 10 == 0
    log = logs[0]
    assert "message" in log
    assert "timestamp" in log
    assert "level" in log


@pytest.mark.ml_access()
def test_get_access_logs(logs_client):
    logs = logs_client.get_logs(8002, log_type=LogType.ACCESS)

    _confirm_last_request({
        "format": "json",
        "filename": "8002_AccessLog.txt",
    })
    log = next(logs)
    assert "message" in log
    assert "timestamp" not in log
    assert "level" not in log


@pytest.mark.ml_access()
def test_get_access_logs_with_search_params(logs_client):
    logs = logs_client.get_logs(
        8002,
        log_type=LogType.ACCESS,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request")

    _confirm_last_request({
        "format": "json",
        "filename": "8002_AccessLog.txt",
    })
    log = next(logs)
    assert "message" in log
    assert "timestamp" not in log
    assert "level" not in log


@pytest.mark.ml_access()
def test_get_request_logs(logs_client):
    logs = logs_client.get_logs(8002, log_type=LogType.REQUEST)

    _confirm_last_request({
        "format": "json",
        "filename": "8002_RequestLog.txt",
    })
    log = next(logs)
    assert "message" in log
    assert "timestamp" not in log
    assert "level" not in log


@pytest.mark.ml_access()
def test_get_request_logs_with_search_params(logs_client):
    logs = logs_client.get_logs(
        8002,
        log_type=LogType.REQUEST,
        start_time="00:00",
        end_time="23:59:59",
        regex="Test request")

    _confirm_last_request({
        "format": "json",
        "filename": "8002_RequestLog.txt",
    })
    log = next(logs)
    assert "message" in log
    assert "timestamp" not in log
    assert "level" not in log


@pytest.mark.ml_access()
def _confirm_last_request(
        request_params: dict,
):
    params = urllib.parse.urlencode(request_params).replace("%2B", "+")
    request_url = f"/manage/v2/logs?{params}"

    test_helper.confirm_last_request(
        app_server_port=test_helper.config.provide_config("manage")["port"],
        request_method="GET",
        request_url=request_url)
