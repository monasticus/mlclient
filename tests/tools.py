from __future__ import annotations

import os
from pathlib import Path
from time import sleep

from mlclient import MLManager

_SCRIPT_DIR = Path(__file__).resolve()
_ML_CLIENT_TESTS_DIR = "mlclient"
_RESOURCES_DIR = "resources"
TESTS_PATH = Path(_SCRIPT_DIR).parent
ML_CLIENT_TESTS_PATH = next(TESTS_PATH.glob(_ML_CLIENT_TESTS_DIR))
RESOURCES_PATH = next(TESTS_PATH.glob(_RESOURCES_DIR))


def list_resources(
        test_path: str,
) -> list[str]:
    test_resources_path = get_test_resources_path(test_path)
    return os.listdir(test_resources_path)


def get_test_resource_path(
        test_path: str,
        resource: str,
) -> str:
    test_resources_path = get_test_resources_path(test_path)
    return next(Path(test_resources_path).glob(resource)).as_posix()


def get_test_resources_path(
        test_path: str,
) -> str:
    mlclient_tests_path = ML_CLIENT_TESTS_PATH.as_posix()
    resources_rel_path = test_path.replace(mlclient_tests_path, "")[1:-3]
    resources_rel_path = resources_rel_path.replace("_", "-")
    return next(Path(RESOURCES_PATH).glob(resources_rel_path)).as_posix()


def confirm_last_request(
        environment: str,
        app_server: str,
        request_method: str,
        request_url: str,
):
    """Verifies the last request being sent.

    This function reaches access logs and extracts last request of the app server.
    Every request generates two logs and one of them includes username.
    We filter out redundant logs to get a single log per request.
    """
    sleep(1)
    with MLManager(environment).get_resources_client(app_server) as client:
        filename = f"{client.port}_AccessLog.txt"
        resp = client.get_logs(filename=filename, data_format="json")
        logfile = resp.json()["logfile"]
        logs = [log
                for log in logfile["message"].split("\n")
                if log != "" and f"- {client.username} " not in log]
        assert f"{request_method.upper()} {request_url} HTTP/1.1" in logs[-1]

