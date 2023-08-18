from __future__ import annotations

import os
from pathlib import Path

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

