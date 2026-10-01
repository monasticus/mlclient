from __future__ import annotations

import builtins
import json
import runpy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

from tests.utils.resources import get_test_resources_path


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
