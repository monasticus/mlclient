from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError


@pytest.fixture(autouse=True)
def _work_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env remove"))


def _write_env(name: str, config: dict, *, directory: Path | None = None) -> Path:
    directory = directory or Path.cwd() / ".mlclient"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"mlclient-{name}.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


# --- confirmation ---


def test_removes_after_confirmation() -> None:
    path = _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev", inputs="y\n")

    assert tester.status_code == 0
    assert not path.exists()
    assert "Removed" in tester.io.fetch_output()


def test_keeps_file_when_declined() -> None:
    path = _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev", inputs="n\n")

    assert tester.status_code == 0
    assert path.exists()
    assert "Aborted." in tester.io.fetch_output()


def test_declines_by_default_on_empty_answer() -> None:
    path = _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev", inputs="\n")

    assert path.exists()
    assert "Aborted." in tester.io.fetch_output()


def test_force_removes_without_prompt() -> None:
    path = _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev --force")

    assert tester.status_code == 0
    assert not path.exists()
    assert "Removed" in tester.io.fetch_output()


# --- directory resolution (consistent with env show) ---


def test_removes_from_ancestor_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _write_env("dev", {"host": "dev.example.com"})
    nested = Path.cwd() / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("dev --force")

    assert not path.exists()


def test_removes_from_global_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    path = _write_env("dev", {"host": "home.example.com"}, directory=home / ".mlclient")
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("dev --global --force")

    assert not path.exists()


# --- missing environment ---


def test_errors_when_environment_missing() -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("nope --force")

    assert "No environment [nope]" in str(error.value)
    assert "Available: dev" in str(error.value)


def test_errors_when_no_mlclient_directory() -> None:
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("dev --force")

    assert "No environment [dev]" in str(error.value)
