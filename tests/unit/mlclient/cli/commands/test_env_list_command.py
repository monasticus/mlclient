from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication


@pytest.fixture(autouse=True)
def _work_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env list"))


def _write_env(directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"mlclient-{name}.yaml"
    path.write_text(yaml.safe_dump({"host": f"{name}.example.com"}))


def test_lists_environment_names_sorted() -> None:
    _write_env(Path.cwd() / ".mlclient", "local")
    _write_env(Path.cwd() / ".mlclient", "dev")

    tester = _get_tester()
    tester.execute("")

    assert tester.status_code == 0
    assert tester.io.fetch_output() == "dev\nlocal\n"


def test_ignores_files_that_are_not_environments() -> None:
    directory = Path.cwd() / ".mlclient"
    _write_env(directory, "dev")
    (directory / "notes.yaml").write_text("host: x\n")

    tester = _get_tester()
    tester.execute("")

    assert tester.io.fetch_output() == "dev\n"


def test_reports_no_environments_when_directory_empty() -> None:
    tester = _get_tester()
    tester.execute("")

    directory = Path.cwd() / ".mlclient"
    assert tester.status_code == 0
    assert tester.io.fetch_output() == f"No environments found in {directory}\n"


def test_names_ancestor_directory_it_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    ancestor_dir = Path.cwd() / ".mlclient"
    _write_env(ancestor_dir, "dev")
    nested = Path.cwd() / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("")

    assert tester.status_code == 0
    assert tester.io.fetch_output() == f"Reading {ancestor_dir}\n\ndev\n"


@pytest.mark.parametrize("flag", ["--global", "-g"])
def test_reads_global_directory(
    flag: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    _write_env(home / ".mlclient", "home-env")
    _write_env(Path.cwd() / ".mlclient", "local")
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute(flag)

    assert tester.status_code == 0
    assert tester.io.fetch_output() == "home-env\n"
