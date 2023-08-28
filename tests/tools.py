from __future__ import annotations

import os
import shutil
from pathlib import Path
from time import sleep

from mlclient import MLManager, constants

_SCRIPT_DIR = Path(__file__).resolve()
_ML_CLIENT_TESTS_DIR = "mlclient"
_RESOURCES_DIR = "resources"
_COMMON_RESOURCES_DIR = "common"
TESTS_PATH = Path(_SCRIPT_DIR).parent
ML_CLIENT_TESTS_PATH = next(TESTS_PATH.glob(_ML_CLIENT_TESTS_DIR))
RESOURCES_PATH = next(TESTS_PATH.glob(_RESOURCES_DIR))
COMMON_RESOURCES_PATH = next(RESOURCES_PATH.glob(_COMMON_RESOURCES_DIR))


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


def get_common_resource_path(
        resource: str,
) -> str:
    return next(COMMON_RESOURCES_PATH.glob(resource)).as_posix()


def get_test_resources_path(
        test_path: str,
) -> str:
    mlclient_tests_path = ML_CLIENT_TESTS_PATH.as_posix()
    resources_rel_path = test_path.replace(mlclient_tests_path, "")[1:-3]
    resources_rel_path = resources_rel_path.replace("_", "-")
    return next(Path(RESOURCES_PATH).glob(resources_rel_path)).as_posix()


class TestHelper:

    def __init__(
            self,
            environment_name: str,
    ):
        self._environment = environment_name
        self._ml_manager = None

    def setup_environment(
            self,
    ):
        ml_client_dir = Path(constants.ML_CLIENT_DIR)
        if not ml_client_dir.exists() or not ml_client_dir.is_dir():
            ml_client_dir.mkdir()
        env_path = get_common_resource_path(f"mlclient-{self._environment}.yaml")
        shutil.copy(env_path, constants.ML_CLIENT_DIR)

        self._ml_manager = MLManager(self._environment)

    def clean_environment(
            self,
    ):
        Path(f"{constants.ML_CLIENT_DIR}/mlclient-{self._environment}.yaml").unlink()
        ml_client_dir = Path(constants.ML_CLIENT_DIR)
        if ml_client_dir.exists() and not os.listdir(constants.ML_CLIENT_DIR):
            ml_client_dir.rmdir()
        self._ml_manager = None

    def confirm_last_request(
        self,
        app_server: str,
        request_method: str,
        request_url: str,
    ):
        sleep(1)
        with self._ml_manager.get_resources_client(app_server) as client:
            filename = f"{client.port}_AccessLog.txt"
            resp = client.get_logs(filename=filename, data_format="json")
            logfile = resp.json()["logfile"]
            logs = [log
                    for log in logfile["message"].split("\n")
                    if log != "" and f"- {client.username} " not in log]
            assert f"{request_method.upper()} {request_url} HTTP/1.1" in logs[-1]

