from __future__ import annotations

import json

from tests.utils.ml_mockers import MLRespXMocker

CLUSTER_STATUS_URL = "http://localhost:8002/manage/v2?view=healthcheck&format=json"

HEALTHY_CLUSTER_STATUS = {
    "clusterId": "1111111111111111111",
    "hostId": "2222222222222222222",
    "serverInitializing": False,
    "serverRestarting": False,
    "serverShutdown": False,
    "quorumExists": True,
    "serverHealthStatus": [{"serverId": "3333333333333333333", "healthy": True}],
    "backgroundHealthStatus": [{"backgroundName": "XDQP Server", "healthy": True}],
    "databaseHealthStatus": [{"databaseId": "4444444444444444444", "healthy": "true"}],
}


def mock_cluster_eval(hosts: dict[str, bool]):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body_part("map", json.dumps(hosts))
    return ml_mocker.mock_post()


def mock_forbidden_eval():
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8000/v1/eval")
    ml_mocker.with_response_code(400)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"errorResponse": {"messageCode": "SEC-PRIV"}})
    return ml_mocker.mock_post()


def mock_manage_version(version: str):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/properties")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body({"version": version})
    return ml_mocker.mock_get()


def mock_cluster_status(status: dict | None = None, status_code: int = 200):
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url(CLUSTER_STATUS_URL)
    ml_mocker.with_response_code(status_code)
    ml_mocker.with_response_content_type("application/json")
    ml_mocker.with_response_body(status or HEALTHY_CLUSTER_STATUS)
    return ml_mocker.mock_get()


def unhealthy_cluster_statuses() -> list[dict]:
    flag_changes = [
        {"serverInitializing": True},
        {"serverRestarting": True},
        {"serverShutdown": True},
        {"quorumExists": False},
    ]
    list_changes = [
        {"serverHealthStatus": [{"serverId": "1", "healthy": False}]},
        {"backgroundHealthStatus": [{"backgroundName": "database", "healthy": False}]},
        {"databaseHealthStatus": [{"databaseId": "1", "healthy": "false"}]},
    ]
    return [HEALTHY_CLUSTER_STATUS | change for change in flag_changes + list_changes]
