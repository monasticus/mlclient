import pytest

from mlclient import MLResourcesClient
from mlclient.clients import LogsClient, LogType
from tests import tools


@pytest.fixture(scope="module", autouse=True)
def _setup():
    with MLResourcesClient(auth_method="digest") as client:
        for i in range(10):
            client.eval(xquery=f'xdmp:log("Test request {i+1}", "ERROR")')

    return


def test_get_error_logs():
    with LogsClient(auth_method="digest") as client:
        logs = client.get_logs(8002)

        _confirm_last_request({
            "format": "json",
            "filename": "8002_ErrorLog.txt",
        })
        log = next(logs)
        assert "message" in log
        assert "timestamp" in log
        assert "level" in log


def test_get_logs_access_logs():
    with LogsClient(auth_method="digest") as client:
        logs = client.get_logs(8002, log_type=LogType.ACCESS)

        _confirm_last_request({
            "format": "json",
            "filename": "8002_AccessLog.txt",
        })
        log = next(logs)
        assert "message" in log
        assert "timestamp" not in log
        assert "level" not in log


def test_get_logs_request_logs():
    with LogsClient(auth_method="digest") as client:
        logs = client.get_logs(8002, log_type=LogType.REQUEST)

        _confirm_last_request({
            "format": "json",
            "filename": "8002_RequestLog.txt",
        })
        log = next(logs)
        assert "message" in log
        assert "timestamp" not in log
        assert "level" not in log


def _confirm_last_request(
        request_params: dict,
):
    request_url = f"/manage/v2/logs?{'&'.join('='.join([key, val]) for key, val in request_params.items())}"
    tools.confirm_last_request(
        environment="local",
        app_server="manage",
        request_method="GET",
        request_url=request_url)
