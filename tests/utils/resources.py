from __future__ import annotations

import builtins
import inspect
import itertools
import json
import runpy
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass
from pathlib import Path
from typing import cast

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
class QueryCase:
    name: str
    directory: Path
    parameter_indices: tuple[int, ...]

    def assert_matches(self, request=None) -> None:
        namespace = runpy.run_path(
            str(self.directory / "case.py"),
        )
        run = namespace["run"]
        parameters = {}
        marks = [
            mark
            for mark in getattr(run, "pytestmark", [])
            if mark.name == "parametrize"
        ]
        for mark, index in zip(marks, self.parameter_indices, strict=True):
            names = mark.args[0]
            names = names.split(",") if isinstance(names, str) else names
            selected = mark.args[1][index]
            values = (
                selected.values
                if hasattr(selected, "marks") and hasattr(selected, "values")
                else ((selected,) if len(names) == 1 else selected)
            )
            parameters.update(
                zip((name.strip() for name in names), values, strict=True),
            )
        for name in inspect.signature(run).parameters:
            if name not in parameters:
                parameters[name] = request.getfixturevalue(name)
        run(**parameters)


def discover_query_cases(test_path: str) -> list[QueryCase]:
    resources = Path(get_test_resources_path(test_path))
    cases = []
    for path in sorted(resources.iterdir()):
        if not path.is_dir() or not (path / "case.py").is_file():
            continue
        namespace = runpy.run_path(str(path / "case.py"))
        run = namespace.get("run")
        if not callable(run):
            message = f"{path}/case.py must define run()"
            raise TypeError(message)
        marks = [
            mark
            for mark in getattr(run, "pytestmark", [])
            if mark.name == "parametrize"
        ]
        for indices in itertools.product(*(range(len(mark.args[1])) for mark in marks)):
            suffix = "-".join(map(str, indices))
            cases.append(
                QueryCase(
                    f"{path.name}-{suffix}" if suffix else path.name,
                    path,
                    indices,
                ),
            )
    if not cases:
        message = f"No query cases in {resources}"
        raise ValueError(message)
    return cases


def render_test_resource(test_path: str, name: str, /, **fragments: str) -> str:
    """Insert test-owned fragments, preserving XQuery braces and variables."""
    source = read_test_resource_text(test_path, name)
    placeholders = set(re.findall(r"@@(\w+)@@", source))
    if placeholders != fragments.keys():
        message = f"Expected fragments {sorted(placeholders)}, got {sorted(fragments)}"
        raise ValueError(message)
    return re.sub(r"@@(\w+)@@", lambda match: fragments[match[1]], source)


def read_query_expectation(case_path: str, name: str):
    path = Path(case_path).parent / name
    return _read_json(path) if path.suffix == ".json" else path.read_text()


def read_query_input(test_path: str, name: str):
    return runpy.run_path(get_test_resource_path(test_path, name))["build"]()
