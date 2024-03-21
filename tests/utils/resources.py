from __future__ import annotations

import json
import os
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve()
_RESOURCES_DIR = "resources"
_COMMON_RESOURCES_DIR = "common"
TESTS_PATH = Path(_SCRIPT_DIR).parent.parent
RESOURCES_PATH = next(TESTS_PATH.glob(_RESOURCES_DIR))
COMMON_RESOURCES_PATH = next(RESOURCES_PATH.glob(_COMMON_RESOURCES_DIR))


def list_resources(
    test_path: str,
) -> list[str]:
    test_resources_path = get_test_resources_path(test_path)
    return os.listdir(test_resources_path)


def get_test_resource_json(
    test_path: str,
    resource: str,
) -> dict:
    test_resource_path = get_test_resource_path(test_path, resource)
    with Path(test_resource_path).open() as file:
        return json.load(file)


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
    tests_path = TESTS_PATH.as_posix()
    resources_rel_path = test_path.replace(tests_path, "")[1:-3]
    resources_rel_path = resources_rel_path.replace("_", "-")
    return next(Path(RESOURCES_PATH).glob(resources_rel_path)).as_posix()
