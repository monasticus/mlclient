from __future__ import annotations

import builtins
import json
import runpy
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from xml.etree.ElementTree import tostring

import pytest

_SCRIPT_DIR = Path(__file__).resolve()
_RESOURCES_DIR = "resources"
_COMMON_RESOURCES_DIR = "common"
TESTS_PATH = Path(_SCRIPT_DIR).parent.parent
RESOURCES_PATH = next(TESTS_PATH.glob(_RESOURCES_DIR))


def get_test_resources(
    test_path: str,
) -> dict:
    resources = {}
    for resource in list_resources(test_path):
        abs_path = get_test_resource_path(test_path, resource)
        resources[resource] = {
            "abs_path": abs_path,
            "bytes": Path(abs_path).read_bytes(),
            "str": Path(abs_path).read_text(),
        }
        if abs_path.endswith(".json"):
            resources[resource]["json"] = get_test_resource_json(test_path, resource)
    return resources


def list_resources(
    test_path: str,
) -> Generator[str]:
    test_resources_path = get_test_resources_path(test_path)
    return (
        str(p.relative_to(test_resources_path))
        for p in Path(test_resources_path).iterdir()
    )


def get_test_resource_json(
    test_path: str,
    resource: str,
) -> dict:
    test_resource_path = get_test_resource_path(test_path, resource)
    with Path(test_resource_path).open() as file:
        return json.load(file)


def read_test_resource_bytes(
    test_path: str,
    resource: str,
) -> bytes:
    return Path(get_test_resource_path(test_path, resource)).read_bytes()


def read_test_resource_text(
    test_path: str,
    resource: str,
) -> str:
    return Path(get_test_resource_path(test_path, resource)).read_text()


def get_test_resource_path(
    test_path: str,
    resource: str,
) -> str:
    test_resources_path = get_test_resources_path(test_path)
    return next(Path(test_resources_path).glob(resource)).as_posix()


def get_test_resources_path(
    test_path: str,
) -> str:
    tests_path = TESTS_PATH.as_posix()
    resources_rel_path = test_path.replace(tests_path, "")[1:-3]
    resources_rel_path = resources_rel_path.replace("_", "-")
    return next(Path(RESOURCES_PATH).glob(resources_rel_path)).as_posix()


@dataclass(frozen=True)
class XqyCompilationCase:
    name: str
    directory: Path

    def assert_matches(self) -> None:
        namespace = runpy.run_path(str(self.directory / "expression.py"))
        run = namespace.get("run")
        if not callable(run):
            message = f"{self.name}/expression.py must define run()"
            raise TypeError(message)

        error_path = self.directory / "error.json"
        if error_path.is_file():
            _assert_error(run, _read_json(error_path))
            return

        code = (self.directory / "expected.xqy").read_text().removesuffix("\n")
        variables = _read_json(self.directory / "variables.json")
        assert run() == (code, variables)


def discover_xqy_compilation_cases(test_path: str) -> list[XqyCompilationCase]:
    resources = Path(get_test_resources_path(test_path))
    return [
        XqyCompilationCase(path.name, path)
        for path in sorted(resources.iterdir())
        if path.is_dir() and (path / "expression.py").is_file()
    ]


def _assert_error(action: Callable[[], object], expected: dict) -> None:
    error_type = getattr(builtins, expected["type"], None)
    if not isinstance(error_type, type) or not issubclass(error_type, BaseException):
        message = f"unsupported error type: {expected['type']}"
        raise TypeError(message)
    with pytest.raises(cast(type[BaseException], error_type)) as error:
        action()
    assert str(error.value) == expected["message"]


def _read_json(path: Path) -> dict:
    with path.open() as file:
        return json.load(file)


@dataclass(frozen=True)
class SerializationCase:
    name: str
    directory: Path

    def assert_matches(self) -> None:
        namespace = runpy.run_path(str(self.directory / "expression.py"))
        run = namespace["run"]
        error_path = self.directory / "error.json"
        if error_path.is_file():
            _assert_error(run, _read_json(error_path))
            return

        component = run()
        expected_json = _read_json(self.directory / "expected.json")
        expected_xml = (self.directory / "expected.xml").read_text().removesuffix("\n")
        assert component.to_json() == expected_json
        assert tostring(component.to_xml(), encoding="unicode") == expected_xml


def discover_serialization_cases(test_path: str) -> list[SerializationCase]:
    resources = Path(get_test_resources_path(test_path))
    return [
        SerializationCase(path.name, path)
        for path in sorted(resources.iterdir())
        if path.is_dir() and (path / "expression.py").is_file()
    ]


def render_test_resource(test_path: str, name: str, /, **fragments: str) -> str:
    """Insert test-owned fragments, preserving XQuery braces and variables."""
    source = read_test_resource_text(test_path, name)
    placeholders = set(re.findall(r"@@(\w+)@@", source))
    if placeholders != fragments.keys():
        message = f"Expected fragments {sorted(placeholders)}, got {sorted(fragments)}"
        raise ValueError(message)
    return re.sub(r"@@(\w+)@@", lambda match: fragments[match[1]], source)


def read_query_input(test_path: str, name: str):
    return runpy.run_path(get_test_resource_path(test_path, name))["build"]()
